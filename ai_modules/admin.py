from django.contrib import admin
from .models import UserSkill, TrainingSkill, Recommendation, ChatbotInteraction

@admin.register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
    list_display = ('user', 'skill_name', 'proficiency_level', 'last_updated')
    list_filter = ('skill_name', 'proficiency_level')
    search_fields = ('user__username', 'skill_name')

@admin.register(TrainingSkill)
class TrainingSkillAdmin(admin.ModelAdmin):
    list_display = ('training', 'skill_name', 'minimum_level')
    list_filter = ('skill_name', 'minimum_level')
    search_fields = ('training__title', 'skill_name')

admin.site.register(Recommendation)
admin.site.register(ChatbotInteraction)