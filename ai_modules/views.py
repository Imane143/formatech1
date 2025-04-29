from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from .models import UserSkill, TrainingSkill, Recommendation, ChatbotInteraction
from formation.models import Training, Participant
from users.models import User
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

@login_required
def skill_analysis(request):
    """Vue pour l'analyse des compétences"""
    user_skills = UserSkill.objects.filter(user=request.user)
    return render(request, 'ai_modules/skill_analysis.html', {
        'user_skills': user_skills
    })

@login_required
def training_recommendations(request):
    """Vue pour les recommandations de formation"""
    # Récupérer ou générer des recommandations
    recommendations = Recommendation.objects.filter(user=request.user).order_by('-score')[:5]
    
    # Si aucune recommandation n'existe, en générer de nouvelles
    if not recommendations:
        generate_recommendations(request.user)
        recommendations = Recommendation.objects.filter(user=request.user).order_by('-score')[:5]
    
    return render(request, 'ai_modules/training_recommendations.html', {
        'recommendations': recommendations
    })

@login_required
def chatbot_interface(request):
    """Vue pour l'interface du chatbot"""
    recent_interactions = ChatbotInteraction.objects.filter(user=request.user).order_by('-timestamp')[:5]
    return render(request, 'ai_modules/chatbot.html', {
        'recent_interactions': recent_interactions
    })

@login_required
def chatbot_query(request):
    """Endpoint API pour les requêtes du chatbot"""
    if request.method == 'POST':
        data = json.loads(request.body)
        query = data.get('query', '')
        
        # Logique simple de traitement de requête
        response = process_chatbot_query(query, request.user)
        
        # Enregistrer l'interaction
        interaction = ChatbotInteraction(
            user=request.user,
            query=query,
            response=response
        )
        interaction.save()
        
        return JsonResponse({'response': response})
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

@login_required
def user_skills(request, user_id):
    """Vue pour afficher les compétences d'un utilisateur"""
    user = get_object_or_404(User, pk=user_id)
    skills = UserSkill.objects.filter(user=user)
    
    # Si c'est l'utilisateur courant ou un admin qui consulte
    if request.user.id == user_id or request.user.is_staff:
        return render(request, 'ai_modules/user_skills.html', {
            'viewed_user': user,
            'skills': skills
        })
    else:
        messages.error(request, "Vous n'avez pas l'autorisation de voir ces informations.")
        return redirect('formation:training_list')

@login_required
def training_skills(request, training_id):
    """Vue pour afficher les compétences requises pour une formation"""
    training = get_object_or_404(Training, pk=training_id)
    skills = TrainingSkill.objects.filter(training=training)
    
    return render(request, 'ai_modules/training_skills.html', {
        'training': training,
        'skills': skills
    })

# Fonctions utilitaires
def generate_recommendations(user):
    """Génère des recommandations de formation pour un utilisateur avec IA simple"""
    # Supprimer les anciennes recommandations
    Recommendation.objects.filter(user=user).delete()
    
    # Récupérer les compétences de l'utilisateur
    user_skills = UserSkill.objects.filter(user=user)
    user_skill_names = [skill.skill_name.lower() for skill in user_skills]
    
    # Récupérer les formations déjà suivies
    completed_trainings = Training.objects.filter(
        trainingsession__participant__user=user,
        trainingsession__participant__completion_status='COMPLETED'
    )
    completed_ids = [t.id for t in completed_trainings]
    
    # Récupérer toutes les formations
    trainings = Training.objects.all()
    
    # Initialiser dictionnaire pour stocker les formations les plus populaires par domaine
    domain_popularity = {}
    
    # Déterminer la popularité des formations par domaine
    for training in trainings:
        # Extraire le domaine (premier mot du titre)
        domain = training.title.split()[0].lower() if training.title else "general"
        
        # Calculer la popularité
        participant_count = Participant.objects.filter(session__training=training).count()
        
        if domain not in domain_popularity:
            domain_popularity[domain] = []
        
        domain_popularity[domain].append((training.id, participant_count))
    
    # Trier par popularité dans chaque domaine
    for domain in domain_popularity:
        domain_popularity[domain].sort(key=lambda x: x[1], reverse=True)
    
    recommendations = []
    
    for training in trainings:
        # Ne pas recommander les formations déjà suivies
        if training.id in completed_ids:
            continue
        
        # Initialiser le score et les raisons
        score = 0
        match_reason = []
        
        # 1. Score basé sur la correspondance des compétences
        training_skills = TrainingSkill.objects.filter(training=training)
        skill_match = 0
        skill_gap = 0
        
        for training_skill in training_skills:
            skill_name = training_skill.skill_name.lower()
            if skill_name in user_skill_names:
                skill_match += 1
                match_reason.append(f"Vous possédez déjà la compétence: {training_skill.skill_name}")
            else:
                skill_gap += 1
                match_reason.append(f"Vous pourriez acquérir la compétence: {training_skill.skill_name}")
        
        # Calcul du score de compétence (max 2 points)
        if training_skills.count() > 0:
            # Valorise à la fois les compétences correspondantes et les nouvelles
            skill_score = (skill_match * 0.5 + skill_gap * 1.0) / training_skills.count() * 2
            score += skill_score
        
        # 2. Score basé sur la popularité (max 1 point)
        participant_count = Participant.objects.filter(session__training=training).count()
        popularity_score = min(participant_count / 10, 1.0)
        score += popularity_score
        
        if popularity_score > 0.3:
            match_reason.append(f"Formation populaire avec {participant_count} participants")
        
        # 3. Score basé sur les tendances du domaine (max 1 point)
        domain = training.title.split()[0].lower() if training.title else "general"
        if domain in domain_popularity and len(domain_popularity[domain]) > 0:
            # Vérifier si cette formation est parmi les plus populaires de son domaine
            domain_items = domain_popularity[domain]
            for idx, (train_id, _) in enumerate(domain_items):
                if train_id == training.id:
                    # Plus la formation est haute dans le classement, plus le score est élevé
                    domain_rank_score = 1.0 - (idx / len(domain_items) if len(domain_items) > 1 else 0)
                    score += domain_rank_score
                    
                    if domain_rank_score > 0.5:
                        match_reason.append(f"Formation tendance dans le domaine {domain.capitalize()}")
                    break
        
        # 4. Score basé sur la progression logique (1 point)
        # Regarder si l'utilisateur a complété des formations préalables
        prerequisites_completed = 0
        for completed_training in completed_trainings:
            # Vérifier si le titre de la formation complétée est mentionné dans les prérequis
            if completed_training.title.lower() in (training.prerequisites or "").lower():
                prerequisites_completed += 1
        
        if prerequisites_completed > 0 and training.prerequisites:
            score += 1.0
            match_reason.append("Progression logique basée sur vos formations précédentes")
        
        # Normaliser le score final (1-5)
        final_score = min(max(score, 0.1), 5.0)
        
        # Sauvegarder la recommandation
        reason = ". ".join(match_reason)
        recommendation = Recommendation(
            user=user,
            training=training,
            score=final_score,
            reason=reason
        )
        recommendation.save()
        recommendations.append(recommendation)
    
    return recommendations
def process_chatbot_query(query, user):
    """Traite une requête chatbot et renvoie une réponse"""
    query = query.lower()
    
    # Réponses préconfigurées pour des questions communes
    if "formation" in query and "disponible" in query:
        trainings = Training.objects.all()[:5]
        response = "Voici quelques formations disponibles: "
        for t in trainings:
            response += f"\n- {t.title}"
        return response
    
    elif "compétence" in query or "compétences" in query:
        skills = UserSkill.objects.filter(user=user)
        if skills:
            response = "Vos compétences actuelles sont: "
            for s in skills:
                response += f"\n- {s.skill_name} (niveau {s.proficiency_level})"
            return response
        else:
            return "Vous n'avez pas encore de compétences enregistrées dans notre système."
    
    elif "recommandation" in query:
        recommendations = Recommendation.objects.filter(user=user).order_by('-score')[:3]
        if recommendations:
            response = "Voici quelques formations recommandées pour vous: "
            for r in recommendations:
                response += f"\n- {r.training.title}: {r.reason}"
            return response
        else:
            return "Je n'ai pas encore de recommandations personnalisées pour vous."
    
    elif "bonjour" in query or "salut" in query or "hey" in query:
        return f"Bonjour {user.first_name if user.first_name else user.username}! Comment puis-je vous aider avec votre développement professionnel aujourd'hui?"
    
    elif "merci" in query:
        return "De rien! N'hésitez pas si vous avez d'autres questions."
    
    elif "au revoir" in query or "bye" in query:
        return "Au revoir! Bonne journée et bonne formation!"
    
    # Réponse par défaut
    return "Je ne comprends pas complètement votre demande. Vous pouvez me demander des informations sur les formations disponibles, vos compétences, ou des recommandations personnalisées."