from django import forms
# superadmi/forms.py
from .models import ( 
    Hospital, Usuario, Rol, Especialidad,
    HospitalEspecialidad, Auditoria, ConfiguracionSistema, Reporte
)
# ... el resto del código del formulario ...
from django.contrib.auth.hashers import make_password

class HospitalForm(forms.ModelForm):
    """Formulario para crear/editar hospitales"""
    class Meta:
        model = Hospital
        fields = ['nombre', 'direccion', 'telefono', 'email', 'capacidad_total', 'estado']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'capacidad_total': forms.NumberInput(attrs={'class': 'form-control'}),
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class RolForm(forms.ModelForm):
    """Formulario para gestionar roles del sistema"""
    class Meta:
        model = Rol
        fields = ['nombre', 'descripcion', 'nivel_acceso']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'nivel_acceso': forms.Select(attrs={'class': 'form-control'}, choices=[
                (1, 'SuperAdmin'),
                (2, 'Admin'),
                (3, 'Doctor'),
                (4, 'Enfermera'),
            ]),
        }

class EspecialidadForm(forms.ModelForm):
    """Formulario para gestionar especialidades médicas"""
    class Meta:
        model = Especialidad
        fields = ['nombre', 'descripcion', 'codigo', 'estado']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class UsuarioForm(forms.ModelForm):
    """Formulario para crear/editar usuarios del sistema"""
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text='Dejar en blanco para mantener la contraseña actual'
    )
    confirmar_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False
    )
    
    class Meta:
        model = Usuario
        fields = [
            'nombre_completo', 'email', 'telefono', 'rol', 'hospital',
            'numero_colegiatura', 'especialidad', 'estado'
        ]
        widgets = {
            'nombre_completo': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'rol': forms.Select(attrs={'class': 'form-control'}),
            'hospital': forms.Select(attrs={'class': 'form-control'}),
            'numero_colegiatura': forms.TextInput(attrs={'class': 'form-control'}),
            'especialidad': forms.Select(attrs={'class': 'form-control'}),
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirmar_password = cleaned_data.get('confirmar_password')
        
        if password and password != confirmar_password:
            raise forms.ValidationError('Las contraseñas no coinciden')
        
        return cleaned_data
    
    def save(self, commit=True):
        usuario = super().save(commit=False)
        password = self.cleaned_data.get('password')
        
        if password:
            usuario.password_hash = make_password(password)
        
        if commit:
            usuario.save()
        return usuario

class HospitalEspecialidadForm(forms.ModelForm):
    """Formulario para asignar especialidades a hospitales"""
    class Meta:
        model = HospitalEspecialidad
        fields = ['hospital', 'especialidad', 'capacidad_camas', 'estado']
        widgets = {
            'hospital': forms.Select(attrs={'class': 'form-control'}),
            'especialidad': forms.Select(attrs={'class': 'form-control'}),
            'capacidad_camas': forms.NumberInput(attrs={'class': 'form-control'}),
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ConfiguracionSistemaForm(forms.ModelForm):
    """Formulario para configuración del sistema"""
    class Meta:
        model = ConfiguracionSistema
        fields = ['clave', 'valor', 'descripcion', 'tipo_dato', 'modificable_por']
        widgets = {
            'clave': forms.TextInput(attrs={'class': 'form-control'}),
            'valor': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'tipo_dato': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('string', 'Texto'),
                ('number', 'Número'),
                ('boolean', 'Booleano'),
                ('json', 'JSON'),
            ]),
            'modificable_por': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('superadmin', 'Solo SuperAdmin'),
                ('admin', 'Admin y SuperAdmin'),
            ]),
        }

class ReporteForm(forms.ModelForm):
    """Formulario para generar reportes"""
    class Meta:
        model = Reporte
        fields = ['titulo', 'tipo_reporte', 'hospital', 'fecha_desde', 'fecha_hasta']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_reporte': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('ocupacion', 'Reporte de Ocupación'),
                ('derivaciones', 'Reporte de Derivaciones'),
                ('personal', 'Reporte de Personal'),
                ('equipamiento', 'Reporte de Equipamiento'),
            ]),
            'hospital': forms.Select(attrs={'class': 'form-control'}),
            'fecha_desde': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_hasta': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class FiltroAuditoriaForm(forms.Form):
    """Formulario para filtrar auditoría"""
    usuario = forms.ModelChoiceField(
        queryset=Usuario.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    accion = forms.ChoiceField(
        choices=[('', 'Todas')] + [
            ('crear', 'Crear'),
            ('editar', 'Editar'),
            ('eliminar', 'Eliminar'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )