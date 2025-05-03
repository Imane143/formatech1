import os
import django

# Configurez l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'formatech.settings')
django.setup()

from users.models import Role, Permission, RolePermission

def initialize_roles():
    # Créer les rôles standard
    roles = [
        {
            'name': 'Admin',
            'description': 'Administrateur avec accès complet au système'
        },
        {
            'name': 'Formateur',
            'description': 'Formateur qui anime des sessions de formation'
        },
        {
            'name': 'Participant',
            'description': 'Utilisateur standard qui participe aux formations'
        }
    ]
    
    for role_data in roles:
        role, created = Role.objects.get_or_create(
            name=role_data['name'],
            defaults={'description': role_data['description']}
        )
        if created:
            print(f"Rôle créé: {role.name}")
        else:
            print(f"Rôle existant: {role.name}")
    
    # Créer les permissions standard
    permissions = [
        {
            'name': 'Gérer les formations',
            'code': 'manage_trainings',
            'description': 'Créer, modifier, supprimer des formations'
        },
        {
            'name': 'Gérer les sessions',
            'code': 'manage_sessions',
            'description': 'Créer, modifier, supprimer des sessions'
        },
        {
            'name': 'Gérer les utilisateurs',
            'code': 'manage_users',
            'description': 'Créer, modifier, supprimer des utilisateurs'
        },
        {
            'name': 'Voir les rapports',
            'code': 'view_reports',
            'description': 'Consulter les rapports'
        },
        {
            'name': 'S\'inscrire aux formations',
            'code': 'register_trainings',
            'description': 'S\'inscrire aux formations disponibles'
        },
        {
            'name': 'Voir son profil',
            'code': 'view_profile',
            'description': 'Consulter et modifier son profil'
        }
    ]
    
    for perm_data in permissions:
        perm, created = Permission.objects.get_or_create(
            code=perm_data['code'],
            defaults={
                'name': perm_data['name'],
                'description': perm_data['description']
            }
        )
        if created:
            print(f"Permission créée: {perm.name}")
        else:
            print(f"Permission existante: {perm.name}")
    
    # Attribuer les permissions aux rôles
    # Admin - Toutes les permissions
    admin_role = Role.objects.get(name='Admin')
    for perm in Permission.objects.all():
        RolePermission.objects.get_or_create(role=admin_role, permission=perm)
    
    # Formateur - Permissions spécifiques
    trainer_role = Role.objects.get(name='Formateur')
    trainer_perms = ['view_profile', 'view_reports']
    for code in trainer_perms:
        perm = Permission.objects.get(code=code)
        RolePermission.objects.get_or_create(role=trainer_role, permission=perm)
    
    # Participant - Permissions limitées
    participant_role = Role.objects.get(name='Participant')
    participant_perms = ['view_profile', 'register_trainings']
    for code in participant_perms:
        perm = Permission.objects.get(code=code)
        RolePermission.objects.get_or_create(role=participant_role, permission=perm)
    
    print("Attribution des permissions terminée")

if __name__ == '__main__':
    initialize_roles()