from django import forms
from .models import Training, TrainingSession, Trainer, Participant, Certificate
from users.models import User

class TrainingForm(forms.ModelForm):
    class Meta:
        model = Training
        fields = ('title', 'description', 'objectives', 'prerequisites', 'duration', 'max_participants')

class TrainingSessionForm(forms.ModelForm):
    class Meta:
        model = TrainingSession
        fields = ('training', 'start_date', 'end_date', 'location', 'status')
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class TrainerForm(forms.ModelForm):
    class Meta:
        model = Trainer
        fields = ('user', 'specializations', 'biography', 'hire_date', 'contract_number', 'department')
        widgets = {
            'hire_date': forms.DateInput(attrs={'type': 'date'}),
        }

class ParticipantForm(forms.ModelForm):
    # Ajoutez explicitement le champ user
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        label="Participant",
        empty_label="Sélectionner un utilisateur"
    )
    
    class Meta:
        model = Participant
        fields = ('user', 'attendance_status', 'completion_status', 'feedback', 'rating')
        widgets = {
            'feedback': forms.Textarea(attrs={'rows': 3}),
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5}),
        }

class CertificateForm(forms.ModelForm):
    class Meta:
        model = Certificate
        fields = ('participant', 'expiry_date', 'certificate_number', 'status')
        widgets = {
            'expiry_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }