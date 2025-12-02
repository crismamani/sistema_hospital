from django.db import models
from admin_app.models import (
    Paciente,
    Internacion,
    Cama,
    Derivacion,
    SolicitudCama,
    TransferenciaInterna,
    Sala
)
from superadmi.models import Usuario

# ==============================================================
# 3. MÓDULO DOCTOR (SOLO IMPORTS Y HELPERS)
# ==============================================================

# Se exponen los modelos que el doctor usará para que el ORM de Django los reconozca
# aunque estén definidos en otra App.

# Ejemplo de Helper (para lógica de negocio específica del doctor)
class DoctorQueryHelper:
    '''Helper para queries específicas del doctor'''
        
    @staticmethod
    def mis_pacientes(doctor_user_id):
        '''Obtener pacientes asignados al doctor'''
        # Usa el ID del usuario directamente, ya que doctor_responsable es un FK a Usuario
        return Internacion.objects.filter(
            doctor_responsable_id=doctor_user_id,
            estado='activo'
        ).select_related('paciente', 'cama', 'hospital')
        
    @staticmethod
    def mis_derivaciones(doctor_user_id):
        '''Obtener derivaciones creadas por el doctor'''
        return Derivacion.objects.filter(
            doctor_solicitante_id=doctor_user_id
        ).order_by('-fecha_solicitud')
        
    @staticmethod
    def camas_disponibles(hospital_id, especialidad_id):
        '''Ver camas disponibles para la especialidad'''
        return Cama.objects.filter(
            hospital_id=hospital_id,
            especialidad_id=especialidad_id,
            estado_cama='disponible'
        )

# NOTA: Asegúrate de que tu doctor/admin.py esté vacío o solo contenga el registro 
# de estas clases si las vas a usar en el panel de administración de Django.