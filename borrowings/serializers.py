from rest_framework import serializers
from books.serializers import BookSerializer
from .models import Borrowing


class BorrowingReadSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "user",
        )
        read_only_fields = fields


class BorrowingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = ("book", "expected_return_date")

    def validate_expected_return_date(self, value):
        from django.utils import timezone

        if value < timezone.localdate():
            raise serializers.ValidationError(
                "Expected return date cannot be before today."
            )
        return value

    def create(self, validated_data):
        from .services import create_borrowing

        return create_borrowing(user=self.context["request"].user, **validated_data)

    def to_representation(self, instance):
        return BorrowingReadSerializer(instance, context=self.context).data
