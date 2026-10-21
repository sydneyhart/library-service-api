from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless

from django.contrib.auth import get_user_model
from django.db import close_old_connections, connection
from django.test import TransactionTestCase
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from books.models import Book

from .models import Borrowing
from .services import create_borrowing, return_borrowing


@skipUnless(
    connection.vendor == "postgresql", "Real row-lock contention requires PostgreSQL"
)
class ConcurrentInventoryTests(TransactionTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            "parallel@example.com", "Parallel-password-2026!"
        )
        self.book = Book.objects.create(
            title="Last copy",
            author="Writer",
            cover="HARD",
            inventory=1,
            daily_fee="1.00",
        )

    def compete(self, action):
        barrier = Barrier(5)

        def worker(_):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                action()
                return "success"
            except ValidationError:
                return "rejected"
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=5) as pool:
            return list(pool.map(worker, range(5)))

    def test_five_users_cannot_borrow_the_last_copy_twice(self):
        users = [
            get_user_model().objects.create_user(
                f"reader{i}@example.com", "Reader-password-2026!"
            )
            for i in range(5)
        ]
        barrier = Barrier(5)

        def borrow(user):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                create_borrowing(
                    user=user, book=self.book, expected_return_date=timezone.localdate()
                )
                return "success"
            except ValidationError:
                return "rejected"
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=5) as pool:
            results = list(pool.map(borrow, users))
        self.assertEqual(results.count("success"), 1)
        self.assertEqual(results.count("rejected"), 4)
        self.assertEqual(Borrowing.objects.count(), 1)
        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, 0)

    def test_five_returns_restore_exactly_one_copy(self):
        borrowing = create_borrowing(
            user=self.user, book=self.book, expected_return_date=timezone.localdate()
        )
        results = self.compete(lambda: return_borrowing(borrowing_id=borrowing.pk))
        self.assertEqual(results.count("success"), 1)
        self.assertEqual(results.count("rejected"), 4)
        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, 1)
