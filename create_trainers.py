# create_trainers.py
import os
import django

# Configurez l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'formatech.settings')
django.setup()

# Maintenant importez vos modèles
from users.models import User
from formation.models import Trainer
from datetime import datetime

def create_trainers():
    # Vérifiez d'abord si vous avez des utilisateurs
    users = User.objects.all()
    print(f"Nombre d'utilisateurs: {users.count()}")
    
    # Si vous avez des utilisateurs, créez des formateurs
    if users.exists():
        for user in users:
            # Vérifiez si un formateur existe déjà pour cet utilisateur
            if not Trainer.objects.filter(user=user).exists():
                trainer = Trainer(
                    user=user,
                    specializations=f"Spécialité de {user.username}",
                    biography=f"Formateur expérimenté en {user.username}",
                    hire_date=datetime.now().date(),
                    contract_number=f"TR-2025-{user.id}",
                    department="Formation"
                )
                trainer.save()
                print(f"Formateur créé pour: {user.username}")
            else:
                print(f"Un formateur existe déjà pour l'utilisateur: {user.username}")
    else:
        print("Aucun utilisateur trouvé. Créez d'abord des utilisateurs.")
    
    # Vérifiez les formateurs créés
    trainers = Trainer.objects.all()
    print(f"Nombre de formateurs: {trainers.count()}")
    for trainer in trainers:
        print(f"Formateur: {trainer.user.username} - {trainer.specializations}")

if __name__ == '__main__':
    create_trainers()
    