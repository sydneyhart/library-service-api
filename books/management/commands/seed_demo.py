from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from books.models import Book


class Command(BaseCommand):
    help = "Seed sample books and optional public local-demo accounts."

    def add_arguments(self, parser):
        parser.add_argument("--with-users", action="store_true")

    def handle(self, *args, **options):
        for title, author, cover, stock, fee in [
            ("Dune", "Frank Herbert", "HARD", 3, "1.50"),
            ("Pride and Prejudice", "Jane Austen", "SOFT", 5, "0.75"),
            ("The Time Machine", "H. G. Wells", "SOFT", 0, "1.00"),
        ]:
            Book.objects.get_or_create(
                title=title,
                author=author,
                defaults={"cover": cover, "inventory": stock, "daily_fee": fee},
            )
        if options["with_users"]:
            for email, staff in [
                ("admin@example.com", True),
                ("reader@example.com", False),
            ]:
                if not get_user_model().objects.filter(email=email).exists():
                    get_user_model().objects.create_user(
                        email, "Library-demo-2026!", is_staff=staff, is_superuser=staff
                    )
        self.stdout.write(self.style.SUCCESS("Demo data ready."))
