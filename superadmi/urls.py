# superadmi/urls.py
from django.urls import path
from . import views  # Importa las vistas de la misma carpeta

app_name = 'superadmin'  # Namespace para usar en templates: {% url 'superadmin:dashboard' %}

urlpatterns = [
    path('', views.dashboard_superadmin, name='dashboard'),
    
    # Hospitales
    path('hospitales/', views.listar_hospitales, name='listar_hospitales'),
    path('hospitales/crear/', views.crear_hospital, name='crear_hospital'),
    path('hospitales/editar/<int:pk>/', views.editar_hospital, name='editar_hospital'),
    path('hospitales/detalle/<int:pk>/', views.detalle_hospital, name='detalle_hospital'),
    
    # Usuarios
    path('usuarios/', views.listar_usuarios, name='listar_usuarios'),
    path('usuarios/crear/', views.crear_usuario, name='crear_usuario'),
    path('usuarios/editar/<int:pk>/', views.editar_usuario, name='editar_usuario'),
    
    # Roles y Especialidades
    path('roles/', views.listar_roles, name='listar_roles'),
    path('roles/crear/', views.crear_rol, name='crear_rol'),
    path('especialidades/', views.listar_especialidades, name='listar_especialidades'),
    path('especialidades/crear/', views.crear_especialidad, name='crear_especialidad'),
    
    # Auditoría y Config
    path('auditoria/', views.auditoria, name='auditoria'),
    path('configuracion/', views.configuracion_sistema, name='configuracion_sistema'),
]