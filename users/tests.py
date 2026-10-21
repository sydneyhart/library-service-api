from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from .admin import CreateUserForm


class AccountTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.payload = {
            "email": "Reader@Example.com",
            "password": "Reader-pass-2026!",
            "first_name": "Ari",
            "last_name": "Lane",
        }

    def register(self):
        return self.client.post("/api/users/", self.payload)

    def test_register_hashes_password_and_never_grants_staff(self):
        response = self.client.post(
            "/api/users/", {**self.payload, "is_staff": True, "is_superuser": True}
        )
        self.assertEqual(response.status_code, 201)
        self.assertNotIn("password", response.data)
        user = get_user_model().objects.get()
        self.assertEqual(user.email, "reader@example.com")
        self.assertTrue(user.check_password(self.payload["password"]))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_weak_missing_password_and_duplicate_email(self):
        for fields in [{"password": "123"}, {"email": "invalid"}]:
            self.assertEqual(
                self.client.post("/api/users/", {**self.payload, **fields}).status_code,
                400,
            )
        self.assertEqual(
            self.client.post(
                "/api/users/", {"email": "missing@example.com"}
            ).status_code,
            400,
        )
        self.register()
        self.assertEqual(
            self.client.post(
                "/api/users/", {**self.payload, "email": "READER@EXAMPLE.COM"}
            ).status_code,
            400,
        )

    def test_authorize_header_login_refresh_and_profile(self):
        self.register()
        response = self.client.post(
            "/api/users/token/",
            {"email": "READER@EXAMPLE.COM", "password": self.payload["password"]},
        )
        self.assertEqual(response.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZE=f"Bearer {response.data['access']}")
        self.assertEqual(self.client.get("/api/users/me/").data["first_name"], "Ari")
        response = self.client.post(
            "/api/users/token/refresh/", {"refresh": response.data["refresh"]}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)

    def test_profile_is_private(self):
        self.assertEqual(self.client.get("/api/users/me/").status_code, 401)
        self.register()
        self.client.force_authenticate(get_user_model().objects.get())
        response = self.client.patch(
            "/api/users/me/",
            {
                "first_name": "New",
                "password": "Changed-password-2026!",
                "is_staff": True,
            },
        )
        self.assertEqual(response.status_code, 200)
        user = get_user_model().objects.get()
        self.assertEqual(user.first_name, "New")
        self.assertTrue(user.check_password("Changed-password-2026!"))
        self.assertFalse(user.is_staff)

    def test_invalid_and_inactive_credentials(self):
        self.register()
        self.assertEqual(
            self.client.post(
                "/api/users/token/", {**self.payload, "password": "wrong"}
            ).status_code,
            401,
        )
        get_user_model().objects.update(is_active=False)
        self.assertEqual(
            self.client.post("/api/users/token/", self.payload).status_code, 401
        )

    def test_manager_and_admin_creation(self):
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user("", "password")
        with self.assertRaises(ValueError):
            get_user_model().objects.create_superuser(
                "admin@example.com", "password", is_staff=False
            )
        admin = get_user_model().objects.create_superuser(
            "admin@example.com", "Strong-password-2026!"
        )
        self.assertTrue(admin.is_superuser and admin.is_staff)
        form = CreateUserForm(
            data={
                "email": "new-admin@example.com",
                "password1": "Strong-password-2026!",
                "password2": "Strong-password-2026!",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_profile_put_does_not_require_password(self):
        self.register()
        user = get_user_model().objects.get()
        self.client.force_authenticate(user)
        response = self.client.put(
            "/api/users/me/",
            {"email": user.email, "first_name": "Changed", "last_name": "Lane"},
        )
        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.check_password(self.payload["password"]))
