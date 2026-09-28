from django.views.generic import ListView

from apps.accounts.models import Role
from apps.core.mixins import RoleRequiredMixin

from .models import AuditLog


class AuditLogListView(RoleRequiredMixin, ListView):
    allowed_roles = (Role.SUPER_ADMIN, Role.CLIENT_ADMIN)
    model = AuditLog
    template_name = "audit/audit_list.html"
    context_object_name = "logs"
    paginate_by = 50

    def get_queryset(self):
        qs = AuditLog.objects.select_related("actor")
        if self.request.user.is_client_admin:
            qs = qs.filter(actor__client=self.request.user.client)
        return qs
