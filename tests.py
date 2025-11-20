import json

from django.test import TestCase
from django.urls import reverse

from django.contrib.auth import get_user_model
from core.models.dashboard import DashboardLayout

User = get_user_model()


class PagesViewTests(TestCase):
    def test_index_renders_for_anonymous_users(self):
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Campfire Connections")


class SaveLayoutViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="layout.user",
            password="pass1234",
            user_type=User.UserType.ADMIN,
        )

    def test_hide_widget_creates_preference(self):
        self.client.force_login(self.user)
        payload = {"action": "hide_widget", "widget_key": "test-card", "portal_key": "facility"}
        response = self.client.post(
            reverse("save_layout"),
            json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        layout = DashboardLayout.objects.get(user=self.user, portal_key="facility")
        self.assertIn("test-card", layout.hidden_widgets)

    def test_show_widget_removes_from_hidden(self):
        layout = DashboardLayout.objects.create(
            user=self.user,
            portal_key="facility",
            hidden_widgets=["test-card", "other"],
        )
        self.client.force_login(self.user)
        payload = {"action": "show_widget", "widget_key": "test-card", "portal_key": "facility"}
        response = self.client.post(
            reverse("save_layout"),
            json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        layout.refresh_from_db()
        self.assertNotIn("test-card", layout.hidden_widgets)
        self.assertIn("other", layout.hidden_widgets)

    def test_reset_hidden_clears_list(self):
        DashboardLayout.objects.create(
            user=self.user,
            portal_key="facility",
            hidden_widgets=["one", "two"],
        )
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("save_layout"),
            json.dumps({"action": "reset_hidden", "portal_key": "facility"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        layout = DashboardLayout.objects.get(user=self.user, portal_key="facility")
        self.assertEqual(layout.hidden_widgets, [])

    def test_invalid_action_returns_error(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("save_layout"),
            json.dumps({"action": "unknown"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
