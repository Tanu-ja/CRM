from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView

from apps.accounts.models import Role
from apps.audit.services import log_action
from apps.core.mixins import RoleRequiredMixin, role_required

from .forms import ClientForm
from .models import Client


class ClientListView(RoleRequiredMixin, ListView):
    allowed_roles = (Role.SUPER_ADMIN,)
    model = Client
    template_name = "clients/client_list.html"
    context_object_name = "clients"
    queryset = Client.objects.all()


class ClientCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = (Role.SUPER_ADMIN,)
    model = Client
    form_class = ClientForm
    template_name = "clients/client_form.html"
    success_url = reverse_lazy("clients:list")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        log_action(
            actor=self.request.user,
            action="client.created",
            entity="Client",
            entity_id=self.object.pk,
            detail=self.object.name,
        )
        messages.success(self.request, f"Client '{self.object.name}' created.")
        return response


@login_required
@role_required(Role.SUPER_ADMIN)
def client_toggle_active(request, pk):
    client = get_object_or_404(Client, pk=pk)
    client.is_active = not client.is_active
    client.save(update_fields=["is_active"])
    log_action(
        actor=request.user,
        action="client.deactivated" if not client.is_active else "client.activated",
        entity="Client",
        entity_id=client.pk,
        detail=client.name,
    )
    messages.success(request, f"{client.name} is now {'active' if client.is_active else 'deactivated'}.")
    return redirect("clients:list")
