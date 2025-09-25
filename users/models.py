from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class CustomUserManager(BaseUserManager):
    def create_user(self, email, phone, password=None, **extra_fields):
        """Создаёт обычного пользователя"""
        if not email:
            raise ValueError("Email is required")
        if not phone:
            raise ValueError("Phone number is required")

        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", True)
        user = self.model(email=email, phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, phone, password=None, **extra_fields):
        """Создаёт суперпользователя с правами администратора"""
        email = self.normalize_email(email)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_active", True)

        return self.create_user(email, phone, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Кастомная модель пользователя с email и телефоном"""
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, unique=True)

    is_verified = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)  # Для Django Admin
    is_active = models.BooleanField(default=True)  # Может ли пользователь войти

    verification_token = models.CharField(max_length=100, blank=True, null=True)
    reset_token = models.CharField(max_length=100, blank=True, null=True)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["phone"]

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True
