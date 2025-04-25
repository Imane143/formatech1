from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db import models
from .models import Report
from formation.models import Training, TrainingSession, Participant, Certificate
from users.models import User
import json
import csv
from io import StringIO, BytesIO
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

@login_required
def report_list(request):
    """Vue pour la liste des rapports"""
    reports = Report.objects.filter(created_by=request.user).order_by('-created_at')
    return render(request, 'reports/report_list.html', {'reports': reports})

@login_required
def report_detail(request, pk):
    """Vue pour les détails d'un rapport"""
    report = get_object_or_404(Report, pk=pk)
    
    # Vérifier que l'utilisateur est autorisé à voir ce rapport
    if report.created_by != request.user and not request.user.is_staff:
        messages.error(request, "Vous n'avez pas l'autorisation de voir ce rapport.")
        return redirect('reports:report_list')
    
    # Générer les données du rapport
    report_data = generate_report_data(report)
    
    return render(request, 'reports/report_detail.html', {
        'report': report,
        'report_data': report_data
    })

@login_required
def report_create(request):
    """Vue pour créer un nouveau rapport"""
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        report_type = request.POST.get('type')
        parameters = request.POST.get('parameters', '{}')
        
        try:
            # Valider que les paramètres sont un JSON valide
            json.loads(parameters)
            
            report = Report(
                title=title,
                description=description,
                type=report_type,
                parameters=parameters,
                created_by=request.user
            )
            report.save()
            
            messages.success(request, 'Rapport créé avec succès!')
            return redirect('reports:report_detail', pk=report.id)
            
        except json.JSONDecodeError:
            messages.error(request, 'Les paramètres doivent être au format JSON valide.')
    
    return render(request, 'reports/report_form.html', {
        'report_types': Report.REPORT_TYPES
    })

@login_required
def report_update(request, pk):
    """Vue pour mettre à jour un rapport"""
    report = get_object_or_404(Report, pk=pk)
    
    # Vérifier que l'utilisateur est autorisé à modifier ce rapport
    if report.created_by != request.user and not request.user.is_staff:
        messages.error(request, "Vous n'avez pas l'autorisation de modifier ce rapport.")
        return redirect('reports:report_list')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        report_type = request.POST.get('type')
        parameters = request.POST.get('parameters', '{}')
        
        try:
            # Valider que les paramètres sont un JSON valide
            json.loads(parameters)
            
            report.title = title
            report.description = description
            report.type = report_type
            report.parameters = parameters
            report.save()
            
            messages.success(request, 'Rapport mis à jour avec succès!')
            return redirect('reports:report_detail', pk=report.id)
            
        except json.JSONDecodeError:
            messages.error(request, 'Les paramètres doivent être au format JSON valide.')
    
    return render(request, 'reports/report_form.html', {
        'report': report,
        'report_types': Report.REPORT_TYPES
    })

@login_required
def report_delete(request, pk):
    """Vue pour supprimer un rapport"""
    report = get_object_or_404(Report, pk=pk)
    
    # Vérifier que l'utilisateur est autorisé à supprimer ce rapport
    if report.created_by != request.user and not request.user.is_staff:
        messages.error(request, "Vous n'avez pas l'autorisation de supprimer ce rapport.")
        return redirect('reports:report_list')
    
    if request.method == 'POST':
        report.delete()
        messages.success(request, 'Rapport supprimé avec succès!')
        return redirect('reports:report_list')
    
    return render(request, 'reports/report_confirm_delete.html', {'report': report})

@login_required
def report_export(request, pk):
    """Vue pour exporter un rapport"""
    report = get_object_or_404(Report, pk=pk)
    format_type = request.GET.get('format', 'pdf')
    
    # Vérifier que l'utilisateur est autorisé à exporter ce rapport
    if report.created_by != request.user and not request.user.is_staff:
        messages.error(request, "Vous n'avez pas l'autorisation d'exporter ce rapport.")
        return redirect('reports:report_list')
    
    # Générer les données du rapport
    report_data = generate_report_data(report)
    
    # Exporter dans le format demandé
    if format_type == 'csv':
        return export_csv(report, report_data)
    elif format_type == 'pdf':
        return export_pdf(report, report_data)
    else:
        messages.error(request, 'Format d\'exportation non supporté.')
        return redirect('reports:report_detail', pk=report.id)

@login_required
def attendance_report(request):
    """Vue pour le rapport de présence"""
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    training_id = request.GET.get('training_id', '')
    
    sessions = TrainingSession.objects.all().order_by('start_date')
    trainings = Training.objects.all()
    
    # Filtres
    if start_date:
        sessions = sessions.filter(start_date__gte=start_date)
    if end_date:
        sessions = sessions.filter(end_date__lte=end_date)
    if training_id:
        sessions = sessions.filter(training_id=training_id)
    
    # Calculer les statistiques de présence
    attendance_data = []
    for session in sessions:
        total_participants = Participant.objects.filter(session=session).count()
        attended = Participant.objects.filter(session=session, attendance_status='ATTENDED').count()
        absent = Participant.objects.filter(session=session, attendance_status='ABSENT').count()
        attendance_rate = (attended / total_participants * 100) if total_participants > 0 else 0
        
        attendance_data.append({
            'session': session,
            'total': total_participants,
            'attended': attended,
            'absent': absent,
            'rate': attendance_rate
        })
    
    return render(request, 'reports/attendance_report.html', {
        'attendance_data': attendance_data,
        'trainings': trainings,
        'start_date': start_date,
        'end_date': end_date,
        'training_id': training_id
    })

@login_required
def completion_report(request):
    """Vue pour le rapport de complétion"""
    training_id = request.GET.get('training_id', '')
    
    trainings = Training.objects.all()
    
    # Calculer les taux de complétion par formation
    completion_data = []
    
    if training_id:
        trainings = trainings.filter(id=training_id)
    
    for training in trainings:
        total_participants = Participant.objects.filter(session__training=training).count()
        completed = Participant.objects.filter(
            session__training=training, 
            completion_status='COMPLETED'
        ).count()
        in_progress = Participant.objects.filter(
            session__training=training, 
            completion_status='IN_PROGRESS'
        ).count()
        not_started = Participant.objects.filter(
            session__training=training, 
            completion_status='NOT_STARTED'
        ).count()
        failed = Participant.objects.filter(
            session__training=training, 
            completion_status='FAILED'
        ).count()
        
        completion_rate = (completed / total_participants * 100) if total_participants > 0 else 0
        
        completion_data.append({
            'training': training,
            'total': total_participants,
            'completed': completed,
            'in_progress': in_progress,
            'not_started': not_started,
            'failed': failed,
            'rate': completion_rate
        })
    
    return render(request, 'reports/completion_report.html', {
        'completion_data': completion_data,
        'trainings': trainings,
        'training_id': training_id
    })

@login_required
def performance_report(request):
    """Vue pour le rapport de performance"""
    # Récupérer les formateurs et leurs statistiques
    trainers = []
    
    for trainer in User.objects.filter(trainer__isnull=False):
        sessions_count = TrainingSession.objects.filter(
            trainer_sessions__trainer__user=trainer
        ).count()
        
        # Calculer le taux de réussite moyen
        success_rate = 0
        session_participants = Participant.objects.filter(
            session__trainer_sessions__trainer__user=trainer
        )
        completed_count = session_participants.filter(completion_status='COMPLETED').count()
        
        if session_participants.count() > 0:
            success_rate = completed_count / session_participants.count() * 100
        
        # Récupérer la note moyenne
        average_rating = Participant.objects.filter(
            session__trainer_sessions__trainer__user=trainer,
            rating__isnull=False
        ).values('rating').aggregate(avg_rating=models.Avg('rating'))['avg_rating'] or 0
        
        trainers.append({
            'user': trainer,
            'sessions_count': sessions_count,
            'success_rate': success_rate,
            'average_rating': average_rating
        })
    
    return render(request, 'reports/performance_report.html', {
        'trainers': trainers
    })

@login_required
def satisfaction_report(request):
    """Vue pour le rapport de satisfaction"""
    training_id = request.GET.get('training_id', '')
    
    trainings = Training.objects.all()
    satisfaction_data = []
    
    if training_id:
        trainings = trainings.filter(id=training_id)
    
    for training in trainings:
        # Récupérer les évaluations
        ratings = Participant.objects.filter(
            session__training=training,
            rating__isnull=False
        ).values_list('rating', flat=True)
        
        # Calculer la distribution des notes
        rating_counts = {i: 0 for i in range(1, 6)}
        for r in ratings:
            if r in rating_counts:
                rating_counts[r] += 1
        
        # Calculer la note moyenne
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        
        satisfaction_data.append({
            'training': training,
            'ratings': ratings,
            'rating_counts': rating_counts,
            'avg_rating': avg_rating,
            'total_ratings': len(ratings)
        })
    
    return render(request, 'reports/satisfaction_report.html', {
        'satisfaction_data': satisfaction_data,
        'trainings': trainings,
        'training_id': training_id
    })

# Fonctions utilitaires
def generate_report_data(report):
    """Génère les données pour un rapport en fonction de son type et ses paramètres"""
    report_type = report.type
    parameters = json.loads(report.parameters)
    
    # Initialiser les données du rapport
    data = {
        'title': report.title,
        'type': report_type,
        'created_at': report.created_at,
        'parameters': parameters
    }
    
    # Générer les données en fonction du type de rapport
    if report_type == 'ATTENDANCE':
        data.update(generate_attendance_data(parameters))
    elif report_type == 'COMPLETION':
        data.update(generate_completion_data(parameters))
    elif report_type == 'PERFORMANCE':
        data.update(generate_performance_data(parameters))
    elif report_type == 'SATISFACTION':
        data.update(generate_satisfaction_data(parameters))
    elif report_type == 'CUSTOM':
        data.update(generate_custom_data(parameters))
    
    return data

def generate_attendance_data(parameters):
    """Génère les données pour un rapport de présence"""
    start_date = parameters.get('start_date', '')
    end_date = parameters.get('end_date', '')
    training_id = parameters.get('training_id', '')
    
    sessions = TrainingSession.objects.all().order_by('start_date')
    
    # Appliquer les filtres
    if start_date:
        sessions = sessions.filter(start_date__gte=start_date)
    if end_date:
        sessions = sessions.filter(end_date__lte=end_date)
    if training_id:
        sessions = sessions.filter(training_id=training_id)
    
    # Calculer les statistiques de présence
    attendance_data = []
    for session in sessions:
        total_participants = Participant.objects.filter(session=session).count()
        attended = Participant.objects.filter(session=session, attendance_status='ATTENDED').count()
        absent = Participant.objects.filter(session=session, attendance_status='ABSENT').count()
        attendance_rate = (attended / total_participants * 100) if total_participants > 0 else 0
        
        attendance_data.append({
            'session': {
                'id': session.id,
                'training': session.training.title,
                'start_date': session.start_date.strftime('%Y-%m-%d %H:%M'),
                'location': session.location
            },
            'total': total_participants,
            'attended': attended,
            'absent': absent,
            'rate': attendance_rate
        })
    
    # Calculer les statistiques globales
    total_all = sum(item['total'] for item in attendance_data)
    attended_all = sum(item['attended'] for item in attendance_data)
    global_rate = (attended_all / total_all * 100) if total_all > 0 else 0
    
    return {
        'attendance_data': attendance_data,
        'total_all': total_all,
        'attended_all': attended_all,
        'global_rate': global_rate
    }

def generate_completion_data(parameters):
    """Génère les données pour un rapport de complétion"""
    training_id = parameters.get('training_id', '')
    
    trainings = Training.objects.all()
    
    if training_id:
        trainings = trainings.filter(id=training_id)
    
    completion_data = []
    
    for training in trainings:
        total_participants = Participant.objects.filter(session__training=training).count()
        completed = Participant.objects.filter(
            session__training=training, 
            completion_status='COMPLETED'
        ).count()
        in_progress = Participant.objects.filter(
            session__training=training, 
            completion_status='IN_PROGRESS'
        ).count()
        not_started = Participant.objects.filter(
            session__training=training, 
            completion_status='NOT_STARTED'
        ).count()
        failed = Participant.objects.filter(
            session__training=training, 
            completion_status='FAILED'
        ).count()
        
        completion_rate = (completed / total_participants * 100) if total_participants > 0 else 0
        
        completion_data.append({
            'training': {
                'id': training.id,
                'title': training.title
            },
            'total': total_participants,
            'completed': completed,
            'in_progress': in_progress,
            'not_started': not_started,
            'failed': failed,
            'rate': completion_rate
        })
    
    # Calculer les statistiques globales
    total_all = sum(item['total'] for item in completion_data)
    completed_all = sum(item['completed'] for item in completion_data)
    global_rate = (completed_all / total_all * 100) if total_all > 0 else 0
    
    return {
        'completion_data': completion_data,
        'total_all': total_all,
        'completed_all': completed_all,
        'global_rate': global_rate
    }

def generate_performance_data(parameters):
    """Génère les données pour un rapport de performance"""
    # À implémenter
    return {'message': 'Fonctionnalité en cours de développement'}

def generate_satisfaction_data(parameters):
    """Génère les données pour un rapport de satisfaction"""
    # À implémenter
    return {'message': 'Fonctionnalité en cours de développement'}

def generate_custom_data(parameters):
    """Génère les données pour un rapport personnalisé"""
    # À implémenter
    return {'message': 'Fonctionnalité en cours de développement'}

def export_csv(report, report_data):
    """Exporte les données d'un rapport au format CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{report.title.replace(" ", "_")}.csv"'
    
    csv_file = StringIO()
    writer = csv.writer(csv_file)
    
    # Écrire l'en-tête
    writer.writerow(['Rapport', report.title])
    writer.writerow(['Type', dict(Report.REPORT_TYPES).get(report.type, report.type)])
    writer.writerow(['Date de création', report.created_at.strftime('%Y-%m-%d %H:%M')])
    writer.writerow([])
    
    # Écrire les données en fonction du type de rapport
    if report.type == 'ATTENDANCE':
        writer.writerow(['Formation', 'Date', 'Lieu', 'Total participants', 'Présents', 'Absents', 'Taux de présence (%)'])
        for item in report_data.get('attendance_data', []):
            writer.writerow([
                item['session']['training'],
                item['session']['start_date'],
                item['session']['location'],
                item['total'],
                item['attended'],
                item['absent'],
                f"{item['rate']:.2f}"
            ])
    elif report.type == 'COMPLETION':
        writer.writerow(['Formation', 'Total participants', 'Terminé', 'En cours', 'Non démarré', 'Échec', 'Taux de complétion (%)'])
        for item in report_data.get('completion_data', []):
            writer.writerow([
                item['training']['title'],
                item['total'],
                item['completed'],
                item['in_progress'],
                item['not_started'],
                item['failed'],
                f"{item['rate']:.2f}"
            ])
    # Ajouter d'autres types de rapports selon les besoins
    
    response.write(csv_file.getvalue())
    return response

def export_pdf(report, report_data):
    """Exporte les données d'un rapport au format PDF"""
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{report.title.replace(" ", "_")}.pdf"'
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []
    
    # Titre du rapport
    elements.append(Paragraph(report.title, styles['Title']))
    elements.append(Spacer(1, 12))
    
    # Informations générales
    elements.append(Paragraph(f"Type: {dict(Report.REPORT_TYPES).get(report.type, report.type)}", styles['Normal']))
    elements.append(Paragraph(f"Date de création: {report.created_at.strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    elements.append(Paragraph(f"Créé par: {report.created_by.get_full_name() or report.created_by.username}", styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Contenu en fonction du type de rapport
    if report.type == 'ATTENDANCE':
        elements.append(Paragraph("Rapport de présence", styles['Heading2']))
        elements.append(Spacer(1, 6))
        
        # Tableau des données
        data = [
            ['Formation', 'Date', 'Lieu', 'Total', 'Présents', 'Absents', 'Taux (%)']
        ]
        
        for item in report_data.get('attendance_data', []):
            data.append([
                item['session']['training'],
                item['session']['start_date'],
                item['session']['location'],
                str(item['total']),
                str(item['attended']),
                str(item['absent']),
                f"{item['rate']:.2f}"
            ])
        
        # Ajouter une ligne pour les totaux
        data.append([
            'TOTAL', '', '', 
            str(report_data.get('total_all', 0)),
            str(report_data.get('attended_all', 0)),
            str(report_data.get('total_all', 0) - report_data.get('attended_all', 0)),
            f"{report_data.get('global_rate', 0):.2f}"
        ])
        
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        
        elements.append(table)
    
    # Générer le PDF
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    
    response.write(pdf)
    return response