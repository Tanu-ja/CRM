from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView

from apps.audit.services import log_action
from apps.core.mixins import RoleRequiredMixin, role_required
from apps.core.permissions import can_manage_client_staff, can_reset_password

from .forms import AdminSetPasswordForm, EmailAuthenticationForm, StaffCreateForm
from .models import Role, User


class EmailLoginView(auth_views.LoginView):
    template_name = "accounts/login.html"
    authentication_form = EmailAuthenticationForm
    redirect_authenticated_user = True


class StaffListView(RoleRequiredMixin, ListView):
    allowed_roles = (Role.SUPER_ADMIN, Role.CLIENT_ADMIN)
    model = User
    template_name = "accounts/staff_list.html"
    context_object_name = "staff"

    def get_queryset(self):
        user = self.request.user
        qs = User.objects.select_related("client").exclude(pk=user.pk)
        if user.is_client_admin:
            return qs.filter(client=user.client, role=Role.TELECALLER)
        return qs.filter(role__in=(Role.CLIENT_ADMIN, Role.TELECALLER))


class StaffCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = (Role.SUPER_ADMIN, Role.CLIENT_ADMIN)
    model = User
    form_class = StaffCreateForm
    template_name = "accounts/staff_form.html"
    success_url = reverse_lazy("accounts:staff_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["actor"] = self.request.user
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        log_action(
            actor=self.request.user,
            action="staff.created",
            entity="User",
            entity_id=self.object.pk,
            detail=f"Created {self.object.email} ({self.object.role})",
        )
        messages.success(self.request, f"Staff account created for {self.object.email}.")
        return response


@login_required
@role_required(Role.SUPER_ADMIN, Role.CLIENT_ADMIN)
def staff_toggle_active(request, pk):
    target = get_object_or_404(User, pk=pk)
    if not can_manage_client_staff(request.user, target.client):
        raise PermissionDenied
    target.is_active = not target.is_active
    target.save(update_fields=["is_active"])
    log_action(
        actor=request.user,
        action="staff.disabled" if not target.is_active else "staff.enabled",
        entity="User",
        entity_id=target.pk,
        detail=target.email,
    )
    messages.success(request, f"{target.email} is now {'active' if target.is_active else 'disabled'}.")
    return redirect("accounts:staff_list")


@login_required
@role_required(Role.SUPER_ADMIN, Role.CLIENT_ADMIN)
def staff_reset_password(request, pk):
    target = get_object_or_404(User, pk=pk)
    if not can_reset_password(request.user, target):
        raise PermissionDenied

    if request.method == "POST":
        form = AdminSetPasswordForm(target, request.POST)
        if form.is_valid():
            form.save()
            target.mark_sessions_stale()
            log_action(
                actor=request.user,
                action="staff.password_reset",
                entity="User",
                entity_id=target.pk,
                detail=target.email,
            )
            messages.success(request, f"Password reset for {target.email}.")
            return redirect("accounts:staff_list")
    else:
        form = AdminSetPasswordForm(target)

    return render(request, "accounts/staff_reset_password.html", {"form": form, "target": target})
