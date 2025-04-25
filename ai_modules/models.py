from django.db import models
from django.conf import settings
from formation.models import Training

class UserSkill(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='skills')
    skill_name = models.CharField(max_length=100)
    proficiency_level = models.IntegerField(default=1)  # 1-5 scale
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'skill_name')
    
    def __str__(self):
        return f"{self.user.username} - {self.skill_name} (Level {self.proficiency_level})"

class TrainingSkill(models.Model):
    training = models.ForeignKey(Training, on_delete=models.CASCADE, related_name='required_skills')
    skill_name = models.CharField(max_length=100)
    minimum_level = models.IntegerField(default=1)  # 1-5 scale
    
    class Meta:
        unique_together = ('training', 'skill_name')
    
    def __str__(self):
        return f"{self.training.title} - {self.skill_name} (Min Level {self.minimum_level})"

class Recommendation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recommendations')
    training = models.ForeignKey(Training, on_delete=models.CASCADE)
    score = models.FloatField()  # Score de pertinence
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'training')
        ordering = ['-score']
    
    def __str__(self):
        return f"{self.user.username} - {self.training.title} (Score: {self.score})"

class ChatbotInteraction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chatbot_interactions')
    query = models.TextField()
    response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"