from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
import uuid
from .models import User
from .serializers import UserSerializer, UserRegistrationSerializer, UserLoginSerializer, ResetPasswordSerializer
from .utils import send_verification_email, send_reset_password_email

class UserViewSet(viewsets.ViewSet):
    """
    ViewSet для управления пользователями (регистрация, вход, восстановление пароля).
    """

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def register(self, request):
        """Регистрация пользователя."""
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.is_verified = False
            user.verification_token = str(uuid.uuid4())  # Генерируем токен
            user.save()
            send_verification_email(user.email, user.verification_token)  # Отправляем email
            return Response({"message": "На вашу почту отправлено письмо для подтверждения."})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"], url_path="verify-email/(?P<token>[^/.]+)", permission_classes=[AllowAny])
    def verify_email(self, request, token=None):
        """Подтверждение email."""
        try:
            user = User.objects.get(verification_token=token)
            user.is_verified = True
            user.verification_token = None
            user.save()
            return Response({"message": "Email подтвержден!"})
        except User.DoesNotExist:
            return Response({"error": "Неверный токен"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def login(self, request):
        """Авторизация пользователя."""
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Получение информации о текущем пользователе."""
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["patch"], permission_classes=[IsAuthenticated])
    def update_me(self, request):
        """Редактирование данных пользователя."""
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["delete"], permission_classes=[IsAuthenticated])
    def delete_me(self, request):
        """Удаление аккаунта."""
        request.user.delete()
        return Response({"message": "Аккаунт удален"}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def forgot_password(self, request):
        """Отправка ссылки для сброса пароля."""
        email = request.data.get("email")
        try:
            user = User.objects.get(email=email)
            user.reset_token = str(uuid.uuid4())
            user.save()
            send_reset_password_email(user.email, user.reset_token)
            return Response({"message": "На почту отправлено письмо с инструкцией по сбросу пароля."})
        except User.DoesNotExist:
            return Response({"error": "Пользователь с таким email не найден."}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=["post"], url_path="reset-password/(?P<token>[^/.]+)", permission_classes=[AllowAny])
    def reset_password(self, request, token=None):
        """Сброс пароля по токену."""
        try:
            user = User.objects.get(reset_token=token)
        except User.DoesNotExist:
            return Response({"error": "Неверный или устаревший токен."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            user.set_password(serializer.validated_data["new_password"])
            user.reset_token = None
            user.save()
            return Response({"message": "Пароль успешно изменен."})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
