from django.db import models
from django.conf import settings

class Report(models.Model):
    REPORT_TYPES = (
        ('ATTENDANCE', 'Attendance'),
        ('COMPLETION', 'Completion'),
        ('PERFORMANCE', 'Performance'),
        ('SATISFACTION', 'Satisfaction'),
        ('CUSTOM', 'Custom'),
    )
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    type = models.CharField(max_length=20, choices=REPORT_TYPES)
    parameters = models.TextField(help_text="JSON format parameters")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    def generate(self):
        # Logique pour générer le rapport
        # (sera implémentée dans un service distinct)
        pass
    
    def export(self, format='PDF'):
        # Logique pour exporter le rapport
        # (sera implémentée dans un service distinct)
        pass