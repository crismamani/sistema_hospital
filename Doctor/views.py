# views/doctor.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from superadmi.models import Hospital, Usuario, Especialidad
from admin_app.models import (
    Paciente, Internacion, Derivacion, SolicitudCama,
    Turno, HistoriaClinica  
)
# Asumimos que existen estos formularios
from .forms import (
    HistoriaClinicaForm, DerivacionForm, 
    SolicitudCamaForm, 
)
##login
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dashboard_doctor(request):
    # Por ahora renderizamos una plantilla básica
    return render(request, 'doctor/dashboard.html')
    
@login_required
def agenda_medico(request):
    return render(request, 'Doctor/agenda.html', {})
    ##login
def verificar_doctor(user):
    """Verificar que el usuario es doctor (Nivel 3)"""
    return user.is_authenticated and user.rol.nivel_acceso == 3

@login_required
def dashboard_doctor(request):
    """Dashboard principal del médico"""
    if not verificar_doctor(request.user):
        messages.error(request, 'No tienes permisos de médico')
        return redirect('login')
    
    hospital = request.user.hospital
    doctor = request.user
    
    # Pacientes a cargo actualmente (Internados)
    mis_pacientes = Internacion.objects.filter(
        hospital=hospital,
        doctor_responsable=doctor,
        estado='activo'
    ).count()
    
    # Turnos para hoy
    turnos_hoy = Turno.objects.filter(
        medico=doctor,
        fecha=timezone.now().date(),
        estado='pendiente'
    ).count()
    
    # Derivaciones solicitadas por este médico pendientes
    derivaciones_pendientes = Derivacion.objects.filter(
        medico_solicitante=doctor,
        estado='pendiente'
    ).count()

    context = {
        'mis_pacientes': mis_pacientes,
        'turnos_hoy': turnos_hoy,
        'derivaciones_pendientes': derivaciones_pendientes,
    }
    
    return render(request, 'doctor/dashboard.html', context)

# ========== GESTIÓN CLÍNICA ==========

@login_required
def mis_pacientes_internados(request):
    """Listar pacientes internados a cargo del médico"""
    if not verificar_doctor(request.user):
        return redirect('login')
        
    internaciones = Internacion.objects.filter(
        hospital=request.user.hospital,
        doctor_responsable=request.user,
        estado='activo'
    ).select_related('paciente', 'cama', 'cama__sala')
    
    return render(request, 'doctor/pacientes/internados.html', {'internaciones': internaciones})

@login_required
def historia_clinica_paciente(request, paciente_id):
    """Ver y editar historia clínica"""
    if not verificar_doctor(request.user):
        return redirect('login')
        
    paciente = get_object_or_404(Paciente, pk=paciente_id)
    historial_internaciones = Internacion.objects.filter(paciente=paciente).order_by('-fecha_ingreso')
    
    return render(request, 'doctor/pacientes/historia_clinica.html', {
        'paciente': paciente,
        'internaciones': historial_internaciones 
          })

# ========== GESTIÓN DE SOLICITUDES Y DERIVACIONES ==========

@login_required
def solicitar_derivacion(request, internacion_id):
    """Solicitar derivación a otro hospital"""
    if not verificar_doctor(request.user):
        return redirect('login')
    
    internacion = get_object_or_404(Internacion, pk=internacion_id)
    
    if request.method == 'POST':
        form = DerivacionForm(request.POST)
        if form.is_valid():
            derivacion = form.save(commit=False)
            derivacion.paciente = internacion.paciente
            derivacion.hospital_origen = request.user.hospital
            derivacion.medico_solicitante = request.user
            derivacion.estado = 'pendiente'
            derivacion.save()
            messages.success(request, 'Solicitud de derivación enviada')
            return redirect('doctor:dashboard')
    else:
        form = DerivacionForm()
    
    return render(request, 'doctor/gestion/form_derivacion.html', {
        'form': form,
        'internacion': internacion
    })

@login_required
def solicitar_cama_uti(request, paciente_id):
    """Solicitar cama específica (ej. UTI) en otro centro"""
    if not verificar_doctor(request.user):
        return redirect('login')
        
    paciente = get_object_or_404(Paciente, pk=paciente_id)
    
    if request.method == 'POST':
        form = SolicitudCamaForm(request.POST)
        if form.is_valid():
            solicitud = form.save(commit=False)
            solicitud.paciente = paciente
            solicitud.hospital_solicitante = request.user.hospital
            solicitud.medico_solicitante = request.user
            solicitud.save()
            messages.success(request, 'Solicitud de cama enviada')
            return redirect('doctor:dashboard')
    else:
        form = SolicitudCamaForm()
        
    return render(request, 'doctor/gestion/form_solicitud_cama.html', {'form': form, 'paciente': paciente})

# ========== AGENDA ==========

@login_required
def mi_agenda(request):
    """Ver turnos asignados"""
    if not verificar_doctor(request.user):
        return redirect('login')
        
    turnos = Turno.objects.filter(
        medico=request.user,
        fecha__gte=timezone.now().date()
    ).order_by('fecha', 'hora_inicio')
    
    return render(request, 'doctor/agenda/listar.html', {'turnos': turnos})