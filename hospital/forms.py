from django import forms
from superadmi.models import Hospital
from .models import Paciente, Cama, EvolucionMedica, Especialidad, Cuarto, Derivacion, FormularioD7b, FormularioD7, ContrarreferenciaD7a, ReporteDiario
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
        # Agregamos 'prioridad' a la lista de campos
        fields = ['cuarto', 'numero', 'estado', 'prioridad']
        
        widgets = {
            'cuarto': forms.Select(attrs={'class': 'form-select'}),
            'numero': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ej: Cama-01'
            }),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'prioridad': forms.Select(attrs={'class': 'form-select'}),
        }

class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        # IMPORTANTE: Añadir los nuevos campos médicos aquí
        fields = [
            'nombre_completo', 'dni', 'fecha_nacimiento', 'genero', 
            'telefono', 'direccion', 'hospital', 'cama_asignada',
            'motivo_ingreso', 'presion_arterial', 'temperatura', 
            'frecuencia_cardiaca', 'saturacion_oxigeno', 'alergias'
        ]
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'motivo_ingreso': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Diagnóstico inicial...'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'alergias': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtro de seguridad para no asignar camas ocupadas
        self.fields['cama_asignada'].queryset = Cama.objects.filter(estado='LIBRE')
        
        # Aplicamos la clase 'form-control' a TODOS los campos automáticamente para que se vean PRO
        for field in self.fields:
            if field not in ['hospital', 'cama_asignada', 'genero']:
                self.fields[field].widget.attrs.update({'class': 'form-control form-control-pro'})
            else:
                self.fields[field].widget.attrs.update({'class': 'form-select form-control-pro'})
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
class D7Form(forms.ModelForm):
    class Meta:
        model = FormularioD7
        fields = '__all__'
        exclude = ['paciente']

class D7bForm(forms.ModelForm):
    class Meta:
        model = FormularioD7b
        fields = '__all__'
        exclude = ['paciente'] # Esto es importante para que no falle al guardar

class ContrarreferenciaD7aForm(forms.ModelForm):
    class Meta:
        model = ContrarreferenciaD7a
        fields = '__all__'
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
            'hora': forms.TimeInput(attrs={'type': 'time'}),
        }
##control diario
class ReporteDiarioForm(forms.ModelForm):
    class Meta:
        model = ReporteDiario
        exclude = ['hospital', 'creado_por', 'fecha_registro']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'turno': forms.Select(attrs={'class': 'form-select'}),
            'observaciones': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Aplicamos clases de Bootstrap a todos los campos numéricos y de texto
        for field in self.fields:
            if field not in ['fecha', 'turno', 'observaciones']:
                self.fields[field].widget.attrs.update({'class': 'form-control'})
