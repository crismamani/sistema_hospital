
## 1. VIEWS DE SUPERADMIN (views/superadmin.py)
# views/superadmin.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse
from django.utils import timezone

from .models import (
    Hospital, Usuario, Rol, Especialidad,
    HospitalEspecialidad, Auditoria, ConfiguracionSistema, Reporte
)
from .forms import (
    HospitalForm, UsuarioForm, RolForm, EspecialidadForm,
    HospitalEspecialidadForm, ConfiguracionSistemaForm, ReporteForm,
    FiltroAuditoriaForm
)

# C:\Users\cris\Sis_Hospital\superadmi\views.py

from django.shortcuts import render
# ... otras importaciones

# Define la vista que el sistema está buscando
def login_view(request):
    # Por ahora, solo devuelve una respuesta HTTP simple o una plantilla vacía
    # Más tarde, aquí irá la lógica de autenticación
    return render(request, 'login.html') 
    # O, si no tienes la plantilla aún:
    # from django.http import HttpResponse
    # return HttpResponse("Página de Login Temporal")

def verificar_superadmin(user):
    """Verificar que el usuario es superadmin"""
    return user.is_authenticated and user.rol.nivel_acceso == 1

@login_required
def dashboard_superadmin(request):
    """Dashboard principal del superadmin"""
    if not verificar_superadmin(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección')
        return redirect('login')
    
    # Estadísticas generales
    total_hospitales = Hospital.objects.filter(estado=True).count()
    total_usuarios = Usuario.objects.filter(estado=True).count()
    total_especialidades = Especialidad.objects.filter(estado=True).count()
    
    # Actividad reciente
    actividad_reciente = Auditoria.objects.all().order_by('-fecha_accion')[:10]
    
    context = {
        'total_hospitales': total_hospitales,
        'total_usuarios': total_usuarios,
        'total_especialidades': total_especialidades,
        'actividad_reciente': actividad_reciente,
    }
    
    return render(request, 'superadmin/dashboard.html', context)

# ========== GESTIÓN DE HOSPITALES ==========

@login_required
def listar_hospitales(request):
    """Listar todos los hospitales"""
    if not verificar_superadmin(request.user):
        return redirect('login')
    
    hospitales = Hospital.objects.all().order_by('nombre')
    return render(request, 'superadmin/hospitales/listar.html', {'hospitales': hospitales})

@login_required
def crear_hospital(request):
    """Crear nuevo hospital"""
    if not verificar_superadmin(request.user):
        return redirect('login')
    
    if request.method == 'POST':
        form = HospitalForm(request.POST)
        if form.is_valid():
            hospital = form.save()
            
            # Registrar en auditoría
            Auditoria.objects.create(
                usuario=request.user,
                accion='crear',
                tabla_afectada='hospitales',
                registro_id=hospital.id,
                datos_nuevos={'nombre': hospital.nombre}
            )
            
            messages.success(request, 'Hospital creado exitosamente')
            return redirect('superadmin:listar_hospitales')
    else:
        form = HospitalForm()
    
    return render(request, 'superadmin/hospitales/formulario.html', {'form': form})

@login_required
def editar_hospital(request, pk):
    """Editar hospital existente"""
    if not verificar_superadmin(request.user):
        return redirect('login')
    
    hospital = get_object_or_404(Hospital, pk=pk)
    
    if request.method == 'POST':
        form = HospitalForm(request.POST, instance=hospital)
        if form.is_valid():
            form.save()
            messages.success(request, 'Hospital actualizado exitosamente')
            return redirect('superadmin:listar_hospitales')
    else:
        form = HospitalForm(instance=hospital)
    
    return render(request, 'superadmin/hospitales/formulario.html', {
        'form': form,
        'hospital': hospital
    })

@login_required
def detalle_hospital(request, pk):
    """Ver detalles de un hospital"""
    if not verificar_superadmin(request.user):
        return redirect('login')
    
    hospital = get_object_or_404(Hospital, pk=pk)
    especialidades = HospitalEspecialidad.objects.filter(hospital=hospital)
    usuarios = Usuario.objects.filter(hospital=hospital)
    
    context = {
        'hospital': hospital,
        'especialidades': especialidades,
        'usuarios': usuarios,
    }
    
    return render(request, 'superadmin/hospitales/detalle.html', context)

# ========== GESTIÓN DE USUARIOS ==========

@login_required
def listar_usuarios(request):
    """Listar todos los usuarios"""
    if not verificar_superadmin(request.user):
        return redirect('login')
    
    usuarios = Usuario.objects.all().select_related('rol', 'hospital').order_by('nombre_completo')
    return render(request, 'superadmin/usuarios/listar.html', {'usuarios': usuarios})

@login_required
def crear_usuario(request):
    """Crear nuevo usuario"""
    if not verificar_superadmin(request.user):
        return redirect('login')
    
    if request.method == 'POST':
        form = UsuarioForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            messages.success(request, f'Usuario {usuario.nombre_completo} creado exitosamente')
            return redirect('superadmin:listar_usuarios')
    else:
        form = UsuarioForm()
    
    return render(request, 'superadmin/usuarios/formulario.html', {'form': form})

@login_required
def editar_usuario(request, pk):
    """Editar usuario existente"""
    if not verificar_superadmin(request.user):
        return redirect('login')
    
    usuario = get_object_or_404(Usuario, pk=pk)
    
    if request.method == 'POST':
        form = UsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuario actualizado exitosamente')
            return redirect('superadmin:listar_usuarios')
    else:
        form = UsuarioForm(instance=usuario)
    
    return render(request, 'superadmin/usuarios/formulario.html', {
        'form': form,
        'usuario': usuario
    })

# ========== GESTIÓN DE ROLES ==========

@login_required
def listar_roles(request):
    """Listar roles del sistema"""
    if not verificar_superadmin(request.user):
        return redirect('login')
    
    roles = Rol.objects.all().order_by('nivel_acceso')
    return render(request, 'superadmin/roles/listar.html', {'roles': roles})

@login_required
def crear_rol(request):
    """Crear nuevo rol"""
    if not verificar_superadmin(request.user):
        return redirect('login')
    
    if request.method == 'POST':
        form = RolForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Rol creado exitosamente')
            return redirect('superadmin:listar_roles')
    else:
        form = RolForm()
    
    return render(request, 'superadmin/roles/formulario.html', {'form': form})

# ========== GESTIÓN DE ESPECIALIDADES ==========

@login_required
def listar_especialidades(request):
    """Listar especialidades médicas"""
    if not verificar_superadmin(request.user):
        return redirect('login')
    
    especialidades = Especialidad.objects.all().order_by('nombre')
    return render(request, 'superadmin/especialidades/listar.html', {'especialidades': especialidades})

@login_required
def crear_especialidad(request):
    """Crear nueva especialidad"""
    if not verificar_superadmin(request.user):
        return redirect('login')
    
    if request.method == 'POST':
        form = EspecialidadForm(request.POST)
        if form.is_valid():
            especialidad = form.save(commit=False)
            especialidad.creado_por = request.user
            especialidad.save()
            messages.success(request, 'Especialidad creada exitosamente')
            return redirect('superadmin:listar_especialidades')
    else:
        form = EspecialidadForm()
    
    return render(request, 'superadmin/especialidades/formulario.html', {'form': form})

# ========== ASIGNACIÓN DE ESPECIALIDADES A HOSPITALES ==========

@login_required
def asignar_especialidad_hospital(request):
    """Asignar especialidad a hospital"""
    if not verificar_superadmin(request.user):
        return redirect('login')
    
    if request.method == 'POST':
        form = HospitalEspecialidadForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Especialidad asignada exitosamente')
            return redirect('superadmin:listar_hospitales')
    else:
        form = HospitalEspecialidadForm()
    
    return render(request, 'superadmin/hospital_especialidades/formulario.html', {'form': form})

# ========== AUDITORÍA ==========

@login_required
def auditoria(request):
    """Ver registros de auditoría"""
    if not verificar_superadmin(request.user):
        return redirect('login')
    
    registros = Auditoria.objects.all().select_related('usuario').order_by('-fecha_accion')
    
    # Aplicar filtros
    form = FiltroAuditoriaForm(request.GET)
    if form.is_valid():
        if form.cleaned_data.get('usuario'):
            registros = registros.filter(usuario=form.cleaned_data['usuario'])
        if form.cleaned_data.get('accion'):
            registros = registros.filter(accion=form.cleaned_data['accion'])
        if form.cleaned_data.get('fecha_desde'):
            registros = registros.filter(fecha_accion__gte=form.cleaned_data['fecha_desde'])
        if form.cleaned_data.get('fecha_hasta'):
            registros = registros.filter(fecha_accion__lte=form.cleaned_data['fecha_hasta'])
    
    # Paginación
    from django.core.paginator import Paginator
    paginator = Paginator(registros, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'registros': page_obj,
        'form': form,
    }
    
    return render(request, 'superadmin/auditoria/listar.html', context)

# ========== CONFIGURACIÓN DEL SISTEMA ==========

@login_required
def configuracion_sistema(request):
    """Gestionar configuración del sistema"""
    if not verificar_superadmin(request.user):
        return redirect('login')
    
    configuraciones = ConfiguracionSistema.objects.all().order_by('clave')
    return render(request, 'superadmin/configuracion/listar.html', {'configuraciones': configuraciones})

@login_required
def editar_configuracion(request, pk):
    """Editar configuración"""
    if not verificar_superadmin(request.user):
        return redirect('login')
    
    config = get_object_or_404(ConfiguracionSistema, pk=pk)
    
    if request.method == 'POST':
        form = ConfiguracionSistemaForm(request.POST, instance=config)
        if form.is_valid():
            config = form.save(commit=False)
            config.actualizado_por = request.user
            config.save()
            messages.success(request, 'Configuración actualizada')
            return redirect('superadmin:configuracion_sistema')
    else:
        form = ConfiguracionSistemaForm(instance=config)
    
    return render(request, 'superadmin/configuracion/formulario.html', {
        'form': form,
        'config': config
    })

# ========== REPORTES ==========

@login_required
def generar_reporte(request):
    """Generar reportes del sistema"""
    if not verificar_superadmin(request.user):
        return redirect('login')
    
    if request.method == 'POST':
        form = ReporteForm(request.POST)
        if form.is_valid():
            reporte = form.save(commit=False)
            reporte.generado_por = request.user
            
            # Aquí iría la lógica para generar el reporte según el tipo
            # Por ahora solo guardamos el registro
            reporte.save()
            
            messages.success(request, 'Reporte generado exitosamente')
            return redirect('superadmin:ver_reporte', pk=reporte.id)
    else:
        form = ReporteForm()
    
    return render(request, 'superadmin/reportes/formulario.html', {'form': form})

@login_required
def listar_reportes(request):
    """Listar reportes generados"""
    if not verificar_superadmin(request.user):
        return redirect('login')
    
    reportes = Reporte.objects.all().order_by('-fecha_generacion')
    return render(request, 'superadmin/reportes/listar.html', {'reportes': reportes})