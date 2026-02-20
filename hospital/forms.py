from django import forms
from superadmi.models import Hospital
from .models import Paciente, Cama, EvolucionMedica, Especialidad, Cuarto, Derivacion
class CuartoForm(forms.ModelForm):
    class Meta:
        model = Cuarto
        fields = ['hospital', 'especialidad', 'numero_cuarto', 'piso']
        widgets = {
            'hospital': forms.Select(attrs={'class': 'form-select'}),
            'especialidad': forms.Select(attrs={'class': 'form-select'}),
            'numero_cuarto': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 101'}),
            'piso': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Nro de piso'}),
        }

class CamaForm(forms.ModelForm):
    class Meta:
        model = Cama
        fields = ['cuarto', 'numero', 'estado']
        widgets = {
            'cuarto': forms.Select(attrs={'class': 'form-select'}),
            'numero': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Cama-01'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
        }

class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = ['nombre_completo', 'dni', 'fecha_nacimiento', 'genero', 'telefono', 'direccion', 'hospital', 'cama_asignada']
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'nombre_completo': forms.TextInput(attrs={'class': 'form-control'}),
            'dni': forms.TextInput(attrs={'class': 'form-control'}),
            'hospital': forms.Select(attrs={'class': 'form-select'}),
            'genero': forms.Select(attrs={'class': 'form-select'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo mostramos camas que estén LIBRES para no sobreescribir pacientes
        self.fields['cama_asignada'].queryset = Cama.objects.filter(estado='LIBRE')
        self.fields['cama_asignada'].widget.attrs.update({'class': 'form-select'})

class EvolucionMedicaForm(forms.ModelForm):
    class Meta:
        model = EvolucionMedica
        fields = ['tipo', 'temperatura', 'presion_arterial', 'frecuencia_cardiaca', 'descripcion', 'indicaciones']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'temperatura': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'presion_arterial': forms.TextInput(attrs={'class': 'form-control'}),
            'frecuencia_cardiaca': forms.NumberInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'indicaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class DerivacionForm(forms.ModelForm):
    class Meta:
        model = Derivacion
        fields = ['hospital_destino', 'prioridad', 'motivo_traslado']
        widgets = {
            'hospital_destino': forms.Select(attrs={'class': 'form-select'}),
            'prioridad': forms.Select(attrs={'class': 'form-select'}),
            'motivo_traslado': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describa el cuadro clínico...'}),
        }

    def __init__(self, *args, **kwargs):
        especialidad_id = kwargs.pop('especialidad_id', None)
        super().__init__(*args, **kwargs)
        if especialidad_id:
            # Solo mostramos hospitales que tengan al menos una cama LIBRE en esa especialidad
            self.fields['hospital_destino'].queryset = Hospital.objects.filter(
                cuartos__especialidad_id=especialidad_id,
                cuartos__camas__estado='LIBRE'
            ).distinct()