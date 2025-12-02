# views/enfermeria.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

# Importamos modelos definidos en los otros módulos
from superadmi.models import Hospital, Usuario
from admin_app.models import (
    Paciente, Internacion, Sala, Cama, 
    TransferenciaInterna, 
)
# Asumimos formularios de enfermería
from .forms import (
 TransferenciaInternaForm, RegistroAsistenciaForms, CambioEstadoCamaForm
)

def verificar_enfermeria(user):
    """Verificar que el usuario es enfermero/a (Nivel 4)"""
    return user.is_authenticated and user.rol.nivel_acceso == 4

@login_required
def dashboard_enfermeria(request):
    """Dashboard de enfermería"""
    if not verificar_enfermeria(request.user):
        messages.error(request, 'No tienes permisos de enfermería')
        return redirect('login')
    
    hospital = request.user.hospital
    
    # Camas ocupadas en el hospital (o en su sector si se tuviera esa lógica)
    camas_ocupadas = Cama.objects.filter(
        hospital=hospital, 
        estado_cama='ocupada'
    ).count()
    
    # Pacientes ingresados hoy
    ingresos_hoy = Internacion.objects.filter(
        hospital=hospital,
        fecha_ingreso__date=timezone.now().date()
    ).count()
    
    context = {
        'camas_ocupadas': camas_ocupadas,
        'ingresos_hoy': ingresos_hoy,
        'fecha_actual': timezone.now()
    }
    
    return render(request, 'enfermeria/dashboard.html', context)

# ========== GESTIÓN DE SALAS Y CAMAS (VISTA OPERATIVA) ==========

@login_required
def mapa_camas(request):
    """Ver estado de todas las camas y pacientes por sala"""
    if not verificar_enfermeria(request.user):
        return redirect('login')
        
    hospital = request.user.hospital
    salas = Sala.objects.filter(hospital=hospital).prefetch_related('cama_set')
    
    # Obtenemos las internaciones activas para mostrar nombre del paciente en la cama
    internaciones_activas = Internacion.objects.filter(
        hospital=hospital, 
        estado='activo'
    ).select_related('paciente', 'cama')
    
    # Diccionario para acceso rápido cama_id -> internacion
    mapa_pacientes = {i.cama.id: i for i in internaciones_activas}
    
    return render(request, 'enfermeria/camas/mapa.html', {
        'salas': salas,
        'mapa_pacientes': mapa_pacientes
    })

# ========== ATENCIÓN AL PACIENTE ==========

##@login_required
##def nota_enfermeria(request, internacion_id):
    """Agregar nota de enfermería al expediente"""
    if not verificar_enfermeria(request.user):
        return redirect('login')
        
    internacion = get_object_or_404(Internacion, pk=internacion_id)
    
    if request.method == 'POST':
        form = NotaEnfermeriaForm(request.POST)
        if form.is_valid():
            nota = form.save(commit=False)
            nota.internacion = internacion
            nota.enfermero = request.user
            nota.save()
            messages.success(request, 'Nota registrada')
            return redirect('enfermeria:detalle_paciente', pk=internacion.id)
    else:
        form = NotaEnfermeriaForm()
        
    return render(request, 'enfermeria/pacientes/form_nota.html', {
        'form': form,
        'internacion': internacion
    })

@login_required
def detalle_paciente_enfermeria(request, pk):
    """Ver detalles operativos del paciente para enfermería"""
    if not verificar_enfermeria(request.user):
        return redirect('login')
        
    internacion = get_object_or_404(Internacion, pk=pk)   
    return render(request, 'enfermeria/pacientes/detalle.html', {
        'internacion': internacion,
        
    })

# ========== MOVIMIENTOS INTERNOS ==========

@login_required
def transferencia_interna(request, internacion_id):
    """Mover paciente de una cama/sala a otra dentro del hospital"""
    if not verificar_enfermeria(request.user):
        return redirect('login')
        
    internacion = get_object_or_404(Internacion, pk=internacion_id)
    cama_actual = internacion.cama
    
    if request.method == 'POST':
        form = TransferenciaInternaForm(request.POST, hospital=request.user.hospital)
        if form.is_valid():
            nueva_cama = form.cleaned_data['cama_destino']
            motivo = form.cleaned_data['motivo']
            
            # Registrar historial de transferencia
            TransferenciaInterna.objects.create(
                internacion=internacion,
                cama_origen=cama_actual,
                cama_destino=nueva_cama,
                usuario=request.user,
                motivo=motivo
            )
            
            # Actualizar estados de camas
            cama_actual.estado_cama = 'disponible'
            cama_actual.save()
            
            nueva_cama.estado_cama = 'ocupada'
            nueva_cama.save()
            
            # Actualizar internación
            internacion.cama = nueva_cama
            internacion.save()
            
            messages.success(request, f'Paciente transferido a {nueva_cama.codigo_cama}')
            return redirect('enfermeria:mapa_camas')
    else:
        # Pasamos el hospital para filtrar solo camas disponibles de este hospital
        form = TransferenciaInternaForm(hospital=request.user.hospital)
        
    return render(request, 'enfermeria/gestion/transferencia.html', {
        'form': form,
        'internacion': internacion,
        'cama_actual': cama_actual
    })