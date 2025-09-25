import django_filters
from .models import Reservation

class ReservationFilter(django_filters.FilterSet):
    date = django_filters.DateFilter(field_name="date", lookup_expr="exact")
    table = django_filters.NumberFilter(field_name="table__id", lookup_expr="exact")
    status = django_filters.CharFilter(field_name="status", lookup_expr="exact")

    class Meta:
        model = Reservation
        fields = ["date", "table", "status"]
