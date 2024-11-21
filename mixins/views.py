# pages/mixins/views.py
from django.contrib.auth.mixins import (
    PermissionRequiredMixin,
    UserPassesTestMixin,
    LoginRequiredMixin as BaseLoginRequiredMixin,
)
from django.contrib import messages
from django.shortcuts import redirect


class LoginRequiredMixin(BaseLoginRequiredMixin):
    login_url = "/login/"
    redirect_field_name = "next"

    def handle_no_permission(self):
        messages.info(self.request, "Please log in to access this page.")
        self.request.session["original_url"] = self.request.get_full_path()
        return super().handle_no_permission()


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        messages.warning(
            self.request, "You do not have permission to access this page."
        )
        return redirect("forbidden")


class SuperUserRequired(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        messages.error(self.request, "This page is restricted to superusers.")
        return redirect("forbidden")


class FormMessagesMixin:
    success_message = ""
    error_message = ""
    success_message_level = messages.SUCCESS
    error_message_level = messages.ERROR

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.success_message:
            dynamic_message = self.success_message.format(obj=form.instance)
            messages.add_message(
                self.request, self.success_message_level, dynamic_message
            )
        return response

    def form_invalid(self, form):
        response = super().form_invalid(form)
        if self.error_message:
            dynamic_message = self.error_message.format(obj=form.instance)
            messages.add_message(
                self.request, self.error_message_level, dynamic_message
            )
        return response


class ObjectPermissionRequiredMixin(PermissionRequiredMixin):
    def has_permission(self):
        obj = self.get_object()
        if isinstance(self.permission_required, (list, tuple)):
            return all(
                self.request.user.has_perm(perm, obj)
                for perm in self.permission_required
            )
        return self.request.user.has_perm(self.permission_required, obj)

    def handle_no_permission(self):
        messages.error(
            self.request, "You do not have permission to perform this action."
        )
        return redirect("forbidden")


class UserGroupRequiredMixin(UserPassesTestMixin):
    required_groups = []

    def test_func(self):
        return any(
            group.name in self.required_groups
            for group in self.request.user.groups.all()
        )

    def handle_no_permission(self):
        messages.error(
            self.request,
            "You do not have the required group membership to access this page.",
        )
        return redirect("forbidden")


class CustomRedirectMixin:
    success_redirect_url = None
    failure_redirect_url = None

    def get_success_redirect_url(self):
        return self.success_redirect_url or self.request.GET.get("next", "/")

    def get_failure_redirect_url(self):
        return self.failure_redirect_url or "/forbidden/"

    def redirect_on_condition(self, condition, success=True):
        if condition:
            return redirect(self.get_success_redirect_url())
        return redirect(self.get_failure_redirect_url())


class DynamicLoginRedirectMixin(LoginRequiredMixin):
    def get_redirect_url(self):
        if self.request.user.is_staff:
            return "/staff/dashboard/"
        elif self.request.user.is_superuser:
            return "/admin/dashboard/"
        return super().get_redirect_url()
