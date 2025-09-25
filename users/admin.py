from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    list_display = ("id", "email", "phone", "is_verified", "is_staff", "is_superuser")
    list_filter = ("is_verified", "is_staff", "is_superuser")
    fieldsets = (
        (None, {"fields": ("email", "phone", "password")}),
        ("Permissions", {"fields": ("is_verified", "is_staff", "is_superuser")}),
        ("Important dates", {"fields": ("last_login",)}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "phone", "password1", "password2"),
        }),
    )
    search_fields = ("email", "phone")
    ordering = ("email",)

admin.site.register(User, CustomUserAdmin)
