from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Borrowing
from .serializers import BorrowingReadSerializer


class BorrowingViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = Borrowing.objects.select_related("book", "user")
    serializer_class = BorrowingReadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)
