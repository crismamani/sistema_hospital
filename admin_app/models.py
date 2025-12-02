from django.db import models
# Importamos modelos definidos en SuperAdmin
from superadmi.models import Hospital, Usuario, Especialidad 

# ==============================================================
# 2. TABLAS DE GESTIÓN OPERATIVA HOSPITALARIA (Gestionadas por Admin)
# ==============================================================

class HistoriaClinica(models.Model):
    '''Registro médico completo de un paciente'''
    # Relaciones
    paciente = models.OneToOneField('Paciente', on_delete=models.CASCADE, primary_key=True)
    medico_responsable = models.ForeignKey('Personal', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Campos de registro
    fecha_apertura = models.DateField(auto_now_add=True)
    diagnostico_inicial = models.TextField()
    antecedentes_personales = models.TextField(blank=True, null=True)
    antecedentes_familiares = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'historia_clinica'
        verbose_name = 'Historia Clínica'
        verbose_name_plural = 'Historias Clínicas'
        
    def __str__(self):
        return f"HC de {self.paciente.nombre_completo}" # Asumiendo un campo nombre_completo en Paciente
class Paciente(models.Model):
    '''Información de pacientes del sistema'''
    numero_documento = models.CharField(max_length=20, unique=True)
    tipo_documento = models.CharField(max_length=20)
    nombre_completo = models.CharField(max_length=200)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    genero = models.CharField(max_length=20, null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    direccion = models.TextField(null=True, blank=True)
    contacto_emergencia = models.CharField(max_length=200, null=True, blank=True)
    telefono_emergencia = models.CharField(max_length=20, null=True, blank=True)
    seguro_medico = models.CharField(max_length=100, null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pacientes'
        verbose_name = 'Paciente'
        verbose_name_plural = 'Pacientes'


class Notificacion(models.Model):
    '''Notificaciones del sistema para usuarios'''
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=50) 
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    prioridad = models.CharField(max_length=20, default='normal')
    leida = models.BooleanField(default=False)
    url_referencia = models.CharField(max_length=255, null=True, blank=True)
    entidad_tipo = models.CharField(max_length=50, null=True, blank=True)
    entidad_id = models.IntegerField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_lectura = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'notificaciones'
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        indexes = [
            models.Index(fields=['usuario']),
            models.Index(fields=['leida']),
        ]


class Sala(models.Model):
    '''Salas del hospital'''
    nombre = models.CharField(max_length=100)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    especialidad = models.ForeignKey(Especialidad, on_delete=models.SET_NULL, null=True, blank=True)
    piso = models.IntegerField(null=True, blank=True)
    capacidad_total = models.IntegerField()
    tipo_sala = models.CharField(max_length=50)
    estado = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'salas'
        verbose_name = 'Sala'
        verbose_name_plural = 'Salas'


class Cama(models.Model):
    '''Camas del hospital'''
    codigo_cama = models.CharField(max_length=50)
    sala = models.ForeignKey(Sala, on_delete=models.CASCADE)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    especialidad = models.ForeignKey(Especialidad, on_delete=models.SET_NULL, null=True, blank=True)
    estado_cama = models.CharField(max_length=20, default='disponible')
    tipo_cama = models.CharField(max_length=50)
    ubicacion_detalle = models.CharField(max_length=100, null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'camas'
        verbose_name = 'Cama'
        verbose_name_plural = 'Camas'
        unique_together = ('hospital', 'codigo_cama')
        indexes = [
            models.Index(fields=['hospital']),
            models.Index(fields=['estado_cama']),
        ]


class HistorialCama(models.Model):
    '''Historial de cambios de estado de camas'''
    cama = models.ForeignKey(Cama, on_delete=models.CASCADE)
    paciente = models.ForeignKey(Paciente, on_delete=models.SET_NULL, null=True, blank=True)
    # Referencia forward a 'Internacion', se define después
    internacion = models.ForeignKey('Internacion', on_delete=models.SET_NULL, null=True, blank=True)
    estado_anterior = models.CharField(max_length=20, null=True, blank=True)
    estado_nuevo = models.CharField(max_length=20)
    motivo_cambio = models.TextField(null=True, blank=True)
    realizado_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_cambio = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'historial_camas'
        verbose_name = 'Historial de Cama'
        verbose_name_plural = 'Historial de Camas'


class Derivacion(models.Model):
    '''Derivaciones entre hospitales'''
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    internacion_origen = models.ForeignKey('Internacion', on_delete=models.SET_NULL, null=True, blank=True)
    hospital_origen = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='derivaciones_enviadas')
    hospital_destino = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='derivaciones_recibidas')
    especialidad_solicitada = models.ForeignKey(Especialidad, on_delete=models.SET_NULL, null=True, blank=True)
    doctor_solicitante = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='derivaciones_solicitadas')
    doctor_receptor = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='derivaciones_recibidas')
    motivo_derivacion = models.TextField()
    diagnostico = models.TextField(null=True, blank=True)
    prioridad = models.CharField(max_length=20, default='normal')
    estado = models.CharField(max_length=30, default='pendiente')
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_respuesta = models.DateTimeField(null=True, blank=True)
    fecha_traslado = models.DateTimeField(null=True, blank=True)
    observaciones = models.TextField(null=True, blank=True)
    motivo_rechazo = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'derivaciones'
        verbose_name = 'Derivación'
        verbose_name_plural = 'Derivaciones'
        indexes = [
            models.Index(fields=['hospital_origen']),
            models.Index(fields=['hospital_destino']),
            models.Index(fields=['estado']),
        ]


class SolicitudCama(models.Model):
    '''Solicitudes de cama para derivaciones'''
    derivacion = models.ForeignKey(Derivacion, on_delete=models.SET_NULL, null=True, blank=True)
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    hospital_solicitante = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='solicitudes_enviadas')
    hospital_destino = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='solicitudes_recibidas')
    especialidad = models.ForeignKey(Especialidad, on_delete=models.CASCADE)
    sala_preferida = models.ForeignKey(Sala, on_delete=models.SET_NULL, null=True, blank=True)
    tipo_cama_requerida = models.CharField(max_length=50)
    prioridad = models.CharField(max_length=20, default='normal')
    estado = models.CharField(max_length=30, default='pendiente')
    cama_asignada = models.ForeignKey(Cama, on_delete=models.SET_NULL, null=True, blank=True)
    motivo_solicitud = models.TextField()
    diagnostico_preliminar = models.TextField(null=True, blank=True)
    solicitado_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='solicitudes_realizadas')
    respondido_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='solicitudes_respondidas')
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_respuesta = models.DateTimeField(null=True, blank=True)
    fecha_asignacion = models.DateTimeField(null=True, blank=True)
    observaciones = models.TextField(null=True, blank=True)
    motivo_rechazo = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'solicitudes_cama'
        verbose_name = 'Solicitud de Cama'
        verbose_name_plural = 'Solicitudes de Cama'
        indexes = [
            models.Index(fields=['estado']),
            models.Index(fields=['hospital_destino']),
        ]


class Internacion(models.Model):
    '''Pacientes internados'''
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    cama = models.ForeignKey(Cama, on_delete=models.CASCADE)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    especialidad = models.ForeignKey(Especialidad, on_delete=models.SET_NULL, null=True, blank=True)
    doctor_responsable = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_ingreso = models.DateTimeField()
    fecha_egreso = models.DateTimeField(null=True, blank=True)
    motivo_internacion = models.TextField()
    diagnostico = models.TextField(null=True, blank=True)
    estado = models.CharField(max_length=20, default='activo')
    observaciones = models.TextField(null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'internaciones'
        verbose_name = 'Internación'
        verbose_name_plural = 'Internaciones'
        indexes = [
            models.Index(fields=['paciente']),
            models.Index(fields=['estado']),
        ]


# admin_app/models.py

# Opciones para el campo estado_laboral
ESTADO_LABORAL_CHOICES = [
    ('activo', 'Activo'),
    ('licencia', 'Licencia'),
    ('retirado', 'Retirado'),
    ('vacaciones', 'Vacaciones'),
]

class Personal(models.Model):
    '''Personal médico y de enfermería'''
    # Campos existentes
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    tipo_personal = models.CharField(max_length=50) 
    numero_licencia = models.CharField(max_length=50, null=True, blank=True)
    especialidad = models.ForeignKey(Especialidad, on_delete=models.SET_NULL, null=True, blank=True)
    foto_perfil = models.CharField(max_length=255, null=True, blank=True)
    fecha_contratacion = models.DateField(null=True, blank=True)
    tipo_contrato = models.CharField(max_length=50, null=True, blank=True)
    
    # --- CAMPOS AÑADIDOS PARA RESOLVER EL FIELDERROR ---
    
    horario_preferencia = models.CharField(
        max_length=50, 
        default='Rotativo', 
        help_text='Horario asignado (ej: Mañana, Tarde, Noche, Rotativo)'
    ) 
    
    estado_laboral = models.CharField(
        max_length=20, 
        choices=ESTADO_LABORAL_CHOICES, 
        default='activo'
    )
    
    class Meta:
        db_table = 'personal'
        verbose_name = 'Personal'
        verbose_name_plural = 'Personal'
        
    def __str__(self):
        # Asumiendo que el modelo Usuario tiene un campo nombre o username
        return f"{self.usuario.username} - {self.tipo_personal}"

class Turno(models.Model):
    '''Turnos programados del personal'''
    personal = models.ForeignKey(Personal, on_delete=models.CASCADE)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    especialidad = models.ForeignKey(Especialidad, on_delete=models.SET_NULL, null=True, blank=True)
    sala = models.ForeignKey(Sala, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_turno = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    tipo_turno = models.CharField(max_length=30)
    estado = models.CharField(max_length=30, default='programado')
    observaciones = models.TextField(null=True, blank=True)
    creado_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'turnos'
        verbose_name = 'Turno'
        verbose_name_plural = 'Turnos'
        indexes = [
            models.Index(fields=['personal']),
            models.Index(fields=['fecha_turno']),
        ]


class Asistencia(models.Model):
    '''Registro de asistencia del personal'''
    turno = models.ForeignKey(Turno, on_delete=models.CASCADE)
    personal = models.ForeignKey(Personal, on_delete=models.CASCADE)
    hora_entrada = models.DateTimeField(null=True, blank=True)
    hora_salida = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=30)
    justificacion = models.TextField(null=True, blank=True)
    registrado_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'asistencias'
        verbose_name = 'Asistencia'
        verbose_name_plural = 'Asistencias'


class TransferenciaInterna(models.Model):
    '''Transferencias dentro del mismo hospital'''
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    internacion = models.ForeignKey(Internacion, on_delete=models.CASCADE)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    cama_origen = models.ForeignKey(Cama, on_delete=models.CASCADE, related_name='transferencias_origen')
    cama_destino = models.ForeignKey(Cama, on_delete=models.CASCADE, related_name='transferencias_destino')
    especialidad_origen = models.ForeignKey(Especialidad, on_delete=models.SET_NULL, null=True, blank=True, related_name='transferencias_desde')
    especialidad_destino = models.ForeignKey(Especialidad, on_delete=models.SET_NULL, null=True, blank=True, related_name='transferencias_hacia')
    motivo_transferencia = models.TextField()
    estado = models.CharField(max_length=30, default='pendiente')
    solicitado_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='transferencias_solicitadas')
    aprobado_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='transferencias_aprobadas')
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_aprobacion = models.DateTimeField(null=True, blank=True)
    fecha_transferencia = models.DateTimeField(null=True, blank=True)
    observaciones = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'transferencias_internas'
        verbose_name = 'Transferencia Interna'
        verbose_name_plural = 'Transferencias Internas'

