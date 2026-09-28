from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView

from apps.audit.services import log_action
from apps.leads.models import Lead

from .forms import AdmissionForm
from .models import Admission


class AdmissionListView(LoginRequiredMixin, ListView):
    model = Admission
    template_name = "admissions/admission_list.html"
    context_object_name = "admissions"
    paginate_by = 25

    def get_queryset(self):
        qs = Admission.objects.visible_detail(self.request.user).select_related("lead", "lead__client")
        status = self.request.GET.get("status", "")
        if status:
            qs = qs.filter(status=status)
        return qs


@login_required
def add_admission(request, lead_pk):
    lead = get_object_or_404(Lead.objects.visible_detail(request.user), pk=lead_pk)
    if request.method == "POST":
        form = AdmissionForm(request.POST)
        if form.is_valid():
            admission = form.save(commit=False)
            admission.lead = lead
            admission.created_by = request.user
            if admission.status == "CONFIRMED":
                admission.confirmed_by = request.user
            admission.save()
            log_action(
                actor=request.user,
                action="admission.created",
                entity="Admission",
                entity_id=admission.pk,
                detail=f"Lead {lead.lead_id} - {admission.status}",
            )
            messages.success(request, "Admission recorded.")
    return redirect("leads:detail", pk=lead_pk)
