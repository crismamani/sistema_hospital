from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from .models import Usuario

class HospitalAuthBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None):
        try:
            # Buscamos al usuario en TU tabla usando el email
            user = Usuario.objects.get(email=username)
            # Comparamos la clave escrita con tu campo password_hash
            if check_password(password, user.password_hash):
                return user
        except Usuario.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return Usuario.objects.get(pk=user_id)
        except Usuario.DoesNotExist:
            return None