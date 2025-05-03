# set_admin_role.py
import os
import django

# Configurez l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'formatech.settings')
django.setup()

from users.models import User, Role

def set_admin_role(email):
    try:
        user = User.objects.get(email=email)
        admin_role = Role.objects.get(name="Admin")
        user.role = admin_role
        user.save()
        print(f"L'utilisateur {user.username} ({email}) est maintenant Admin")
    except User.DoesNotExist:
        print(f"Utilisateur avec l'email {email} non trouvé")
    except Role.DoesNotExist:
        print("Rôle Admin non trouvé, exécutez d'abord create_roles.py")

if __name__ == '__main__':
    email = input("Entrez l'email de l'utilisateur à promouvoir comme Admin: ")
    set_admin_role(email)