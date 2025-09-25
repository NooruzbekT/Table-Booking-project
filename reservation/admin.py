from django.contrib import admin
from .models import Table, Reservation

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ("id", "number", "seats", "type", "status")
    list_filter = ("type", "status")
    search_fields = ("number",)
    ordering = ("number",)

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "table", "date", "time", "status")
    list_filter = ("status", "date")
    search_fields = ("user__email", "table__number")
    ordering = ("date", "time")
