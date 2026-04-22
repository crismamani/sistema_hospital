from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Sum
from django.urls import reverse
from django.core.paginator import Paginator
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
#para los reportes 
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Table, TableStyle
from reportlab.pdfgen import canvas
from django.utils import timezone
# Importación de modelos y formularios
from .models import (
    Hospital, Usuario, Rol, Especialidad,
    HospitalEspecialidad, Auditoria, ConfiguracionSistema,   
)
from hospital.models import Paciente, Cama, Hospital, Cuarto

from .forms import (
    LoginForm, HospitalForm, UsuarioForm, RolForm, EspecialidadForm,
    ConfiguracionSistemaForm, RegistroPersonalForm, AsignarCapacidadForm, PacienteForm
)
# --- FUNCIONES DE ACCESO (PROTECCIÓN POR ROL) ---
# =================================================================

def es_superadmin(user):
    """Verifica si es Superadmin o el usuario maestro admin2"""
    nombre_rol = getattr(user.rol, 'nombre', '').upper()
    return 'SUPERADMI' in nombre_rol or user.username == 'admin2' or getattr(user, 'is_admin', False)

def es_admin_o_superior(user):
    """Verifica si es Administrador de hospital o Superadmin"""
    nombre_rol = getattr(user.rol, 'nombre', '').upper()
    return 'ADMIN' in nombre_rol or es_superadmin(user)
# 1. Vista de Login
def login_view(request):
    if request.user.is_authenticated:
        return redirect('superadmin:dashboard_redirect')

    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        
        user = authenticate(request, username=u, password=p)
        
        if user is not None:
            login(request, user)
            # Al usar el namespace 'superadmin', aseguramos que encuentre la ruta
            return redirect('superadmin:dashboard_redirect')
        else:
            messages.error(request, "Credenciales incorrectas. Verifica el usuario y la clave.")
            
    return render(request, 'superadmi/login.html')

# 2. Función de Redirección (El "Cerebro" de los Roles)
@login_required(login_url='superadmin:login')
def dashboard_redirect(request):
    user = request.user 
    if es_superadmin(user):
        return redirect('superadmin:dashboard_superadmin')

    # Validar existencia de Rol para evitar errores de tipo 'NoneType'
    if not user.rol:
        messages.warning(request, "Tu cuenta no tiene un rol asignado. Contacta a soporte.")
        logout(request)
        return redirect('superadmin:login')
        
    # Limpiamos el nombre del rol para comparar (Mayúsculas y sin espacios)
    nombre_rol = user.rol.nombre.upper().strip()
    
    # Mapeo de los 4 Roles (Superadmi, Admin, Doctor, Enfermera)
    if 'SUPERADMI' in nombre_rol or 'ADMIN' in nombre_rol:
        return redirect('superadmin:dashboard_superadmin')
    
    elif 'DOCTOR' in nombre_rol or 'MEDICO' in nombre_rol:
        return redirect('hospital:home')
    
    elif 'ENFERMER' in nombre_rol:
        # Redirige a la landing que mencionaste
        return redirect('hospital:landing_page')
    
    # Caso por defecto si el rol no coincide con los anteriores
    return redirect('hospital:home')

# 3. Vista de Logout
def logout_view(request):
    logout(request)
    messages.success(request, "Sesión cerrada correctamente.")
    return redirect('superadmin:login')
# =================================================================
# --- DASHBOARD PRINCIPAL ---
# =================================================================
@login_required(login_url='superadmin:login')
@user_passes_test(es_admin_o_superior) # Solo Admins y Superadmins
def dashboard_superadmin(request):
    user = request.user
    
    # --- LÓGICA DE FILTRO POR HOSPITAL ---
    # Si es Superadmin global ve todo, si es Admin de Hospital solo ve SU hospital
    if es_superadmin(user) and user.username == 'admin2':
        hospitales_qs = Hospital.objects.all()
    else:
        # Si el usuario tiene un hospital asignado, filtramos solo ese
        if user.hospital:
            hospitales_qs = Hospital.objects.filter(id=user.hospital.id)
        else:
            hospitales_qs = Hospital.objects.all()

    # --- TALENTO HUMANO GLOBAL (Filtrado) ---
    usuarios_base = Usuario.objects.filter(hospital__in=hospitales_qs) if not es_superadmin(user) else Usuario.objects.all()
    doctores_totales = Usuario.objects.filter(rol__nombre__icontains='DOCTOR').count()
    enfermeras_totales = Usuario.objects.filter(rol__nombre__icontains='ENFERMERA').count()
    administrativos_totales = Usuario.objects.filter(rol__nombre__icontains='ADMIN').count()
    
    resumen_hospitales = []
    g_total_camas = 0
    g_total_pacientes = 0
    g_total_libres = 0
    g_total_ocupadas = 0
    g_total_reservadas = 0
    g_total_soporte = 0
    hosp_criticos_count = 0
    h_3er_nivel = 0
    h_2do_nivel = 0

    for hosp in hospitales_qs:
        # Filtrado de Camas
        camas_hosp = Cama.objects.filter(cuarto__hospital=hosp)
        c_total = camas_hosp.count()
        c_libres = camas_hosp.filter(estado='LIBRE').count()
        c_ocupadas = camas_hosp.filter(estado='OCUPADO').count()
        c_reservadas = camas_hosp.filter(estado='RESERVADO').count()
        c_limpieza = camas_hosp.filter(estado='LIMPIEZA').count()
        c_mantenimiento = camas_hosp.filter(estado='MANTENIMIENTO').count()
        c_soporte = c_limpieza + c_mantenimiento
        
        # --- TALENTO HUMANO POR HOSPITAL ---
        h_medicos = Usuario.objects.filter(hospital=hosp, rol__nombre__icontains='DOCTOR').count()
        h_enfermeras = Usuario.objects.filter(hospital=hosp, rol__nombre__icontains='ENFERMERA').count()
        h_admin = Usuario.objects.filter(hospital=hosp, rol__nombre__icontains='ADMIN').count()
        h_limpieza = Usuario.objects.filter(hospital=hosp, rol__nombre__icontains='LIMPIEZA').count()

        if "3er" in hosp.nombre or "III" in hosp.nombre: h_3er_nivel += 1
        else: h_2do_nivel += 1

        g_total_camas += c_total
        g_total_pacientes += Paciente.objects.filter(hospital=hosp, estado='INTERNADO').count()
        g_total_libres += c_libres
        g_total_ocupadas += c_ocupadas
        g_total_reservadas += c_reservadas
        g_total_soporte += c_soporte

        # Lógica de Semáforo Hospitalario
        porcentaje_hosp = (c_ocupadas / c_total * 100) if c_total > 0 else 0
        h_critico = porcentaje_hosp >= 90
        if h_critico: hosp_criticos_count += 1
        
        h_color = "danger" if porcentaje_hosp >= 90 else ("warning" if porcentaje_hosp >= 70 else "success")
        h_estado = "CRÍTICO" if porcentaje_hosp >= 90 else ("PREVENTIVO" if porcentaje_hosp >= 70 else "ESTABLE")

        # ============================================================
        # --- DETALLES ESPECIALIDADES (SINCRONIZACIÓN CORREGIDA) ---
        # ============================================================
        detalles_esp = []
        
        # En lugar de HospitalEspecialidad, buscamos especialidades que tengan cuartos en este hospital
        especialidades_vivas_ids = Cuarto.objects.filter(
            hospital=hosp
        ).values_list('especialidad_id', flat=True).distinct()
        
        especialidades_vivas = Especialidad.objects.filter(id__in=especialidades_vivas_ids)

        for esp in especialidades_vivas:
            # Buscamos camas para esta especialidad específica en este hospital
            c_esp = Cama.objects.filter(cuarto__especialidad=esp, cuarto__hospital=hosp)
            t_e = c_esp.count()
            o_e = c_esp.filter(estado='OCUPADO').count()
            l_e = c_esp.filter(estado='LIBRE').count()
            
            p_e = (o_e / t_e * 100) if t_e > 0 else 0
            
            # Determinamos el color basado en la carga
            if t_e == 0:
                color_e = "secondary" # Gris si no hay camas aún
                estado_txt_e = "SIN CAMAS"
            else:
                color_e = "success" if p_e < 60 else ("warning" if p_e < 85 else "danger")
                estado_txt_e = f"{round(p_e, 1)}%"

            detalles_esp.append({
                'nombre': esp.nombre,
                'libres': l_e,
                'porcentaje': round(p_e, 1),
                'color': color_e,
                'estado_texto': estado_txt_e
            })

        resumen_hospitales.append({
            'id': hosp.id,
            'nombre': hosp.nombre,
            'pacientes': Paciente.objects.filter(hospital=hosp, estado='INTERNADO').count(),
            'libres': c_libres,
            'ocupadas': c_ocupadas,
            'reservadas': c_reservadas,
            'limpieza': c_limpieza,
            'mantenimiento': c_mantenimiento,
            'total_camas': c_total,
            'porcentaje_gral': round(porcentaje_hosp, 1),
            'es_critico': h_critico,
            'semaforo_color': h_color,
            'estado_texto': h_estado,
            'especialidades_list': detalles_esp,
            'h_medicos': h_medicos,
            'h_enfermeras': h_enfermeras,
            'h_admin': h_admin,
            'h_limpieza': h_limpieza
        })

    context = {
        'resumen_hospitales': resumen_hospitales,
        'global': {
            'total_camas': g_total_camas,
            'pacientes': g_total_pacientes,
            'libres': g_total_libres,
            'ocupadas': g_total_ocupadas,
            'hosp_criticos': hosp_criticos_count,
            'h_3er': h_3er_nivel,
            'h_2do': h_2do_nivel,
            'porcentaje': round((g_total_ocupadas / g_total_camas * 100), 1) if g_total_camas > 0 else 0,
        },
        'personal_global': {
            'doctores': doctores_totales,
            'enfermeras': enfermeras_totales,
            'administrativos': administrativos_totales,
        },
        'nombre_admin': request.user.username,
    }
    return render(request, 'superadmi/dashboard.html', context)
# =================================================================
# --- GESTIÓN DE HOSPITALES ---
# =================================================================
@login_required(login_url='superadmin:login')
@user_passes_test(es_superadmin)
def listar_hospitales(request):
    # Traemos la base de datos con prefetch para optimizar
    hospitales_db = Hospital.objects.all().prefetch_related('especialidades_asignadas__especialidad').order_by('-id')
    
    # ============================================================
    # --- LÓGICA DE AGRUPACIÓN POR NIVELES (SINCRONIZACIÓN) ---
    # ============================================================
    # Separamos para los subtítulos en el HTML
    hospitales_3er = hospitales_db.filter(nivel=3)
    hospitales_2do = hospitales_db.filter(nivel=2)
    hospitales_1er = hospitales_db.filter(nivel=1)

    context = {
        'hospitales': hospitales_db, # Mantenemos la lista completa por si la usas
        'hospitales_3er': hospitales_3er,
        'hospitales_2do': hospitales_2do,
        'hospitales_1er': hospitales_1er,
        'form': HospitalForm(),
        'especialidades_globales': Especialidad.objects.filter(estado=True),
        'total_h': hospitales_db.count(),
        'total_c': hospitales_db.aggregate(Sum('capacidad_camas'))['capacidad_camas__sum'] or 0
    }
    return render(request, 'superadmi/hospitales/listar.html', context)

def crear_hospital(request):
    if request.method == 'POST':
        h = Hospital()
        h.nombre = request.POST.get('nombre')
        
        # --- Sincronizamos el NIVEL ---
        nivel = request.POST.get('nivel')
        h.nivel = int(nivel) if nivel else 1
        
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
        
        # --- Sincronizamos el NIVEL en edición ---
        nivel = request.POST.get('nivel')
        h.nivel = int(nivel) if nivel else h.nivel
        
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
@user_passes_test(lambda u: es_admin_o_superior(u))
def listar_usuarios(request):
    user = request.user
    q = request.GET.get('q')
    if q:
        usuarios_tabla = usuarios_tabla.filter(
        Q(nombre_completo__icontains=q) | Q(email__icontains=q)
    )
    # Filtro de pertenencia: Si no es superadmin total, solo ve su hospital
    if es_superadmin(user) and user.username == 'admin2':
        todos_los_usuarios = Usuario.objects.all()
        hospitales_visibles = Hospital.objects.all()
    else:
        todos_los_usuarios = Usuario.objects.filter(hospital=user.hospital)
        hospitales_visibles = Hospital.objects.filter(id=user.hospital.id) if user.hospital else Hospital.objects.none()

    # Contadores basados en el filtro anterior
    activos_count = todos_los_usuarios.filter(estado=True).count()
    cirugia_count = todos_los_usuarios.filter(estado=False).count() # 'En Cirugía' o Inactivos
    sedes_count = hospitales_visibles.count()

    # Filtro de estado por GET
    estado_filtro = request.GET.get('estado')
    usuarios_tabla = todos_los_usuarios.select_related('hospital', 'especialidad', 'rol')

    if estado_filtro == 'disponible':
        usuarios_tabla = usuarios_tabla.filter(estado=True)
    elif estado_filtro == 'ocupado':
        usuarios_tabla = usuarios_tabla.filter(estado=False)

    context = {
        'usuarios': usuarios_tabla.order_by('-id'),
        'activos_count': activos_count,
        'cirugia_count': cirugia_count,
        'sedes_count': sedes_count,
        'hospitales': hospitales_visibles,
        'especialidades': Especialidad.objects.all(),
        'roles_list': Rol.objects.all(),
    }
    return render(request, 'superadmi/usuarios/listar.html', context)

@login_required(login_url='superadmin:login')
def editar_usuario(request, pk):
    usuario = get_object_or_404(Usuario, id=pk)
    
    if request.method == 'POST':
        # CAPTURA DEL ROL POR ID
        rol_id = request.POST.get('rol_administrativo')
        if rol_id:
            # Buscamos el rol por su ID (PK)
            rol_instancia = get_object_or_404(Rol, id=rol_id)
            usuario.rol = rol_instancia

        # Otros campos
        usuario.nombre_completo = request.POST.get('nombre_completo')
        usuario.email = request.POST.get('email')
        usuario.telefono = request.POST.get('telefono')
        usuario.ciudad = request.POST.get('ciudad')
        usuario.direccion = request.POST.get('direccion')
        usuario.turno_asignado = request.POST.get('turno')
        usuario.estado = request.POST.get('estado') == 'true'
        
        # Hospital y Especialidad
        hospital_id = request.POST.get('hospital')
        especialidad_id = request.POST.get('especialidad')
        
        if hospital_id:
            usuario.hospital = get_object_or_404(Hospital, id=hospital_id)
        if especialidad_id:
            usuario.especialidad = get_object_or_404(Especialidad, id=especialidad_id)
        
        usuario.save()
        
        # Auditoría
        Auditoria.objects.create(
            usuario=request.user,
            accion="EDICIÓN",
            detalles=f"Editó a {usuario.nombre_completo} - Rol: {usuario.rol.nombre}",
            tabla_afectada="Usuario"
        )
        
        messages.success(request, f"Personal {usuario.nombre_completo} actualizado.")
        return redirect('superadmin:listar_usuarios')
    
    # IMPORTANTE: Si llegas aquí por GET (para renderizar), 
    # necesitas enviar los roles a la plantilla
    roles = Rol.objects.all()
    return render(request, 'tu_plantilla.html', {'usuario': usuario, 'roles': roles})

@login_required(login_url='superadmin:login')
def registrar_personal(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre_completo')
        email = request.POST.get('email')
        rol_id = request.POST.get('rol_administrativo')
        h_id = request.POST.get('hospital')

        # Seguridad: Si el usuario no es superadmin, forzamos su propio hospital
        if not es_superadmin(request.user) or request.user.username != 'admin2':
            h_id = request.user.hospital.id if request.user.hospital else h_id

        try:
            if Usuario.objects.filter(email=email).exists():
                messages.error(request, f"El correo {email} ya existe.")
                return redirect('superadmin:listar_usuarios')

            rol_instancia = get_object_or_404(Rol, id=rol_id)
            
            nuevo_usuario = Usuario(
                username=email,
                nombre_completo=nombre,
                email=email,
                rol=rol_instancia,
                telefono=request.POST.get('telefono'),
                ciudad=request.POST.get('ciudad'),
                direccion=request.POST.get('direccion'),
                turno_asignado=request.POST.get('turno'),
                estado=request.POST.get('estado') == 'true',
                hospital_id=h_id,
                especialidad_id=request.POST.get('especialidad')
            )
            
            nuevo_usuario.set_password(request.POST.get('password'))
            nuevo_usuario.save()

            Auditoria.objects.create(
                usuario=request.user,
                accion="REGISTRO",
                detalles=f"Registró nuevo personal: {nombre} con rol {rol_instancia.nombre}",
                tabla_afectada="Usuario"
            )

            messages.success(request, f"Especialista {nombre} registrado con éxito.")
            
        except Exception as e:
            messages.error(request, f"Error al registrar: {e}")

    return redirect('superadmin:listar_usuarios')
def eliminar_usuario(request, pk):
    # Solo permitimos eliminar mediante POST por seguridad
    if request.method == 'POST':
        usuario = get_object_or_404(Usuario, id=pk)
        nombre_eliminado = usuario.nombre_completo
        email_eliminado = usuario.email
        
        # 1. Registrar en la tabla de Auditoría (como tienes en tu código)
        Auditoria.objects.create(
            usuario=request.user,
            accion="ELIMINACION",
            detalles=f"Eliminó permanentemente al personal: {nombre_eliminado} ({email_eliminado})",
            tabla_afectada="Usuario"
        )

        # 2. Eliminar el registro
        usuario.delete()
        
        messages.success(request, f"El personal {nombre_eliminado} ha sido eliminado del sistema.")
        
    return redirect('superadmin:listar_usuarios')
def desactivar_usuario(request, pk):
    usuario = get_object_or_404(Usuario, id=pk)
    # Cambiamos el estado a False (Desactivado/En Cirugía/Inactivo)
    usuario.estado = False 
    usuario.save()
    
    messages.warning(request, f"El personal {usuario.nombre_completo} ha sido desactivado.")
    return redirect('superadmin:listar_usuarios')
# =================================================================
# --- CAPACIDADES Y ESPECIALIDADES ---
# =================================================================

@login_required(login_url='superadmin:login')
def listar_capacidades(request):
    user = request.user
    if es_superadmin(user) and user.username == 'admin2':
        capacidades = HospitalEspecialidad.objects.all()
    else:
        capacidades = HospitalEspecialidad.objects.filter(hospital=user.hospital)
        
    return render(request, 'superadmi/capacidades/listar.html', {
        'capacidades': capacidades.select_related('hospital', 'especialidad')
    })
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

#-----------------------------
#Reportes 
#---------------
@login_required
def reporte_hospital_pdf(request, hospital_id):
    # Seguridad: Un admin no puede ver reporte de otro hospital
    if not es_superadmin(request.user) or request.user.username != 'admin2':
        if request.user.hospital and request.user.hospital.id != int(hospital_id):
            return HttpResponse("No tienes permiso para ver este reporte.", status=403)

    hospital = get_object_or_404(Hospital, id=hospital_id)
    camas = Cama.objects.filter(cuarto__hospital=hospital)
    
    # Contadores de personal sincronizados
    usuarios_hosp = Usuario.objects.filter(hospital=hospital)
    medicos_count = Usuario.objects.filter(hospital=hospital, rol__nombre='MEDICO').count()
    enfermeras_count =Usuario.objects.filter(hospital=hospital, rol__nombre='ENFERMERA').count()
    admin_count = Usuario.objects.filter(hospital=hospital, rol__nombre='ADMINISTRATIVO').count()

    # Crear el objeto de respuesta PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Reporte_{hospital.nombre}_{datetime.now().strftime("%d-%m-%Y")}.pdf"'

    p = canvas.Canvas(response, pagesize=letter)
    
    # --- ENCABEZADO INSTITUCIONAL ---
    p.setFont("Helvetica-Bold", 14)
    p.drawString(100, 750, "GOBIERNO AUTÓNOMO DEPARTAMENTAL DE POTOSÍ")
    p.setFont("Helvetica", 10)
    p.drawString(100, 735, "Sistema Departamental de Salud - SEDES POTOSÍ")
    p.line(100, 730, 520, 730)

    # --- DATOS DEL HOSPITAL Y FECHA REAL ---
    p.setFont("Helvetica-Bold", 12)
    p.drawString(100, 700, f"Hospital: {hospital.nombre}")
    p.setFont("Helvetica", 10)
    # Fecha y hora real de Bolivia
    fecha_actual = timezone.now().strftime("%d/%m/%Y %H:%M:%S")
    p.drawString(100, 685, f"Fecha y Hora de emisión: {fecha_actual}") 
    p.drawString(100, 670, f"Generado por: {request.user.nombre_completo or request.user.username}")

    # --- TABLA 1: RESUMEN DE CAMAS ---
    p.setFont("Helvetica-Bold", 11)
    p.drawString(100, 640, "ESTADO DE CAPACIDAD (CAMAS)")
    
    data_camas = [
        ['Estado', 'Cantidad'],
        ['Libres', camas.filter(estado='LIBRE').count()],
        ['Ocupadas', camas.filter(estado='OCUPADO').count()],
        ['Limpieza', camas.filter(estado='LIMPIEZA').count()],
        ['Mantenimiento', camas.filter(estado='MANTENIMIENTO').count()],
        ['TOTAL CAMAS', camas.count()],
    ]

    table_camas = Table(data_camas, colWidths=[150, 100])
    table_camas.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.red), # Color institucional
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    ]))
    
    table_camas.wrapOn(p, 100, 500)
    table_camas.drawOn(p, 100, 500)

    # --- TABLA 2: TALENTO HUMANO (LO NUEVO) ---
    p.setFont("Helvetica-Bold", 11)
    p.drawString(100, 460, "PERSONAL EN TURNO / ASIGNADO")

    data_personal = [
        ['Cargo / Rol', 'Total Registrados'],
        ['Médicos Especialistas', medicos_count],
        ['Personal de Enfermería', enfermeras_count],
        ['Personal Administrativo', admin_count],
    ]

    table_staff = Table(data_personal, colWidths=[150, 100])
    table_staff.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))

    table_staff.wrapOn(p, 100, 380)
    table_staff.drawOn(p, 100, 380)

    # Pie de página
    p.setFont("Helvetica-Oblique", 8)
    p.drawString(100, 50, "Este documento es un reporte oficial emitido por el Monitor de Red Hospitalaria de Potosí.")

    p.showPage()
    p.save()
    return response

