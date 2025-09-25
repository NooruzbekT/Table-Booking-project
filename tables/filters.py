import django_filters
from .models import Table

class TableFilter(django_filters.FilterSet):
    type = django_filters.CharFilter(field_name="type", lookup_expr="exact")
    seats = django_filters.NumberFilter(field_name="seats", lookup_expr="exact")

    class Meta:
        model = Table
        fields = ["type", "seats"]
