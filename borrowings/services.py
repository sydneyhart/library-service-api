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


@transaction.atomic
def return_borrowing(*, borrowing_id):
    from django.utils import timezone

    borrowing = Borrowing.objects.select_for_update().get(pk=borrowing_id)
    if borrowing.actual_return_date is not None:
        raise ValidationError("This borrowing has already been returned.")
    book = Book.objects.select_for_update().get(pk=borrowing.book_id)
    borrowing.actual_return_date = timezone.localdate()
    borrowing.save(update_fields=["actual_return_date"])
    Book.objects.filter(pk=book.pk).update(inventory=F("inventory") + 1)
    borrowing.book.refresh_from_db()
    return borrowing
