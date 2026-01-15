from django.urls import path
from . import views

app_name = 'superadmin'

urlpatterns = [
    # Autenticación
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard Principal
    path('', views.dashboard_superadmin, name='dashboard_superadmin'),
    path('redirect/', views.dashboard_redirect, name='dashboard_redirect'),
    
    # Hospitales
    path('hospitales/', views.listar_hospitales, name='listar_hospitales'),
    path('hospitales/crear/', views.crear_hospital, name='crear_hospital'),
    path('hospitales/editar/<int:pk>/', views.editar_hospital, name='editar_hospital'),
    path('hospitales/eliminar/<int:pk>/', views.eliminar_hospital, name='eliminar_hospital'),
    
    # Usuarios
    path('usuarios/', views.listar_usuarios, name='listar_usuarios'),
    path('usuarios/registrar/', views.registrar_personal, name='registrar_personal'),
    path('usuarios/editar/<int:pk>/', views.editar_usuario, name='editar_usuario'),
    path('usuarios/eliminar/<int:pk>/', views.eliminar_usuario, name='eliminar_usuario'),
    
    # Roles y Especialidades
    path('roles/', views.listar_roles, name='listar_roles'),
    path('especialidades/', views.listar_especialidades, name='listar_especialidades'),
    path('especialidades/crear/', views.crear_especialidad, name='crear_especialidad'),
    
    # Auditoría y Configuración
    path('auditoria/', views.auditoria, name='auditoria'),
    path('configuracion/', views.configuracion_sistema, name='configuracion_sistema'),

    # Pacientes y Camas
    path('pacientes/', views.listar_pacientes, name='listar_pacientes'),
    path('crear-camas-prueba/', views.crear_camas_prueba, name='crear_camas_prueba'),
    
    # Gestión de Capacidades (HospitalEspecialidad)
    path('capacidades/', views.listar_capacidades, name='listar_capacidades'),
    path('capacidades/asignar/', views.asignar_capacidad, name='asignar_capacidad'),
    path('capacidades/editar/<int:pk>/', views.editar_capacidad, name='editar_capacidad'),
]