from django.contrib import admin
from .models import Rol, Usuario, Hospital

# Registramos los modelos para poder verlos en /django-admin/
admin.site.register(Rol)
admin.site.register(Usuario)
admin.site.register(Hospital)