from django.contrib import admin
from .models import Hospital, Especialidad, HospitalEspecialidad, Rol, Usuario

# Registramos los modelos para poder verlos en /django-admin/
admin.site.register(Rol)
admin.site.register(Usuario)
admin.site.register(Hospital)

@admin.register(Especialidad)
class EspecialidadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')

@admin.register(HospitalEspecialidad)
class HospitalEspecialidadAdmin(admin.ModelAdmin):
    list_display = ('hospital', 'especialidad')
    list_filter = ('hospital',)