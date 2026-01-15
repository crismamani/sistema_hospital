from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Hospital, Usuario, Auditoria
# Importa otros modelos que quieras auditar

@receiver(post_save, sender=Hospital)
@receiver(post_save, sender=Usuario)
def auditar_guardado(sender, instance, created, **kwargs):
    accion = "CREAR" if created else "MODIFICAR"
    tabla = sender.__name__
    
    # Nota: El usuario que realiza la acción suele venir del request, 
    # en señales es más complejo obtenerlo directamente, pero aquí 
    # dejamos la base para registrar el cambio en el objeto.
    Auditoria.objects.create(
        accion=accion,
        tabla_afectada=tabla,
        registro_id=instance.id,
        detalles=f"Se {accion.lower()} el registro {instance}"
    )