from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Cuarto, Cama, Especialidad, Hospital, Paciente, Derivacion
from .forms import CuartoForm, CamaForm, PacienteForm, EvolucionMedicaForm, DerivacionForm
from superadmi.models import Hospital, Usuario
from django.db.models import Count, Q, ExpressionWrapper, FloatField
from django.utils import timezone
from django.urls import reverse
@login_required
def home(request):
    """
    Redirige al usuario a su panel correspondiente según su ROL
    basado en el modelo de Usuario del Sprint 1.
    """
    usuario = request.user
    
    # Verificamos si el usuario tiene un rol asignado
    if hasattr(usuario, 'rol') and usuario.rol:
        rol_nombre = usuario.rol.nombre.upper()
        
        if rol_nombre == 'SUPERADMIN' or rol_nombre == 'SISTEMAADMI':
            return redirect('superadmin:dashboard') # Ajusta según tu name de URL
        elif rol_nombre == 'DOCTOR':
            return redirect('hospital:panel_doctor')
        elif rol_nombre == 'ENFERMERA':
            return redirect('hospital:panel_enfermera')
        elif rol_nombre == 'ADMINISTRADOR':
            return redirect('hospital:panel_administrador')
    
    # Si no tiene rol o no es reconocido
    return render(request, 'hospital/sin_acceso.html')

# ==========================================
# GESTIÓN DE INFRAESTRUCTURA (CUARTOS Y CAMAS)
# ==========================================

@login_required
def gestionar_infraestructura(request):
    hospital_id = request.GET.get('hospital_id')
    piso_filtro = request.GET.get('piso') # Nuevo filtro
    hospital = get_object_or_404(Hospital, id=hospital_id)

    # Obtenemos especialidades con contadores detallados
    especialidades = Especialidad.objects.filter(cuartos__hospital=hospital)
    
    if piso_filtro:
        especialidades = especialidades.filter(cuartos__piso=piso_filtro)

    especialidades = especialidades.annotate(
        total_camas=Count('cuartos__camas'),
        libres=Count('cuartos__camas', filter=Q(cuartos__camas__estado='LIBRE')),
        ocupadas=Count('cuartos__camas', filter=Q(cuartos__camas__estado='OCUPADO')),
        mantenimiento=Count('cuartos__camas', filter=Q(cuartos__camas__estado='MANTENIMIENTO')),
        limpieza=Count('cuartos__camas', filter=Q(cuartos__camas__estado='EN LIMPIEZA')),
        reserva=Count('cuartos__camas', filter=Q(cuartos__camas__estado='RESERVADO')),
    ).distinct()

    # Obtener lista de pisos disponibles para el buscador
    lista_pisos = Cuarto.objects.filter(hospital=hospital).values_list('piso', flat=True).distinct().order_by('piso')

    return render(request, 'hospital/especialidades_list.html', {
        'hospital': hospital,
        'especialidades': especialidades,
        'lista_pisos': lista_pisos,
        'piso_seleccionado': piso_filtro
    })

@login_required
def detalle_camas_especialidad(request, hospital_id, especialidad_id):
    """NIVEL 2: Vista de Camas de una especialidad específica"""
    hospital = get_object_or_404(Hospital, id=hospital_id)
    especialidad = get_object_or_404(Especialidad, id=especialidad_id)
    
    # Filtrar cuartos y camas
    cuartos = Cuarto.objects.filter(
        hospital=hospital, 
        especialidad=especialidad
    ).prefetch_related('camas')

    # --- CORRECCIÓN: CÁLCULO DE CONTADORES ---
    todas_las_camas = Cama.objects.filter(cuarto__in=cuartos)
    stats = {
        'total': todas_las_camas.count(),
        'libres': todas_las_camas.filter(estado='LIBRE').count(),
        'ocupadas': todas_las_camas.filter(estado='OCUPADO').count(),
        'limpieza': todas_las_camas.filter(estado__in=['LIMPIEZA', 'MANTENIMIENTO']).count(),
    }

    pacientes_sin_cama = Paciente.objects.filter(
        hospital=hospital, 
        cama_asignada__isnull=True, 
        estado='INTERNADO'
    )
    
    lista_hospitales = Hospital.objects.exclude(id=hospital.id).order_by('nombre')

    return render(request, 'hospital/detalle_camas.html', {
        'hospital': hospital,
        'especialidad': especialidad,
        'cuartos': cuartos,
        'stats': stats,  # Enviar stats corregido
        'pacientes_sin_cama': pacientes_sin_cama,
        'lista_hospitales': lista_hospitales,
    })
def crear_cuarto(request):
    if request.method == 'POST':
        # Obtenemos el ID del hospital que viene del input hidden
        hospital_id = request.POST.get('hospital')
        especialidad_id = request.POST.get('especialidad')
        
        try:
            h = Hospital.objects.get(id=hospital_id)
            e = Especialidad.objects.get(id=especialidad_id)
            
            Cuarto.objects.create(
                hospital=h,
                especialidad=e,
                numero_cuarto=request.POST.get('numero_cuarto'),
                piso=request.POST.get('piso')
            )
            messages.success(request, "Cuarto creado con éxito.")
            return redirect(f"/hospital/infraestructura/?hospital_id={hospital_id}")
            
        except Exception as err:
            messages.error(request, f"Error al crear cuarto: {err}")
            # Si hay error, intentamos volver a la infraestructura si tenemos el ID
            if hospital_id:
                return redirect(f"/hospital/infraestructura/?hospital_id={hospital_id}")
            return redirect('superadmin:dashboard_superadmin')
            
    return redirect('superadmin:dashboard_superadmin')

def agregar_cama(request, cuarto_id):
    cuarto = get_object_or_404(Cuarto, id=cuarto_id)
    if request.method == 'POST':
        numero = request.POST.get('numero_cama')
        if numero:
            Cama.objects.create(cuarto=cuarto, numero=numero, estado='LIBRE')
            messages.success(request, f"Cama {numero} agregada al cuarto {cuarto.numero_cuarto}.")
        else:
            messages.error(request, "El número de cama es obligatorio.")
            
    return redirect(f"/hospital/infraestructura/?hospital_id={cuarto.hospital.id}")

def editar_cuarto(request, cuarto_id):
    if request.method == 'POST':
        cuarto = get_object_or_404(Cuarto, id=cuarto_id)
        
        # Obtenemos los datos del formulario (los nombres deben coincidir con el HTML)
        nuevo_numero = request.POST.get('numero_cuarto')
        nuevo_piso = request.POST.get('piso')
        
        try:
            cuarto.numero_cuarto = nuevo_numero
            cuarto.piso = nuevo_piso
            cuarto.save()
            messages.success(request, f"El cuarto {cuarto.numero_cuarto} se actualizó correctamente.")
        except Exception as e:
            messages.error(request, f"Error al actualizar: {e}")
            
        # Redirigimos de vuelta a la infraestructura de ese hospital
        return redirect(f'/hospital/infraestructura/?hospital_id={cuarto.hospital.id}')
    
    return redirect('superadmin:dashboard_superadmin')

def editar_cama(request, cama_id):
    if request.method == 'POST':
        cama = get_object_or_404(Cama, id=cama_id)
        nuevo_nombre = request.POST.get('numero_cama') # El nombre que viene del input
        
        if nuevo_nombre:
            cama.numero = nuevo_nombre
            cama.save()
            messages.success(request, f"Cama actualizada a: {nuevo_nombre}")
        
        # Redirigir a la misma página de infraestructura
        return redirect(f'/hospital/infraestructura/?hospital_id={cama.cuarto.hospital.id}')
    
    return redirect('superadmin:dashboard_superadmin')

@login_required
def lista_pacientes(request):
    # Solo pacientes internados para la gestión diaria
    pacientes = Paciente.objects.filter(estado='INTERNADO').select_related('hospital', 'cama_asignada__cuarto')
    return render(request, 'hospital/lista_pacientes.html', {'pacientes': pacientes})

@login_required
def historial_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    evoluciones = paciente.evoluciones.all().order_by('-fecha_registro')
    
    if request.method == 'POST':
        form = EvolucionMedicaForm(request.POST)
        if form.is_valid():
            evolucion = form.save(commit=False)
            evolucion.paciente = paciente
            # Asignamos al médico/usuario actual
            evolucion.creado_por = request.user
            evolucion.save()
            messages.success(request, "Nota médica añadida correctamente.")
            return redirect('hospital:historial_paciente', paciente_id=paciente.id)
    else:
        form = EvolucionMedicaForm()
        
    return render(request, 'hospital/historial_paciente.html', {
        'paciente': paciente,
        'evoluciones': evoluciones,
        'form': form
    })
@login_required
def internar_paciente(request):
    if request.method == 'POST':
        cama_id = request.POST.get('cama_id')
        paciente_id = request.POST.get('paciente_id')
        
        cama = get_object_or_404(Cama, id=cama_id)
        paciente = get_object_or_404(Paciente, id=paciente_id)
        
        # Lógica de unión
        cama.estado = 'OCUPADO'
        cama.save()
        
        paciente.cama_asignada = cama
        paciente.save()
        
        messages.success(request, f"Paciente {paciente.nombre_completo} asignado a Cama {cama.numero}")
        return redirect(f"{reverse('hospital:gestionar_infraestructura')}?hospital_id={cama.cuarto.hospital.id}")
    
    return redirect('hospital:home')

@login_required
def dar_alta_paciente(request, paciente_id): 
    paciente = get_object_or_404(Paciente, id=paciente_id)
    
    # 1. Liberar la cama definitivamente
    if paciente.cama_asignada:
        cama = paciente.cama_asignada
        cama.estado = 'LIMPIEZA'
        cama.paciente_actual = None
        cama.save()
    
    # 2. Cambiar estado del paciente para que aparezca en el Historial
    paciente.estado = 'ALTA'
    paciente.cama_asignada = None
    paciente.save()
    
    messages.success(request, f"Alta registrada para {paciente.nombre_completo}")
    return redirect('hospital:historial_paciente', paciente_id=paciente.id)

@login_required
def registrar_paciente(request):
    if request.method == 'POST':
        form = PacienteForm(request.POST)
        if form.is_valid():
            paciente = form.save(commit=False)
            if paciente.cama_asignada:
                cama = paciente.cama_asignada
                cama.estado = 'OCUPADO'
                cama.save()
            paciente.save()
            messages.success(request, "Paciente registrado e internado con éxito.")
            return redirect('hospital:lista_pacientes')
    else:
        form = PacienteForm()
    return render(request, 'hospital/registrar_paciente.html', {'form': form})

@login_required
def detalle_camas_especialidad(request, hospital_id, especialidad_id):
    hospital = get_object_or_404(Hospital, id=hospital_id)
    especialidad = get_object_or_404(Especialidad, id=especialidad_id)
    
    cuartos = Cuarto.objects.filter(hospital=hospital, especialidad=especialidad).prefetch_related('camas')

    # --- AGREGAR ESTO: Camas libres de TODO el hospital para traslados ---
    todas_las_camas_libres = Cama.objects.filter(
        cuarto__hospital=hospital, 
        estado='LIBRE'
    ).select_related('cuarto', 'cuarto__especialidad')

    # Estadísticas
    todas_las_camas = Cama.objects.filter(cuarto__in=cuartos)
    stats = {
        'total': todas_las_camas.count(),
        'libres': todas_las_camas.filter(estado='LIBRE').count(),
        'ocupadas': todas_las_camas.filter(estado='OCUPADO').count(),
        'limpieza': todas_las_camas.filter(estado__in=['LIMPIEZA', 'MANTENIMIENTO']).count(),
    }

    pacientes_sin_cama = Paciente.objects.filter(hospital=hospital, cama_asignada__isnull=True, estado='INTERNADO')
    lista_hospitales = Hospital.objects.exclude(id=hospital.id).order_by('nombre')

    return render(request, 'hospital/detalle_camas.html', {
        'hospital': hospital,
        'especialidad': especialidad,
        'cuartos': cuartos,
        'stats': stats,
        'pacientes_sin_cama': pacientes_sin_cama,
        'lista_hospitales': lista_hospitales,
        'todas_las_camas_libres': todas_las_camas_libres, # <--- IMPORTANTE
    })

def cambiar_estado_cama(request, cama_id):
    cama = get_object_or_404(Cama, id=cama_id)
    hospital_id = cama.cuarto.hospital.id 
    especialidad_id = cama.cuarto.especialidad.id
    
    # Lógica de rotación corregida:
    if cama.estado == 'LIBRE':
        cama.estado = 'MANTENIMIENTO'
    elif cama.estado == 'MANTENIMIENTO':
        cama.estado = 'LIMPIEZA'
    elif cama.estado == 'LIMPIEZA':
        cama.estado = 'LIBRE'
    elif cama.estado == 'OCUPADO':
        messages.warning(request, f"La cama {cama.numero} está ocupada.")
        # Redirigir a detalle_camas_especialidad para no perder la vista
        return redirect('hospital:detalle_camas_especialidad', hospital_id=hospital_id, especialidad_id=especialidad_id)
    
    cama.save()
    messages.info(request, f"Cama {cama.numero} actualizada.")
    
    # CORRECCIÓN: Redirigir de vuelta a la especialidad, NO a infraestructura general
    return redirect('hospital:detalle_camas_especialidad', hospital_id=hospital_id, especialidad_id=especialidad_id)
@login_required
def liberar_cama(request, cama_id):
    cama = get_object_or_404(Cama, id=cama_id)
    if cama.estado == 'LIMPIEZA':
        cama.estado = 'LIBRE'
        cama.save()
        messages.success(request, f"La cama {cama.numero} ha sido desinfectada y está LIBRE.")
    return redirect('hospital:central_limpieza')
def eliminar_cama(request, cama_id):
    cama = get_object_or_404(Cama, id=cama_id)
    hospital_id = cama.cuarto.hospital.id
    cama.delete()
    return redirect(f"{reverse('hospital:gestionar_infraestructura')}?hospital_id={hospital_id}")

@login_required
def buscar_cupo_red(request, especialidad_id):
    # Buscamos hospitales que tengan al menos una cama LIBRE en esa especialidad
    hospitales_con_cupo = Hospital.objects.filter(
        cuartos__especialidad_id=especialidad_id,
        cuartos__camas__estado='LIBRE'
    ).annotate(
        camas_disponibles=Count('cuartos__camas', filter=Q(cuartos__camas__estado='LIBRE'))
    ).filter(camas_disponibles__gt=0)

    return render(request, 'hospital/buscar_cupo.html', {
        'hospitales': hospitales_con_cupo,
        'especialidad': Especialidad.objects.get(id=especialidad_id)
    })

@login_required
def monitor_red(request):
    # 1. Red hospitalaria con conteos automáticos corregidos
    red_hospitalaria = Hospital.objects.annotate(
        total_camas=Count('cuartos__camas'),
        libres=Count('cuartos__camas', filter=Q(cuartos__camas__estado='LIBRE')),
        ocupadas=Count('cuartos__camas', filter=Q(cuartos__camas__estado='OCUPADO')),
        limpieza=Count('cuartos__camas', filter=Q(cuartos__camas__estado='LIMPIEZA')),
        mantenimiento=Count('cuartos__camas', filter=Q(cuartos__camas__estado='MANTENIMIENTO')) # <-- FALTA ESTA LÍNEA
    ).order_by('-libres')

    # 2. Lógica para "Ver Detalles"
    hosp_id = request.GET.get('hosp_id')
    pacientes_seleccionados = None
    hosp_nombre = ""

    if hosp_id:
        hosp_seleccionado = get_object_or_404(Hospital, id=hosp_id)
        hosp_nombre = hosp_seleccionado.nombre
        pacientes_seleccionados = Paciente.objects.filter(
            hospital=hosp_seleccionado, 
            estado='INTERNADO'
        ).select_related('cama_asignada__cuarto__especialidad')

    # 3. Traslados activos (cuadro negro)
    derivaciones_activas = Derivacion.objects.filter(
        estado='PENDIENTE'
    ).select_related('paciente', 'hospital_origen', 'hospital_destino')

    # --- NUEVOS INDICADORES (ESTADÍSTICAS) ---
    traslados_hoy = Derivacion.objects.filter(
        fecha_solicitud__date=timezone.now().date()
    ).count()

    en_camino = derivaciones_activas.count()

    # Buscamos el hospital con más camas libres para la "Mejor Opción"
    hospital_mas_libre = None
    if red_hospitalaria:
        hospital_mas_libre = max(red_hospitalaria, key=lambda x: x.libres)
    # 4. Historial de traslados finalizados (los últimos 5)
    historial_traslados = Derivacion.objects.filter(
        estado='COMPLETADO'
    ).select_related('paciente', 'hospital_origen', 'hospital_destino').order_by('-id')[:5]
    
    return render(request, 'hospital/monitor_red.html', {
        'red': red_hospitalaria,
        'derivaciones': derivaciones_activas,
        'pacientes': pacientes_seleccionados,
        'hosp_nombre': hosp_nombre,
        # Nuevos datos:
        'traslados_hoy': traslados_hoy,
        'en_camino': en_camino,
        'hosp_libre': hospital_mas_libre,
        'historial': historial_traslados,
    })

@login_required
def solicitar_derivacion(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    # Mostramos todos los hospitales excepto donde ya está el paciente
    hospitales_destino = Hospital.objects.exclude(id=paciente.hospital.id)

    if request.method == 'POST':
        destino_id = request.POST.get('hospital_destino')
        motivo_form = request.POST.get('motivo')
        prioridad_form = request.POST.get('prioridad', 'MEDIA')

        # 1. Liberar la cama actual y resetearla por completo
        if paciente.cama_asignada:
            cama_actual = paciente.cama_asignada
            cama_actual.estado = 'LIMPIEZA'
            cama_actual.paciente_actual = None  # IMPORTANTE: Quitar al paciente de la cama
            cama_actual.save()

        # 2. Crear la derivación
        from .models import Derivacion
        Derivacion.objects.create(
            paciente=paciente,
            hospital_origen=paciente.hospital,
            hospital_destino_id=destino_id,
            prioridad=prioridad_form,
            motivo_traslado=motivo_form,
            estado='PENDIENTE'
        )

        # 3. Desvincular al paciente de la cama y actualizar su estado
        paciente.cama_asignada = None
        paciente.estado = 'TRANSITO' # Opcional: para saber que no está en cama pero sigue bajo cuidado
        paciente.save()

        return redirect('hospital:monitor_red')

    return render(request, 'hospital/derivar_form.html', {
        'paciente': paciente, 
        'hospitales': hospitales_destino
    })
@login_required
def confirmar_recepcion(request, derivacion_id):
    derivacion = get_object_or_404(Derivacion, id=derivacion_id)
    
    if request.method == 'POST':
        cama_id = request.POST.get('cama_id')
        nueva_cama = get_object_or_404(Cama, id=cama_id)
        paciente = derivacion.paciente

        # --- PASO NUEVO: LIBERAR CAMA DE ORIGEN ---
        # Antes de moverlo, identificamos qué cama está dejando
        cama_anterior = paciente.cama_asignada
        if cama_anterior:
            cama_anterior.estado = 'LIMPIEZA' # <-- Aquí es donde activas el flujo de limpieza
            cama_anterior.save()

        # 1. Completar la derivación
        derivacion.estado = 'RECIBIDO'
        derivacion.save()
        
        # 2. Mover al paciente al nuevo hospital y asignar la nueva cama
        paciente.hospital = derivacion.hospital_destino
        paciente.cama_asignada = nueva_cama
        paciente.estado = 'INTERNADO'
        paciente.save()
        
        # 3. Ocupar la nueva cama
        nueva_cama.estado = 'OCUPADO'
        nueva_cama.save()
        
        messages.success(request, f"Paciente {paciente.nombre_completo} recibido. La cama de origen ha sido enviada a desinfección.")
        return redirect('hospital:monitor_red')

    # Si es GET, mostramos las camas libres del hospital destino
    camas_libres = Cama.objects.filter(cuarto__hospital=derivacion.hospital_destino, estado='LIBRE')
    return render(request, 'hospital/confirmar_recepcion.html', {
        'derivacion': derivacion,
        'camas_libres': camas_libres
    })

@login_required
def derivacion_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    # Buscamos hospitales que tengan camas LIBRES
    hospitales_disponibles = Hospital.objects.filter(cuartos__camas__estado='LIBRE').distinct()
    
    if request.method == 'POST':
        hospital_destino_id = request.POST.get('hospital_destino')
        # Aquí ejecutaríamos la lógica de "mover" al paciente
        # 1. Liberar cama actual
        # 2. Asignar nueva cama en destino
        # 3. Registrar en historial de traslados
        return redirect('hospital:monitor_red')

    return render(request, 'hospital/derivacion_form.html', {
        'paciente': paciente,
        'hospitales': hospitales_disponibles
    })
@login_required
def trasladar_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    
    if request.method == 'POST':
        tipo = request.POST.get('tipo_movimiento')
        
        # CASO A: Derivación a otro hospital (Externa)
        if tipo == 'externo':
            return redirect('hospital:derivar_paciente', paciente_id=paciente.id)
            
        # CASO B: Movimiento de cama (Interno)
        elif tipo == 'interno':
            nueva_cama_id = request.POST.get('nueva_cama_id')
            if nueva_cama_id:
                nueva_cama = get_object_or_404(Cama, id=nueva_cama_id)
                
                # 1. Liberar la cama donde estaba antes
                if paciente.cama_asignada:
                    cama_anterior = paciente.cama_asignada
                    cama_anterior.estado = 'LIMPIEZA'
                    cama_anterior.paciente_actual = None 
                    cama_anterior.save()
                
                # 2. Ocupar la nueva cama
                nueva_cama.estado = 'OCUPADO'
                nueva_cama.paciente_actual = paciente
                nueva_cama.save()
                
                # 3. Vincular paciente a la nueva cama
                paciente.cama_asignada = nueva_cama
                paciente.save()
                
                messages.success(request, f"Traslado interno exitoso a Cama {nueva_cama.numero}")
        
    return redirect(request.META.get('HTTP_REFERER', 'hospital:monitor_red'))
###para eñl pde
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO

@login_required
def generar_pdf_traslado(request, derivacion_id):
    derivacion = get_object_or_404(Derivacion, id=derivacion_id)
    
    data = {
        'derivacion': derivacion,
        'fecha': derivacion.fecha_solicitud,
    }
    
    # Cargar el template HTML para el PDF
    template = get_template('hospital/pdf_traslado.html')
    html = template.render(data)
    
    # Crear el PDF
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return HttpResponse("Error al generar el PDF", status=400)
@login_required
def central_limpieza(request):
    # Solo vemos camas que están en estado LIMPIEZA
    camas_sucias = Cama.objects.filter(estado='LIMPIEZA').select_related('cuarto__hospital')
    return render(request, 'hospital/central_limpieza.html', {'camas_sucias': camas_sucias})
@login_required
def finalizar_limpieza(request, cama_id):
    cama = get_object_or_404(Cama, id=cama_id)
    if cama.estado == 'LIMPIEZA':
        cama.estado = 'LIBRE'
        cama.save()
        messages.success(request, f"La cama {cama.numero} del {cama.cuarto.hospital.nombre} ahora está disponible.")
    return redirect('hospital:central_limpieza')
