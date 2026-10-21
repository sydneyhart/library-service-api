from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class Book(models.Model):
    class Cover(models.TextChoices):
        HARD = "HARD", "Hardcover"
        SOFT = "SOFT", "Softcover"

    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    cover = models.CharField(max_length=4, choices=Cover.choices)
    inventory = models.PositiveIntegerField(default=0)
    daily_fee = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )

    class Meta:
        ordering = ["title", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(inventory__gte=0), name="book_stock_nonnegative"
            ),
            models.CheckConstraint(
                condition=models.Q(daily_fee__gt=0), name="book_fee_positive"
            ),
        ]

    def __str__(self):
        return f"{self.title} by {self.author}"
