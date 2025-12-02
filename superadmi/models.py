from django.db import models
from django.contrib.auth.models import AbstractUser # Opcional: para usar un modelo de usuario más robusto

# ==============================================================
# 1. TABLAS DE CATÁLOGOS Y ESTRUCTURA CORE (Solo SuperAdmin)
# ==============================================================

class Rol(models.Model):
    '''Catálogo de roles del sistema'''
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField()
    # 1=superadmin, 2=admin, 3=doctor, 4=enfermera, etc.
    nivel_acceso = models.IntegerField(default=5) 
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'roles'
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'


class Especialidad(models.Model):
    '''Catálogo global de especialidades médicas'''
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(null=True, blank=True)
    codigo = models.CharField(max_length=20, unique=True)
    estado = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    # Referencia forward a 'Usuario', se define después
    creado_por = models.ForeignKey(
        'Usuario', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        # AÑADE el related_name aquí para resolver el conflicto E303
        related_name='especialidades_creadas' 
    )
    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'especialidades'
        verbose_name = 'Especialidad'
        verbose_name_plural = 'Especialidades'


class Hospital(models.Model):
    '''Gestión de hospitales del sistema'''
    nombre = models.CharField(max_length=200)
    direccion = models.TextField()
    telefono = models.CharField(max_length=20, null=True, blank=True)
    email = models.CharField(max_length=100, null=True, blank=True)
    capacidad_total = models.IntegerField(default=0)
    estado = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'hospitales'
        verbose_name = 'Hospital'
        verbose_name_plural = 'Hospitales'


class Usuario(models.Model): 
    '''Todos los usuarios del sistema (Se recomienda User model de Django, pero se usa este por el diseño)'''
    nombre_completo = models.CharField(max_length=200)
    email = models.CharField(max_length=100, unique=True)
    password_hash = models.CharField(max_length=255)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    rol = models.ForeignKey(Rol, on_delete=models.PROTECT) # Evita borrar roles si tienen usuarios
    hospital = models.ForeignKey(Hospital, on_delete=models.SET_NULL, null=True, blank=True)
    numero_colegiatura = models.CharField(max_length=50, null=True, blank=True)
    especialidad = models.ForeignKey(Especialidad, on_delete=models.SET_NULL, null=True, blank=True)
    estado = models.BooleanField(default=True)
    ultimo_acceso = models.DateTimeField(null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.nombre_completo

    class Meta:
        db_table = 'usuarios'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'


class HospitalEspecialidad(models.Model):
    '''Especialidades disponibles por hospital'''
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    especialidad = models.ForeignKey(Especialidad, on_delete=models.CASCADE)
    capacidad_camas = models.IntegerField(default=0)
    estado = models.BooleanField(default=True)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.hospital.nombre} - {self.especialidad.nombre}"

    class Meta:
        db_table = 'hospital_especialidades'
        unique_together = ('hospital', 'especialidad')
        verbose_name = 'Hospital-Especialidad'
        verbose_name_plural = 'Hospital-Especialidades'

# === SUPERVISIÓN Y CONTROL ===

class Auditoria(models.Model):
    '''Registro de todas las acciones del sistema'''
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    accion = models.CharField(max_length=100)
    tabla_afectada = models.CharField(max_length=50)
    registro_id = models.IntegerField(null=True, blank=True)
    # JSONField para almacenar diccionarios/datos no estructurados
    datos_anteriores = models.JSONField(null=True, blank=True)
    datos_nuevos = models.JSONField(null=True, blank=True)
    ip_address = models.CharField(max_length=50, null=True, blank=True)
    detalles = models.TextField(null=True, blank=True)
    fecha_accion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'auditoria'
        verbose_name = 'Auditoría'
        verbose_name_plural = 'Auditorías'
        indexes = [
            models.Index(fields=['usuario']),
            models.Index(fields=['fecha_accion']),
        ]

class ConfiguracionSistema(models.Model):
    '''Parámetros globales del sistema'''
    clave = models.CharField(max_length=100, unique=True)
    valor = models.TextField()
    descripcion = models.TextField(null=True, blank=True)
    tipo_dato = models.CharField(max_length=20)
    modificable_por = models.CharField(max_length=20, default='superadmin')
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    actualizado_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'configuracion_sistema'
        verbose_name = 'Configuración'
        verbose_name_plural = 'Configuraciones'

class Reporte(models.Model):
    '''Reportes generados en el sistema'''
    titulo = models.CharField(max_length=200)
    tipo_reporte = models.CharField(max_length=50)
    generado_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, null=True, blank=True)
    parametros = models.JSONField(null=True, blank=True)
    fecha_desde = models.DateField(null=True, blank=True)
    fecha_hasta = models.DateField(null=True, blank=True)
    resultado = models.JSONField(null=True, blank=True)
    fecha_generacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reportes'
        verbose_name = 'Reporte'
        verbose_name_plural = 'Reportes'


