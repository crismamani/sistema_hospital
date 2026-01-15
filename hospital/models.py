from django.db import models

class Hospital(models.Model):
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=200)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)

    def __str__(self):
        return self.nombre

class Cama(models.Model):
    ESTADOS = [
        ('LIBRE', 'Libre'),
        ('OCUPADO', 'Ocupado'),
        ('MANTENIMIENTO', 'Mantenimiento'),
    ]
    numero = models.CharField(max_length=10)
    piso = models.CharField(max_length=50)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='LIBRE')
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='camas')

    def __str__(self):
        return f"Cama {self.numero} ({self.estado})"

class Paciente(models.Model):
    GENEROS = [('M', 'Masculino'), ('F', 'Femenino'), ('O', 'Otro')]
    
    nombre_completo = models.CharField(max_length=200)
    dni = models.CharField(max_length=20, unique=True)
    fecha_nacimiento = models.DateField()
    genero = models.CharField(max_length=1, choices=GENEROS)
    telefono = models.CharField(max_length=20)
    direccion = models.TextField()
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    cama_asignada = models.OneToOneField(Cama, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre_completo
class EvolucionMedica(models.Model):
    TIPO_NOTA = [
        ('MEDICA', 'Nota del Doctor (Diagnóstico/Tratamiento)'),
        ('ENFERMERIA', 'Nota de Enfermería (Signos Vitales/Cuidado)'),
    ]

    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='evoluciones')
    creado_por = models.ForeignKey('superadmi.Usuario', on_delete=models.SET_NULL, null=True)
    tipo = models.CharField(max_length=20, choices=TIPO_NOTA)
    
    # Datos de Signos Vitales (Principalmente para Enfermería)
    temperatura = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    presion_arterial = models.CharField(max_length=20, null=True, blank=True)
    frecuencia_cardiaca = models.IntegerField(null=True, blank=True)
    
    # Evolución y Diagnóstico (Principalmente para Doctores)
    descripcion = models.TextField(verbose_name="Evolución / Observaciones")
    indicaciones = models.TextField(null=True, blank=True, verbose_name="Indicaciones Médicas")
    
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tipo} - {self.paciente.nombre_completo} ({self.fecha_registro.strftime('%d/%m/%Y')})"
