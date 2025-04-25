# update_trainers_specializations.py
import os
import django
import random
from datetime import datetime

# Configurez l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'formatech.settings')
django.setup()

# Maintenant importez vos modèles
from formation.models import Trainer

def update_trainers_specializations():
    # Liste de spécialisations réelles
    specializations_list = [
        "Développement Web (HTML/CSS/JavaScript)",
        "Cybersécurité et Protection des Données",
        "Intelligence Artificielle et Machine Learning",
        "Gestion de Projet Agile (Scrum, Kanban)",
        "Bases de Données et Big Data",
        "DevOps et Cloud Computing",
        "Développement Mobile (iOS/Android)",
        "UX/UI Design",
        "Architecture Logicielle",
        "Blockchain et Technologies Distribuées"
    ]
    
    trainers = Trainer.objects.all()
    
    for trainer in trainers:
        # Assigner 1-3 spécialisations aléatoires
        num_specs = random.randint(1, 3)
        selected_specs = random.sample(specializations_list, num_specs)
        specs_string = ", ".join(selected_specs)
        
        trainer.specializations = specs_string
        trainer.biography = f"Expert(e) en {selected_specs[0]} avec plus de 5 ans d'expérience dans le domaine."
        trainer.save()
        
        print(f"Formateur mis à jour: {trainer.user.username} - Nouvelles spécialisations: {specs_string}")

if __name__ == '__main__':
    update_trainers_specializations()