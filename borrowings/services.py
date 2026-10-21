from django.db import transaction
from django.db.models import F
from rest_framework.exceptions import ValidationError
from books.models import Book
from .models import Borrowing


@transaction.atomic
def create_borrowing(*, user, book, expected_return_date):
    try:
        locked_book = Book.objects.select_for_update().get(pk=book.pk)
    except Book.DoesNotExist as error:
        raise ValidationError({"book": "This book is no longer available."}) from error
    if locked_book.inventory < 1:
        raise ValidationError({"book": "This book is out of stock."})
    Book.objects.filter(pk=locked_book.pk).update(inventory=F("inventory") - 1)
    return Borrowing.objects.create(
        user=user, book=locked_book, expected_return_date=expected_return_date
    )
