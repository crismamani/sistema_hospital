# forms/admin.py
from django import forms
from .models import (
    Paciente, Sala, Cama, Derivacion, SolicitudCama,
    Internacion, Personal, Turno, Asistencia,
    TransferenciaInterna, Notificacion
)
from superadmi.models import Hospital, Especialidad, Usuario

class PacienteForm(forms.ModelForm):
    """Formulario para registrar/editar pacientes"""
    class Meta:
        model = Paciente
        fields = [
            'numero_documento', 'tipo_documento', 'nombre_completo',
            'fecha_nacimiento', 'genero', 'telefono', 'direccion',
            'contacto_emergencia', 'telefono_emergencia', 'seguro_medico'
        ]
        widgets = {
            'numero_documento': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_documento': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('DNI', 'DNI'),
                ('CI', 'Carnet de Identidad'),
            ]),
            'nombre_completo': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_nacimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'genero': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('M', 'Masculino'),
                ('F', 'Femenino'),
                ('Otro', 'Otro'),
            ]),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'contacto_emergencia': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono_emergencia': forms.TextInput(attrs={'class': 'form-control'}),
            'seguro_medico': forms.TextInput(attrs={'class': 'form-control'}),
        }

class SalaForm(forms.ModelForm):
    """Formulario para gestionar salas"""
    class Meta:
        model = Sala
        fields = ['nombre', 'hospital', 'especialidad', 'piso', 'capacidad_total', 'tipo_sala', 'estado']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'hospital': forms.Select(attrs={'class': 'form-control'}),
            'especialidad': forms.Select(attrs={'class': 'form-control'}),
            'piso': forms.NumberInput(attrs={'class': 'form-control'}),
            'capacidad_total': forms.NumberInput(attrs={'class': 'form-control'}),
            'tipo_sala': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('UCI', 'Unidad de Cuidados Intensivos'),
                ('emergencia', 'Emergencia'),
                ('hospitalizacion', 'Hospitalización'),
                ('pediatria', 'Pediatría'),
            ]),
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class CamaForm(forms.ModelForm):
    """Formulario para gestionar camas"""
    class Meta:
        model = Cama
        fields = ['codigo_cama', 'sala', 'hospital', 'especialidad', 'estado_cama', 'tipo_cama', 'ubicacion_detalle']
        widgets = {
            'codigo_cama': forms.TextInput(attrs={'class': 'form-control'}),
            'sala': forms.Select(attrs={'class': 'form-control'}),
            'hospital': forms.Select(attrs={'class': 'form-control'}),
            'especialidad': forms.Select(attrs={'class': 'form-control'}),
            'estado_cama': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('disponible', 'Disponible'),
                ('ocupada', 'Ocupada'),
                ('mantenimiento', 'En Mantenimiento'),
                ('bloqueada', 'Bloqueada'),
            ]),
            'tipo_cama': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('estandar', 'Estándar'),
                ('uci', 'UCI'),
                ('observacion', 'Observación'),
            ]),
            'ubicacion_detalle': forms.TextInput(attrs={'class': 'form-control'}),
        }

class InternacionForm(forms.ModelForm):
    """Formulario para registrar internaciones"""
    class Meta:
        model = Internacion
        fields = [
            'paciente', 'cama', 'hospital', 'especialidad',
            'doctor_responsable', 'fecha_ingreso', 'motivo_internacion',
            'diagnostico', 'observaciones'
        ]
        widgets = {
            'paciente': forms.Select(attrs={'class': 'form-control'}),
            'cama': forms.Select(attrs={'class': 'form-control'}),
            'hospital': forms.Select(attrs={'class': 'form-control'}),
            'especialidad': forms.Select(attrs={'class': 'form-control'}),
            'doctor_responsable': forms.Select(attrs={'class': 'form-control'}),
            'fecha_ingreso': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'motivo_internacion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'diagnostico': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class EgresoForm(forms.Form):
    """Formulario para registrar egreso de paciente"""
    fecha_egreso = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'})
    )
    observaciones = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False
    )

class PersonalForm(forms.ModelForm):
    """Formulario para gestionar personal"""
    class Meta:
        model = Personal
        fields = [
            'usuario', 'hospital', 'tipo_personal', 'numero_licencia',
            'especialidad', 'fecha_contratacion', 'tipo_contrato',
            'estado_laboral', 'horario_preferencia'
        ]
        widgets = {
            'usuario': forms.Select(attrs={'class': 'form-control'}),
            'hospital': forms.Select(attrs={'class': 'form-control'}),
            'tipo_personal': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('doctor', 'Doctor'),
                ('enfermera', 'Enfermera'),
                ('tecnico', 'Técnico'),
            ]),
            'numero_licencia': forms.TextInput(attrs={'class': 'form-control'}),
            'especialidad': forms.Select(attrs={'class': 'form-control'}),
            'fecha_contratacion': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'tipo_contrato': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('indefinido', 'Indefinido'),
                ('temporal', 'Temporal'),
                ('practicas', 'Prácticas'),
            ]),
            'estado_laboral': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('activo', 'Activo'),
                ('inactivo', 'Inactivo'),
                ('vacaciones', 'Vacaciones'),
                ('licencia', 'Licencia'),
            ]),
            'horario_preferencia': forms.TextInput(attrs={'class': 'form-control'}),
        }

class TurnoForm(forms.ModelForm):
    """Formulario para programar turnos"""
    class Meta:
        model = Turno
        fields = [
            'personal', 'hospital', 'especialidad', 'sala',
            'fecha_turno', 'hora_inicio', 'hora_fin', 'tipo_turno', 'observaciones'
        ]
        widgets = {
            'personal': forms.Select(attrs={'class': 'form-control'}),
            'hospital': forms.Select(attrs={'class': 'form-control'}),
            'especialidad': forms.Select(attrs={'class': 'form-control'}),
            'sala': forms.Select(attrs={'class': 'form-control'}),
            'fecha_turno': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'hora_inicio': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'hora_fin': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'tipo_turno': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('mañana', 'Mañana (06:00-14:00)'),
                ('tarde', 'Tarde (14:00-22:00)'),
                ('noche', 'Noche (22:00-06:00)'),
            ]),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class AsistenciaForm(forms.ModelForm):
    """Formulario para registrar asistencia"""
    class Meta:
        model = Asistencia
        fields = ['turno', 'personal', 'hora_entrada', 'hora_salida', 'estado', 'justificacion']
        widgets = {
            'turno': forms.Select(attrs={'class': 'form-control'}),
            'personal': forms.Select(attrs={'class': 'form-control'}),
            'hora_entrada': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'hora_salida': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'estado': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('presente', 'Presente'),
                ('ausente', 'Ausente'),
                ('tardanza', 'Tardanza'),
            ]),
            'justificacion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class TransferenciaInternaForm(forms.ModelForm):
    """Formulario para transferencias internas"""
    class Meta:
        model = TransferenciaInterna
        fields = [
            'paciente', 'internacion', 'cama_origen', 'cama_destino',
            'especialidad_origen', 'especialidad_destino', 'motivo_transferencia', 'observaciones'
        ]
        widgets = {
            'paciente': forms.Select(attrs={'class': 'form-control'}),
            'internacion': forms.Select(attrs={'class': 'form-control'}),
            'cama_origen': forms.Select(attrs={'class': 'form-control'}),
            'cama_destino': forms.Select(attrs={'class': 'form-control'}),
            'especialidad_origen': forms.Select(attrs={'class': 'form-control'}),
            'especialidad_destino': forms.Select(attrs={'class': 'form-control'}),
            'motivo_transferencia': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class NotificacionForm(forms.ModelForm):
    """Formulario para enviar notificaciones"""
    class Meta:
        model = Notificacion
        fields = ['usuario', 'tipo', 'titulo', 'mensaje', 'prioridad']
        widgets = {
            'usuario': forms.Select(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('derivacion', 'Derivación'),
                ('solicitud_cama', 'Solicitud de Cama'),
                ('alerta', 'Alerta'),
                ('informacion', 'Información'),
            ]),
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'mensaje': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'prioridad': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('baja', 'Baja'),
                ('normal', 'Normal'),
                ('alta', 'Alta'),
                ('urgente', 'Urgente'),
            ]),
        }