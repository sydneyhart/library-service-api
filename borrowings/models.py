from django.conf import settings
from django.db import models
from django.utils import timezone


class Borrowing(models.Model):
    borrow_date = models.DateField(default=timezone.localdate, editable=False)
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)
    book = models.ForeignKey(
        "books.Book", on_delete=models.PROTECT, related_name="borrowings"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="borrowings"
    )

    class Meta:
        ordering = ["-borrow_date", "-id"]
        indexes = [models.Index(fields=["user", "actual_return_date"])]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(expected_return_date__gte=models.F("borrow_date")),
                name="borrowing_expected_after_start",
            ),
            models.CheckConstraint(
                condition=models.Q(actual_return_date__isnull=True)
                | models.Q(actual_return_date__gte=models.F("borrow_date")),
                name="borrowing_actual_after_start",
            ),
        ]

    def __str__(self):
        return f"Borrowing {self.pk}: {self.book.title}"
