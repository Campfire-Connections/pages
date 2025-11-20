from django.test import TestCase
from django.urls import reverse


class PagesViewTests(TestCase):
    def test_index_renders_for_anonymous_users(self):
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Campfire Connections")
