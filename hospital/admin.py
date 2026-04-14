from django.contrib import admin
from .models import Cuarto, Cama, Paciente, EvolucionMedica, Ambulancia, Derivacion, FormularioD7, FormularioD7b
@admin.register(Cama)
class CamaAdmin(admin.ModelAdmin):
    list_display = ('numero', 'cuarto', 'estado')
    list_filter = ('estado', 'cuarto__especialidad')
    search_fields = ('numero',)

@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'dni', 'hospital', 'estado', 'cama_asignada')
    search_fields = ('nombre_completo', 'dni')
    list_filter = ('estado', 'hospital')

@admin.register(Derivacion)
class DerivacionAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'hospital_origen', 'hospital_destino', 'prioridad', 'estado')
    list_filter = ('estado', 'prioridad')