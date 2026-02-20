from django.db import models
# Importamos los modelos del Sprint 1 para que sea la MISMA base de datos
from superadmi.models import Hospital, Especialidad, Usuario

class Cuarto(models.Model):
    # Usamos los modelos de superadmi que ya tienen datos
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='cuartos')
    especialidad = models.ForeignKey(Especialidad, on_delete=models.CASCADE, related_name='cuartos')
    numero_cuarto = models.CharField(max_length=10, verbose_name="Nro de Cuarto")
    piso = models.CharField(max_length=50)
    
    class Meta:
        verbose_name = "Cuarto"
        verbose_name_plural = "Cuartos"
        unique_together = ('hospital', 'numero_cuarto')

    def __str__(self):
        # Esto quita el "Hospital object (1)" y muestra el nombre real
        return f"Cuarto {self.numero_cuarto} - {self.hospital.nombre}"

class Cama(models.Model):
    ESTADOS = [
        ('LIBRE', 'Libre'),
        ('OCUPADO', 'Ocupado'),
        ('MANTENIMIENTO', 'Mantenimiento'),
        ('LIMPIEZA', 'En Limpieza'),     
        ('RESERVADO', 'Reservado')
    ]
    cuarto = models.ForeignKey(Cuarto, on_delete=models.CASCADE, related_name='camas')
    numero = models.CharField(max_length=10, verbose_name="Código/Nro de Cama")
    estado = models.CharField(max_length=20, choices=ESTADOS, default='LIBRE')

    def __str__(self):
        return f"Cama {self.numero} - {self.cuarto.numero_cuarto}"

class Paciente(models.Model):
    GENEROS = [('M', 'Masculino'), ('F', 'Femenino'), ('O', 'Otro')]
    ESTADOS = [('INTERNADO', 'Internado'), ('ALTA', 'De Alta')]
    
    nombre_completo = models.CharField(max_length=200)
    dni = models.CharField(max_length=20, unique=True)
    fecha_nacimiento = models.DateField()
    genero = models.CharField(max_length=1, choices=GENEROS)
    telefono = models.CharField(max_length=20)
    direccion = models.TextField()
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='pacientes')
    # OneToOneField asegura que un paciente tenga una cama y una cama un solo paciente
    cama_asignada = models.OneToOneField(Cama, on_delete=models.SET_NULL, null=True, blank=True, related_name='paciente_actual')
    fecha_registro = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='INTERNADO')

    def __str__(self):
        return self.nombre_completo

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
class Derivacion(models.Model):
    ESTADOS = [('PENDIENTE', 'En Camino'), ('RECIBIDO', 'Recibido'), ('CANCELADO', 'Cancelado')]
    PRIORIDAD = [('BAJA', 'Baja'), ('MEDIA', 'Media'), ('ALTA', 'Urgencia')]

    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    hospital_origen = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='salidas')
    hospital_destino = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='entradas')
    prioridad = models.CharField(max_length=10, choices=PRIORIDAD, default='MEDIA')
    motivo_traslado = models.TextField()
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')

    def __str__(self):
        return f"Traslado de {self.paciente} a {self.hospital_destino}"
        