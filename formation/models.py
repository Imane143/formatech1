from django.db import models
from django.conf import settings
from datetime import timedelta

class Training(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    objectives = models.TextField()
    prerequisites = models.TextField(blank=True, null=True)
    duration = models.IntegerField(help_text="Duration in hours")
    max_participants = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    def get_upcoming_sessions(self):
        return self.trainingsession_set.filter(status='PLANNED').order_by('start_date')
    
    def get_trainers(self):
        return Trainer.objects.filter(trainer_sessions__session__training=self).distinct()
    
    def is_available(self):
        return self.get_upcoming_sessions().exists()

class Trainer(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    specializations = models.TextField(help_text="Comma-separated specializations")
    biography = models.TextField(blank=True, null=True)
    hire_date = models.DateField()
    contract_number = models.CharField(max_length=50)
    department = models.CharField(max_length=100)
    rating = models.FloatField(default=0)
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"
    
    def get_upcoming_sessions(self):
        return TrainingSession.objects.filter(
            trainer_sessions__trainer=self,
            status='PLANNED'
        ).order_by('start_date')
    
    def get_rating(self):
        return self.rating

class TrainingSession(models.Model):
    STATUS_CHOICES = (
        ('PLANNED', 'Planned'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    )
    
    training = models.ForeignKey(Training, on_delete=models.CASCADE)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    location = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLANNED')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.training.title} - {self.start_date.strftime('%Y-%m-%d')}"
    
    def get_participants(self):
        return self.participant_set.all()
    
    def is_full(self):
        return self.get_participants().count() >= self.training.max_participants
    
    def generate_reminders(self):
        reminder_date = self.start_date - timedelta(days=2)
        reminders = []
        
        for participant in self.get_participants():
            reminder = Reminder(
                session=self,
                recipient=participant.user,
                message=f"Rappel: Votre formation {self.training.title} commence le {self.start_date.strftime('%d/%m/%Y à %H:%M')}.",
                scheduled_date=reminder_date,
                status='PENDING'
            )
            reminder.save()
            reminders.append(reminder)
        
        return reminders

class TrainerSession(models.Model):
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE, related_name='trainer_sessions')
    session = models.ForeignKey(TrainingSession, on_delete=models.CASCADE, related_name='trainer_sessions')
    
    class Meta:
        unique_together = ('trainer', 'session')

class Participant(models.Model):
    ATTENDANCE_STATUS = (
        ('REGISTERED', 'Registered'),
        ('CONFIRMED', 'Confirmed'),
        ('ATTENDED', 'Attended'),
        ('ABSENT', 'Absent'),
    )
    
    COMPLETION_STATUS = (
        ('NOT_STARTED', 'Not Started'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    session = models.ForeignKey(TrainingSession, on_delete=models.CASCADE)
    registration_date = models.DateTimeField(auto_now_add=True)
    attendance_status = models.CharField(max_length=20, choices=ATTENDANCE_STATUS, default='REGISTERED')
    completion_status = models.CharField(max_length=20, choices=COMPLETION_STATUS, default='NOT_STARTED')
    feedback = models.TextField(blank=True, null=True)
    rating = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'session')
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - {self.session}"
    
    def get_certificate(self):
        try:
            return Certificate.objects.get(participant=self)
        except Certificate.DoesNotExist:
            return None

class Certificate(models.Model):
    STATUS_CHOICES = (
        ('ISSUED', 'Issued'),
        ('EXPIRED', 'Expired'),
        ('REVOKED', 'Revoked'),
    )
    
    participant = models.OneToOneField(Participant, on_delete=models.CASCADE)
    issue_date = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateTimeField(null=True, blank=True)
    certificate_number = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ISSUED')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Certificate {self.certificate_number}"
    
    def generate_pdf(self):
        # Logique pour générer un PDF du certificat
        # (sera implémentée dans un service distinct)
        pass
    
    def verify(self):
        return self.status == 'ISSUED'

class Reminder(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('SENT', 'Sent'),
        ('FAILED', 'Failed'),
    )
    
    session = models.ForeignKey(TrainingSession, on_delete=models.CASCADE)
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    scheduled_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Reminder for {self.session} to {self.recipient}"
    
    def send(self):
        # Logique pour envoyer la notification
        # (sera implémentée dans un service distinct)
        self.status = 'SENT'
        self.save()
        return True