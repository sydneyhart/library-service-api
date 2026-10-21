from datetime import timedelta
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from books.models import Book
from .models import Borrowing


class BorrowingTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "reader@example.com", "Reader-password-2026!"
        )
        self.other = get_user_model().objects.create_user(
            "other@example.com", "Other-password-2026!"
        )
        self.book = Book.objects.create(
            title="Dune", author="Herbert", cover="HARD", inventory=2, daily_fee="1.50"
        )
        self.today = timezone.localdate()
        self.borrowing = Borrowing.objects.create(
            book=self.book,
            user=self.user,
            expected_return_date=self.today + timedelta(days=3),
        )
        self.url = f"/api/borrowings/{self.borrowing.pk}/"
        self.client.force_authenticate(self.user)

    def test_list_detail_and_own_records_only(self):
        Borrowing.objects.create(
            book=self.book, user=self.other, expected_return_date=self.today
        )
        response = self.client.get("/api/borrowings/")
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["book"]["title"], "Dune")
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_authentication_required(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/borrowings/").status_code, 401)
        self.assertEqual(self.client.get(self.url).status_code, 401)

    def test_arbitrary_updates_and_deletion_disallowed(self):
        for method in ("put", "patch", "delete"):
            self.assertEqual(
                getattr(self.client, method)(self.url, {}).status_code, 405
            )

    def test_database_date_constraints(self):
        for fields in [
            {"expected_return_date": self.today - timedelta(days=1)},
            {"actual_return_date": self.today - timedelta(days=1)},
        ]:
            with (
                self.subTest(fields=fields),
                self.assertRaises(IntegrityError),
                transaction.atomic(),
            ):
                Borrowing.objects.filter(pk=self.borrowing.pk).update(**fields)

    def test_book_with_history_cannot_be_deleted(self):
        self.user.is_staff = True
        self.user.save()
        self.assertEqual(
            self.client.delete(f"/api/books/{self.book.pk}/").status_code, 400
        )
        self.assertTrue(Book.objects.filter(pk=self.book.pk).exists())

    def test_string_representation(self):
        self.assertIn("Dune", str(self.borrowing))
