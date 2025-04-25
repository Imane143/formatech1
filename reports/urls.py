from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.report_list, name='report_list'),
    path('<int:pk>/', views.report_detail, name='report_detail'),
    path('create/', views.report_create, name='report_create'),
    path('<int:pk>/edit/', views.report_update, name='report_update'),
    path('<int:pk>/delete/', views.report_delete, name='report_delete'),
    path('<int:pk>/export/', views.report_export, name='report_export'),
    path('attendance/', views.attendance_report, name='attendance_report'),
    path('completion/', views.completion_report, name='completion_report'),
    path('performance/', views.performance_report, name='performance_report'),
    path('satisfaction/', views.satisfaction_report, name='satisfaction_report'),
]