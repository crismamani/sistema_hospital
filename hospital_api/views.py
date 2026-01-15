from rest_framework.viewsets import ModelViewSet
from django.contrib.auth import get_user_model  # Importación correcta
from .serializers import UserSerializer

# Esta función obtiene automáticamente tu modelo 'superadmi.Usuario'
User = get_user_model()

class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer