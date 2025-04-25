# formation/admin.py
from django.contrib import admin
from .models import Training, Trainer, TrainingSession, TrainerSession, Participant, Certificate, Reminder

@admin.register(Training)
class TrainingAdmin(admin.ModelAdmin):
    list_display = ('title', 'duration', 'max_participants', 'created_at')
    search_fields = ('title', 'description')

@admin.register(Trainer)
class TrainerAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'rating')
    search_fields = ('user__username', 'user__email', 'department')

@admin.register(TrainingSession)
class TrainingSessionAdmin(admin.ModelAdmin):
    list_display = ('training', 'start_date', 'end_date', 'location', 'status')
    list_filter = ('status', 'start_date')
    search_fields = ('training__title', 'location')

admin.site.register(TrainerSession)
admin.site.register(Participant)
admin.site.register(Certificate)
admin.site.register(Reminder)