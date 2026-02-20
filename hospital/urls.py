from django.urls import path
from . import views

app_name = 'hospital'

urlpatterns = [
    # --- Gestión General ---
    path('', views.home, name='home'),
    path('monitor-red/', views.monitor_red, name='monitor_red'),
    path('limpieza/', views.central_limpieza, name='central_limpieza'),

    # --- Infraestructura ---
    path('infraestructura/', views.gestionar_infraestructura, name='gestionar_infraestructura'),
    # ESTA ES LA URL QUE USAS EN EL NIVEL 2:
    path('infraestructura/hospital/<int:hospital_id>/especialidad/<int:especialidad_id>/', 
         views.detalle_camas_especialidad, name='detalle_camas_especialidad'),
    
    path('infraestructura/cuarto/crear/', views.crear_cuarto, name='crear_cuarto'),
    path('infraestructura/cama/agregar/<int:cuarto_id>/', views.agregar_cama, name='agregar_cama'),
    path('cambiar-estado-cama/<int:cama_id>/', views.cambiar_estado_cama, name='cambiar_estado_cama'),
    path('liberar-cama/<int:cama_id>/', views.liberar_cama, name='liberar_cama'),
    path('limpieza/finalizar/<int:cama_id>/', views.finalizar_limpieza, name='finalizar_limpieza'),
    
    path('internar-paciente/', views.internar_paciente, name='internar_paciente'),
    path('paciente/trasladar/<int:paciente_id>/', views.trasladar_paciente, name='trasladar_paciente'),

    # --- Gestión de Pacientes ---
    path('pacientes/', views.lista_pacientes, name='lista_pacientes'),
    path('pacientes/registrar/', views.registrar_paciente, name='registrar_paciente'),
    path('paciente/<int:paciente_id>/historial/', views.historial_paciente, name='historial_paciente'),
    path('paciente/<int:paciente_id>/alta/', views.dar_alta_paciente, name='dar_alta_paciente'),
    path('cama/<int:cama_id>/cambiar-estado/', views.cambiar_estado_cama, name='cambiar_estado_cama'),
   

    # --- Derivaciones ---
    # Cambiado para que coincida con tu función: solicitar_derivacion
    path('derivacion/<int:paciente_id>/', views.solicitar_derivacion, name='derivar_paciente'),
    path('confirmar-recepcion/<int:derivacion_id>/', views.confirmar_recepcion, name='confirmar_recepcion'),
    path('derivacion/<int:derivacion_id>/pdf/', views.generar_pdf_traslado, name='pdf_traslado'),
]