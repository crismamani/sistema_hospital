# sis_hospital_project/urls.py

from django.contrib import admin as django_admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# 1. IMPORTA LA VISTA DE LOGIN
from superadmi import views as superadmi_views # <--- ¡AGREGA ESTA LÍNEA!

urlpatterns = [
    # 2. RUTA DE INICIO: Captura la ruta vacía ('/') y la dirige al login
    path('', superadmi_views.login_view, name='home'), # <--- ¡AGREGA ESTA LÍNEA!
    
    # Admin por defecto de Django
    path('django-admin/', django_admin.site.urls),

    # TUS APPS (Rutas principales)
    path('superadmin/', include('superadmi.urls')),
    path('gestion/', include('admin_app.urls')),
    path('medico/', include('Doctor.urls')),
    path('enfermeria/', include('Enfermera.urls')),
]

# Configuración para archivos estáticos/media en modo DEBUG (¡Esto está bien!)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)