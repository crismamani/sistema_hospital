# forms/enfermera.py
from django import forms
from .models import Cama, Asistencia
from datetime import datetime

class TransferenciaInternaForm(forms.Form):
    """Formulario para transferir un paciente de una cama a otra."""
    
    # Este campo se inicializa en __init__ para filtrar camas disponibles por hospital
    cama_destino = forms.ModelChoiceField(
        queryset=Cama.objects.none(), 
        label="Cama Destino",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    motivo = forms.CharField(
        label="Motivo de Transferencia", 
        max_length=255,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )

    def __init__(self, *args, hospital=None, **kwargs):
        super().__init__(*args, **kwargs)
        if hospital:
            # Filtra solo las camas DISPONIBLES en el hospital
            self.fields['cama_destino'].queryset = Cama.objects.filter(
                hospital=hospital, 
                estado_cama='disponible'
            ).order_by('codigo_cama')
class CambioEstadoCamaForm(forms.Form):
    """Formulario para cambiar estado de cama"""
    estado_nuevo = forms.ChoiceField(
        choices=[
            ('disponible', 'Disponible'),
            ('ocupada', 'Ocupada'),
            ('mantenimiento', 'En Mantenimiento'),
            ('limpieza', 'En Limpieza'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Nuevo Estado'
    )
    motivo_cambio = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label='Motivo del Cambio'
    )

class RegistroAsistenciaForms(forms.ModelForm):
    """Formulario para registrar asistencia"""
    class Meta:
        model = Asistencia
        fields = ['hora_entrada']
        widgets = {
            'hora_entrada': forms.DateTimeInput}