from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework.exceptions import ValidationError
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Borrowing
from .serializers import BorrowingCreateSerializer, BorrowingReadSerializer


class BorrowingViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Borrowing.objects.select_related("book", "user")
    serializer_class = BorrowingReadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.queryset.none()
        queryset = self.queryset
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        elif self.request.query_params.get("user_id") is not None:
            raw_id = self.request.query_params["user_id"]
            try:
                user_id = int(raw_id)
                if user_id < 1:
                    raise ValueError
            except ValueError as error:
                raise ValidationError({"user_id": "Use a positive integer."}) from error
            queryset = queryset.filter(user_id=user_id)
        active = self.request.query_params.get("is_active")
        if active is not None:
            value = active.lower()
            if value not in {"true", "false", "1", "0"}:
                raise ValidationError({"is_active": "Use true or false."})
            queryset = queryset.filter(
                actual_return_date__isnull=value in {"true", "1"}
            )
        return queryset

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "user_id",
                OpenApiTypes.INT,
                description="Staff only: filter by customer ID.",
            ),
            OpenApiParameter(
                "is_active",
                OpenApiTypes.BOOL,
                description="True for not returned; false for returned.",
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.action == "create":
            return BorrowingCreateSerializer
        return BorrowingReadSerializer

    @extend_schema(
        request=BorrowingCreateSerializer, responses={201: BorrowingReadSerializer}
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
