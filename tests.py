import json

from django.test import TestCase
from django.urls import reverse

from django.contrib.auth import get_user_model
from core.models.dashboard import DashboardLayout
from core.models.navigation import NavigationPreference
from core.tests import BaseDomainTestCase, mute_profile_signals
from facility.models.faculty import FacultyProfile
from organization.models import Organization

User = get_user_model()


class PagesViewTests(TestCase):
    def test_index_renders_for_anonymous_users(self):
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Campfire Connections")


class ResourceAndHelpViewTests(BaseDomainTestCase):
    def test_resources_show_public_entries_for_anonymous_users(self):
        response = self.client.get(reverse("resources"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Get Started")
        self.assertContains(response, "Request Access")
        self.assertNotContains(response, "Admin Portal")

    def test_resources_show_admin_operational_links(self):
        user = User.objects.create_user(
            username="resource.admin",
            password="pass1234",
            user_type=User.UserType.ADMIN,
            is_admin=True,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("resources"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Administration")
        self.assertContains(response, "Facilities")
        self.assertContains(response, "Enrollment Windows")

    def test_resources_show_facility_context_for_faculty(self):
        with mute_profile_signals():
            user = User.objects.create_user(
                username="resource.faculty",
                password="pass1234",
                user_type=User.UserType.FACULTY,
            )
        FacultyProfile.objects.create(
            user=user,
            organization=self.organization,
            facility=self.facility,
            role=FacultyProfile.FacultyRole.STAFF,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("resources"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Facility")
        self.assertContains(response, "My Faculty Enrollments")
        self.assertContains(
            response,
            f"/facilities/{self.facility.slug}/faculty/{user.get_profile().slug}/enrollments/",
        )

    def test_help_shows_role_workflow_reference(self):
        response = self.client.get(reverse("help"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Workflow reference")
        self.assertContains(response, "Enrollment")
        self.assertContains(response, "faction chain")


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

    def test_save_layout_accepts_list(self):
        self.client.force_login(self.user)
        payload = {"action": "save_layout", "portal_key": "facility", "layout": ["a", "b"]}
        response = self.client.post(
            reverse("save_layout"),
            json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        layout = DashboardLayout.objects.get(user=self.user, portal_key="facility")
        self.assertEqual(json.loads(layout.layout), ["a", "b"])

    def test_save_layout_rejects_non_list_layout(self):
        self.client.force_login(self.user)
        payload = {"action": "save_layout", "portal_key": "facility", "layout": "a,b"}
        response = self.client.post(
            reverse("save_layout"),
            json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["message"], "Invalid layout payload")

    def test_save_layout_rejects_non_string_widget_key(self):
        self.client.force_login(self.user)
        payload = {"action": "hide_widget", "widget_key": ["bad"], "portal_key": "facility"}
        response = self.client.post(
            reverse("save_layout"),
            json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["message"], "Invalid widget key")

    def test_invalid_action_returns_error(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("save_layout"),
            json.dumps({"action": "unknown"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_invalid_json_returns_error(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("save_layout"),
            "{invalid-json",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["message"], "Invalid JSON payload")


class ToggleNavFavoriteViewTests(TestCase):
    def setUp(self):
        with mute_profile_signals():
            self.user = User.objects.create_user(
                username="nav.user",
                password="pass1234",
                user_type=User.UserType.LEADER,
            )
        self.url = reverse("toggle_nav_favorite")

    def _post(self, payload):
        self.client.force_login(self.user)
        return self.client.post(
            self.url,
            json.dumps(payload),
            content_type="application/json",
        )

    def test_add_favorite_creates_preference(self):
        response = self._post({"key": "factions.dashboard"})
        self.assertEqual(response.status_code, 200)
        pref = NavigationPreference.objects.get(user=self.user)
        self.assertIn("factions.dashboard", pref.favorite_keys)
        self.assertTrue(response.json()["pinned"])

    def test_remove_favorite_discards_key(self):
        pref = NavigationPreference.objects.create(
            user=self.user,
            favorite_keys=["factions.dashboard", "reports.index"],
        )
        response = self._post(
            {"key": "factions.dashboard", "action": "remove"}
        )
        self.assertEqual(response.status_code, 200)
        pref.refresh_from_db()
        self.assertEqual(pref.favorite_keys, ["reports.index"])
        self.assertEqual(response.json()["state"], "removed")
        self.assertFalse(response.json()["pinned"])

    def test_missing_key_returns_error(self):
        response = self._post({"action": "add"})
        self.assertEqual(response.status_code, 400)


class DynamicDropdownTests(TestCase):
    def test_options_are_filtered_by_parent(self):
        user = User.objects.create_user(
            username="dropdown.user",
            password="pass1234",
            user_type=User.UserType.ADMIN,
        )
        self.client.force_login(user)
        parent = Organization.objects.create(
            name="Test Council",
            abbreviation="TC",
            max_depth=3,
        )
        child = Organization.objects.create(
            name="Test District",
            abbreviation="TD",
            parent=parent,
            max_depth=3,
        )
        Organization.objects.create(
            name="Other District",
            abbreviation="OD",
            max_depth=3,
        )

        response = self.client.get(
            reverse(
                "dynamic-dropdown-options",
                args=("organization", "organization", "parent", parent.id),
            )
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()["options"]
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["value"], child.id)
