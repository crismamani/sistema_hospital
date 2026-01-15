# enfermera/urls.py
from django.urls import path
from . import views
###login
from django.urls import path
from . import views

app_name = 'enfermeria'

urlpatterns = [
    path('dashboard/', views.dashboard_enfermeria, name='dashboard'),
    # ... otras URLs de enfermería
]
###login
app_name = 'enfermeria'  # Namespace: {% url 'enfermeria:mapa_camas' %}

urlpatterns = [
    path('dashboard/', views.dashboard_enfermera, name='dashboard_enfermera'),
    
    # Gestión Visual
    path('mapa-camas/', views.mapa_camas, name='mapa_camas'),
    
    # Detalle Paciente Operativo
    ##path('paciente/<int:pk>/detalle/', views.detalle_paciente_enfermeria, name='detalle_paciente'),
    
    # Acciones Diarias
    #path('internacion/<int:internacion_id>/signos/', views.registrar_signos_vitales, name='registrar_signos_vitales'),
    #path('internacion/<int:internacion_id>/nota/', views.nota_enfermeria, name='nota_enfermeria'),
    path('internacion/<int:internacion_id>/transferir/', views.transferencia_interna, name='transferencia_interna'),
]