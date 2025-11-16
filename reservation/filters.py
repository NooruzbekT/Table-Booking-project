import django_filters
from django.utils import timezone
from .models import Reservation


class ReservationFilter(django_filters.FilterSet):
    # Точная дата
    date = django_filters.DateFilter(field_name="date", lookup_expr="exact")

    # Диапазон дат
    date_from = django_filters.DateFilter(field_name="date", lookup_expr="gte")
    date_to = django_filters.DateFilter(field_name="date", lookup_expr="lte")

    # Фильтр по столику
    table = django_filters.NumberFilter(field_name="table__id", lookup_expr="exact")

    # Фильтр по статусу
    status = django_filters.CharFilter(field_name="status", lookup_expr="exact")

    # Фильтр только будущих/прошлых бронирований
    is_upcoming = django_filters.BooleanFilter(method="filter_upcoming")

    def filter_upcoming(self, queryset, name, value):
        """Фильтр будущих (True) или прошлых (False) бронирований"""
        today = timezone.now().date()
        if value:
            return queryset.filter(date__gte=today)
        else:
            return queryset.filter(date__lt=today)

    class Meta:
        model = Reservation
        fields = ["date", "date_from", "date_to", "table", "status", "is_upcoming"]
