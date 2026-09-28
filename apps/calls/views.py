from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from apps.audit.services import log_action
from apps.leads.models import Lead

from .forms import CallForm


@login_required
def add_call(request, lead_pk):
    lead = get_object_or_404(Lead.objects.visible_detail(request.user), pk=lead_pk)
    if request.method == "POST":
        form = CallForm(request.POST)
        if form.is_valid():
            call = form.save(commit=False)
            call.lead = lead
            call.staff = request.user
            try:
                call.duration_seconds = max(0, int(request.POST.get("duration_seconds", 0)))
            except (TypeError, ValueError):
                call.duration_seconds = 0
            call.save()
            log_action(
                actor=request.user,
                action="call.logged",
                entity="Call",
                entity_id=call.pk,
                detail=f"Lead {lead.lead_id} - {call.outcome}",
            )
            messages.success(request, "Call logged.")
    return redirect("leads:detail", pk=lead_pk)
