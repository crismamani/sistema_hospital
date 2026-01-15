from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Sum
from django.core.paginator import Paginator
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

# Importación de modelos y formularios
from .models import (
    Hospital, Usuario, Rol, Especialidad,
    HospitalEspecialidad, Auditoria, ConfiguracionSistema
)
from hospital.models import Paciente, Cama

from .forms import (
    LoginForm, HospitalForm, UsuarioForm, RolForm, EspecialidadForm,
    ConfiguracionSistemaForm, RegistroPersonalForm, AsignarCapacidadForm, PacienteForm
)

# =================================================================
# --- VISTAS DE ACCESO (LOGIN/LOGOUT) ---
# =================================================================

def login_view(request):
    if request.user.is_authenticated:
        return dashboard_redirect(request)

    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        
        if user is not None:
            if user.is_active:
                login(request, user) 
                messages.success(request, f"Bienvenido, {user.nombre_completo}")
                return dashboard_redirect(request)
            else:
                messages.warning(request, "Tu cuenta se encuentra inactiva.")
        else:
            messages.error(request, "Correo o contraseña incorrectos")
            
    return render(request, 'superadmi/login.html')

@login_required
def dashboard_redirect(request):
    if not request.user.rol:
        logout(request)
        return redirect('superadmin:login')
        
    rol = request.user.rol.nombre.upper()
    if 'SUPERADMIN' in rol:
        return redirect('superadmin:dashboard_superadmin')
    elif 'DOCTOR' in rol:
        return redirect('doctor:dashboard_doctor')
    elif 'ENFERMERA' in rol:
        return redirect('enfermeria:dashboard_enfermera')
    elif 'ADMIN_APP' in rol:
        return redirect('admin_app:dashboard')
    
    return redirect('superadmin:dashboard_superadmin')

def logout_view(request):
    logout(request)
    messages.success(request, "Sesión cerrada correctamente.")
    return redirect('superadmin:login')

# =================================================================
# --- DASHBOARD PRINCIPAL ---
# =================================================================

@login_required(login_url='superadmin:login')
def dashboard_superadmin(request):
    user = request.user
    rol = user.rol.nombre.upper() if user.rol else "SIN ROL"

    if rol == 'SUPERADMIN':
        usuarios_qs = Usuario.objects.all()
        pacientes_qs = Paciente.objects.all()
        camas_qs = Cama.objects.all()
        hospitales_qs = Hospital.objects.all()
    else:
        usuarios_qs = Usuario.objects.filter(hospital=user.hospital)
        pacientes_qs = Paciente.objects.filter(hospital=user.hospital)
        camas_qs = Cama.objects.filter(hospital=user.hospital)
        hospitales_qs = Hospital.objects.filter(id=user.hospital.id) if user.hospital else Hospital.objects.none()

    context = {
        'total_hospitales': hospitales_qs.count(),
        'total_usuarios': usuarios_qs.count(),
        'total_pacientes': pacientes_qs.count(),
        'camas_libres': camas_qs.filter(estado='LIBRE').count(),
        'camas_ocupadas': camas_qs.filter(estado='OCUPADO').count(),
        'nombre_admin': user.nombre_completo,
        'rol_usuario': rol,
        'hospital_usuario': user.hospital.nombre if user.hospital else "Sede Central (Global)"
    }
    return render(request, 'superadmi/dashboard.html', context)

# =================================================================
# --- GESTIÓN DE HOSPITALES ---
# =================================================================

@login_required(login_url='superadmin:login')
def listar_hospitales(request):
    hospitales_db = Hospital.objects.all().order_by('-id')
    context = {
        'hospitales': hospitales_db, 
        'form': HospitalForm(),
        'total_h': hospitales_db.count(),
        'total_c': hospitales_db.aggregate(Sum('capacidad_camas'))['capacidad_camas__sum'] or 0
    }
    return render(request, 'superadmi/hospitales/listar.html', context)

def crear_hospital(request):
    if request.method == 'POST':
        h = Hospital()
        h.nombre = request.POST.get('nombre')
        h.direccion = request.POST.get('direccion')
        h.telefono = request.POST.get('telefono')
        h.email = request.POST.get('email')
        camas = request.POST.get('capacidad_camas')
        h.capacidad_camas = int(camas) if camas and camas.isdigit() else 0
        h.estado = True 
        h.save()
        messages.success(request, f"¡{h.nombre} registrado con éxito!")
    return redirect('superadmin:listar_hospitales')

def editar_hospital(request, pk):
    h = get_object_or_404(Hospital, id=pk)
    if request.method == 'POST':
        h.nombre = request.POST.get('nombre')
        h.direccion = request.POST.get('direccion')
        h.telefono = request.POST.get('telefono')
        h.email = request.POST.get('email')
        camas = request.POST.get('capacidad_camas')
        h.capacidad_camas = int(camas) if camas else 0
        estado_web = request.POST.get('estado')
        h.estado = (estado_web == 'True')
        h.save()
        messages.success(request, "Cambios guardados correctamente.")
    return redirect('superadmin:listar_hospitales')

def eliminar_hospital(request, pk):
    if request.method == 'POST':
        hospital = get_object_or_404(Hospital, id=pk)
        nombre = hospital.nombre
        hospital.delete()
        messages.success(request, f"El hospital {nombre} fue eliminado correctamente.")
    return redirect('superadmin:listar_hospitales')

# =================================================================
# --- GESTIÓN DE USUARIOS ---
# =================================================================
@login_required(login_url='superadmin:login')
def listar_usuarios(request):
    usuarios = Usuario.objects.all().order_by('-id')
    # Preparamos todo lo que necesitan los modales
    context = {
        'usuarios': usuarios,
        'roles': Rol.objects.all(),
        'hospitales': Hospital.objects.all(),
        'especialidades': Especialidad.objects.all(),
        'form': RegistroPersonalForm()
    }
    return render(request, 'superadmi/usuarios/listar.html', context)

@login_required(login_url='superadmin:login')
def registrar_personal(request):
    if request.method == 'POST':
        form = RegistroPersonalForm(request.POST)
        if form.is_valid():
            usuario = form.save(commit=False)
            usuario.set_password(form.cleaned_data['password'])
            usuario.save()
            messages.success(request, f"Usuario {usuario.username} creado con éxito.")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error en {field}: {error}")
    return redirect('superadmin:listar_usuarios')

@login_required(login_url='superadmin:login')
def editar_usuario(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    if request.method == 'POST':
        form = UsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuario actualizado correctamente.")
        else:
            messages.error(request, "Error al actualizar el usuario.")
    return redirect('superadmin:listar_usuarios')

@login_required(login_url='superadmin:login')
def eliminar_usuario(request, pk):
    # Nota: Si usas el botón directo en el HTML, cámbialo a POST
    usuario = get_object_or_404(Usuario, pk=pk)
    email = usuario.email
    Auditoria.objects.create(
        usuario=request.user,
        accion="ELIMINACION",
        detalles=f"Eliminó al usuario: {email}",
        tabla_afectada="Usuario"
    )
    usuario.delete()
    messages.success(request, "Usuario eliminado.")
    return redirect('superadmin:listar_usuarios')
# =================================================================
# --- CAPACIDADES Y ESPECIALIDADES ---
# =================================================================

@login_required(login_url='superadmin:login')
def listar_capacidades(request):
    capacidades = HospitalEspecialidad.objects.all().select_related('hospital', 'especialidad')
    return render(request, 'superadmi/capacidades/listar.html', {'capacidades': capacidades})

@login_required(login_url='superadmin:login')
def asignar_capacidad(request):
    if request.method == 'POST':
        form = AsignarCapacidadForm(request.POST)
        if form.is_valid():
            capacidad_asignada = form.save(commit=False)
            hospital = capacidad_asignada.hospital
            camas_ya_usadas = HospitalEspecialidad.objects.filter(hospital=hospital).aggregate(total=Sum('capacidad_camas'))['total'] or 0
            disponible = hospital.capacidad_camas - camas_ya_usadas
            
            if capacidad_asignada.capacidad_camas > disponible:
                messages.error(request, f"Error: Solo quedan {disponible} camas disponibles en este hospital.")
            else:
                capacidad_asignada.save()
                messages.success(request, "Capacidad asignada correctamente.")
                return redirect('superadmin:listar_capacidades')
    else:
        form = AsignarCapacidadForm()
    return render(request, 'superadmi/asignar_capacidad.html', {'form': form})

@login_required(login_url='superadmin:login')
def editar_capacidad(request, pk):
    capacidad = get_object_or_404(HospitalEspecialidad, pk=pk)
    if request.method == 'POST':
        form = AsignarCapacidadForm(request.POST, instance=capacidad)
        if form.is_valid():
            nueva_capacidad = form.save(commit=False)
            hospital = nueva_capacidad.hospital
            camas_otras = HospitalEspecialidad.objects.filter(hospital=hospital).exclude(pk=pk).aggregate(total=Sum('capacidad_camas'))['total'] or 0
            disponible = hospital.capacidad_camas - camas_otras
            
            if nueva_capacidad.capacidad_camas > disponible:
                messages.error(request, f"Excedido. El hospital solo tiene {disponible} camas libres.")
            else:
                nueva_capacidad.save()
                messages.success(request, "Capacidad actualizada.")
                return redirect('superadmin:listar_capacidades')
    else:
        form = AsignarCapacidadForm(instance=capacidad)
    return render(request, 'superadmi/capacidades/editar.html', {'form': form})

@login_required(login_url='superadmin:login')
def listar_roles(request):
    roles = Rol.objects.all().order_by('nombre')
    return render(request, 'superadmi/roles/listar.html', {'roles': roles})

@login_required(login_url='superadmin:login')
def listar_especialidades(request):
    if request.method == 'POST':
        form = EspecialidadForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Especialidad creada.')
            return redirect('superadmin:listar_especialidades')
    especialidades = Especialidad.objects.all().order_by('nombre')
    return render(request, 'superadmi/especialidades/listar.html', {'especialidades': especialidades, 'form': EspecialidadForm()})

@login_required(login_url='superadmin:login')
def crear_especialidad(request):
    if request.method == 'POST':
        form = EspecialidadForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Nueva especialidad agregada.")
            return redirect('superadmin:listar_especialidades')
    return redirect('superadmin:listar_especialidades')

# =================================================================
# --- PACIENTES Y CAMAS ---
# =================================================================

@login_required(login_url='superadmin:login')
def listar_pacientes(request):
    pacientes = Paciente.objects.all().select_related('hospital', 'cama_asignada').order_by('-fecha_registro')
    if request.method == 'POST':
        form = PacienteForm(request.POST)
        if form.is_valid():
            paciente = form.save(commit=False)
            if paciente.cama_asignada:
                cama = paciente.cama_asignada
                cama.estado = 'OCUPADO'
                cama.save()
            paciente.save()
            messages.success(request, "Paciente registrado correctamente.")
            return redirect('superadmin:listar_pacientes')
    else:
        form = PacienteForm()
    return render(request, 'superadmi/pacientes/listar.html', {'pacientes': pacientes, 'form': form})

@login_required(login_url='superadmin:login')
def crear_camas_prueba(request):
    hospital = Hospital.objects.first()
    if hospital:
        for i in range(1, 11):
            Cama.objects.get_or_create(
                numero=f"C-PRUEBA-{i}",
                hospital=hospital,
                defaults={'piso': 'Piso 1', 'estado': 'LIBRE'}
            )
        messages.success(request, f"10 Camas de prueba creadas.")
    return redirect('superadmin:dashboard_superadmin')

# =================================================================
# --- AUDITORIA Y CONFIGURACIÓN ---
# =================================================================

@login_required(login_url='superadmin:login')
def auditoria(request):
    log_list = Auditoria.objects.select_related('usuario').all().order_by('-fecha_accion')
    paginator = Paginator(log_list, 20)
    page = request.GET.get('page')
    entries = paginator.get_page(page)
    return render(request, 'superadmi/auditoria/listar.html', {'auditoria_entries': entries})

@login_required(login_url='superadmin:login')
def configuracion_sistema(request):
    config, _ = ConfiguracionSistema.objects.get_or_create(pk=1)
    if request.method == 'POST':
        form = ConfiguracionSistemaForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, 'Configuración actualizada.')
            return redirect('superadmin:configuracion_sistema')
    else:
        form = ConfiguracionSistemaForm(instance=config)
    return render(request, 'superadmi/configuracion/formulario.html', {'form': form})