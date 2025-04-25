from django.urls import path
from . import views

app_name = 'ai_modules'

urlpatterns = [
    path('skills/', views.skill_analysis, name='skill_analysis'),
    path('recommendations/', views.training_recommendations, name='training_recommendations'),
    path('chatbot/', views.chatbot_interface, name='chatbot_interface'),
    path('chatbot/query/', views.chatbot_query, name='chatbot_query'),
    path('skills/user/<int:user_id>/', views.user_skills, name='user_skills'),
    path('skills/training/<int:training_id>/', views.training_skills, name='training_skills'),
]