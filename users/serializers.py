from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone", "password", "confirm_password"]

    def validate(self, data):
        """Проверяем, совпадают ли пароли."""
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError({"password": "Пароли не совпадают."})
        return data

    def create(self, validated_data):
        """Создаем нового пользователя."""
        validated_data.pop("confirm_password")
        validated_data["password"] = make_password(validated_data["password"])
        return User.objects.create(**validated_data)




class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        """Аутентификация пользователя."""
        email = data.get("email")
        password = data.get("password")

        user = authenticate(email=email, password=password)
        if not user:
            raise serializers.ValidationError("Неверный email или пароль.")

        if not user.is_verified:
            raise serializers.ValidationError("Email не подтвержден.")

        tokens = RefreshToken.for_user(user)
        return {
            "refresh": str(tokens),
            "access": str(tokens.access_token),
        }





class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, min_length=6)

    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "email", "phone", "is_verified", "password"]
        read_only_fields = ["id", "is_verified", "email"]

    def update(self, instance, validated_data):
        """Обновление профиля пользователя."""
        if "password" in validated_data:
            validated_data["password"] = make_password(validated_data["password"])
        return super().update(instance, validated_data)



class ResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, min_length=6)

    def validate_new_password(self, value):
        """Минимальная длина пароля 6 символов"""
        if len(value) < 6:
            raise serializers.ValidationError("Пароль должен содержать минимум 6 символов.")
        return value
