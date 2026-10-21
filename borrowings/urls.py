from rest_framework.routers import DefaultRouter
from .views import BorrowingViewSet

router = DefaultRouter()
router.register("", BorrowingViewSet, basename="borrowing")
urlpatterns = router.urls
