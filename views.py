# core/views.py

import json

from django.apps import apps
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
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
        if isinstance(layout_data, list):
            layout.layout = json.dumps(layout_data)
        else:
            layout.layout = layout_data
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
    return render(request, "help.html", {"section": section})


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
