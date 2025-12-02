# forms/doctor.py
from django import forms
from .models import Derivacion, SolicitudCama, Internacion
from superadmi.models import Hospital, Especialidad 
from admin_app.models import HistoriaClinica
class DerivacionForm(forms.ModelForm):
    """Formulario para crear derivaciones"""
    class Meta:
        model = Derivacion
        fields = [
            'paciente', 'hospital_destino', 'especialidad_solicitada',
            'motivo_derivacion', 'diagnostico', 'prioridad', 'observaciones'
        ]
        widgets = {
            'paciente': forms.Select(attrs={'class': 'form-control'}),
            'hospital_destino': forms.Select(attrs={'class': 'form-control'}),
            'especialidad_solicitada': forms.Select(attrs={'class': 'form-control'}),
            'motivo_derivacion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'diagnostico': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'prioridad': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('baja', 'Baja'),
                ('normal', 'Normal'),
                ('alta', 'Alta'),
                ('urgente', 'Urgente'),
            ]),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class RespuestaDerivacionForm(forms.Form):
    """Formulario para responder derivación"""
    estado = forms.ChoiceField(
        choices=[
            ('aceptada', 'Aceptar Derivación'),
            ('rechazada', 'Rechazar Derivación'),
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    observaciones = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False,
        label='Observaciones'
    )
    motivo_rechazo = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False,
        label='Motivo de Rechazo (si aplica)'
    )

class SolicitudCamaForm(forms.ModelForm):
    """Formulario para solicitar cama"""
    class Meta:
        model = SolicitudCama
        fields = [
            'paciente', 'hospital_destino', 'especialidad', 'sala_preferida',
            'tipo_cama_requerida', 'prioridad', 'motivo_solicitud',
            'diagnostico_preliminar'
        ]
        widgets = {
            'paciente': forms.Select(attrs={'class': 'form-control'}),
            'hospital_destino': forms.Select(attrs={'class': 'form-control'}),
            'especialidad': forms.Select(attrs={'class': 'form-control'}),
            'sala_preferida': forms.Select(attrs={'class': 'form-control'}),
            'tipo_cama_requerida': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('estandar', 'Estándar'),
                ('uci', 'UCI'),
                ('observacion', 'Observación'),
            ]),
            'prioridad': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('baja', 'Baja'),
                ('normal', 'Normal'),
                ('alta', 'Alta'),
                ('urgente', 'Urgente'),
            ]),
            'motivo_solicitud': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'diagnostico_preliminar': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

class RespuestaSolicitudCamaForm(forms.Form):
    """Formulario para responder solicitud de cama"""
    estado = forms.ChoiceField(
        choices=[
            ('aprobada', 'Aprobar Solicitud'),
            ('rechazada', 'Rechazar Solicitud'),
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    cama_asignada = forms.ChoiceField(
        choices=[],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Cama Asignada'
    )
    observaciones = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False
    )
    motivo_rechazo = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        camas_disponibles = kwargs.pop('camas_disponibles', [])
        super().__init__(*args, **kwargs)
        self.fields['cama_asignada'].choices = [(c.id, f"{c.codigo_cama} - {c.sala.nombre}") for c in camas_disponibles]

class ActualizarDiagnosticoForm(forms.Form):
    """Formulario para actualizar diagnóstico de internación"""
    diagnostico = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        label='Diagnóstico Actualizado'
    )
    observaciones = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False,
        label='Observaciones Adicionales'
    )

class BuscarPacienteForm(forms.Form):
    """Formulario para buscar pacientes"""
    termino = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre o documento...'
        }),
        label='Buscar Paciente'
    )
    especialidad = forms.ModelChoiceField(
        queryset=Especialidad.objects.filter(estado=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Filtrar por Especialidad'
    )

    # Doctor/forms.py (Añade esto al final del archivo)

class HistoriaClinicaForm(forms.ModelForm):
    """Formulario para crear y editar la Historia Clínica."""
    class Meta:
        model = HistoriaClinica 
        fields = [
            'paciente',
            'medico_responsable',
            'diagnostico_inicial',
            'antecedentes_personales',
            'antecedentes_familiares',
        ]
        # (Puedes añadir widgets si lo necesitas)