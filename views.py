# core/views.py

import json

from django.apps import apps
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import NoReverseMatch, reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView
from core.models.messaging import Message, Notification
from core.models.dashboard import DashboardLayout
from core.models.navigation import NavigationPreference
from .forms import MessageForm


class ReportView(TemplateView):
    template_name = "base/reports.html"


class ResourceView(TemplateView):
    template_name = "base/resources.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["resource_sections"] = build_resource_sections(self.request.user)
        return context


def safe_reverse(name, kwargs=None):
    try:
        return reverse(name, kwargs=kwargs or {})
    except NoReverseMatch:
        return "#"


def user_profile(user):
    if not getattr(user, "is_authenticated", False):
        return None
    return getattr(user, "get_profile", lambda: None)()


def profile_context(user):
    profile = user_profile(user)
    return {
        "profile": profile,
        "organization": getattr(profile, "organization", None),
        "facility": getattr(profile, "facility", None),
        "faction": getattr(profile, "faction", None),
    }


def link(label, description, icon, url_name=None, kwargs=None, url=None):
    return {
        "label": label,
        "description": description,
        "icon": icon,
        "url": url or safe_reverse(url_name, kwargs),
    }


def build_resource_sections(user):
    if not getattr(user, "is_authenticated", False):
        return [
            {
                "title": "Get Started",
                "description": "Public entry points for visitors and new account requests.",
                "items": [
                    link("Sign In", "Open an existing Campfire Connections workspace.", "fa-sign-in-alt", "login"),
                    link("Request Access", "Create an account for your organization, facility, or faction role.", "fa-user-plus", "signup"),
                    link("Help", "Review the core workflows before signing in.", "fa-circle-question", "help"),
                ],
            }
        ]

    ctx = profile_context(user)
    profile = ctx["profile"]
    facility = ctx["facility"]
    faction = ctx["faction"]
    user_type = getattr(user, "user_type", "")
    sections = [
        {
            "title": "Workspace",
            "description": "Daily operational pages for your account.",
            "items": [
                link("Dashboard", "Return to your role dashboard and pinned navigation.", "fa-gauge-high", "dashboard"),
                link("Profile", "Open your user profile and account settings.", "fa-id-badge", "profile"),
                link("Reports", "Review saved reports and operational summaries.", "fa-chart-line", "reports:list_user_reports"),
                link("Help", "Workflow reference for your role.", "fa-circle-question", "help"),
            ],
        }
    ]

    if user_type == "ADMIN" or getattr(user, "is_staff", False) or getattr(user, "is_admin", False):
        sections.append(
            {
                "title": "Administration",
                "description": "System-wide setup and catalog maintenance.",
                "items": [
                    link("Admin Portal", "Open Django administration tools.", "fa-toolbox", url="/admin/"),
                    link("Organizations", "Manage councils, districts, and organization hierarchy.", "fa-sitemap", "organizations:index"),
                    link("Facilities", "Manage camp properties, quarters, and facility staff.", "fa-campground", "facilities:index"),
                    link("Factions", "Manage attendee groups and leader rosters.", "fa-users", "factions:index"),
                    link("Courses", "Maintain courses, classes, and requirements.", "fa-book-open", "courses:index"),
                    link("Enrollment Windows", "Configure weeks, periods, and active enrollment context.", "fa-calendar-week", "enrollments:week:index"),
                ],
            }
        )

    if facility:
        facility_kwargs = {"facility_slug": facility.slug}
        items = [
            link("Facility Dashboard", "Open the facility workspace for staffing and operations.", "fa-building", "facilities:faculty:dashboard", facility_kwargs),
            link("Faculty Directory", "Review facility faculty profiles.", "fa-chalkboard-user", "facilities:faculty:index", facility_kwargs),
            link("Facility Enrollments", "Track facility-level enrollment periods and assignments.", "fa-clipboard-list", "facilities:enrollments:index", facility_kwargs),
        ]
        if profile and getattr(profile, "slug", None):
            items.append(
                link(
                    "My Faculty Enrollments",
                    "Review your assigned classes and enrollment details.",
                    "fa-list-check",
                    "facilities:faculty:enrollments:index",
                    {"facility_slug": facility.slug, "faculty_slug": profile.slug},
                )
            )
        sections.append(
            {
                "title": "Facility",
                "description": f"Facility-scoped tools for {facility}.",
                "items": items,
            }
        )

    if faction:
        faction_kwargs = {"faction_slug": faction.slug}
        items = [
            link("Faction Dashboard", "Open the faction workspace for rosters and schedule context.", "fa-people-group", "factions:leaders:dashboard", faction_kwargs),
            link("Faction Detail", "Review faction profile, hierarchy, and related people.", "fa-address-card", "factions:show", faction_kwargs),
            link("Leader Directory", "Review leaders in this faction chain.", "fa-user-tie", "factions:leaders:index", faction_kwargs),
            link("Attendee Directory", "Review attendees and sub-faction assignments.", "fa-child-reaching", "factions:attendees:index", faction_kwargs),
            link("Faction Enrollments", "Track faction enrollment status.", "fa-clipboard-check", "factions:enrollments:index", faction_kwargs),
        ]
        if profile and getattr(profile, "slug", None) and user_type == "ATTENDEE":
            items.append(
                link(
                    "My Enrollments",
                    "Review your selected classes and enrollment status.",
                    "fa-list-check",
                    "attendees:enrollments:index",
                    {"attendee_slug": profile.slug},
                )
            )
        sections.append(
            {
                "title": "Faction",
                "description": f"Faction-scoped tools for {faction}.",
                "items": items,
            }
        )

    return sections


def build_help_sections(user):
    ctx = profile_context(user)
    facility = ctx["facility"]
    faction = ctx["faction"]
    sections = [
        {
            "title": "Navigation",
            "items": [
                "Use Dashboard for role-specific work and Resources for cross-role links.",
                "Pinned navigation items are stored per user and can be changed from the sidebar.",
                "Detail pages use tabs for profile, enrollment, and related operational views.",
            ],
        },
        {
            "title": "Enrollment",
            "items": [
                "Attendee enrollment pages are scoped by attendee slug.",
                "Faculty enrollment pages are scoped by facility and faculty slug.",
                "Leader access follows the faction chain so root-faction leaders can review sub-faction attendees.",
            ],
        },
    ]

    if facility:
        sections.append(
            {
                "title": "Facility Workflows",
                "items": [
                    f"Your facility context is {facility}.",
                    "Department admins can manage faculty for their facility.",
                    "Staff without management permissions see the branded access-denied page.",
                ],
            }
        )

    if faction:
        sections.append(
            {
                "title": "Faction Workflows",
                "items": [
                    f"Your faction context is {faction}.",
                    "Faction dashboards summarize roster and enrollment activity.",
                    "Attendee and leader detail pages expose enrollment tabs when the viewer is in the same faction chain.",
                ],
            }
        )

    return sections


@login_required
def save_layout(request):
    if request.method != "POST":
        return JsonResponse({"status": "error"}, status=400)

    user = request.user
    try:
        data = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse(
            {"status": "error", "message": "Invalid JSON payload"},
            status=400,
        )
    action = data.get("action")
    widget_key = data.get("widget_key")
    portal_key = data.get("portal_key") or data.get("portal") or request.GET.get(
        "portal"
    )

    if portal_key is not None and not isinstance(portal_key, str):
        return JsonResponse(
            {"status": "error", "message": "Invalid portal key"},
            status=400,
        )

    if widget_key is not None and not isinstance(widget_key, str):
        return JsonResponse(
            {"status": "error", "message": "Invalid widget key"},
            status=400,
        )

    layout, _ = DashboardLayout.objects.get_or_create(
        user=user, portal_key=portal_key or "default"
    )

    if action == "hide_widget" and widget_key:
        hidden = set(layout.hidden_widgets or [])
        hidden.add(widget_key)
        layout.hidden_widgets = list(hidden)
        layout.save()
        return JsonResponse({"status": "success", "hidden_widgets": layout.hidden_widgets})

    if action == "show_widget" and widget_key:
        hidden = set(layout.hidden_widgets or [])
        hidden.discard(widget_key)
        layout.hidden_widgets = list(hidden)
        layout.save()
        return JsonResponse({"status": "success", "hidden_widgets": layout.hidden_widgets})

    layout_data = data.get("layout")
    if layout_data is not None:
        if not isinstance(layout_data, list) or not all(
            isinstance(item, str) for item in layout_data
        ):
            return JsonResponse(
                {"status": "error", "message": "Invalid layout payload"},
                status=400,
            )
        layout.layout = json.dumps(layout_data[:100])
        layout.save()
        return JsonResponse({"status": "success"})

    if action == "reset_hidden":
        layout.hidden_widgets = []
        layout.save()
        return JsonResponse({"status": "success", "hidden_widgets": []})

    return JsonResponse({"status": "error", "message": "Invalid action"}, status=400)


@login_required
@require_POST
def toggle_nav_favorite(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        payload = request.POST

    key = payload.get("key") or payload.get("menu_key")
    if not key:
        return JsonResponse(
            {"status": "error", "message": "Missing menu key"}, status=400
        )

    action = (payload.get("action") or "add").lower()
    preferences, _ = NavigationPreference.objects.get_or_create(user=request.user)

    if action == "remove":
        preferences.remove_favorite(key)
        state = "removed"
        pinned = False
    else:
        preferences.add_favorite(key)
        state = "added"
        pinned = True

    favorite_keys = preferences.favorite_keys
    return JsonResponse(
        {
            "status": "success",
            "state": state,
            "pinned": pinned,
            "favorite_keys": favorite_keys,
            "favorites": favorite_keys,
        }
    )


@login_required
def mark_message_as_read(request, message_id):
    message = get_object_or_404(Message, id=message_id, receiver=request.user)
    message.read = True
    message.save()
    return redirect("inbox")


@login_required
def mark_notification_as_read(request, notification_id):
    notification = get_object_or_404(
        Notification, id=notification_id, user=request.user
    )
    notification.read = True
    notification.save()
    return redirect("notifications")


@login_required
def inbox(request):
    messages = Message.objects.filter(receiver=request.user).order_by("-timestamp")
    return render(request, "messaging/inbox.html", {"messages": messages})


@login_required
def sent_messages(request):
    messages = Message.objects.filter(sender=request.user).order_by("-timestamp")
    return render(request, "messaging/sent_messages.html", {"messages": messages})


@login_required
def send_message(request):
    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.save()
            # Create a notification
            Notification.objects.create(
                user=message.receiver,
                message=message,
                content=f"New message from {request.user}",
            )
            return redirect("inbox")
    else:
        form = MessageForm()
    return render(request, "messaging/send_message.html", {"form": form})


@login_required
def notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by(
        "-timestamp"
    )
    return render(
        request, "messaging/notifications.html", {"notifications": notifications}
    )


@login_required
def dynamic_dropdown_options(request, app_label, model_name, field_name, filter_value):
    allowed_models = {
        ("organization", "organization"),
        ("facility", "facility"),
        ("facility", "quarters"),
        ("faction", "faction"),
        ("course", "course"),
        ("enrollment", "facilityenrollment"),
    }
    model_key = (app_label.lower(), model_name.lower())
    if model_key not in allowed_models:
        return JsonResponse({"error": "Model not allowed"}, status=400)

    Model = apps.get_model(app_label, model_name)
    try:
        model_field = Model._meta.get_field(field_name)
    except Exception:
        return JsonResponse({"error": "Field not allowed"}, status=400)

    if not model_field.is_relation:
        return JsonResponse({"error": "Field is not a relation"}, status=400)

    filter_field_name = f"{field_name}__id"
    options = Model.objects.filter(**{filter_field_name: filter_value})
    response_data = [{"value": obj.pk, "text": str(obj)} for obj in options]
    return JsonResponse({"options": response_data})


def index(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "index.html", context={})


def help(request, section=None):
    return render(
        request,
        "help.html",
        {"section": section, "help_sections": build_help_sections(request.user)},
    )


def dynamic_css(request):
    css_content = """
    body {
        background-color: #f0f0f0;
        color: #333333;
    }
    /* More dynamic CSS content */
    """
    return HttpResponse(css_content, content_type="text/css")


def error_404(request, exception):
    return render(request, "errors/404.html", status=404)


def error_403(request, exception=None):
    return render(request, "errors/403.html", status=403)


def error_500(request):
    return render(request, "errors/500.html", status=500)
