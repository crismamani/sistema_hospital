from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from functools import wraps

def solo_personal_autorizado(view_func):
    """
    LLAVE MAESTRA: Deja pasar a admin2, superusuarios y cualquier personal con rol.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = request.user
        
        if not user.is_authenticated:
            return redirect('login')

        # El "Pase VIP" para admin2 y Superuser
        if getattr(user, 'is_superuser', False) or user.username == 'admin2':
            return view_func(request, *args, **kwargs)
        
        # El pase para personal con cualquier rol asignado
        if hasattr(user, 'rol') and user.rol is not None:
            return view_func(request, *args, **kwargs)
            
        raise PermissionDenied
    return _wrapped_view

def solo_roles(roles_permitidos):
    """
    FILTRO ESPECÍFICO: Solo deja pasar a ciertos nombres de roles.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = request.user
            
            if not user.is_authenticated:
                return redirect('login')

            # admin2 y superuser SIEMPRE pasan, incluso filtros específicos
            if getattr(user, 'is_superuser', False) or user.username == 'admin2':
                return view_func(request, *args, **kwargs)

            # Verificación por nombre de rol
            if hasattr(user, 'rol') and user.rol is not None:
                if user.rol.nombre.upper() in [r.upper() for r in roles_permitidos]:
                    return view_func(request, *args, **kwargs)
            
            raise PermissionDenied
        return _wrapped_view
    return decorator