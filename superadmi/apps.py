from django.apps import AppConfig

class SuperadmiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'superadmi'

    def ready(self):
        import superadmi.signals  # Esto activa las señales