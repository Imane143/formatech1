from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Training, TrainingSession, Trainer, Participant, Certificate, TrainerSession
from .forms import TrainingForm, TrainingSessionForm, TrainerForm, ParticipantForm, CertificateForm
import uuid
from datetime import datetime, timedelta

# Formations
@login_required
def training_list(request):
    trainings = Training.objects.all().order_by('-created_at')
    return render(request, 'formation/training_list.html', {'trainings': trainings})

@login_required
def training_detail(request, pk):
    training = get_object_or_404(Training, pk=pk)
    sessions = training.trainingsession_set.all().order_by('start_date')
    return render(request, 'formation/training_detail.html', {'training': training, 'sessions': sessions})

@login_required
def training_create(request):
    if request.method == 'POST':
        form = TrainingForm(request.POST)
        if form.is_valid():
            training = form.save()
            messages.success(request, 'Formation créée avec succès!')
            return redirect('formation:training_detail', pk=training.id)
    else:
        form = TrainingForm()
    
    return render(request, 'formation/training_form.html', {'form': form, 'action': 'Créer'})

@login_required
def training_update(request, pk):
    training = get_object_or_404(Training, pk=pk)
    
    if request.method == 'POST':
        form = TrainingForm(request.POST, instance=training)
        if form.is_valid():
            form.save()
            messages.success(request, 'Formation mise à jour avec succès!')
            return redirect('formation:training_detail', pk=training.id)
    else:
        form = TrainingForm(instance=training)
    
    return render(request, 'formation/training_form.html', {'form': form, 'action': 'Modifier', 'training': training})
@login_required
def trainer_remove(request, session_pk, trainer_pk):
    session = get_object_or_404(TrainingSession, pk=session_pk)
    trainer = get_object_or_404(Trainer, pk=trainer_pk)
    
    trainer_session = get_object_or_404(TrainerSession, trainer=trainer, session=session)
    trainer_session.delete()
    
    messages.success(request, 'Formateur retiré avec succès!')
    return redirect('formation:session_detail', pk=session_pk)
@login_required
def training_delete(request, pk):
    training = get_object_or_404(Training, pk=pk)
    
    if request.method == 'POST':
        training.delete()
        messages.success(request, 'Formation supprimée avec succès!')
        return redirect('formation:training_list')
    
    return render(request, 'formation/training_confirm_delete.html', {'training': training})

# Sessions
@login_required
def session_list(request):
    sessions = TrainingSession.objects.all().order_by('start_date')
    return render(request, 'formation/session_list.html', {'sessions': sessions})

@login_required
def session_detail(request, pk):
    session = get_object_or_404(TrainingSession, pk=pk)
    participants = session.get_participants()
    trainers = Trainer.objects.filter(trainer_sessions__session=session)
    
    return render(request, 'formation/session_detail.html', {
        'session': session,
        'participants': participants,
        'trainers': trainers
    })

@login_required
def session_create(request):
    if request.method == 'POST':
        form = TrainingSessionForm(request.POST)
        if form.is_valid():
            session = form.save()
            messages.success(request, 'Session créée avec succès!')
            return redirect('formation:session_detail', pk=session.id)
    else:
        form = TrainingSessionForm()
    
    return render(request, 'formation/session_form.html', {'form': form, 'action': 'Créer'})

@login_required
def session_update(request, pk):
    session = get_object_or_404(TrainingSession, pk=pk)
    
    if request.method == 'POST':
        form = TrainingSessionForm(request.POST, instance=session)
        if form.is_valid():
            form.save()
            messages.success(request, 'Session mise à jour avec succès!')
            return redirect('formation:session_detail', pk=session.id)
    else:
        form = TrainingSessionForm(instance=session)
    
    return render(request, 'formation/session_form.html', {'form': form, 'action': 'Modifier', 'session': session})

@login_required
def session_delete(request, pk):
    session = get_object_or_404(TrainingSession, pk=pk)
    
    if request.method == 'POST':
        session.delete()
        messages.success(request, 'Session supprimée avec succès!')
        return redirect('formation:session_list')
    
    return render(request, 'formation/session_confirm_delete.html', {'session': session})

# Participants
@login_required
def participant_register(request, session_pk):
    session = get_object_or_404(TrainingSession, pk=session_pk)
    
    if session.is_full():
        messages.error(request, 'Cette session est complète. Veuillez choisir une autre date.')
        return redirect('formation:session_detail', pk=session_pk)
    
    if request.method == 'POST':
        form = ParticipantForm(request.POST)
        if form.is_valid():
            selected_user = form.cleaned_data['user']
            
            # Vérifier si l'utilisateur sélectionné est déjà inscrit
            if Participant.objects.filter(user=selected_user, session=session).exists():
                messages.error(request, f'L\'utilisateur {selected_user.username} est déjà inscrit à cette session.')
                return redirect('formation:session_detail', pk=session_pk)
            
            participant = form.save(commit=False)
            participant.session = session
            participant.save()
            messages.success(request, 'Inscription réussie!')
            return redirect('formation:session_detail', pk=session_pk)
    else:
        form = ParticipantForm()
    
    return render(request, 'formation/participant_form.html', {'form': form, 'session': session})
@login_required
def participant_update(request, pk):
    participant = get_object_or_404(Participant, pk=pk)
    
    if request.method == 'POST':
        # Créer une copie du POST pour la modifier
        post_data = request.POST.copy()
        
        # S'assurer que l'ID de l'utilisateur est toujours présent
        if 'user' not in post_data or not post_data['user']:
            post_data['user'] = str(participant.user.id)
        
        form = ParticipantForm(post_data, instance=participant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Statut du participant mis à jour!')
            return redirect('formation:session_detail', pk=participant.session.id)
        else:
            messages.error(request, f'Erreurs dans le formulaire: {form.errors}')
    else:
        form = ParticipantForm(instance=participant, initial={'user': participant.user.id})
    
    return render(request, 'formation/participant_form.html', {
        'form': form,
        'participant': participant,
        'session': participant.session
    })
@login_required
def trainer_assign(request, session_pk):
    session = get_object_or_404(TrainingSession, pk=session_pk)
    
    if request.method == 'POST':
        trainer_id = request.POST.get('trainer')
        if trainer_id:
            trainer = get_object_or_404(Trainer, pk=trainer_id)
            # Vérifier si ce formateur est déjà assigné à cette session
            if not TrainerSession.objects.filter(trainer=trainer, session=session).exists():
                trainer_session = TrainerSession(trainer=trainer, session=session)
                trainer_session.save()
                messages.success(request, 'Formateur assigné avec succès!')
            else:
                messages.error(request, 'Ce formateur est déjà assigné à cette session.')
        return redirect('formation:session_detail', pk=session_pk)
    
    # Liste des formateurs disponibles
    trainers = Trainer.objects.all()
    return render(request, 'formation/trainer_assign.html', {
        'session': session,
        'trainers': trainers
    })
# Certificats
@login_required
def certificate_detail(request, pk):
    certificate = get_object_or_404(Certificate, pk=pk)
    return render(request, 'formation/certificate_detail.html', {'certificate': certificate})

@login_required
def certificate_generate(request, pk):
    participant = get_object_or_404(Participant, pk=pk)
    
    if participant.completion_status != 'COMPLETED':
        messages.error(request, 'Le participant n\'a pas complété la formation.')
        return redirect('formation:session_detail', pk=participant.session.id)
    
    # Vérifier si un certificat existe déjà
    try:
        certificate = Certificate.objects.get(participant=participant)
        messages.info(request, 'Un certificat existe déjà pour ce participant.')
    except Certificate.DoesNotExist:
        # Générer un nouveau certificat
        certificate = Certificate(
            participant=participant,
            certificate_number=str(uuid.uuid4())[:8].upper(),
            expiry_date=datetime.now() + timedelta(days=365)
        )
        certificate.save()
        messages.success(request, 'Certificat généré avec succès!')
    
    return redirect('formation:certificate_detail', pk=certificate.id)

@login_required
def certificate_verify(request, pk):
    certificate = get_object_or_404(Certificate, pk=pk)
    is_valid = certificate.verify()
    
    return render(request, 'formation/certificate_verify.html', {
        'certificate': certificate,
        'is_valid': is_valid
    })