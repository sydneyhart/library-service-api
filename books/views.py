from django.db.models.deletion import ProtectedError
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from .permissions import StaffWritePublicRead

from .models import Book
from .serializers import BookSerializer


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [StaffWritePublicRead]

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError as error:
            raise ValidationError(
                "Books with borrowing history cannot be deleted."
            ) from error
