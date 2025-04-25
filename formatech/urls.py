from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('formation/', include('formation.urls')),
    path('reports/', include('reports.urls')),
    path('ai/', include('ai_modules.urls')),
    
    # Ajoutez ces lignes pour gérer l'authentification
    path('accounts/login/', RedirectView.as_view(url='/users/login/', permanent=False)),
    path('accounts/logout/', RedirectView.as_view(url='/users/logout/', permanent=False)),
    
    path('', RedirectView.as_view(url='formation/', permanent=False)),
]

# Ajouter les URLs pour les fichiers statiques et media en mode développement
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)