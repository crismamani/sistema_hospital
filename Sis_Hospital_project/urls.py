import os  # <-- SE AÑADIÓ ESTO PARA EVITAR EL NAMEERROR
from django.contrib import admin as django_admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# 1. IMPORTA LA VISTA DE LOGIN
from superadmi import views as superadmi_views 

urlpatterns = [
    path('', superadmi_views.login_view, name='home'),
    path('django-admin/', django_admin.site.urls),
    
    # Apps con sus respectivos prefijos y namespaces
    path('superadmin/', include('superadmi.urls', namespace='superadmin')),
    path('gestion/', include('admin_app.urls', namespace='admin_app')),
    path('medico/', include('doctor.urls', namespace='doctor')),
    path('enfermeria/', include('enfermera.urls', namespace='enfermera')),
    ##path('api/', include('hospital_api.urls')),
    path('hospital/', include('hospital.urls')),
]

# Configuración para archivos estáticos y media en modo DEBUG
if settings.DEBUG:
    # Se usa settings.BASE_DIR para que la ruta sea exacta en Windows
    urlpatterns += static(settings.STATIC_URL, document_root=os.path.join(settings.BASE_DIR, 'static'))
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)