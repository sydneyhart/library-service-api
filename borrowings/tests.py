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

    def test_create_borrowing_decreases_stock_and_sets_current_user(self):
        response = self.client.post(
            "/api/borrowings/",
            {
                "book": self.book.pk,
                "expected_return_date": str(self.today),
                "user": self.other.pk,
                "borrow_date": "1999-01-01",
                "actual_return_date": str(self.today),
            },
        )
        self.assertEqual(response.status_code, 201)
        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, 1)
        created = Borrowing.objects.get(pk=response.data["id"])
        self.assertEqual(created.user, self.user)
        self.assertEqual(created.borrow_date, self.today)
        self.assertIsNone(created.actual_return_date)
        self.assertEqual(response.data["book"]["title"], "Dune")

    def test_out_of_stock_invalid_date_and_missing_book_are_rejected(self):
        payload = {"book": self.book.pk, "expected_return_date": str(self.today)}
        for fields in [
            {"expected_return_date": str(self.today - timedelta(days=1))},
            {"expected_return_date": "bad"},
            {"book": 999},
        ]:
            self.assertEqual(
                self.client.post("/api/borrowings/", {**payload, **fields}).status_code,
                400,
            )
        Book.objects.filter(pk=self.book.pk).update(inventory=0)
        self.assertEqual(self.client.post("/api/borrowings/", payload).status_code, 400)
        self.assertEqual(Borrowing.objects.count(), 1)

    def test_anonymous_cannot_borrow(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.post("/api/borrowings/", {}).status_code, 401)

    def test_failed_creation_rolls_back_inventory(self):
        from unittest.mock import patch

        from borrowings.services import create_borrowing

        with patch(
            "borrowings.services.Borrowing.objects.create",
            side_effect=RuntimeError("failure"),
        ):
            with self.assertRaises(RuntimeError):
                create_borrowing(
                    user=self.user, book=self.book, expected_return_date=self.today
                )
        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, 2)

    def test_active_filter_and_invalid_boolean(self):
        Borrowing.objects.create(
            book=self.book,
            user=self.user,
            expected_return_date=self.today,
            actual_return_date=self.today,
        )
        for value, count in [("true", 1), ("false", 1), ("1", 1), ("0", 1)]:
            self.assertEqual(
                self.client.get(f"/api/borrowings/?is_active={value}").data["count"],
                count,
            )
        self.assertEqual(
            self.client.get("/api/borrowings/?is_active=perhaps").status_code, 400
        )

    def test_staff_sees_all_and_can_filter_by_customer(self):
        other = Borrowing.objects.create(
            book=self.book, user=self.other, expected_return_date=self.today
        )
        self.user.is_staff = True
        self.user.save()
        self.assertEqual(self.client.get("/api/borrowings/").data["count"], 2)
        response = self.client.get(f"/api/borrowings/?user_id={self.other.pk}")
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], other.pk)
        self.assertEqual(
            self.client.get(f"/api/borrowings/{other.pk}/").status_code, 200
        )
        for value in ["bad", "0", "-1"]:
            self.assertEqual(
                self.client.get(f"/api/borrowings/?user_id={value}").status_code, 400
            )

    def test_customer_user_id_filter_cannot_expose_other_records(self):
        Borrowing.objects.create(
            book=self.book, user=self.other, expected_return_date=self.today
        )
        response = self.client.get(f"/api/borrowings/?user_id={self.other.pk}")
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["user"], self.user.pk)
