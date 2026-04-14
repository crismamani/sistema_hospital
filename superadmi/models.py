from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

# --- MANAGER DE USUARIOS ---
class UsuarioManager(BaseUserManager):
    def create_user(self, username, email, nombre_completo, password=None, **extra_fields):
        if not username:
            raise ValueError('El nombre de usuario es obligatorio')
        if not email:
            raise ValueError('El email es obligatorio')
        
        email = self.normalize_email(email)
        user = self.model(
            username=username, 
            email=email, 
            nombre_completo=nombre_completo,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, nombre_completo, password=None, **extra_fields):
        extra_fields.setdefault('is_admin', True)
        # El superusuario se crea sin rol inicial porque la tabla de roles suele estar vacía
        return self.create_user(username, email, nombre_completo, password, **extra_fields)

# --- TABLAS DE CATÁLOGOS ---

class Rol(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(null=True, blank=True)
    nivel_acceso = models.IntegerField(default=5) 
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'roles'
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'


class Hospital(models.Model):
    nombre = models.CharField(max_length=200)
    nivel = models.IntegerField(choices=[(1, '1er Nivel'), (2, '2do Nivel'), (3, '3er Nivel')], default=1)
    direccion = models.TextField()
    telefono = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(max_length=100, null=True, blank=True)
    capacidad_camas = models.IntegerField(default=0) 
    estado = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre
    
class Especialidad(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(null=True, blank=True)
    codigo = models.CharField(max_length=20, unique=True, null=True, blank=True)
    estado = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    # Referencia a Usuario (se usa string 'Usuario' porque se define abajo)
    creado_por = models.ForeignKey(
        'Usuario', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='especialidades_creadas' 
    )

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'especialidades'
        verbose_name = 'Especialidad'
        verbose_name_plural = 'Especialidades'
class HospitalEspecialidad(models.Model):
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='especialidades_asignadas')
    especialidad = models.ForeignKey(Especialidad, on_delete=models.CASCADE)
    # Aquí es donde vive la capacidad específica que querías
    capacidad_camas = models.IntegerField(default=0) 
    estado = models.BooleanField(default=True)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'hospital_especialidades'
        unique_together = ('hospital', 'especialidad')

# --- MODELO DE USUARIO PERSONALIZADO ---
class Usuario(AbstractBaseUser):
    username = models.CharField(max_length=50, unique=True)
    nombre_completo = models.CharField(max_length=200)
    email = models.EmailField(max_length=100, unique=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    
    # Campos que se habían borrado y causaron el error
    numero_colegiatura = models.CharField(max_length=50, null=True, blank=True)
    
    # Nuevos campos para dirección y turno
    ciudad = models.CharField(max_length=100, null=True, blank=True)
    direccion = models.CharField(max_length=255, null=True, blank=True)
    turno_asignado = models.CharField(max_length=100, null=True, blank=True)

    rol = models.ForeignKey(Rol, on_delete=models.SET_NULL, null=True, blank=True)
    hospital = models.ForeignKey(Hospital, on_delete=models.SET_NULL, null=True, blank=True)
    especialidad = models.ForeignKey(Especialidad, on_delete=models.SET_NULL, null=True, blank=True)
    
    estado = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    objects = UsuarioManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'nombre_completo']

    class Meta:
        db_table = 'usuarios'

    def __str__(self):
        return self.nombre_completo

    @property
    def is_staff(self):
        return self.is_admin

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return self.is_admin

# --- RELACIONES Y AUDITORÍA ---

class Auditoria(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    accion = models.CharField(max_length=100) 
    tabla_afectada = models.CharField(max_length=50)
    registro_id = models.IntegerField(null=True, blank=True)
    datos_anteriores = models.JSONField(null=True, blank=True)
    datos_nuevos = models.JSONField(null=True, blank=True)
    ip_address = models.CharField(max_length=50, null=True, blank=True)
    detalles = models.TextField(null=True, blank=True)
    fecha_accion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'auditoria'
        verbose_name = 'Auditoría'
        verbose_name_plural = 'Auditorías'
        ordering = ['-fecha_accion'] 
        indexes = [
            models.Index(fields=['usuario']),
            models.Index(fields=['fecha_accion']),
            models.Index(fields=['tabla_afectada']),
        ]

    def __str__(self):
        return f"{self.usuario} - {self.accion} ({self.fecha_accion})"


class ConfiguracionSistema(models.Model):
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
