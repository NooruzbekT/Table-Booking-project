from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
import uuid
from datetime import timedelta
from django.utils import timezone
from .models import User
from .serializers import UserSerializer, UserRegistrationSerializer, UserLoginSerializer, ResetPasswordSerializer, \
    ForgotPasswordInputSerializer, MessageSerializer, TokenPairSerializer
from .utils import send_verification_email, send_reset_password_email
from .throttling import LoginRateThrottle, RegisterRateThrottle


@extend_schema(tags=['Users'])
class UserViewSet(viewsets.GenericViewSet):
    """
    ViewSet для управления пользователями (регистрация, вход, восстановление пароля).
    """

    serializer_action_classes = {
        'register': UserRegistrationSerializer,
        'login': UserLoginSerializer,
        'me': UserSerializer,
        'update_me': UserSerializer,
        'reset_password': ResetPasswordSerializer,
        'forgot_password': ForgotPasswordInputSerializer,
    }

    def get_serializer_class(self):
        return self.serializer_action_classes.get(self.action, UserSerializer)

    @extend_schema(
        summary="Регистрация",
        request=UserRegistrationSerializer,
        responses={201: MessageSerializer}
    )
    @action(detail=False, methods=["post"], permission_classes=[AllowAny], throttle_classes=[RegisterRateThrottle])
    def register(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.is_verified = False
            user.verification_token = str(uuid.uuid4())
            user.verification_token_expires_at = timezone.now() + timedelta(hours=24)
            user.save()
            send_verification_email(user.email, user.verification_token)
            return Response({"message": "На вашу почту отправлено письмо для подтверждения."}, status=201)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Подтверждение email",
        parameters=[OpenApiParameter(name="token", location=OpenApiParameter.PATH, required=True, type=str)],
        responses={200: MessageSerializer, 400: OpenApiResponse(description="Неверный токен")}
    )
    @action(detail=False, methods=["get"], url_path="verify-email/(?P<token>[^/.]+)", permission_classes=[AllowAny])
    def verify_email(self, request, token=None):
        try:
            user = User.objects.get(verification_token=token)

            # Проверяем истечение токена
            if user.verification_token_expires_at and timezone.now() > user.verification_token_expires_at:
                return Response({"error": "Токен истек. Пожалуйста, зарегистрируйтесь снова."},
                              status=status.HTTP_400_BAD_REQUEST)

            user.is_verified = True
            user.verification_token = None
            user.verification_token_expires_at = None
            user.save()
            return Response({"message": "Email подтвержден!"})
        except User.DoesNotExist:
            return Response({"error": "Неверный токен"}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Логин",
        request=UserLoginSerializer,
        responses={200: TokenPairSerializer, 400: OpenApiResponse(description="Ошибка аутентификации")}
    )
    @action(detail=False, methods=["post"], permission_classes=[AllowAny], throttle_classes=[LoginRateThrottle])
    def login(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # serializer.validate уже формирует dict с токенами
            tokens = TokenPairSerializer(serializer.validated_data).data
            return Response(tokens, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(summary="Текущий пользователь", responses=UserSerializer)
    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(summary="Обновить профиль", request=UserSerializer, responses=UserSerializer)
    @action(detail=False, methods=["patch"], permission_classes=[IsAuthenticated])
    def update_me(self, request):
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(summary="Удалить аккаунт", responses={204: OpenApiResponse(description="Аккаунт удален")})
    @action(detail=False, methods=["delete"], permission_classes=[IsAuthenticated])
    def delete_me(self, request):
        request.user.delete()
        return Response({"message": "Аккаунт удален"}, status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        summary="Забыли пароль",
        request=ForgotPasswordInputSerializer,
        responses={200: MessageSerializer, 404: OpenApiResponse(description="Пользователь не найден")}
    )
    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def forgot_password(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        try:
            user = User.objects.get(email=email)
            user.reset_token = str(uuid.uuid4())
            user.reset_token_expires_at = timezone.now() + timedelta(hours=1)
            user.save()
            send_reset_password_email(user.email, user.reset_token)
            return Response({"message": "На почту отправлено письмо с инструкцией по сбросу пароля."})
        except User.DoesNotExist:
            return Response({"error": "Пользователь с таким email не найден."}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        summary="Сброс пароля по токену",
        request=ResetPasswordSerializer,
        parameters=[OpenApiParameter(name="token", location=OpenApiParameter.PATH, required=True, type=str)],
        responses={200: MessageSerializer, 400: OpenApiResponse(description="Неверный/устаревший токен")}
    )
    @action(detail=False, methods=["post"], url_path="reset-password/(?P<token>[^/.]+)", permission_classes=[AllowAny])
    def reset_password(self, request, token=None):
        try:
            user = User.objects.get(reset_token=token)
        except User.DoesNotExist:
            return Response({"error": "Неверный или устаревший токен."}, status=status.HTTP_400_BAD_REQUEST)

        # Проверяем истечение токена
        if user.reset_token_expires_at and timezone.now() > user.reset_token_expires_at:
            return Response({"error": "Токен истек. Пожалуйста, запросите сброс пароля снова."},
                          status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user.set_password(serializer.validated_data["new_password"])
            user.reset_token = None
            user.reset_token_expires_at = None
            user.save()
            return Response({"message": "Пароль успешно изменен."})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

