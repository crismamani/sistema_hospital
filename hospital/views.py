from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Cuarto, Cama, Paciente, Derivacion, EvolucionMedica, Ambulancia, FormularioD7b, FormularioD7, ContrarreferenciaD7a, ReporteDiario, IncidenciaCRUEM 
from .forms import CuartoForm, CamaForm, PacienteForm, EvolucionMedicaForm, DerivacionForm, D7bForm, D7Form, ContrarreferenciaD7aForm,ReporteDiarioForm
from superadmi.models import Hospital, Usuario, Especialidad
from django.db.models import Count, Q, ExpressionWrapper, FloatField
from django.utils import timezone
from django.urls import reverse
from django.db import transaction
from datetime import datetime
from .decorators import solo_roles # Importación local
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
    piso_filtro = request.GET.get('piso')
    
    if not hospital_id:
        return HttpResponseBadRequest("Falta el ID del hospital")

    hospital = get_object_or_404(Hospital, id=hospital_id)

    # 1. Obtenemos las especialidades con presencia en este hospital
    especialidades_ids = Cuarto.objects.filter(
        hospital=hospital
    ).values_list('especialidad_id', flat=True).distinct()

    especialidades_del_hospital = Especialidad.objects.filter(id__in=especialidades_ids)

    especialidades_con_datos = []
    
    for esp in especialidades_del_hospital:
        cuartos_qs = Cuarto.objects.filter(hospital=hospital, especialidad=esp)
        
        if piso_filtro:
            cuartos_qs = cuartos_qs.filter(piso=piso_filtro)
            if not cuartos_qs.exists():
                continue

        camas_qs = Cama.objects.filter(cuarto__in=cuartos_qs)
        
        # --- CÁLCULO DE CARGA ---
        total = camas_qs.count()
        ocupadas = camas_qs.filter(estado='OCUPADO').count()
        carga = (ocupadas / total * 100) if total > 0 else 0
        
        if carga > 80: color = 'danger'
        elif carga > 50: color = 'warning'
        else: color = 'success'

        especialidades_con_datos.append({
            'id': esp.id,
            'nombre': esp.nombre,
            'total_camas': total,
            'libres': camas_qs.filter(estado='LIBRE').count(),
            'ocupadas': ocupadas,
            'mantenimiento': camas_qs.filter(estado='MANTENIMIENTO').count(),
            'limpieza': camas_qs.filter(estado='LIMPIEZA').count(),
            'reserva': camas_qs.filter(estado='RESERVADO').count(),
            'carga': round(carga, 1),
            'color_carga': color,
        })

    lista_pisos = Cuarto.objects.filter(hospital=hospital).values_list('piso', flat=True).distinct().order_by('piso')

    return render(request, 'hospital/especialidades_list.html', {
        'hospital': hospital,
        'especialidades': especialidades_con_datos,
        'lista_pisos': lista_pisos,
        'piso_seleccionado': piso_filtro
    })

def crear_especialidad(request):
    if request.method == 'POST':
        nombre_esp = request.POST.get('nombre')
        hospital_id = request.POST.get('hospital_id')
        piso_form = request.POST.get('piso', 1)
        # El error 'NOT NULL constraint failed' venía de aquí (estaba llegando vacío)
        numero_cuarto = request.POST.get('numero_cuarto') 
        
        if not numero_cuarto:
            messages.error(request, "Debe asignar un número de cuarto para la especialidad.")
            return redirect(f"/hospital/infraestructura/?hospital_id={hospital_id}")

        if nombre_esp and hospital_id:
            hospital = get_object_or_404(Hospital, id=hospital_id)
            
            esp, created = Especialidad.objects.get_or_create(
                nombre=nombre_esp.upper().strip()
            )
            
            # Verificamos si la especialidad ya existe en ese hospital
            cuarto_existe = Cuarto.objects.filter(hospital=hospital, especialidad=esp).exists()
            
            if not cuarto_existe:
                try:
                    Cuarto.objects.create(
                        hospital=hospital,
                        especialidad=esp,
                        piso=piso_form,
                        numero_cuarto=numero_cuarto
                    )
                    messages.success(request, f"Especialidad '{nombre_esp}' registrada con éxito.")
                except IntegrityError:
                    # Ahora que IntegrityError está importado, esto funcionará perfecto
                    messages.error(request, f"Error: El número de cuarto {numero_cuarto} ya existe en este hospital.")
                except Exception as e:
                    messages.error(request, f"Error inesperado: {e}")
            else:
                messages.info(request, f"La especialidad '{nombre_esp}' ya está configurada para este hospital.")
        
        return redirect(f"/hospital/infraestructura/?hospital_id={hospital_id}")
    return redirect('superadmin:hospitales')

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
            # REDIRIGIR AL DETALLE DE ESA ESPECIALIDAD
            return redirect('hospital:detalle_camas_especialidad', hospital_id=h.id, especialidad_id=e.id)
            
        except Exception as err:
            messages.error(request, f"Error: {err}")
            return redirect(f"/hospital/infraestructura/?hospital_id={hospital_id}")
            
    return redirect('superadmin:dashboard_superadmin')
def crear_cama(request):
    if request.method == 'POST':
        cuarto_id = request.POST.get('cuarto_id')
        numero = request.POST.get('numero')
        
        try:
            cuarto = get_object_or_404(Cuarto, id=cuarto_id)
            Cama.objects.create(
                cuarto=cuarto, 
                numero=numero, 
                estado='LIBRE'
            )
            messages.success(request, f"Cama {numero} agregada al cuarto {cuarto.numero_cuarto}.")
        except Exception as e:
            messages.error(request, f"Error al crear cama: {e}")
            
        return redirect(request.META.get('HTTP_REFERER', '/'))
    return redirect('superadmin:dashboard_superadmin')

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
def registrar_paciente(request, paciente_id=None):
    # 1. Detectar si es edición o creación
    paciente_edit = get_object_or_404(Paciente, id=paciente_id) if paciente_id else None

    if request.method == 'POST':
        nombre = request.POST.get('nombre_completo')
        dni = request.POST.get('dni')
        cama_id = request.POST.get('cama_asignada')
        
        try:
            with transaction.atomic():
                if not paciente_edit:
                    paciente_edit = Paciente()
                    paciente_edit.estado = 'INTERNADO'
                    f_ent = request.POST.get('fecha_entrada')
                    paciente_edit.fecha_entrada = f_ent if f_ent and f_ent.strip() else timezone.now()
                else:
                    f_ent = request.POST.get('fecha_entrada')
                    if f_ent and f_ent.strip():
                        paciente_edit.fecha_entrada = f_ent

                # Asignación de datos
                paciente_edit.nombre_completo = nombre
                paciente_edit.dni = dni
                f_nac = request.POST.get('fecha_nacimiento')
                paciente_edit.fecha_nacimiento = f_nac if f_nac and f_nac.strip() else None
                paciente_edit.genero = request.POST.get('genero')
                paciente_edit.hospital_id = request.POST.get('hospital')
                paciente_edit.motivo_ingreso = request.POST.get('motivo_ingreso')
                paciente_edit.presion_arterial = request.POST.get('presion_arterial')
                paciente_edit.temperatura = float(request.POST.get('temperatura') or 0)
                paciente_edit.frecuencia_cardiaca = int(request.POST.get('frecuencia_cardiaca') or 0)
                paciente_edit.saturacion_oxigeno = int(request.POST.get('saturacion_oxigeno') or 0)
                
                # Lógica de Cama
                if cama_id:
                    nueva_cama = Cama.objects.get(id=cama_id)
                    if not paciente_edit.cama_asignada or paciente_edit.cama_asignada.id != int(cama_id):
                        if nueva_cama.estado == 'OCUPADO':
                            messages.error(request, f"La cama {nueva_cama.numero} ya está ocupada.")
                            return redirect('hospital:lista_pacientes')

                        if paciente_edit.cama_asignada:
                            c_anterior = paciente_edit.cama_asignada
                            c_anterior.estado = 'LIBRE'
                            c_anterior.save()
                        
                        nueva_cama.estado = 'OCUPADO'
                        nueva_cama.save()
                        paciente_edit.cama_asignada = nueva_cama
                
                paciente_edit.save()
                
                EvolucionMedica.objects.create(
                    paciente=paciente_edit,
                    tipo='RUTINA',
                    temperatura=paciente_edit.temperatura,
                    presion_arterial=paciente_edit.presion_arterial,
                    descripcion=f"INGRESO/ACTUALIZACIÓN: {paciente_edit.motivo_ingreso}",
                    creado_por=request.user
                )

                messages.success(request, f"Registro de {nombre} procesado correctamente.")
                # REDIRECCIÓN AL ALIAS (Para no romper dashboards)
                return redirect('hospital:lista_pacientes')

        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

    # --- Lógica GET ---
    pacientes = Paciente.objects.filter(estado='INTERNADO').order_by('-fecha_entrada')
    form = PacienteForm(instance=paciente_edit)
    
    # Filtrado dinámico de camas
    if paciente_edit and paciente_edit.cama_asignada:
        camas_disponibles = Cama.objects.filter(estado='LIBRE') | Cama.objects.filter(id=paciente_edit.cama_asignada.id)
    else:
        camas_disponibles = Cama.objects.filter(estado='LIBRE')
    
    form.fields['cama_asignada'].queryset = camas_disponibles
    
    # RENDER AL ARCHIVO RENOMBRADO
    return render(request, 'hospital/lista_pacientes.html', {
        'pacientes': pacientes, 
        'form': form,
        'paciente_edit': paciente_edit
    })
def eliminar_paciente(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)
    paciente.delete()
    return redirect('hospital:registrar_paciente')

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
    red_hospitalaria = Hospital.objects.annotate(
        total_camas=Count('cuartos__camas', distinct=True),
        libres=Count('cuartos__camas', filter=Q(cuartos__camas__estado='LIBRE'), distinct=True),
        ambulancias_count=Count('ambulancias', distinct=True)
    ).order_by('-libres')

    derivaciones_activas = Derivacion.objects.filter(estado='PENDIENTE').select_related(
        'paciente', 'hospital_origen', 'hospital_destino', 'ambulancia'
    ).order_by('-prioridad')

    # Indicadores
    traslados_hoy = Derivacion.objects.filter(fecha_solicitud__date=timezone.now().date()).count()
    unidades_listas = Ambulancia.objects.filter(estado='DISPONIBLE').count()
    en_movimiento = derivaciones_activas.filter(ambulancia__isnull=False).count()

    # Acción Ver Detalle
    hosp_id = request.GET.get('hosp_id')
    pacientes_internados = None
    hosp_nombre = ""
    if hosp_id:
        hosp_seleccionado = get_object_or_404(Hospital, id=hosp_id)
        hosp_nombre = hosp_seleccionado.nombre
        pacientes_internados = Paciente.objects.filter(
            hospital=hosp_seleccionado, estado='INTERNADO'
        ).select_related('cama_asignada__cuarto__especialidad')

    # Kardex
    kardex_recepcion = Derivacion.objects.filter(estado='COMPLETADO').select_related(
        'paciente', 'hospital_destino'
    ).order_by('-fecha_solicitud')[:10]

    return render(request, 'hospital/monitor_red.html', {
        'red': red_hospitalaria,
        'derivaciones': derivaciones_activas,
        'pacientes': pacientes_internados,
        'hosp_nombre': hosp_nombre,
        'traslados_hoy': traslados_hoy,
        'unidades_listas': unidades_listas,
        'en_camino': en_movimiento,
        'kardex': kardex_recepcion,
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
            estado='PENDIENTE',
            creado_por=request.user
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
@transaction.atomic
def confirmar_recepcion(request, derivacion_id):
    derivacion = get_object_or_404(Derivacion, id=derivacion_id)
    
    if request.method == 'POST':
        cama_id = request.POST.get('cama_id')
        nueva_cama = get_object_or_404(Cama, id=cama_id)
        paciente = derivacion.paciente

        # 1. Finalizar derivación
        derivacion.estado = 'COMPLETADO' 
        derivacion.fecha_recepcion = timezone.now() # Recomendado: guardar cuándo llegó
        derivacion.save()
        
        # 2. Actualizar Paciente al nuevo hospital
        paciente.hospital = derivacion.hospital_destino
        paciente.cama_asignada = nueva_cama
        paciente.estado = 'INTERNADO'
        paciente.save()
        
        # 3. Ocupar nueva cama y vincular paciente
        nueva_cama.estado = 'OCUPADO'
        nueva_cama.paciente_actual = paciente # No olvides esta relación inversa si la usas
        nueva_cama.save()

        # 4. Liberar Ambulancia
        if derivacion.ambulancia:
            ambulancia = derivacion.ambulancia
            ambulancia.estado = 'DISPONIBLE'
            ambulancia.save()
        
        messages.success(request, f"Paciente {paciente.nombre_completo} recibido correctamente.")
        return redirect('hospital:monitor_red')

    # Solo mostrar camas del hospital de DESTINO que estén LIBRES
    camas_libres = Cama.objects.filter(
        cuarto__hospital=derivacion.hospital_destino, 
        estado='LIBRE'
    )
    return render(request, 'hospital/confirmar_recepcion.html', {
        'derivacion': derivacion,
        'camas_libres': camas_libres
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

###ambulancias
@login_required
@solo_roles(['ADMIN', 'DOCTOR', 'SUPERADMIN'])
def gestion_ambulancias(request):
    estado_filtro = request.GET.get('estado') # Captura el clic del botón de color
    paciente_id = request.GET.get('paciente_id')
    paciente_obj = None
    
    # 1. Base de la consulta
    unidades = Ambulancia.objects.all()
    
    # 2. Obtener objeto paciente si existe (para el flujo de derivación)
    if paciente_id:
        from django.shortcuts import get_object_or_404
        paciente_obj = get_object_or_404(Paciente, id=paciente_id)
        # Si estamos derivando, queremos ver todas las unidades de la red
        unidades = Ambulancia.objects.all()

    # 3. Aplicar filtros de botones de colores si existen
    if estado_filtro == 'disponibles':
        unidades = unidades.filter(estado='DISPONIBLE')
    elif estado_filtro == 'movimiento':
        unidades = unidades.filter(estado='EN_CAMINO')
    
    # 4. FILTRO DE SEGURIDAD (CORREGIDO PARA EVITAR EL ATTRIBUTEERROR)
    # Cambiamos 'is_superuser' por la validación de tu campo 'rol'
    elif request.user.rol != 'ADMIN' and not paciente_id:
        unidades = unidades.filter(hospital=request.user.hospital)

    return render(request, 'hospital/ambulancias.html', {
        'hospital_unidades': unidades,
        'paciente_seleccion': paciente_obj, # No olvides pasar esto para el HTML
        'hospitales_lista': Hospital.objects.all(),
        'personal_choferes': Usuario.objects.all(),
        'titulo_listado': f"Unidades {estado_filtro.capitalize()}" if estado_filtro else "Gestión de Unidades"
    })
def guardar_ambulancia(request):
    if request.method == 'POST':
        placa = request.POST.get('placa')
        tipo = request.POST.get('tipo')
        modelo = request.POST.get('modelo')
        hospital_id = request.POST.get('hospital_id')
        chofer_texto = request.POST.get('chofer_texto')
        paciente_id = request.POST.get('paciente_id')

        # Creación robusta de la unidad
        nueva_unidad = Ambulancia.objects.create(
            placa=placa,
            tipo=tipo,
            modelo=modelo,
            hospital_id=hospital_id,
            estado='DISPONIBLE'
        )        
        # Redirección inteligente
        if paciente_id:
            return redirect(f"{reverse('hospital:ambulancias')}?paciente_id={paciente_id}")
            
    return redirect('hospital:ambulancias')

# NUEVA VISTA: Para conectar físicamente la ambulancia al paciente
def vincular_ambulancia_paciente(request, paciente_id, ambulancia_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    ambulancia = get_object_or_404(Ambulancia, id=ambulancia_id)
    
    # Asignamos la ambulancia
    paciente.ambulancia_asignada = ambulancia
    paciente.save()
    
    messages.success(request, f"Ambulancia {ambulancia.placa} asignada correctamente.")
    
    # Redirigimos usando el NAME correcto: 'derivar_paciente'
    # Y el parámetro correcto: 'paciente_id'
    return redirect('hospital:derivar_paciente', paciente_id=paciente.id)

def guardar_ambulancia(request):
    if request.method == 'POST':
        placa = request.POST.get('placa')
        tipo = request.POST.get('tipo')
        modelo = request.POST.get('modelo')
        
        # Creamos la ambulancia amarrada al hospital del usuario logueado
        Ambulancia.objects.create(
            placa=placa,
            tipo=tipo,
            modelo=modelo,
            hospital=request.user.hospital, # Esto garantiza la pertenencia
            estado='disponible'
        )
    return redirect('hospital:ambulancias')

def lista_ambulancias(request):
    # Esto busca todas las ambulancias para mostrarlas en una lista
    ambulancias = Ambulancia.objects.all()
    return render(request, 'hospital/lista_ambulancias.html', {
        'ambulancias': ambulancias
    })
def panel_chofer(request, ambulancia_id):
    # Obtenemos la ambulancia específica
    ambulancia = get_object_or_404(Ambulancia, id=ambulancia_id)
    return render(request, 'hospital/panel_chofer.html', {'ambulancia': ambulancia})

def cambiar_estado_ambulancia(request, ambulancia_id, nuevo_estado):
    ambulancia = get_object_or_404(Ambulancia, id=ambulancia_id)
    # Solo permitimos estados válidos
    if nuevo_estado in ['DISPONIBLE', 'EN_CAMINO', 'MANTENIMIENTO']:
        ambulancia.estado = nuevo_estado
        ambulancia.save()
    return redirect('hospital:panel_chofer', ambulancia_id=ambulancia.id)
def editar_ambulancia(request, pk): 
    unidad = get_object_or_404(Ambulancia, pk=pk)
    
    if request.method == 'POST':
        unidad.placa = request.POST.get('placa')
        unidad.tipo = request.POST.get('tipo')
        unidad.modelo = request.POST.get('modelo')
        unidad.estado = request.POST.get('estado')
        
        hospital_id = request.POST.get('hospital_id')
        if hospital_id:
            unidad.hospital_id = hospital_id
        # Si no hay hospital_id en el POST, NO hacemos nada para mantener el que ya tenía.
            
        unidad.nombre_chofer_manual = request.POST.get('chofer_texto')
        unidad.save()
        return redirect('hospital:ambulancias') # Nombre correcto
    
    return redirect('hospital:ambulancias')

def eliminar_ambulancia(request, pk):
    unidad = get_object_or_404(Ambulancia, pk=pk)
    unidad.delete()
    return redirect('hospital:ambulancias')
def vincular_ambulancia(request, paciente_id, ambulancia_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    ambulancia = get_object_or_404(Ambulancia, id=ambulancia_id)
    
    # Lógica de asignación
    ambulancia.estado = 'EN_CAMINO'
    # Aquí podrías guardar la relación en tu modelo de Traslado o Referencia
    ambulancia.save()
    
    return redirect('hospital:gestion_ambulancias')

def detalle_transferencia_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    
    # Filtramos ambulancias que no estén en misión
    ambulancias = Ambulancia.objects.filter(estado='DISPONIBLE')
    
    context = {
        'paciente': paciente,
        'ambulancias_activas': ambulancias,
        # Aquí podrías pasar instancias de tus 3 formularios
    }
    return render(request, 'hospital/modals/transferencia.html', context)

def formulario_d7_view(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    
    # Buscamos si ya existe uno
    instancia = FormularioD7.objects.filter(paciente=paciente).first()

    if request.method == 'POST':
        form = D7Form(request.POST, instance=instancia)
        if form.is_valid():
            f = form.save(commit=False)
            f.paciente = paciente
            f.save()
            return redirect('derivacion_detalle', paciente_id=paciente.id)
    else:
        form = D7Form(instance=instancia)

    # Renderiza el archivo que tienes en VS Code
    return render(request, 'hospital/formularios/D7.html', {
        'paciente': paciente,
        'form': form
    })

def formulario_d7a_view(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    # Renderiza el HTML de Consentimiento
    return render(request, 'hospital/formularios/D7a.html', {'paciente': paciente})

def formulario_d7b_view(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    
    # Buscamos si ya existe un registro para este paciente para editarlo, si no, creamos uno
    instancia = FormularioD7b.objects.filter(paciente=paciente).first()

    if request.method == 'POST':
        form = D7bForm(request.POST, instance=instancia)
        if form.is_valid():
            formulario_guardado = form.save(commit=False)
            formulario_guardado.paciente = paciente
            formulario_guardado.save()
            # Cambia 'detalle_derivacion' por el nombre de tu URL de retorno
            return redirect('detalle_derivacion', paciente_id=paciente.id)
    else:
        form = D7bForm(instance=instancia)

    # IMPORTANTE: La ruta debe coincidir con tu carpeta en VS Code
    return render(request, 'hospital/formularios/D7b.html', {
        'paciente': paciente,
        'form': form
    })
def crear_contrarreferencia_d7a(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    
    if request.method == 'POST':
        form = ContrarreferenciaD7aForm(request.POST)
        if form.is_valid():
            contrarreferencia = form.save(commit=False)
            contrarreferencia.paciente = paciente
            contrarreferencia.save()
            return redirect('detalle_paciente', pk=paciente.id)
    else:
        # Pre-llenamos datos si quieres que el médico trabaje menos
        form = ContrarreferenciaD7aForm(initial={
            'eess_contrarrefiere': 'HOSPITAL BRACAMONTE',
            'red_salud': 'POTOSÍ',
        })
    return render(request, 'tu_template.html', {'form': form, 'paciente': paciente})  

##reporte diario

@login_required
def monitor_disponibilidad(request):
    # 1. Obtenemos el mes y año actual
    ahora = datetime.now()
    
    # 2. Capturamos Mes, Año y HOSPITAL de la URL
    try:
        mes = int(request.GET.get('mes', ahora.month))
        anio = int(request.GET.get('anio', ahora.year))
        hospital_id = request.GET.get('hospital_id') # <-- NUEVO: Captura el hospital
    except ValueError:
        mes = ahora.month
        anio = ahora.year
        hospital_id = None

    # 3. Obtenemos todos los hospitales para el selector del template
    todos_hospitales = Hospital.objects.all()

    # 4. Buscamos qué días tienen reporte, filtrando por hospital si se seleccionó uno
    reportes_qs = ReporteDiario.objects.filter(fecha__month=mes, fecha__year=anio)
    
    hospital_seleccionado = None
    if hospital_id:
        hospital_seleccionado = get_object_or_404(Hospital, id=hospital_id)
        reportes_qs = reportes_qs.filter(hospital=hospital_seleccionado)

    registrados = reportes_qs.values_list('fecha__day', flat=True)

    # 5. Enviamos todo al contexto
    contexto = {
        'reportes_registrados': list(registrados),
        'mes_actual': mes,
        'anio_actual': anio,
        'hospitales': todos_hospitales,
        'hospital_id': int(hospital_id) if hospital_id else None,
        'hospital_seleccionado': hospital_seleccionado,
    }
    
    return render(request, 'hospital/calendario.html', contexto)

@login_required
def registrar_reporte_diario(request):
    if request.method == 'POST':
        form = ReporteDiarioForm(request.POST)
        if form.is_valid():
            try:
                reporte = form.save(commit=False)
                
                # Sincronización de Hospital: Prioridad al perfil del usuario
                if hasattr(request.user, 'hospital_pertenece') and request.user.hospital_pertenece:
                    reporte.hospital = request.user.hospital_pertenece
                elif hasattr(request.user, 'perfil') and request.user.perfil.hospital:
                    reporte.hospital = request.user.perfil.hospital
                else:
                    # Si es SuperAdmin sin hospital, intentamos agarrar el del formulario o el primero
                    reporte.hospital = Hospital.objects.first() 
                
                reporte.creado_por = request.user
                reporte.save()
                messages.success(request, "Reporte de turno guardado con éxito.")
                return redirect('hospital:monitor_disponibilidad')
            except Exception as e:
                messages.error(request, f"Error al guardar: {e}")
    else:
        form = ReporteDiarioForm()
    
    return render(request, 'hospital/reporte_diario.html', {'form': form})
def crear_reporte_diario(request):
    if request.method == 'POST':
        # Obtenemos el hospital del perfil del usuario (ajusta según tu modelo de Usuario)
        mi_hospital = request.user.hospital_pertenece 
        
        ReporteDiario.objects.create(
            hospital=mi_hospital,
            creado_por=request.user,
            personal_reporta=request.POST.get('personal_reporta'),
            # ... todos los demás campos ...
        )
        return redirect('hospital:monitor_disponibilidad')
    
    return render(request, 'hospital/reporte_diario.html')
def lista_reportes(request):
    # Añadimos filtro de hospital también a la lista general si se desea
    hospital_id = request.GET.get('hospital_id')
    reportes = ReporteDiario.objects.all().order_by('-fecha', '-hora')
    
    if hospital_id:
        reportes = reportes.filter(hospital_id=hospital_id)
        
    return render(request, 'hospital/lista_reportes.html', {
        'reportes': reportes,
        'hospitales': Hospital.objects.all()
    })

@login_required
def seleccionar_tipo_incidencia(request):
    return render(request, 'hospital/seleccionar_tipo.html')

@login_required
def registrar_incidencia(request, tipo=None):
    # 1. Si no hay tipo, redirigir a la selección
    if not tipo:
        return redirect('hospital:seleccionar_tipo')

    # 2. Diccionario para los títulos según el tipo
    nombres = {
        'PRE': '1 (338) PREHOSPITALARIA',
        'TRA': '2 (110) TRASLADO',
        'REF': '3 (167) REFERENCIA',
        'EVE': '4 EVENTO DEPORTIVO',
    }
    nombre_seleccionado = nombres.get(tipo, 'INCIDENCIA')

    if request.method == 'POST':
        # 3. Guardar con el campo 'tipo' incluido
        incidente = IncidenciaCRUEM(
            tipo=tipo,  # <--- IMPORTANTE: Guardamos el tipo de la URL
            nro_incidente=request.POST.get('nro_incidente'),
            fecha=request.POST.get('fecha'),
            hora_apertura=request.POST.get('hora_apertura'),
            hora_finalizacion=request.POST.get('hora_finalizacion'),
            reportante=request.POST.get('reportante'),
            telefono_celular=request.POST.get('telefono_celular'),
            del_paciente=request.POST.get('del_paciente'),
            motivo_llamada=request.POST.get('motivo_llamada'),
            prioridad=request.POST.get('prioridad'),
            respuesta=request.POST.get('respuesta'),
            coordinacion_traslado=request.POST.get('coordinacion_traslado'),
            usuario_registro=request.user
        )
        incidente.save()
        messages.success(request, f"¡Incidencia de {nombre_seleccionado} registrada!")
        return redirect('hospital:monitor_disponibilidad')
        
    # 4. Pasamos las variables al HTML
    return render(request, 'hospital/incidencia_form.html', {
        'tipo_codigo': tipo,
        'tipo_nombre': nombre_seleccionado
    })
###acceso de roles 
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

@login_required(login_url='superadmin:login')
def landing_page(request):
    user = request.user
    
    # 1. Verificamos si existe el rol para evitar errores
    if not user.rol:
        return redirect('superadmin:login')
    
    # 2. Obtenemos el nombre del rol en mayúsculas para comparar
    nombre_rol = user.rol.nombre.upper().strip()
    
    # 3. Redirecciones basadas en TUS URLs reales
    if 'SUPERADMIN' in nombre_rol:
        return redirect('superadmin:dashboard_superadmin')
        
    elif 'ADMIN' in nombre_rol:
        return redirect('hospital:monitor_red')
        
    elif 'DOCTOR' in nombre_rol:
        # Usamos 'lista_pacientes' que es el name que tienes en tu urls.py
        return redirect('hospital:lista_pacientes')
        
    elif 'ENFERMER' in nombre_rol:
        # Como no tienes 'monitoreo_camas', usamos el Monitor de Red o Infraestructura
        # Ajusta a 'hospital:gestionar_infraestructura' si prefieres
        return redirect('hospital:monitor_red')
    
    # 4. Si nada coincide, al login con namespace
    return redirect('superadmin:login')