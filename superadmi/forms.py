from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.hashers import make_password

# IMPORTACIÓN UNIFICADA: Todo desde tu carpeta actual .models
from .models import ( 
    Hospital, Usuario, Rol, Especialidad,
    HospitalEspecialidad, Auditoria, ConfiguracionSistema, Reporte
)

# Solo importamos Paciente y Cama de la otra app porque no existen en superadmi
from hospital.models import Paciente, Cama

# ==========================================
# 1. FORMULARIO DE HOSPITALES
# ==========================================
class HospitalForm(forms.ModelForm):
    class Meta:
        model = Hospital
        fields = ['nombre', 'direccion', 'telefono', 'email']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control custom-input'})

# ==========================================
# 2. FORMULARIO DE REGISTRO DE PERSONAL
# ==========================================
class RegistroPersonalForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control custom-input', 'placeholder': 'Mínimo 6 caracteres'}),
        min_length=6,
        label="Contraseña"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control custom-input', 'placeholder': 'Repita la contraseña'}),
        label="Confirmar Contraseña"
    )

    class Meta:
        model = Usuario
        fields = [
            'nombre_completo', 'email', 'telefono', 
            'rol', 'hospital', 'numero_colegiatura', 'especialidad'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Aplicamos estilos Bootstrap
        for field_name, field in self.fields.items():
            if field_name not in ['password', 'confirm_password']:
                field.widget.attrs.update({'class': 'form-control custom-input'})
        
        # IMPORTANTE: Usamos el Hospital del queryset correcto (.models)
        self.fields['hospital'].queryset = Hospital.objects.all().order_by('nombre')
        self.fields['hospital'].empty_label = "Seleccione un Hospital"
        
        self.fields['especialidad'].required = False
        self.fields['numero_colegiatura'].required = False

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Usuario.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo electrónico ya está registrado.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Las contraseñas no coinciden")
        return cleaned_data

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.username = usuario.email
        usuario.set_password(self.cleaned_data["password"])
        
        # Cambia esto de 'is_active' a 'estado'
        usuario.estado = True 
        
        if commit:
            usuario.save()
        return usuario

# ==========================================
# 3. FORMULARIO DE EDICIÓN DE USUARIO
# ==========================================
class UsuarioForm(forms.ModelForm):
    class Meta:
        model = Usuario
        # Cambiamos 'is_active' de regreso a 'estado'
        fields = [
            'nombre_completo', 'email', 'telefono', 'rol', 'hospital',
            'numero_colegiatura', 'especialidad', 'estado'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name == 'estado':
                # Si 'estado' es un BooleanField en tu modelo:
                field.widget.attrs.update({'class': 'form-check-input'})
                field.label = "Cuenta Activa"
            else:
                field.widget.attrs.update({'class': 'form-control custom-input'})

# ==========================================
# 4. OTROS FORMULARIOS
# ==========================================
class AsignarCapacidadForm(forms.ModelForm):
    class Meta:
        model = HospitalEspecialidad
        fields = ['hospital', 'especialidad', 'capacidad_camas']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control custom-input'})

class RolForm(forms.ModelForm):
    class Meta:
        model = Rol
        fields = ['nombre', 'descripcion', 'nivel_acceso']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control custom-input'})

class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control custom-input', 'placeholder': 'Usuario'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control custom-input', 'placeholder': 'Contraseña'}))

class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = ['nombre_completo', 'dni', 'fecha_nacimiento', 'genero', 'telefono', 'direccion', 'hospital', 'cama_asignada']
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
            'direccion': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cama_asignada'].queryset = Cama.objects.filter(estado='LIBRE')
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control custom-input'})
# Agrégalo al final de forms.py
class EspecialidadForm(forms.ModelForm):
    class Meta:
        model = Especialidad
        fields = ['nombre', 'descripcion', 'estado']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            # Si el campo es un checkbox de estado, le damos clase de bootstrap distinta
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            else:
                field.widget.attrs.update({'class': 'form-control custom-input'})


# Formularios faltantes para resolver errores de importación en views.py

class ConfiguracionSistemaForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionSistema
        fields = ['clave', 'valor', 'descripcion', 'tipo_dato', 'modificable_por']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control custom-input'})

class ReporteForm(forms.ModelForm):
    class Meta:
        model = Reporte
        fields = ['titulo', 'tipo_reporte', 'hospital', 'fecha_desde', 'fecha_hasta']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if 'fecha' in field_name:
                field.widget = forms.DateInput(attrs={'class': 'form-control custom-input', 'type': 'date'})
            else:
                field.widget.attrs.update({'class': 'form-control custom-input'})

class HospitalEspecialidadForm(forms.ModelForm):
    class Meta:
        model = HospitalEspecialidad
        fields = ['hospital', 'especialidad', 'capacidad_camas', 'estado']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name == 'estado':
                field.widget.attrs.update({'class': 'form-check-input'})
            else:
                field.widget.attrs.update({'class': 'form-control custom-input'})