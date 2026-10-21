from decimal import Decimal
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from rest_framework.test import APIClient
from .models import Book


def account(identifier, **fields):
    return get_user_model().objects.create_user(
        **{get_user_model().USERNAME_FIELD: identifier},
        password="Strong-password-2026!",
        **fields,
    )


class BookCrudTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.staff = account("staff@example.com", is_staff=True)
        self.client.force_authenticate(self.staff)
        self.payload = {
            "title": "Dune",
            "author": "Frank Herbert",
            "cover": "SOFT",
            "inventory": 2,
            "daily_fee": "1.25",
        }

    def test_create_list_detail_update_delete(self):
        response = self.client.post("/api/books/", self.payload)
        self.assertEqual(response.status_code, 201)
        book_id = response.data["id"]
        self.assertEqual(Book.objects.get(pk=book_id).daily_fee, Decimal("1.25"))
        self.assertEqual(self.client.get("/api/books/").data["count"], 1)
        url = f"/api/books/{book_id}/"
        self.assertEqual(self.client.get(url).data["title"], "Dune")
        self.assertEqual(self.client.patch(url, {"inventory": 0}).status_code, 200)
        self.assertEqual(
            self.client.put(url, {**self.payload, "cover": "HARD"}).status_code, 200
        )
        self.assertEqual(self.client.delete(url).status_code, 204)
        self.assertFalse(Book.objects.exists())

    def test_invalid_fields_rejected(self):
        for fields in [
            {"inventory": -1},
            {"daily_fee": "0"},
            {"daily_fee": "-1"},
            {"daily_fee": "1.234"},
            {"cover": "OTHER"},
            {"title": ""},
        ]:
            with self.subTest(fields=fields):
                self.assertEqual(
                    self.client.post(
                        "/api/books/", {**self.payload, **fields}
                    ).status_code,
                    400,
                )
        self.assertEqual(Book.objects.count(), 0)

    def test_missing_book_is_404(self):
        self.assertEqual(self.client.get("/api/books/999/").status_code, 404)

    def test_database_rejects_negative_stock_and_zero_fee(self):
        for fields in [{"inventory": -1}, {"daily_fee": "0"}]:
            with (
                self.subTest(fields=fields),
                self.assertRaises(IntegrityError),
                transaction.atomic(),
            ):
                Book.objects.create(**{**self.payload, **fields})

    def test_string_representation(self):
        self.assertEqual(str(Book(**self.payload)), "Dune by Frank Herbert")
