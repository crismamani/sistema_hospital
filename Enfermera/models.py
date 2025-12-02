from django.db import models
from admin_app.models import (
    Paciente,
    Internacion,
    Cama,
    Sala,
    Asistencia,
    Personal, # Importante para relacionar usuario con turno
    Turno
)
from superadmi.models import Usuario

# ==============================================================
# 4. MÓDULO ENFERMERA (SOLO IMPORTS Y HELPERS)
# ==============================================================

# Ejemplo de Helper (para lógica de negocio específica de la enfermera)
class EnfermeraQueryHelper:
    '''Helper para queries específicas de enfermera'''

    @staticmethod
    def mis_turnos(enfermera_user_id, fecha=None):
        '''Obtener turnos de la enfermera'''
        from datetime import date
        fecha = fecha or date.today()
        
        # Filtra por el Personal que está ligado al Usuario (enfermera_user_id)
        return Turno.objects.filter(
            personal__usuario_id=enfermera_user_id, 
            fecha_turno=fecha
        )
        
    @staticmethod
    def pacientes_mi_sala(enfermera_user_id):
        '''Obtener pacientes en las salas asignadas hoy'''
        from datetime import date
        
        # 1. Obtener salas donde la enfermera tiene turno hoy
        salas_ids = Turno.objects.filter(
            personal__usuario_id=enfermera_user_id,
            fecha_turno=date.today()
        ).values_list('sala_id', flat=True).distinct()
        
        # 2. Obtener internaciones activas en esas salas
        return Internacion.objects.filter(
            cama__sala_id__in=salas_ids,
            estado='activo'
        ).select_related('paciente', 'cama')
        
    @staticmethod
    def camas_mi_sala(enfermera_user_id):
        '''Ver camas de las salas asignadas hoy'''
        from datetime import date
        
        salas_ids = Turno.objects.filter(
            personal__usuario_id=enfermera_user_id,
            fecha_turno=date.today()
        ).values_list('sala_id', flat=True).distinct()
        
        return Cama.objects.filter(
            sala_id__in=salas_ids
        )
        
    @staticmethod
    def registrar_asistencia(enfermera_user_id, turno_id, hora_entrada):
        '''Registrar entrada de la enfermera'''
        # Obtener la instancia de Personal a partir del Usuario
        personal = Personal.objects.get(usuario_id=enfermera_user_id) 
        
        return Asistencia.objects.create(
            turno_id=turno_id,
            personal=personal,
            hora_entrada=hora_entrada,
            estado='presente'
        )