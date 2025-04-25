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
    """Génère des recommandations de formation pour un utilisateur basées sur l'IA"""
    # Supprimer les anciennes recommandations
    Recommendation.objects.filter(user=user).delete()
    
    # Récupérer les compétences de l'utilisateur
    user_skills = UserSkill.objects.filter(user=user)
    user_skill_names = [skill.skill_name.lower() for skill in user_skills]
    user_skill_levels = {skill.skill_name.lower(): skill.proficiency_level for skill in user_skills}
    
    # Récupérer les formations déjà suivies
    completed_trainings = Training.objects.filter(
        trainingsession__participant__user=user,
        trainingsession__participant__completion_status='COMPLETED'
    )
    completed_ids = [t.id for t in completed_trainings]
    
    # Récupérer toutes les formations disponibles
    trainings = Training.objects.all()
    
    # Analyser l'historique des formations pour trouver les formations populaires parmi des profils similaires
    similar_users = []
    for other_user in User.objects.exclude(id=user.id):
        # Calculer la similarité entre utilisateurs basée sur les compétences
        other_skills = UserSkill.objects.filter(user=other_user)
        other_skill_names = [skill.skill_name.lower() for skill in other_skills]
        
        # Intersection des compétences
        common_skills = set(user_skill_names).intersection(set(other_skill_names))
        
        # Calculer un score de similarité (entre 0 et 1)
        if not user_skill_names or not other_skill_names:
            similarity = 0
        else:
            similarity = len(common_skills) / max(len(user_skill_names), len(other_skill_names))
        
        if similarity > 0.3:  # Seuil de similarité
            similar_users.append(other_user.id)
    
    # Formations populaires parmi les utilisateurs similaires
    popular_among_similar = {}
    if similar_users:
        for training in trainings:
            count = Participant.objects.filter(
                user_id__in=similar_users,
                session__training=training,
                completion_status='COMPLETED'
            ).count()
            if count > 0:
                popular_among_similar[training.id] = count
    
    recommendations = []
    
    for training in trainings:
        # Ne pas recommander les formations déjà suivies
        if training.id in completed_ids:
            continue
        
        # Initialiser le score et les raisons
        score = 0
        match_reason = []
        
        # 1. Calculer le score basé sur les compétences requises et acquises
        training_skills = TrainingSkill.objects.filter(training=training)
        skill_match_score = 0
        missing_skills = []
        
        for training_skill in training_skills:
            training_skill_name = training_skill.skill_name.lower()
            
            # L'utilisateur a déjà cette compétence
            if training_skill_name in user_skill_names:
                user_level = user_skill_levels[training_skill_name]
                required_level = training_skill.minimum_level
                
                # Si l'utilisateur a le niveau requis ou plus
                if user_level >= required_level:
                    # Bonus plus petit si l'utilisateur est déjà compétent
                    skill_match_score += 0.3
                    match_reason.append(f"Vous maîtrisez déjà la compétence: {training_skill.skill_name}")
                else:
                    # Bonus pour améliorer une compétence existante
                    skill_match_score += 0.7
                    match_reason.append(f"Cette formation vous permettrait d'améliorer votre niveau en {training_skill.skill_name}")
            else:
                # Bonus plus élevé pour les nouvelles compétences
                skill_match_score += 1
                missing_skills.append(training_skill.skill_name)
        
        # Ajouter une raison pour les compétences manquantes
        if missing_skills:
            match_reason.append(f"Vous pourriez acquérir de nouvelles compétences: {', '.join(missing_skills)}")
        
        # Normaliser le score de compétence (maximum 3 points)
        score += min(skill_match_score, 3)
        
        # 2. Bonus de popularité générale
        participant_count = Participant.objects.filter(session__training=training).count()
        popularity_bonus = min(participant_count / 10, 0.7)  # Max bonus of 0.7
        score += popularity_bonus
        
        if popularity_bonus > 0:
            match_reason.append(f"Formation populaire avec {participant_count} participants")
        
        # 3. Bonus pour les formations populaires parmi des profils similaires
        if training.id in popular_among_similar:
            similar_bonus = min(popular_among_similar[training.id] / 3, 1.0)  # Max bonus of 1.0
            score += similar_bonus
            match_reason.append("Des utilisateurs avec un profil similaire au vôtre ont suivi cette formation")
        
        # 4. Analyse du titre et de la description pour pertinence contextuelle
        relevant_terms = [skill.lower() for skill in user_skill_names]
        relevant_terms.extend(["débutant", "avancé", "intermédiaire"])
        
        title_desc = (training.title + " " + training.description).lower()
        term_matches = sum(1 for term in relevant_terms if term in title_desc)
        context_bonus = min(term_matches * 0.1, 0.5)  # Max bonus of 0.5
        score += context_bonus
        
        # Normaliser le score final (1-5)
        final_score = min(max(score, 0), 5)
        
        # Sauvegarder la recommandation si le score est positif
        if final_score > 0:
            reason = ". ".join(match_reason)
            recommendation = Recommendation(
                user=user,
                training=training,
                score=final_score,
                reason=reason
            )
            recommendation.save()
            recommendations.append(recommendation)
    
    # Trier les recommandations par score (du plus élevé au plus bas)
    recommendations.sort(key=lambda x: x.score, reverse=True)
    
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