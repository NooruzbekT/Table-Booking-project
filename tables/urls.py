from rest_framework.routers import DefaultRouter
from .views import TableViewSet

router = DefaultRouter()
router.register(r"tables", TableViewSet, basename="table")

urlpatterns = router.urls
