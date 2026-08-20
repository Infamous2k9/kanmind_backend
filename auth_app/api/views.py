from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import LoginSerializer, RegistrationSerializer


def build_auth_response(token, user):
    """Baut die einheitliche Token-Response für Login und Registrierung."""
    return {
        "token": token.key,
        "fullname": user.fullname,
        "email": user.email,
        "user_id": user.id,
    }


class RegistrationView(CreateAPIView):
    """Erstellt einen neuen User und liefert direkt ein Auth-Token zurück."""

    permission_classes = [AllowAny]
    serializer_class = RegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            build_auth_response(token, user), status=status.HTTP_201_CREATED
        )


class LoginView(APIView):
    """Authentifiziert einen User und liefert ein Auth-Token zurück."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)
        return Response(build_auth_response(token, user), status=status.HTTP_200_OK)
