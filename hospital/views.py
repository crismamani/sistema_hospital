# hospital/views.py

from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

# NOTA IMPORTANTE: Asume que el usuario tiene un campo 'perfil.rol'
# con valores como 'ADMIN', 'DOCTOR', 'ENFERMERA', 'SISTEMADMI'

@login_required
def home(request):
    """
    Vista que revisa el rol del usuario y lo redirige a su panel.
    """
    user = request.user
    
    # Asegúrate de que el usuario tenga un perfil asociado
    if hasattr(user, 'perfil'):
        rol = user.perfil.rol
        
        if rol == 'ADMINISTRADOR':
            return redirect('panel_administrador') # Redirige a la URL de la app 'admi'
        elif rol == 'DOCTOR':
            return redirect('panel_doctor') # Redirige a la URL de la app 'doc'
        elif rol == 'ENFERMERA':
            return redirect('panel_enfermera') # Redirige a la URL de la app 'enfr'
        elif rol == 'SISTEMAADMI':
            return redirect('panel_sistemaadmi') # Redirige a la URL de la app 'sis'
        else:
            # Si tiene un rol no reconocido o no tiene perfil, lo enviamos al logout
            return redirect('logout') 
    
    # Si el usuario es superusuario pero no tiene perfil (o cualquier otro caso)
    return redirect('logout')