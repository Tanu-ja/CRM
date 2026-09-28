from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView

from apps.accounts.models import Role
from apps.audit.services import log_action
from apps.core.mixins import RoleRequiredMixin

from .forms import CampaignForm
from .models import Campaign


class CampaignListView(RoleRequiredMixin, ListView):
    allowed_roles = (Role.SUPER_ADMIN, Role.CLIENT_ADMIN)
    model = Campaign
    template_name = "campaigns/campaign_list.html"
    context_object_name = "campaigns"

    def get_queryset(self):
        return Campaign.objects.select_related("client").scoped_to_client(self.request.user)


class CampaignCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = (Role.SUPER_ADMIN, Role.CLIENT_ADMIN)
    model = Campaign
    form_class = CampaignForm
    template_name = "campaigns/campaign_form.html"
    success_url = reverse_lazy("campaigns:list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["actor"] = self.request.user
        return kwargs

    def form_valid(self, form):
        if self.request.user.is_client_admin:
            form.instance.client = self.request.user.client
        response = super().form_valid(form)
        log_action(
            actor=self.request.user,
            action="campaign.created",
            entity="Campaign",
            entity_id=self.object.pk,
            detail=self.object.name,
        )
        messages.success(self.request, f"Campaign '{self.object.name}' created.")
        return response
