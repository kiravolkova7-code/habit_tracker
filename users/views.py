from .models import User
from .serializers import UserSerializer, RegisterSerializer
from rest_framework import generics, permissions, viewsets, status
from rest_framework.response import Response


class RegisterView(generics.CreateAPIView):
    """Регистрация нового пользователя с проверкой дубликатов."""

    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except Exception as e:
            if "email" in str(e).lower():
                return Response(
                    {"error": "Пользователь с таким Email уже существует."}, status=status.HTTP_400_BAD_REQUEST
                )
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return User.objects.all()
        return User.objects.filter(pk=self.request.user.pk)

    def get_permissions(self):
        if self.action in ["list", "retrieve", "update", "partial_update"]:
            return [permissions.IsAuthenticated()]
        if self.action == "destroy":
            return [permissions.IsAdminUser()]
        return super().get_permissions()
