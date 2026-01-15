# views/admin.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from datetime import date

from .models import (
    Paciente, Sala, Cama, Derivacion, SolicitudCama,
    Internacion, Personal, Turno, Asistencia,
    TransferenciaInterna, Notificacion
)
from superadmi.models import Hospital, Especialidad, Usuario
from .forms import (
    PacienteForm, SalaForm, CamaForm, InternacionForm, EgresoForm,
    PersonalForm, TurnoForm, AsistenciaForm, TransferenciaInternaForm,
    NotificacionForm
)
##login
from django.contrib.auth.decorators import login_required

@login_required
def dashboard_admin(request):
    return render(request, 'admin_app/dashboard.html')
    
def verificar_admin(user):
    """Verificar que el usuario es admin"""
    return user.is_authenticated and user.rol.nivel_acceso == 2

@login_required
def dashboard_admin(request):
    """Dashboard del administrador hospitalario"""
    if not verificar_admin(request.user):
        messages.error(request, 'No tienes permisos para acceder')
        return redirect('login')
    
    hospital = request.user.hospital
    
    # Estadísticas del hospital
    total_camas = Cama.objects.filter(hospital=hospital).count()
    camas_ocupadas = Cama.objects.filter(hospital=hospital, estado_cama='ocupada').count()
    camas_disponibles = total_camas - camas_ocupadas
    
    pacientes_internados = Internacion.objects.filter(
        hospital=hospital,
        estado='activo'
    ).count()
    
    derivaciones_pendientes = Derivacion.objects.filter(
        hospital_destino=hospital,
        estado='pendiente'
    ).count()
    
    solicitudes_pendientes = SolicitudCama.objects.filter(
        hospital_destino=hospital,
        estado='pendiente'
    ).count()
    
    context = {
        'hospital': hospital,
        'total_camas': total_camas,
        'camas_ocupadas': camas_ocupadas,
        'camas_disponibles': camas_disponibles,
        'pacientes_internados': pacientes_internados,
        'derivaciones_pendientes': derivaciones_pendientes,
        'solicitudes_pendientes': solicitudes_pendientes,
        'porcentaje_ocupacion': round((camas_ocupadas / total_camas * 100) if total_camas > 0 else 0, 1),
    }
    
    return render(request, 'admin/dashboard.html', context)

# ========== GESTIÓN DE PACIENTES ==========

@login_required
def listar_pacientes(request):
    """Listar pacientes"""
    if not verificar_admin(request.user):
        return redirect('login')
    
    pacientes = Paciente.objects.all().order_by('nombre_completo')
    
    # Búsqueda
    buscar = request.GET.get('buscar')
    if buscar:
        pacientes = pacientes.filter(
            Q(nombre_completo__icontains=buscar) |
            Q(numero_documento__icontains=buscar)
        )
    
    return render(request, 'admin/pacientes/listar.html', {'pacientes': pacientes})

@login_required
def crear_paciente(request):
    """Crear nuevo paciente"""
    if not verificar_admin(request.user):
        return redirect('login')
    
    if request.method == 'POST':
        form = PacienteForm(request.POST)
        if form.is_valid():
            paciente = form.save()
            messages.success(request, f'Paciente {paciente.nombre_completo} registrado exitosamente')
            return redirect('admin:listar_pacientes')
    else:
        form = PacienteForm()
    
    return render(request, 'admin/pacientes/formulario.html', {'form': form})

@login_required
def editar_paciente(request, pk):
    """Editar paciente"""
    if not verificar_admin(request.user):
        return redirect('login')
    
    paciente = get_object_or_404(Paciente, pk=pk)
    
    if request.method == 'POST':
        form = PacienteForm(request.POST, instance=paciente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Paciente actualizado exitosamente')
            return redirect('admin:listar_pacientes')
    else:
        form = PacienteForm(instance=paciente)
    
    return render(request, 'admin/pacientes/formulario.html', {
        'form': form,
        'paciente': paciente
    })

@login_required
def detalle_paciente(request, pk):
    """Ver detalles del paciente"""
    if not verificar_admin(request.user):
        return redirect('login')
    
    paciente = get_object_or_404(Paciente, pk=pk)
    internaciones = Internacion.objects.filter(paciente=paciente).order_by('-fecha_ingreso')
    
    context = {
        'paciente': paciente,
        'internaciones': internaciones,
    }
    
    return render(request, 'admin/pacientes/detalle.html', context)

# ========== GESTIÓN DE SALAS Y CAMAS ==========

@login_required
def listar_salas(request):
    """Listar salas del hospital"""
    if not verificar_admin(request.user):
        return redirect('login')
    
    hospital = request.user.hospital
    salas = Sala.objects.filter(hospital=hospital).order_by('nombre')
    
    return render(request, 'admin/salas/listar.html', {'salas': salas})

@login_required
def crear_sala(request):
    """Crear nueva sala"""
    if not verificar_admin(request.user):
        return redirect('login')
    
    if request.method == 'POST':
        form = SalaForm(request.POST)
        if form.is_valid():
            sala = form.save()
            messages.success(request, f'Sala {sala.nombre} creada exitosamente')
            return redirect('admin:listar_salas')
    else:
        form = SalaForm()
        # Pre-llenar hospital del usuario
        form.initial['hospital'] = request.user.hospital
    
    return render(request, 'admin/salas/formulario.html', {'form': form})

@login_required
def listar_camas(request):
    """Listar camas del hospital"""
    if not verificar_admin(request.user):
        return redirect('login')
    
    hospital = request.user.hospital
    camas = Cama.objects.filter(hospital=hospital).select_related('sala').order_by('sala__nombre', 'codigo_cama')
    
    # Filtros
    estado = request.GET.get('estado')
    if estado:
        camas = camas.filter(estado_cama=estado)
    
    sala_id = request.GET.get('sala')
    if sala_id:
        camas = camas.filter(sala_id=sala_id)
    
    salas = Sala.objects.filter(hospital=hospital)
    
    context = {
        'camas': camas,
        'salas': salas,
    }
    
    return render(request, 'admin/camas/listar.html', context)

@login_required
def crear_cama(request):
    """Crear nueva cama"""
    if not verificar_admin(request.user):
        return redirect('login')
    
    if request.method == 'POST':
        form = CamaForm(request.POST)
        if form.is_valid():
            cama = form.save()
            messages.success(request, f'Cama {cama.codigo_cama} creada exitosamente')
            return redirect('admin:listar_camas')
    else:
        form = CamaForm()
        form.initial['hospital'] = request.user.hospital
    
    return render(request, 'admin/camas/formulario.html', {'form': form})

# ========== GESTIÓN DE INTERNACIONES ==========

@login_required
def listar_internaciones(request):
    """Listar internaciones activas"""
    if not verificar_admin(request.user):
        return redirect('login')
    
    hospital = request.user.hospital
    internaciones = Internacion.objects.filter(
        hospital=hospital,
        estado='activo'
    ).select_related('paciente', 'cama', 'doctor_responsable').order_by('-fecha_ingreso')
    
    return render(request, 'admin/internaciones/listar.html', {'internaciones': internaciones})

@login_required
def crear_internacion(request):
    """Crear nueva internación"""
    if not verificar_admin(request.user):
        return redirect('login')
    
    if request.method == 'POST':
        form = InternacionForm(request.POST)
        if form.is_valid():
            internacion = form.save(commit=False)
            internacion.hospital = request.user.hospital
            internacion.save()
            
            # Cambiar estado de la cama
            cama = internacion.cama
            cama.estado_cama = 'ocupada'
            cama.save()
            
            messages.success(request, 'Internación registrada exitosamente')
            return redirect('admin:listar_internaciones')
    else:
        form = InternacionForm()
        form.initial['hospital'] = request.user.hospital
        form.initial['fecha_ingreso'] = timezone.now()
    
    return render(request, 'admin/internaciones/formulario.html', {'form': form})

@login_required
def registrar_egreso(request, pk):
    """Registrar egreso de paciente"""
    if not verificar_admin(request.user):
        return redirect('login')
    
    internacion = get_object_or_404(Internacion, pk=pk, hospital=request.user.hospital)
    
    if request.method == 'POST':
        form = EgresoForm(request.POST)
        if form.is_valid():
            internacion.fecha_egreso = form.cleaned_data['fecha_egreso']
            internacion.observaciones = form.cleaned_data.get('observaciones', '')
            internacion.estado = 'egresado'
            internacion.save()
            
            # Liberar cama
            cama = internacion.cama
            cama.estado_cama = 'disponible'
            cama.save()
            
            messages.success(request, 'Egreso registrado exitosamente')
            return redirect('admin:listar_internaciones')
    else:
        form = EgresoForm()
        form.initial['fecha_egreso'] = timezone.now()
    
    context = {
        'form': form,
        'internacion': internacion,
    }
    
    return render(request, 'admin/internaciones/egreso.html', context)

# ========== GESTIÓN DE DERIVACIONES ==========

@login_required
def listar_derivaciones(request):
    """Listar derivaciones recibidas"""
    if not verificar_admin(request.user):
        return redirect('login')
    
    hospital = request.user.hospital
    derivaciones = Derivacion.objects.filter(
        hospital_destino=hospital
    ).select_related('paciente', 'hospital_origen').order_by('-fecha_solicitud')
    
    # Filtros
    estado = request.GET.get('estado')
    if estado:
        derivaciones = derivaciones.filter(estado=estado)
    
    return render(request, 'admin/derivaciones/listar.html', {'derivaciones': derivaciones})

# ========== GESTIÓN DE SOLICITUDES DE CAMA ==========

@login_required
def listar_solicitudes_cama(request):
    """Listar solicitudes de cama"""
    if not verificar_admin(request.user):
        return redirect('login')
    
    hospital = request.user.hospital
    solicitudes = SolicitudCama.objects.filter(
        hospital_destino=hospital
    ).select_related('paciente', 'hospital_solicitante').order_by('-fecha_solicitud')
    
    return render(request, 'admin/solicitudes_cama/listar.html', {'solicitudes': solicitudes})

# ========== GESTIÓN DE PERSONAL ==========

@login_required
def listar_personal(request):
    """Listar personal del hospital"""
    if not verificar_admin(request.user):
        return redirect('login')
    
    hospital = request.user.hospital
    personal = Personal.objects.filter(hospital=hospital).select_related('usuario')
    
    return render(request, 'admin/personal/listar.html', {'personal': personal})

@login_required
def crear_personal(request):
    """Crear registro de personal"""

    if not verificar_admin(request.user):
        # Si NO es admin, lo mandas a un error o a otra página
        return redirect('no_autorizado')

    # Si es admin, continúas con el formulario