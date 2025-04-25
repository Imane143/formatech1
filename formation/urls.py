from django.urls import path
from . import views

app_name = 'formation'

urlpatterns = [
    # Formations
    path('', views.training_list, name='training_list'),
    path('training/<int:pk>/', views.training_detail, name='training_detail'),
    path('training/create/', views.training_create, name='training_create'),
    path('training/<int:pk>/edit/', views.training_update, name='training_update'),
    path('training/<int:pk>/delete/', views.training_delete, name='training_delete'),
    
    # Sessions
    path('sessions/', views.session_list, name='session_list'),
    path('session/<int:pk>/', views.session_detail, name='session_detail'),
    path('session/create/', views.session_create, name='session_create'),
    path('session/<int:pk>/edit/', views.session_update, name='session_update'),
    path('session/<int:pk>/delete/', views.session_delete, name='session_delete'),
    
    # Participants
    path('session/<int:session_pk>/register/', views.participant_register, name='participant_register'),
    path('participant/<int:pk>/update/', views.participant_update, name='participant_update'),
    # Ajoutez cette ligne à vos urlpatterns
path('session/<int:session_pk>/assign_trainer/', views.trainer_assign, name='trainer_assign'),
    # Certificats
    path('certificate/<int:pk>/', views.certificate_detail, name='certificate_detail'),
    path('certificate/<int:pk>/generate/', views.certificate_generate, name='certificate_generate'),
    path('certificate/<int:pk>/verify/', views.certificate_verify, name='certificate_verify'),
    # Ajouter cette ligne à vos urlpatterns
path('session/<int:session_pk>/remove_trainer/<int:trainer_pk>/', views.trainer_remove, name='trainer_remove'),
]