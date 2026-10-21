from django.test import TestCase
from rest_framework.test import APIClient


class DocumentationTests(TestCase):
    def test_public_documentation_and_api_root(self):
        for url in ["/api/", "/api/docs/", "/api/schema/"]:
            response = APIClient().get(url)
            self.assertEqual(response.status_code, 200)
