from django.db import models
from django.utils import timezone
# Importamos los modelos del Sprint 1 para que sea la MISMA base de datos
from superadmi.models import Hospital, Especialidad, Usuario
from django.conf import settings
from django.contrib.auth.models import User

class Cuarto(models.Model):
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='cuartos')
    especialidad = models.ForeignKey(Especialidad, on_delete=models.CASCADE, related_name='cuartos')
    numero_cuarto = models.CharField(max_length=10, verbose_name="Nro de Cuarto")
    piso = models.CharField(max_length=50)
    
    class Meta:
        verbose_name = "Cuarto"
        verbose_name_plural = "Cuartos"
        unique_together = ('hospital', 'numero_cuarto')

    def __str__(self):
        return f"Cuarto {self.numero_cuarto} - {self.hospital.nombre}"

class Cama(models.Model):
    ESTADOS = [
        ('LIBRE', 'Libre'),
        ('OCUPADO', 'Ocupado'),
        ('MANTENIMIENTO', 'Mantenimiento'),
        ('LIMPIEZA', 'En Limpieza'),     
    ]
    
    cuarto = models.ForeignKey('Cuarto', on_delete=models.CASCADE, related_name='camas')
    numero = models.CharField(max_length=50)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='LIBRE')
    
    fecha_ingreso = models.DateTimeField(null=True, blank=True)
    prioridad = models.CharField(
        max_length=20, 
        choices=[('ESTABLE', 'Estable'), ('URGENTE', 'Urgente'), ('CRITICO', 'Crítico')],
        default='ESTABLE'
    )

    def __str__(self):
        return f"Cama {self.numero} - {self.cuarto.numero_cuarto}"

class Paciente(models.Model):
    GENEROS = [('M', 'Masculino'), ('F', 'Femenino'), ('O', 'Otro')]
    ESTADOS = [('INTERNADO', 'Internado'), ('ALTA', 'De Alta')]
    
    # --- Identidad ---
    nombre_completo = models.CharField(max_length=200)
    dni = models.CharField(max_length=20, unique=True)
    fecha_nacimiento = models.DateField()
    genero = models.CharField(max_length=1, choices=GENEROS)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    direccion = models.TextField()
    fecha_entrada = models.DateTimeField(null=True, blank=True)
    # --- Triaje de Ingreso (Lo que faltaba para el nivel PRO) ---
    motivo_ingreso = models.TextField(verbose_name="Diagnóstico Presuntivo / Motivo")
    presion_arterial = models.CharField(max_length=20, null=True, blank=True)
    temperatura = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    frecuencia_cardiaca = models.IntegerField(null=True, blank=True)
    saturacion_oxigeno = models.IntegerField(null=True, blank=True) # Campo nuevo vital
    alergias = models.TextField(default="Ninguna")

    # --- Logística ---
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='pacientes')
    cama_asignada = models.OneToOneField(Cama, on_delete=models.SET_NULL, null=True, blank=True, related_name='paciente_actual')
    fecha_registro = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='INTERNADO')
    ambulancia_asignada = models.ForeignKey('Ambulancia', on_delete=models.SET_NULL, null=True, blank=True)
    def __str__(self):
        return f"{self.nombre_completo} - {self.dni}"

class EvolucionMedica(models.Model):
    TIPOS_EVOLUCION = [
        ('RUTINA', 'Revisión de Rutina'),
        ('URGENCIA', 'Urgencia/Emergencia'),
        ('ALTA', 'Nota de Alta Médica'),
    ]
    
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='evoluciones')
    fecha_registro = models.DateTimeField(auto_now_add=True)
    tipo = models.CharField(max_length=20, choices=TIPOS_EVOLUCION, default='RUTINA')
    temperatura = models.DecimalField(max_digits=4, decimal_places=1)
    presion_arterial = models.CharField(max_length=20)
    frecuencia_cardiaca = models.IntegerField()
    descripcion = models.TextField(verbose_name="Observaciones Médicas")
    indicaciones = models.TextField(verbose_name="Indicaciones/Tratamiento")
    # Usamos AUTH_USER_MODEL para evitar errores de importación circular
    creado_por = models.ForeignKey('superadmi.Usuario', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Evolución de {self.paciente.nombre_completo} - {self.fecha_registro.date()}"
class Ambulancia(models.Model):
    TIPOS = [
        ('BÁSICA', 'Básica'), 
        ('AVANZADA', 'Avanzada'),
        ('TERAPIA', 'Terapia Intensiva') # Añadimos uno más para la tesis
    ]
    ESTADOS_UNIDAD = [
        ('DISPONIBLE', 'Disponible'), 
        ('EN_CAMINO', 'En Camino / Traslado'), 
        ('MANTENIMIENTO', 'En Mantenimiento')
    ]

    placa = models.CharField(max_length=15, unique=True)
    modelo = models.CharField(max_length=50)
    tipo = models.CharField(max_length=20, choices=TIPOS, default='BÁSICA')
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='ambulancias')
    
    # Mantenemos este por si en el futuro quieres vincular un usuario real
    chofer_asignado = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='ambulancia_personal'
    )

    # NUEVO CAMPO: Para escribir el nombre completo directamente (Nivel Pro)
    nombre_chofer_manual = models.CharField(
        max_length=200, 
        blank=True, 
        null=True, 
        verbose_name="Nombre Completo del Chofer"
    )
    
    estado = models.CharField(max_length=20, choices=ESTADOS_UNIDAD, default='DISPONIBLE')

    def __str__(self):
        return f"{self.placa} ({self.tipo}) - {self.hospital.nombre}"

    class Meta:
        verbose_name = "Ambulancia"
        verbose_name_plural = "Ambulancias"


class Derivacion(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'En Camino'), 
        ('RECIBIDO', 'Recibido'), 
        ('CANCELADO', 'Cancelado')
    ]
    PRIORIDADES = [('BAJA', 'Baja'), ('MEDIA', 'Media'), ('ALTA', 'Alta'), ('CRÍTICA', 'Crítica')]

    paciente = models.ForeignKey('Paciente', on_delete=models.CASCADE)
    hospital_origen = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='salidas')
    hospital_destino = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='entradas')
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    ambulancia = models.ForeignKey(Ambulancia, on_delete=models.SET_NULL, null=True, blank=True, related_name='derivaciones')
    
    prioridad = models.CharField(max_length=10, choices=PRIORIDADES, default='MEDIA')
    motivo_traslado = models.TextField()
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')

    def __str__(self):
        return f"Traslado: {self.paciente} -> {self.hospital_destino.nombre}"

    class Meta:
        verbose_name = "Derivación"
        verbose_name_plural = "Derivaciones"
        
class FormularioBase(models.Model):
    paciente = models.ForeignKey('Paciente', on_delete=models.CASCADE)
    
    # CORRECCIÓN: Apuntar al modelo que importaste de superadmi
    hospital_origen = models.ForeignKey(
        Hospital, 
        on_delete=models.CASCADE, 
        related_name="%(class)s_origen"
    )
    hospital_destino = models.ForeignKey(
        Hospital, 
        on_delete=models.CASCADE, 
        related_name="%(class)s_destino"
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    # CORRECCIÓN: Usar settings.AUTH_USER_MODEL para evitar el error E301
    medico_responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True
    )

    class Meta:
        abstract = True

# 1. REFERENCIA D7 (Envío a mayor complejidad)
class FormularioD7(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='formularios_d7')
    # Datos de Referencia
    eess_solicitante = models.CharField(max_length=200, blank=True, null=True)
    eess_receptor = models.CharField(max_length=200, blank=True, null=True)
    especialidad_solicitada = models.CharField(max_length=100, blank=True, null=True)
    fecha_referencia = models.DateField(auto_now_add=True)
    
    # Resumen Clínico
    motivo_referencia = models.TextField(blank=True, null=True)
    examen_fisico = models.TextField(blank=True, null=True)
    diagnostico_presuntivo = models.CharField(max_length=255, blank=True, null=True)
    cie_10 = models.CharField(max_length=10, blank=True, null=True)
    
    def __str__(self):
        return f"D7 Referencia - {self.paciente.nombre_completo}"

class ContrarreferenciaD7a(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='formularios_d7a')
    
    # C1: Datos del Establecimiento (MODIFICADOS PARA PERMITIR NULOS)
    eess_contrarrefiere = models.CharField(max_length=200, null=True, blank=True)
    servicio = models.CharField(max_length=100, null=True, blank=True)
    red_salud = models.CharField(max_length=100, null=True, blank=True)
    municipio = models.CharField(max_length=100, null=True, blank=True)
    telefono_contacto = models.CharField(max_length=20, null=True, blank=True)
    fecha = models.DateField(null=True, blank=True)
    hora = models.TimeField(null=True, blank=True)
    nivel_eess = models.CharField(max_length=10, null=True, blank=True)

    # C2: Identificación (MODIFICADOS)
    discapacidad = models.CharField(max_length=2, choices=[('SI', 'SI'), ('NO', 'NO')], null=True, blank=True)
    tipo_discapacidad = models.CharField(max_length=100, blank=True, null=True)
    grado_discapacidad = models.CharField(max_length=50, blank=True, null=True)

    # C3: Datos Clínicos de Alta
    dias_internacion = models.IntegerField(null=True, blank=True)
    peso = models.CharField(max_length=10, null=True, blank=True)
    imc = models.CharField(max_length=10, null=True, blank=True)
    temperatura = models.CharField(max_length=10, null=True, blank=True)
    pa = models.CharField(max_length=20, null=True, blank=True)
    fc = models.CharField(max_length=10, null=True, blank=True)
    fr = models.CharField(max_length=10, null=True, blank=True)
    spo2 = models.CharField(max_length=10, null=True, blank=True)

    # C4 y C5: Diagnósticos
    diag_ingreso_a = models.CharField(max_length=255, null=True, blank=True)
    cie10_ingreso_a = models.CharField(max_length=10, null=True, blank=True)
    diag_egreso_a = models.CharField(max_length=255, null=True, blank=True)
    cie10_egreso_a = models.CharField(max_length=10, null=True, blank=True)

    # C6 al C12: Áreas de Texto
    evolucion_complicaciones = models.TextField(null=True, blank=True)
    examenes_complementarios = models.TextField(null=True, blank=True)
    otros_examenes = models.TextField(null=True, blank=True)
    tratamientos_realizados = models.TextField(null=True, blank=True)
    recomendaciones_paciente = models.TextField(null=True, blank=True)
    anexos_pendientes = models.TextField(null=True, blank=True)
    observaciones_contrarreferencia = models.TextField(null=True, blank=True)

    # C13: Destino
    eess_destino = models.CharField(max_length=200, null=True, blank=True)
    contacto_recibe = models.CharField(max_length=200, null=True, blank=True)
    nombre_acompanante = models.CharField(max_length=200, null=True, blank=True)
    
    def __str__(self):
        return f"D7a - {self.paciente.nombre_completo} ({self.fecha})"

# 3. TRANSFERENCIA D7b (Entre servicios o misma complejidad)
class FormularioD7b(models.Model):
    # Relación con el paciente
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='formularios_d7b')
    
    # Datos del establecimiento
    eess_transfiere = models.CharField(max_length=200, blank=True, null=True)
    nivel_eess = models.CharField(max_length=50, blank=True, null=True)
    red_salud = models.CharField(max_length=100, blank=True, null=True)
    municipio = models.CharField(max_length=100, blank=True, null=True)
    fecha = models.DateField(auto_now_add=True)
    hora = models.TimeField(auto_now_add=True)
    
    # Datos del formulario
    domicilio = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    hc = models.CharField(max_length=50, blank=True, null=True)
    procedencia = models.CharField(max_length=100, blank=True, null=True)
    
    # Signos Vitales
    fc = models.CharField(max_length=20, blank=True, null=True)
    fr = models.CharField(max_length=20, blank=True, null=True)
    pa = models.CharField(max_length=20, blank=True, null=True)
    temp = models.CharField(max_length=20, blank=True, null=True)
    peso = models.CharField(max_length=20, blank=True, null=True)
    glasgow = models.CharField(max_length=20, blank=True, null=True)
    spo2 = models.CharField(max_length=20, blank=True, null=True)
    
    # Resumen médico
    anamnesis = models.TextField(blank=True, null=True)
    
    # Diagnósticos
    diag_a = models.CharField(max_length=255, blank=True, null=True)
    cie_a = models.CharField(max_length=10, blank=True, null=True)
    diag_b = models.CharField(max_length=255, blank=True, null=True)
    cie_b = models.CharField(max_length=10, blank=True, null=True)
    
    # Consentimiento
    cons_nombre = models.CharField(max_length=200, blank=True, null=True)
    cons_edad = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return f"D7b - {self.paciente.nombre_completo} ({self.fecha})"
##del control diario    
class ReporteDiario(models.Model):
    # Relaciones y Control
    hospital = models.ForeignKey('superadmi.Hospital', on_delete=models.CASCADE, related_name='reportes_diarios')
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    # Encabezado del Reporte
    personal_reporta = models.CharField(max_length=150, help_text="Nombre de quien llena el form")
    fecha = models.DateField(default=timezone.now)
    hora = models.TimeField(default=timezone.now)

    # Personal de Salud de Turno (Mañana, Tarde, Noche)
    medico_manana = models.CharField(max_length=150, blank=True, null=True)
    auxiliar_manana = models.CharField(max_length=150, blank=True, null=True)
    medico_tarde = models.CharField(max_length=150, blank=True, null=True)
    auxiliar_tarde = models.CharField(max_length=150, blank=True, null=True)
    medico_noche = models.CharField(max_length=150, blank=True, null=True)
    auxiliar_noche = models.CharField(max_length=150, blank=True, null=True)

    # Logística y Ambulancias
    chofer_a = models.CharField(max_length=150, blank=True, null=True)
    chofer_b = models.CharField(max_length=150, blank=True, null=True)
    amb_t1 = models.IntegerField(default=0)
    amb_t1_op = models.CharField(max_length=10, blank=True, null=True) # Operativa (Sí/No)
    amb_t2 = models.IntegerField(default=0)
    amb_t2_op = models.CharField(max_length=10, blank=True, null=True)

    # Camas Disponibles por Servicio (V=Viejas/Totales, L=Libres, M=Mantenimiento)
    # Cirugía
    cir_v = models.IntegerField(default=0)
    cir_l = models.IntegerField(default=0)
    cir_m = models.IntegerField(default=0)
    # Traumatología
    tra_v = models.IntegerField(default=0)
    tra_l = models.IntegerField(default=0)
    tra_m = models.IntegerField(default=0)
    # Medicina Interna
    med_v = models.IntegerField(default=0)
    med_l = models.IntegerField(default=0)
    med_m = models.IntegerField(default=0)
    # Pediatría
    ped_camas = models.IntegerField(default=0)
    ped_cunas = models.IntegerField(default=0)

    # Servicios Especializados (Totales/Disponibles)
    uti = models.IntegerField(default=0)
    neo = models.IntegerField(default=0)
    maternidad = models.IntegerField(default=0)
    infectologia = models.IntegerField(default=0)
    terapia_intermedia = models.IntegerField(default=0)

    # Personal CRUEM (Pre-llenado o fijo)
    cruem_medico = models.CharField(max_length=150, default="DRA. ALEJANDRA ABAJO")
    cruem_auxiliar = models.CharField(max_length=150, default="LIC. MARLENE FLORES DELGADO")

    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        # Evita reportes duplicados del mismo hospital el mismo día
        unique_together = ('hospital', 'fecha')
        verbose_name = "Reporte Diario"
        verbose_name_plural = "Reportes Diarios"

    def __str__(self):
        return f"Reporte {self.hospital.nombre} - {self.fecha}"
###incidencias
class IncidenciaCRUEM(models.Model):
    TIPOS_INCIDENCIA = [
        ('PRE', 'Prehospitalaria'),
        ('TRA', 'Traslado'),
        ('REF', 'Referencia'),
        ('EVE', 'Evento Deportivo'),
    ]
    tipo = models.CharField(max_length=3, choices=TIPOS_INCIDENCIA, default='PRE')
    nro_incidente = models.CharField(max_length=20, verbose_name="N° Incidente")
    fecha = models.DateField()
    hora_apertura = models.TimeField()
    hora_finalizacion = models.TimeField(null=True, blank=True)
    reportante = models.CharField(max_length=150)
    telefono_celular = models.CharField(max_length=20)
    del_paciente = models.CharField(max_length=150)
    diagnostico = models.TextField(null=True, blank=True)
    motivo_llamada = models.TextField()
    prioridad = models.CharField(max_length=50)
    respuesta = models.CharField(max_length=100)
    coordinacion_traslado = models.TextField(null=True, blank=True)
    
    # Para saber qué usuario registró esto
    usuario_registro = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        verbose_name="Usuario que registra"
    )

    def __str__(self):
        return f"Incidente {self.nro_incidente} - {self.del_paciente}"
###CIE
class EnfermedadCIE10(models.Model):
    # db_index=True hace que buscar entre 14,000 datos sea instantáneo
    codigo = models.CharField(max_length=10, unique=True, db_index=True)
    descripcion = models.TextField()

    def __str__(self):
        return f"{self.codigo} - {self.descripcion}"

    class Meta:
        verbose_name = "Enfermedad CIE-10"
        verbose_name_plural = "Enfermedades CIE-10"

