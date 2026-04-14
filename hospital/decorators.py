from django.core.exceptions import PermissionDenied
from functools import wraps

def solo_roles(roles_permitidos):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Verificamos si el usuario tiene el atributo 'rol' y si está en la lista
            if request.user.is_authenticated and getattr(request.user, 'rol', None) in roles_permitidos:
                return view_func(request, *args, **kwargs)
            else:
                raise PermissionDenied
        return _wrapped_view
    return decorator