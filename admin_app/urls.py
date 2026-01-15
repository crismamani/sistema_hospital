# admin_app/urls.py
from django.urls import path
from . import views

app_name = 'admin'  # Namespace: {% url 'admin:listar_pacientes' %}
##
app_name = 'gestion'

urlpatterns = [
    path('dashboard/', views.dashboard_admin, name='dashboard'),
    # ... otras URLs del administrador de gestión
]
##
urlpatterns = [
   path('dashboard/', views.dashboard_admin, name='dashboard_admin'),

    # Pacientes
    path('pacientes/', views.listar_pacientes, name='listar_pacientes'),
    path('pacientes/crear/', views.crear_paciente, name='crear_paciente'),
    path('pacientes/editar/<int:pk>/', views.editar_paciente, name='editar_paciente'),
    path('pacientes/detalle/<int:pk>/', views.detalle_paciente, name='detalle_paciente'),

    # Salas y Camas
    path('salas/', views.listar_salas, name='listar_salas'),
    path('salas/crear/', views.crear_sala, name='crear_sala'),
    path('camas/', views.listar_camas, name='listar_camas'),
    path('camas/crear/', views.crear_cama, name='crear_cama'),

    # Internaciones
    path('internaciones/', views.listar_internaciones, name='listar_internaciones'),
    path('internaciones/ingreso/', views.crear_internacion, name='crear_internacion'),
    path('internaciones/egreso/<int:pk>/', views.registrar_egreso, name='registrar_egreso'),
    
    # Personal
    path('personal/', views.listar_personal, name='listar_personal'),
    path('personal/crear/', views.crear_personal, name='crear_personal'),
]