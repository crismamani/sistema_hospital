from .models import Auditoria

def registrar_auditoria(usuario, accion, tabla, registro_id, anteriores=None, nuevos=None, detalles=None, ip=None):
    Auditoria.objects.create(
        usuario=usuario,
        accion=accion,
        tabla_afectada=tabla,
        registro_id=registro_id,
        datos_anteriores=anteriores,
        datos_nuevos=nuevos,
        detalles=detalles,
        ip_address=ip
    )