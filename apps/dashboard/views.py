from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.shortcuts import render
from django.views.generic import TemplateView

from apps.accounts.models import Role

from .services import dashboard_context, super_admin_context


class DashboardView(LoginRequiredMixin, TemplateView):
    def get_template_names(self):
        role = self.request.user.role
        return [f"dashboard/{role.lower()}.html"]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(dashboard_context(self.request.user))
        return ctx


@login_required
def kpi_fragment(request):
    if request.user.role == Role.SUPER_ADMIN:
        ctx = cache.get_or_set("dashboard:superadmin:kpi", super_admin_context, 60)
    else:
        ctx = dashboard_context(request.user)
    return render(request, "dashboard/partials/kpi_cards.html", ctx)
