from django.urls import path
from . import views

app_name = 'hospital'

urlpatterns = [
     
    # ==========================================
    # GESTIÓN GENERAL Y PANELES
    # ==========================================
    path('', views.home, name='home'),
    path('monitor-red/', views.monitor_red, name='monitor_red'),
    path('limpieza/', views.central_limpieza, name='central_limpieza'),

    # ==========================================
    # INFRAESTRUCTURA (CUARTOS Y CAMAS)
    # ==========================================
    path('infraestructura/', views.gestionar_infraestructura, name='gestionar_infraestructura'),
    
    # Nivel 2: Detalle por hospital y especialidad
    path('infraestructura/hospital/<int:hospital_id>/especialidad/<int:especialidad_id>/', 
         views.detalle_camas_especialidad, name='detalle_camas_especialidad'),
    
    # Gestión de Cuartos
    path('cuarto/crear/', views.crear_cuarto, name='crear_cuarto'),
    path('cuarto/editar/<int:cuarto_id>/', views.editar_cuarto, name='editar_cuarto'),
    
    # Gestión de Camas
    path('cama/crear/', views.crear_cama, name='crear_cama'),
    path('cama/editar/<int:cama_id>/', views.editar_cama, name='editar_cama'),
    path('cama/eliminar/<int:cama_id>/', views.eliminar_cama, name='eliminar_cama'),
    path('cama/<int:cama_id>/cambiar-estado/', views.cambiar_estado_cama, name='cambiar_estado_cama'),
    path('liberar-cama/<int:cama_id>/', views.liberar_cama, name='liberar_cama'),
    path('limpieza/finalizar/<int:cama_id>/', views.finalizar_limpieza, name='finalizar_limpieza'),

    # ==========================================
    # GESTIÓN DE PACIENTES
    # ==========================================
    path('pacientes/', views.registrar_paciente, name='lista_pacientes'), 
    path('pacientes/editar/<int:paciente_id>/', views.registrar_paciente, name='editar_paciente'),
    path('pacientes/registrar/', views.registrar_paciente, name='registrar_paciente'),
    path('pacientes/eliminar/<int:pk>/', views.eliminar_paciente, name='eliminar_paciente'),
    
    # Flujo Clínico
    path('internar-paciente/', views.internar_paciente, name='internar_paciente'),
    path('paciente/<int:paciente_id>/historial/', views.historial_paciente, name='historial_paciente'),
    path('paciente/<int:paciente_id>/alta/', views.dar_alta_paciente, name='dar_alta_paciente'),
    path('paciente/trasladar/<int:paciente_id>/', views.trasladar_paciente, name='trasladar_paciente'),

    # ==========================================
    # RED HOSPITALARIA Y DERIVACIONES
    # ==========================================
    path('especialidad/crear/', views.crear_especialidad, name='crear_especialidad'),
    path('buscar-cupo/<int:especialidad_id>/', views.buscar_cupo_red, name='buscar_cupo_red'),
    
    # Proceso de Traslado
    path('derivacion/<int:paciente_id>/', views.solicitar_derivacion, name='derivar_paciente'),
    path('confirmar-recepcion/<int:derivacion_id>/', views.confirmar_recepcion, name='confirmar_recepcion'),
    path('derivacion/<int:derivacion_id>/pdf/', views.generar_pdf_traslado, name='pdf_traslado'),

    # ==========================================
    # GESTIÓN DE AMBULANCIAS
    # ==========================================
   path('ambulancias/', views.gestion_ambulancias, name='ambulancias'),
# hospital/urls.py
path('ambulancias/', views.gestion_ambulancias, name='ambulancias'),
# Añadimos una ruta específica para el monitor si no la tienes
path('monitor-red/', views.monitor_red, name='monitor_red'),
    # Esta es la que recibe el POST del Modal
    path('ambulancias/guardar/', views.guardar_ambulancia, name='guardar_ambulancia'),
    path('ambulancias/editar/<int:pk>/', views.editar_ambulancia, name='editar_ambulancia'),
path('ambulancias/eliminar/<int:pk>/', views.eliminar_ambulancia, name='eliminar_ambulancia'),
path('vincular-ambulancia/<int:paciente_id>/<int:ambulancia_id>/', 
     views.vincular_ambulancia, 
     name='vincular_ambulancia'),
    # Esta es para cuando el chofer cambia el estado (Disponible/En Camino)
    path('ambulancias/chofer/panel/<int:ambulancia_id>/', views.panel_chofer, name='panel_chofer'),
    path('ambulancias/chofer/estado/<int:ambulancia_id>/<str:nuevo_estado>/', 
         views.cambiar_estado_ambulancia, name='cambiar_estado'),
    
    # Vincular con paciente en el flujo de derivación
    path('ambulancias/vincular/<int:paciente_id>/<int:ambulancia_id>/', 
         views.vincular_ambulancia_paciente, name='vincular_ambulancia'),
    ##formularios 
    path('paciente/<int:paciente_id>/formulario-d7/', views.formulario_d7_view, name='formulario_d7'),
    path('paciente/<int:paciente_id>/formulario-d7a/', views.formulario_d7a_view, name='formulario_d7a'),
    path('paciente/<int:paciente_id>/formulario-d7b/', views.formulario_d7b_view, name='formulario_d7b'),
    path('ambulancias/', views.gestion_ambulancias, name='ambulancias'),
    path('vincular-ambulancia/<int:paciente_id>/<int:ambulancia_id>/', 
     views.vincular_ambulancia_paciente, 
     name='vincular_ambulancia'),
     ###reporte diario
     path('disponibilidad/', views.monitor_disponibilidad, name='monitor_disponibilidad'),
     path('disponibilidad/registrar/', views.registrar_reporte_diario, name='registrar_reporte'),
     path('disponibilidad/registrar/', views.registrar_reporte_diario, name='crear_reporte'),
     path('incidencia/seleccionar/', views.seleccionar_tipo_incidencia, name='seleccionar_tipo'),
     path('incidencia/nueva/', views.registrar_incidencia, name='registrar_incidencia_vacia'),
     path('incidencia/nueva/<str:tipo>/', views.registrar_incidencia, name='registrar_incidencia'),
     ###funcion roles 
     path('landing/', views.landing_page, name='landing_page'),
     ###CIE URLS
     path('buscar-cie10/', views.buscar_cie10_ajax, name='buscar_cie10_ajax'),
]