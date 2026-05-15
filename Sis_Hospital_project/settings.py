import os
from pathlib import Path

# --- RUTAS BÁSICAS ---
BASE_DIR = Path(__file__).resolve().parent.parent

# --- SEGURIDAD ---
SECRET_KEY = 'django-insecure-s4_=98oc_kc*z)9rk$opxpumf6an)ft!r#8i^59w3xmsh7u5&n'
DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

# --- APPS ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Tus aplicaciones
    'superadmi', 
    'enfermera', 
    'doctor', 
    'admin_app',
    'hospital',
    'rest_framework',
]

# --- MIDDLEWARE ---
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'Sis_Hospital_project.urls'

# --- TEMPLATES ---
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'Sis_Hospital_project.wsgi.application'

# --- BASE DE DATOS ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'RED_HOSPITALARIA',
        'USER': 'postgres',
        'PASSWORD': 'admin123',
        'HOST': '127.0.0.1',
        'PORT': '5433',
    }
}

# --- MODELO DE USUARIO PERSONALIZADO ---
# Esto es lo más importante para que funcione tu login
AUTH_USER_MODEL = 'superadmi.Usuario'

# --- INTERNACIONALIZACIÓN ---
LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'America/La_Paz'
USE_I18N = True
USE_TZ = True

# --- ARCHIVOS ESTÁTICOS ---
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# --- CONFIGURACIÓN DE MEDIA ---
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# --- CONFIGURACIÓN DE LOGIN ---
LOGIN_URL = 'superadmin:login'
LOGIN_REDIRECT_URL = 'hospital:landing_page' 
LOGOUT_REDIRECT_URL = 'superadmin:login'
# Esto le dice a Django que, después de loguearse con éxito, 
# ejecute nuestra función de redirección por roles.
LOGIN_REDIRECT_URL = 'dashboard_redirect'
# --- OTROS ---
CSRF_TRUSTED_ORIGINS = ['http://127.0.0.1:8000', 'http://localhost:8000']
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTHENTICATION_BACKENDS = [
    #'superadmi.backends.HospitalAuthBackend',
    'django.contrib.auth.backends.ModelBackend',
    ]
#]# Desactiva la actualización automática del último login para modelos personalizados
# que no tienen el campo 'last_login'
AUTH_USER_MODEL = 'superadmi.Usuario' # Asegúrate que esta línea ya esté
