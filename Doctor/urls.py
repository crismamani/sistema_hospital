# doctor/urls.py
from django.urls import path
from . import views

app_name = 'doctor'  # Namespace: {% url 'doctor:mis_pacientes' %}

urlpatterns = [
    path('', views.dashboard_doctor, name='dashboard'),

    # Pacientes a cargo
    path('mis-pacientes/', views.mis_pacientes_internados, name='mis_pacientes'),
    
    # Historia Clínica (Ojo con el nombre del parametro <int:paciente_id> que debe coincidir con el view)
    path('paciente/<int:paciente_id>/historia/', views.historia_clinica_paciente, name='historia_clinica_paciente'),
    
    # Solicitudes
    path('internacion/<int:internacion_id>/derivar/', views.solicitar_derivacion, name='solicitar_derivacion'),
    path('paciente/<int:paciente_id>/solicitar-cama/', views.solicitar_cama_uti, name='solicitar_cama_uti'),
    
    # Agenda
    path('agenda/', views.mi_agenda, name='mi_agenda'),
]