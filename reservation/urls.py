from rest_framework.routers import DefaultRouter
from .views import ReservationViewSet

router = DefaultRouter()
router.register(r"reservation", ReservationViewSet, basename="reservation")

urlpatterns = router.urls
