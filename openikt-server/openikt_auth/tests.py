from django.test import TestCase

# Create your tests here.
from django.test import TestCase, Client

class MyAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_api_endpoint(self):
        response = self.client.get('/auth/logout')
        self.assertEqual(response.status_code, 200)
        self.assertIn("Logout successful", response.content.decode('utf-8'))