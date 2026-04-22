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
from .decorators import solo_roles 
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseBadRequest
from .decorators import solo_personal_autorizado, solo_roles

@login_required
def home(request):
    """
    Controlador de tráfico: Redirige al usuario según su ROL
    usando los nombres de URL (name) definidos en hospital/urls.py
    """
    usuario = request.user
    
    # 1. Verificación segura del rol (evita errores si el campo está vacío)
    if hasattr(usuario, 'rol') and usuario.rol:
        # Normalizamos a mayúsculas para evitar errores de escritura
        rol_nombre = usuario.rol.nombre.upper()
        
        # --- SUPERADMIN O ADMIN DE SISTEMA ---
        if rol_nombre in ['SUPERADMIN', 'SISTEMAADMI'] or usuario.username == 'admin2':
            # Asumiendo que 'superadmin' es tu app de administración central
            return redirect('superadmin:dashboard')
            
        # --- DOCTOR ---
        # Como no existe 'panel_doctor', lo mandamos a la gestión de pacientes
        elif rol_nombre == 'DOCTOR':
            # Lo mandamos directo a la gestión de infraestructura de SU hospital
            return redirect('hospital:gestionar_infraestructura')
            
        # --- ENFERMERA ---
        # La mandamos al monitor de disponibilidad para que reporte el estado de camas
        elif rol_nombre == 'ENFERMERA':
            return redirect('hospital:monitor_disponibilidad')
            
        # --- ADMINISTRADOR DE HOSPITAL ---
        # Lo mandamos directo a gestionar la infraestructura (camas/cuartos)
        elif rol_nombre == 'ADMINISTRADOR':
            return redirect('hospital:gestionar_infraestructura')

        # --- CHOFER / CONDUCTOR ---
        # Si tienes el rol chofer, lo mandamos a su panel de ambulancia
        elif rol_nombre in ['CHOFER', 'CONDUCTOR']:
            return redirect('hospital:landing_page')

    # 2. Si llegamos aquí, es que el usuario no tiene rol o no es reconocido
    return render(request, 'hospital/sin_acceso.html')
# ==========================================
# GESTIÓN DE INFRAESTRUCTURA (CUARTOS Y CAMAS)
# ==========================================
@login_required
@solo_personal_autorizado
def gestionar_infraestructura(request):
    """
    Panel operativo para Doctores y Administradores.
    Muestra la carga por especialidad, permitiendo gestionar traslados
    internos y derivaciones externas según la saturación.
    """
    # 1. SEGURIDAD: Evitamos errores de campos inexistentes
    es_admin_global = getattr(request.user, 'is_superuser', False) or request.user.username == 'admin2'
    
    # 2. IDENTIFICACIÓN DEL HOSPITAL (Blindado para Doctor/Enfermera/Admin)
    if es_admin_global:
        # El Admin global elige qué hospital ver mediante la URL
        hospital_id = request.GET.get('hospital_id')
    else:
        # Búsqueda inteligente: intenta hospital_pertenece, si falla busca hospital
        hosp_obj = getattr(request.user, 'hospital_pertenece', None) or getattr(request.user, 'hospital', None)
        hospital_id = hosp_obj.id if hosp_obj else None
    
    if not hospital_id:
        return HttpResponseBadRequest("Error: No tienes un hospital asignado. Contacta a soporte técnico.")

    hospital = get_object_or_404(Hospital, id=hospital_id)
    piso_filtro = request.GET.get('piso')

    # 3. FILTRADO DE ESPECIALIDADES
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
        
        # --- CÁLCULO DE MÉTRICAS OPERATIVAS ---
        total = camas_qs.count()
        # Normalizamos estados para evitar errores de conteo
        ocupadas = camas_qs.filter(estado__in=['OCUPADA', 'OCUPADO', 'INTERNADO']).count()
        
        carga = (ocupadas / total * 100) if total > 0 else 0
        
        # Lógica de colores para toma de decisiones médica
        if carga > 80: color = 'danger'   # CRÍTICO: Derivación externa necesaria
        elif carga > 50: color = 'warning' # ALERTA: Monitorear ingresos
        else: color = 'success'           # DISPONIBLE

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

    # 4. LISTA DE PISOS PARA NAVEGACIÓN RÁPIDA
    lista_pisos = Cuarto.objects.filter(hospital=hospital).values_list('piso', flat=True).distinct().order_by('piso')

    # 5. DETERMINAR SI EL USUARIO PUEDE EDITAR (Solo Administradores)
    pueden_editar = es_admin_global or (getattr(request.user.rol, 'nombre', '').upper() == 'ADMINISTRADOR')

    return render(request, 'hospital/especialidades_list.html', {
        'hospital': hospital,
        'especialidades': especialidades_con_datos,
        'lista_pisos': lista_pisos,
        'piso_seleccionado': piso_filtro,
        'pueden_editar': pueden_editar, # Usar esto en el HTML para ocultar botones
    })
@login_required
@solo_personal_autorizado
def crear_especialidad(request):
    if request.method == 'POST':
        nombre_esp = request.POST.get('nombre')
        hospital_id = request.POST.get('hospital_id')
        piso_form = request.POST.get('piso', 1)
        numero_cuarto = request.POST.get('numero_cuarto') 
        
        if not numero_cuarto:
            messages.error(request, "Debe asignar un número de cuarto para la especialidad.")
            return redirect(f"/hospital/infraestructura/?hospital_id={hospital_id}")

        if nombre_esp and hospital_id:
            hospital = get_object_or_404(Hospital, id=hospital_id)
            
            esp, created = Especialidad.objects.get_or_create(
                nombre=nombre_esp.upper().strip()
            )
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
@solo_personal_autorizado
def detalle_camas_especialidad(request, hospital_id, especialidad_id):
    hospital = get_object_or_404(Hospital, id=hospital_id)
    especialidad = get_object_or_404(Especialidad, id=especialidad_id)
    
    # Protección: Un admin local no puede ver camas de OTRO hospital
    if not request.user.is_superuser and request.user.hospital != hospital:
         raise PermissionDenied

    cuartos = Cuarto.objects.filter(hospital=hospital, especialidad=especialidad).prefetch_related('camas')
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
@login_required
@solo_personal_autorizado
def crear_cuarto(request):
    if request.method == 'POST':
        hospital_id = request.POST.get('hospital')
        h = get_object_or_404(Hospital, id=hospital_id)
        # ... (Tu lógica de creación de cuarto igualita)
        Cuarto.objects.create(
            hospital=h,
            especialidad_id=request.POST.get('especialidad'),
            numero_cuarto=request.POST.get('numero_cuarto'),
            piso=request.POST.get('piso')
        )
        messages.success(request, "Cuarto creado.")
        return redirect(request.META.get('HTTP_REFERER', '/'))
    return redirect('superadmin:dashboard_superadmin')
@login_required
@solo_personal_autorizado
def crear_cama(request):
    if request.method == 'POST':
        cuarto_id = request.POST.get('cuarto_id')
        cuarto = get_object_or_404(Cuarto, id=cuarto_id)
        Cama.objects.create(cuarto=cuarto, numero=request.POST.get('numero'), estado='LIBRE')
        messages.success(request, f"Cama agregada al cuarto {cuarto.numero_cuarto}.")
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
@solo_personal_autorizado
def lista_pacientes(request):
    # Filtramos por hospital para que los doctores no vean pacientes de otros centros
    if request.user.is_superuser or request.user.username == 'admin2':
        pacientes = Paciente.objects.filter(estado='INTERNADO')
    else:
        pacientes = Paciente.objects.filter(estado='INTERNADO', hospital=request.user.hospital)
        
    pacientes = pacientes.select_related('hospital', 'cama_asignada__cuarto')
    return render(request, 'hospital/lista_pacientes.html', {'pacientes': pacientes})
@login_required
@solo_personal_autorizado
def historial_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    evoluciones = paciente.evoluciones.all().order_by('-fecha_registro')
    
    if request.method == 'POST':
        form = EvolucionMedicaForm(request.POST)
        if form.is_valid():
            evolucion = form.save(commit=False)
            evolucion.paciente = paciente
            evolucion.creado_by = request.user
            evolucion.save()
            messages.success(request, "Evolución médica actualizada.")
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
@solo_personal_autorizado
def dar_alta_paciente(request, paciente_id): 
    paciente = get_object_or_404(Paciente, id=paciente_id)
    
    with transaction.atomic():
        if paciente.cama_asignada:
            cama = paciente.cama_asignada
            cama.estado = 'LIMPIEZA' # Pasa a limpieza antes de estar LIBRE
            cama.save()
        
        paciente.estado = 'ALTA'
        paciente.cama_asignada = None
        paciente.save()
        
        # Auditoría simple
        messages.success(request, f"Alta médica registrada para {paciente.nombre_completo}. Cama en limpieza.")
    
    return redirect('hospital:historial_paciente', paciente_id=paciente.id)
@login_required
@solo_personal_autorizado
def registrar_paciente(request, paciente_id=None):
    paciente_edit = get_object_or_404(Paciente, id=paciente_id) if paciente_id else None

    if request.method == 'POST':
        nombre = request.POST.get('nombre_completo')
        dni = request.POST.get('dni')
        cama_id = request.POST.get('cama_asignada')
        
        try:
            # transaction.atomic asegura que si algo falla, NO se guarde nada a medias
            with transaction.atomic():
                if not paciente_edit:
                    paciente_edit = Paciente(estado='INTERNADO')
                    f_ent = request.POST.get('fecha_entrada')
                    paciente_edit.fecha_entrada = f_ent if f_ent and f_ent.strip() else timezone.now()
                else:
                    f_ent = request.POST.get('fecha_entrada')
                    if f_ent and f_ent.strip():
                        paciente_edit.fecha_entrada = f_ent

                # Asignación de datos básicos
                paciente_edit.nombre_completo = nombre
                paciente_edit.dni = dni
                paciente_edit.fecha_nacimiento = request.POST.get('fecha_nacimiento') or None
                paciente_edit.genero = request.POST.get('genero')
                paciente_edit.hospital_id = request.POST.get('hospital')
                paciente_edit.motivo_ingreso = request.POST.get('motivo_ingreso')
                paciente_edit.presion_arterial = request.POST.get('presion_arterial')
                paciente_edit.temperatura = float(request.POST.get('temperatura') or 0)
                paciente_edit.frecuencia_cardiaca = int(request.POST.get('frecuencia_cardiaca') or 0)
                paciente_edit.saturacion_oxigeno = int(request.POST.get('saturacion_oxigeno') or 0)
                
                # Lógica de Cama (Tu proceso de intercambio de camas)
                if cama_id:
                    nueva_cama = Cama.objects.get(id=cama_id)
                    # Si el paciente se está moviendo a una cama distinta
                    if not paciente_edit.cama_asignada or paciente_edit.cama_asignada.id != int(cama_id):
                        if nueva_cama.estado == 'OCUPADO':
                            messages.error(request, f"La cama {nueva_cama.numero} ya está ocupada.")
                            return redirect('hospital:lista_pacientes')

                        # Liberamos la cama anterior si tenía una
                        if paciente_edit.cama_asignada:
                            c_anterior = paciente_edit.cama_asignada
                            c_anterior.estado = 'LIBRE'
                            c_anterior.save()
                        
                        nueva_cama.estado = 'OCUPADO'
                        nueva_cama.save()
                        paciente_edit.cama_asignada = nueva_cama
                
                paciente_edit.save()
                
                # Creamos automáticamente la primera evolución médica
                EvolucionMedica.objects.create(
                    paciente=paciente_edit,
                    tipo='RUTINA',
                    temperatura=paciente_edit.temperatura,
                    presion_arterial=paciente_edit.presion_arterial,
                    descripcion=f"REGISTRO INICIAL: {paciente_edit.motivo_ingreso}",
                    creado_by=request.user
                )

                messages.success(request, f"Paciente {nombre} procesado con éxito.")
                return redirect('hospital:lista_pacientes')

        except Exception as e:
            messages.error(request, f"Error en el proceso: {str(e)}")

    # Lógica para mostrar el formulario (GET)
    form = PacienteForm(instance=paciente_edit)
    # Solo mostramos camas libres del hospital seleccionado
    camas_disponibles = Cama.objects.filter(estado='LIBRE')
    if paciente_edit and paciente_edit.cama_asignada:
        camas_disponibles = camas_disponibles | Cama.objects.filter(id=paciente_edit.cama_asignada.id)
    
    form.fields['cama_asignada'].queryset = camas_disponibles
    
    return render(request, 'hospital/lista_pacientes.html', {
        'form': form,
        'paciente_edit': paciente_edit,
        'pacientes': Paciente.objects.filter(estado='INTERNADO').order_by('-fecha_entrada')
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

@login_required
@solo_personal_autorizado
def cambiar_estado_cama(request, cama_id):
    cama = get_object_or_404(Cama, id=cama_id)
    
    # Rotación circular: LIBRE -> MANTENIMIENTO -> LIMPIEZA -> LIBRE
    if cama.estado == 'LIBRE':
        cama.estado = 'MANTENIMIENTO'
    elif cama.estado == 'MANTENIMIENTO':
        cama.estado = 'LIMPIEZA'
    elif cama.estado == 'LIMPIEZA':
        cama.estado = 'LIBRE'
    elif cama.estado == 'OCUPADO':
        messages.warning(request, "No puedes cambiar el estado de una cama ocupada.")
        return redirect(request.META.get('HTTP_REFERER', 'hospital:home'))
    
    cama.save()
    messages.info(request, f"Cama {cama.numero} ahora en {cama.get_estado_display()}.")
    return redirect(request.META.get('HTTP_REFERER', 'hospital:home'))
@login_required
def liberar_cama(request, cama_id):
    cama = get_object_or_404(Cama, id=cama_id)
    if cama.estado == 'LIMPIEZA':
        cama.estado = 'LIBRE'
        cama.save()
        messages.success(request, f"La cama {cama.numero} ha sido desinfectada y está LIBRE.")
    return redirect('hospital:central_limpieza')
@login_required
@solo_personal_autorizado
def eliminar_cama(request, cama_id):
    cama = get_object_or_404(Cama, id=cama_id)
    h_id = cama.cuarto.hospital.id
    cama.delete()
    messages.success(request, "Cama eliminada del sistema.")
    return redirect(f"{reverse('hospital:gestionar_infraestructura')}?hospital_id={h_id}")
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
@solo_personal_autorizado
def monitor_red(request):
    # 1. Definición de permisos segura
    es_super_o_admin2 = getattr(request.user, 'is_superuser', False) or request.user.username == 'admin2'
    
    # 2. Identificación dinámica del hospital del usuario
    # Buscamos 'hospital_pertenece', si no existe, probamos 'hospital'
    mi_hospital = getattr(request.user, 'hospital_pertenece', None)
    if not mi_hospital:
        mi_hospital = getattr(request.user, 'hospital', None)

    # 3. Selección de Hospitales (QuerySet inicial)
    if es_super_o_admin2:
        hospitales_qs = Hospital.objects.all()
    elif mi_hospital:
        # El doctor o personal local solo ve su hospital
        hospitales_qs = Hospital.objects.filter(id=mi_hospital.id)
    else:
        # Si no es admin y no tiene hospital, no ve nada
        hospitales_qs = Hospital.objects.none()

    # 4. Cálculos de disponibilidad
    red_hospitalaria = hospitales_qs.annotate(
        total_camas=Count('cuartos__camas', distinct=True),
        libres=Count('cuartos__camas', filter=Q(cuartos__camas__estado='LIBRE'), distinct=True),
        ambulancias_count=Count('ambulancias', distinct=True)
    ).order_by('-libres')

    # 5. Derivaciones filtradas por hospital del usuario
    if es_super_o_admin2:
        derivaciones_activas = Derivacion.objects.filter(estado='PENDIENTE')
    elif mi_hospital:
        # Doctor solo ve derivaciones de su hospital (origen o destino)
        derivaciones_activas = Derivacion.objects.filter(
            Q(hospital_origen=mi_hospital) | Q(hospital_destino=mi_hospital),
            estado='PENDIENTE'
        )
    else:
        derivaciones_activas = Derivacion.objects.none()

    derivaciones_activas = derivaciones_activas.select_related(
        'paciente', 'hospital_origen', 'hospital_destino', 'ambulancia'
    ).order_by('-prioridad')

    # 6. Indicadores
    traslados_hoy = Derivacion.objects.filter(fecha_solicitud__date=timezone.now().date()).count()
    unidades_listas = Ambulancia.objects.filter(estado='DISPONIBLE').count()
    en_movimiento = derivaciones_activas.filter(ambulancia__isnull=False).count()

    # 7. Acción Ver Detalle
    hosp_id = request.GET.get('hosp_id')
    pacientes_internados = None
    hosp_nombre = ""
    
    # Si es doctor, forzamos que solo vea su hospital si intenta ver detalles
    if not es_super_o_admin2 and mi_hospital:
        hosp_seleccionado = mi_hospital
    elif hosp_id:
        hosp_seleccionado = get_object_or_404(Hospital, id=hosp_id)
    else:
        hosp_seleccionado = None

    if hosp_seleccionado:
        hosp_nombre = hosp_seleccionado.nombre
        pacientes_internados = Paciente.objects.filter(
            hospital=hosp_seleccionado, estado='INTERNADO'
        ).select_related('cama_asignada__cuarto__especialidad')

    return render(request, 'hospital/monitor_red.html', {
        'red': red_hospitalaria,
        'derivaciones': derivaciones_activas,
        'pacientes': pacientes_internados,
        'hosp_nombre': hosp_nombre,
        'traslados_hoy': traslados_hoy,
        'unidades_listas': unidades_listas,
        'en_camino': en_movimiento,
        'kardex': Derivacion.objects.filter(estado='COMPLETADO').order_by('-fecha_solicitud')[:10],
    })
@login_required
@solo_personal_autorizado
@transaction.atomic
def solicitar_derivacion(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    hospitales_destino = Hospital.objects.exclude(id=paciente.hospital.id)

    if request.method == 'POST':
        destino_id = request.POST.get('hospital_destino')
        
        # 1. Liberar la cama actual (Protocolo de Limpieza)
        if paciente.cama_asignada:
            cama_actual = paciente.cama_asignada
            cama_actual.estado = 'LIMPIEZA'
            cama_actual.save()

        # 2. Crear la derivación oficial
        Derivacion.objects.create(
            paciente=paciente,
            hospital_origen=paciente.hospital,
            hospital_destino_id=destino_id,
            prioridad=request.POST.get('prioridad', 'MEDIA'),
            motivo_traslado=request.POST.get('motivo'),
            estado='PENDIENTE',
            creado_by=request.user
        )

        # 3. Paciente en tránsito
        paciente.cama_asignada = None
        paciente.estado = 'TRANSITO'
        paciente.save()

        messages.success(request, f"Solicitud de traslado para {paciente.nombre_completo} enviada a la red.")
        return redirect('hospital:monitor_red')

    return render(request, 'hospital/derivar_form.html', {
        'paciente': paciente, 
        'hospitales': hospitales_destino
    })
@login_required
@solo_personal_autorizado
@transaction.atomic
def confirmar_recepcion(request, derivacion_id):
    """El hospital de destino confirma que el paciente llegó y le asigna cama"""
    derivacion = get_object_or_404(Derivacion, id=derivacion_id)
    
    if request.method == 'POST':
        cama_id = request.POST.get('cama_id')
        nueva_cama = get_object_or_404(Cama, id=cama_id)
        paciente = derivacion.paciente

        # 1. Finalizar derivación
        derivacion.estado = 'COMPLETADO' 
        derivacion.fecha_recepcion = timezone.now()
        derivacion.save()
        
        # 2. Actualizar Paciente al nuevo hospital
        paciente.hospital = derivacion.hospital_destino
        paciente.cama_asignada = nueva_cama
        paciente.estado = 'INTERNADO'
        paciente.save()
        
        # 3. Ocupar nueva cama
        nueva_cama.estado = 'OCUPADO'
        nueva_cama.save()

        # 4. Liberar Ambulancia
        if derivacion.ambulancia:
            ambulancia = derivacion.ambulancia
            ambulancia.estado = 'DISPONIBLE'
            ambulancia.save()
        
        messages.success(request, f"Recepción confirmada. {paciente.nombre_completo} ya tiene cama asignada.")
        return redirect('hospital:monitor_red')

    camas_libres = Cama.objects.filter(cuarto__hospital=derivacion.hospital_destino, estado='LIBRE')
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
@solo_personal_autorizado
def generar_pdf_traslado(request, derivacion_id):
    """Genera la hoja de referencia oficial para la ambulancia"""
    derivacion = get_object_or_404(Derivacion, id=derivacion_id)
    
    data = {
        'derivacion': derivacion,
        'fecha': derivacion.fecha_solicitud,
        'usuario': request.user.nombre_completo if hasattr(request.user, 'nombre_completo') else request.user.username
    }
    
    template = get_template('hospital/pdf_traslado.html')
    html = template.render(data)
    
    result = BytesIO()
    # UTF-8 es vital para que salgan bien las tildes y la 'ñ'
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return HttpResponse("Error al generar el documento PDF", status=400)
@login_required
@solo_personal_autorizado
def central_limpieza(request):
    """Panel para el personal de limpieza de la Red"""
    # Si es Admin2 ve todas las camas sucias de Potosí, si no, solo las de su hospital
    if request.user.is_superuser or request.user.username == 'admin2':
        camas_sucias = Cama.objects.filter(estado='LIMPIEZA')
    else:
        camas_sucias = Cama.objects.filter(estado='LIMPIEZA', cuarto__hospital=request.user.hospital)
        
    return render(request, 'hospital/central_limpieza.html', {
        'camas_sucias': camas_sucias.select_related('cuarto__hospital', 'cuarto__especialidad')
    })

@login_required
@solo_personal_autorizado
def finalizar_limpieza(request, cama_id):
    cama = get_object_or_404(Cama, id=cama_id)
    cama.estado = 'LIBRE'
    cama.save()
    messages.success(request, f"Cama {cama.numero} desinfectada y lista para nuevo paciente.")
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
@login_required
@solo_personal_autorizado
def guardar_ambulancia(request):
    """Creación robusta de unidades"""
    if request.method == 'POST':
        hospital_id = request.POST.get('hospital_id')
        
        # Seguridad: Si no viene hospital_id (personal local), usamos el suyo
        if not hospital_id and hasattr(request.user, 'hospital'):
            hospital_id = request.user.hospital.id

        Ambulancia.objects.create(
            placa=request.POST.get('placa').upper(),
            tipo=request.POST.get('tipo'),
            modelo=request.POST.get('modelo'),
            hospital_id=hospital_id,
            nombre_chofer_manual=request.POST.get('chofer_texto'),
            estado='DISPONIBLE'
        )
        messages.success(request, "Nueva unidad incorporada a la red.")
        
        paciente_id = request.POST.get('paciente_id')
        if paciente_id:
            return redirect(f"{reverse('hospital:gestion_ambulancias')}?paciente_id={paciente_id}")
            
    return redirect('hospital:gestion_ambulancias')

# NUEVA VISTA: Para conectar físicamente la ambulancia al paciente
@login_required
@solo_personal_autorizado
def vincular_ambulancia_paciente(request, paciente_id, ambulancia_id):
    """Conecta la unidad con el paciente y lanza el traslado"""
    paciente = get_object_or_404(Paciente, id=paciente_id)
    ambulancia = get_object_or_404(Ambulancia, id=ambulancia_id)
    
    with transaction.atomic():
        # Actualizamos ambulancia
        ambulancia.estado = 'EN_CAMINO'
        ambulancia.save()
        
        # Vinculamos al paciente (si tienes el campo en el modelo)
        if hasattr(paciente, 'ambulancia_asignada'):
            paciente.ambulancia_asignada = ambulancia
            paciente.save()
            
        messages.success(request, f"Unidad {ambulancia.placa} en camino para traslado de {paciente.nombre_completo}.")
    
    return redirect('hospital:monitor_red')

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
@login_required
def panel_chofer(request, ambulancia_id):
    """Vista simplificada para el conductor"""
    unidad = get_object_or_404(Ambulancia, id=ambulancia_id)
    return render(request, 'hospital/panel_chofer.html', {'ambulancia': unidad})

@login_required
def cambiar_estado_ambulancia(request, ambulancia_id, nuevo_estado):
    unidad = get_object_or_404(Ambulancia, id=ambulancia_id)
    if nuevo_estado in ['DISPONIBLE', 'EN_CAMINO', 'MANTENIMIENTO']:
        unidad.estado = nuevo_estado
        unidad.save()
        messages.info(request, f"Estado de unidad actualizado a {nuevo_estado}")
    return redirect('hospital:panel_chofer', ambulancia_id=unidad.id)
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

@login_required
@solo_personal_autorizado
def eliminar_ambulancia(request, pk):
    unidad = get_object_or_404(Ambulancia, pk=pk)
    unidad.delete()
    messages.warning(request, "Unidad dada de baja del sistema.")
    return redirect('hospital:gestion_ambulancias')
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
@login_required
@solo_personal_autorizado
def formulario_d7_view(request, paciente_id):
    """Hoja de Referencia (D7) - Datos clínicos para el traslado"""
    paciente = get_object_or_404(Paciente, id=paciente_id)
    instancia = FormularioD7.objects.filter(paciente=paciente).first()

    if request.method == 'POST':
        form = D7Form(request.POST, instance=instancia)
        if form.is_valid():
            f = form.save(commit=False)
            f.paciente = paciente
            f.save()
            messages.success(request, "Formulario D7 (Referencia) guardado.")
            return redirect('hospital:monitor_red')
    else:
        form = D7Form(instance=instancia)

    return render(request, 'hospital/formularios/D7.html', {'paciente': paciente, 'form': form})

def formulario_d7a_view(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    # Renderiza el HTML de Consentimiento
    return render(request, 'hospital/formularios/D7a.html', {'paciente': paciente})
@login_required
@solo_personal_autorizado
def formulario_d7b_view(request, paciente_id):
    """Hoja de Contra-Referencia (D7b) - Retorno del paciente"""
    paciente = get_object_or_404(Paciente, id=paciente_id)
    instancia = FormularioD7b.objects.filter(paciente=paciente).first()

    if request.method == 'POST':
        form = D7bForm(request.POST, instance=instancia)
        if form.is_valid():
            f = form.save(commit=False)
            f.paciente = paciente
            f.save()
            messages.success(request, "Formulario D7b (Contra-referencia) actualizado.")
            return redirect('hospital:lista_pacientes')
    else:
        form = D7bForm(instance=instancia)

    return render(request, 'hospital/formularios/D7b.html', {'paciente': paciente, 'form': form})
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
    """Calendario de gestión de red para SEDES Potosí"""
    ahora = datetime.now()
    mes = int(request.GET.get('mes', ahora.month))
    anio = int(request.GET.get('anio', ahora.year))
    hospital_id = request.GET.get('hospital_id')

    reportes_qs = ReporteDiario.objects.filter(fecha__month=mes, fecha__year=anio)
    
    hospital_seleccionado = None
    if hospital_id:
        hospital_seleccionado = get_object_or_404(Hospital, id=hospital_id)
        reportes_qs = reportes_qs.filter(hospital=hospital_seleccionado)

    registrados = reportes_qs.values_list('fecha__day', flat=True)

    return render(request, 'hospital/calendario.html', {
        'reportes_registrados': list(registrados),
        'mes_actual': mes,
        'anio_actual': anio,
        'hospitales': Hospital.objects.all(),
        'hospital_seleccionado': hospital_seleccionado,
    })

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
    if not tipo: return redirect('hospital:seleccionar_tipo')

    nombres = {
        'PRE': '1 (338) PREHOSPITALARIA',
        'TRA': '2 (110) TRASLADO',
        'REF': '3 (167) REFERENCIA',
        'EVE': '4 EVENTO DEPORTIVO',
    }
    
    if request.method == 'POST':
        IncidenciaCRUEM.objects.create(
            tipo=tipo,
            nro_incidente=request.POST.get('nro_incidente'),
            fecha=request.POST.get('fecha'),
            hora_apertura=request.POST.get('hora_apertura'),
            reportante=request.POST.get('reportante'),
            motivo_llamada=request.POST.get('motivo_llamada'),
            prioridad=request.POST.get('prioridad'),
            usuario_registro=request.user
        )
        messages.success(request, f"Incidencia {tipo} registrada correctamente.")
        return redirect('hospital:monitor_disponibilidad')
        
    return render(request, 'hospital/incidencia_form.html', {
        'tipo_codigo': tipo,
        'tipo_nombre': nombres.get(tipo, 'INCIDENCIA')
    })
###acceso de roles 
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

@login_required(login_url='superadmin:login')
def landing_page(request):
    """Redirección inteligente según el rol de Potosí"""
    user = request.user
    
    if not hasattr(user, 'rol') or not user.rol:
        return redirect('superadmin:login')
    
    rol = user.rol.nombre.upper()
    
    if 'SUPERADMIN' in rol:
        return redirect('superadmin:dashboard_superadmin')
        
    elif 'ADMIN' in rol:
        # Administrador de hospital va directo a ver sus camas y red
        return redirect('hospital:monitor_red')
        
    elif 'DOCTOR' in rol:
        # El médico va directo a atender sus pacientes
        return redirect('hospital:lista_pacientes')
        
    elif 'ENFERMER' in rol or 'LIMPIEZA' in rol:
        # Enfermería o Limpieza ven el estado de las camas
        return redirect('hospital:central_limpieza')
    
    return redirect('superadmin:login')