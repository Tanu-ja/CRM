from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView

from apps.admissions.forms import AdmissionForm
from apps.audit.services import log_action
from apps.calls.forms import CallForm
from apps.core.mixins import ScopedQuerysetMixin

from .forms import FollowUpForm, LeadForm, LeadReassignForm, LeadStatusForm
from .models import FollowUp, FollowUpStatus, Lead, LeadStatus, Temperature
from .services import create_lead


class LeadListView(LoginRequiredMixin, ListView):
    model = Lead
    template_name = "leads/lead_list.html"
    context_object_name = "leads"
    paginate_by = 25

    def get_template_names(self):
        if self.request.htmx:
            return ["leads/partials/lead_table.html"]
        return super().get_template_names()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["lead_status_choices"] = LeadStatus.choices
        ctx["temperature_choices"] = Temperature.choices
        return ctx

    def get_queryset(self):
        qs = Lead.objects.visible_detail(self.request.user).select_related("client", "campaign", "assigned_to")
        q = self.request.GET.get("q", "").strip()
        status = self.request.GET.get("status", "")
        temperature = self.request.GET.get("temperature", "")
        period = self.request.GET.get("period", "")

        if q:
            qs = qs.filter(_search_filter(q))
        if status:
            qs = qs.filter(status=status)
        if temperature:
            qs = qs.filter(temperature=temperature)
        if period:
            qs = _apply_period_filter(qs, period)
        return qs


def _search_filter(q):
    from django.db.models import Q

    return (
        Q(lead_id__icontains=q)
        | Q(name__icontains=q)
        | Q(phone__icontains=q)
        | Q(email__icontains=q)
    )


def _apply_period_filter(qs, period):
    now = timezone.localtime()
    if period == "today":
        return qs.filter(created_at__date=now.date())
    if period == "week":
        start = now - timezone.timedelta(days=now.weekday())
        return qs.filter(created_at__gte=start.replace(hour=0, minute=0, second=0, microsecond=0))
    if period == "month":
        return qs.filter(created_at__year=now.year, created_at__month=now.month)
    return qs


class LeadDetailView(ScopedQuerysetMixin, LoginRequiredMixin, DetailView):
    model = Lead
    template_name = "leads/lead_detail.html"
    context_object_name = "lead"

    def get_queryset(self):
        return (
            Lead.objects.visible_detail(self.request.user)
            .select_related("client", "campaign", "assigned_to")
            .prefetch_related("calls", "followups", "admissions")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["status_form"] = LeadStatusForm(instance=self.object)
        ctx["reassign_form"] = LeadReassignForm(instance=self.object, client=self.object.client)
        ctx["followup_form"] = FollowUpForm(client=self.object.client, initial={"assigned_to": self.object.assigned_to})
        ctx["call_form"] = CallForm()
        ctx["admission_form"] = AdmissionForm()
        ctx["timeline"] = sorted(
            [*self.object.calls.all(), *self.object.followups.all(), *self.object.admissions.all()],
            key=lambda obj: obj.created_at,
            reverse=True,
        )
        return ctx


class LeadCreateView(LoginRequiredMixin, CreateView):
    model = Lead
    form_class = LeadForm
    template_name = "leads/lead_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["actor"] = self.request.user
        return kwargs

    def form_valid(self, form):
        data = form.cleaned_data
        lead = create_lead(client=self.request.user.client, created_by=self.request.user, **data)
        self.object = lead
        log_action(
            actor=self.request.user,
            action="lead.created",
            entity="Lead",
            entity_id=lead.pk,
            detail=lead.lead_id,
        )
        messages.success(self.request, f"Lead {lead.lead_id} created.")
        return redirect("leads:detail", pk=lead.pk)


@login_required
def update_status(request, pk):
    lead = get_object_or_404(Lead.objects.visible_detail(request.user), pk=pk)
    if request.method == "POST":
        form = LeadStatusForm(request.POST, instance=lead)
        if form.is_valid():
            old_status = lead.status
            form.save()
            log_action(
                actor=request.user,
                action="lead.status_changed",
                entity="Lead",
                entity_id=lead.pk,
                old_value={"status": old_status},
                new_value={"status": lead.status},
            )
            messages.success(request, "Lead status updated.")
    return redirect("leads:detail", pk=pk)


@login_required
def reassign(request, pk):
    # Only Client Admin / Super Admin may reassign — Telecallers only see their own leads anyway.
    lead = get_object_or_404(Lead.objects.visible_detail(request.user), pk=pk)
    if request.user.is_telecaller:
        raise PermissionDenied
    if request.method == "POST":
        form = LeadReassignForm(request.POST, instance=lead, client=lead.client)
        if form.is_valid():
            old_assignee = lead.assigned_to_id
            form.save()
            log_action(
                actor=request.user,
                action="lead.reassigned",
                entity="Lead",
                entity_id=lead.pk,
                old_value={"assigned_to": old_assignee},
                new_value={"assigned_to": lead.assigned_to_id},
            )
            messages.success(request, "Lead reassigned.")
    return redirect("leads:detail", pk=pk)


@login_required
def add_followup(request, pk):
    lead = get_object_or_404(Lead.objects.visible_detail(request.user), pk=pk)
    if request.method == "POST":
        form = FollowUpForm(request.POST, client=lead.client)
        if form.is_valid():
            followup = form.save(commit=False)
            followup.lead = lead
            followup.created_by = request.user
            followup.save()
            log_action(
                actor=request.user,
                action="followup.scheduled",
                entity="FollowUp",
                entity_id=followup.pk,
                detail=f"Lead {lead.lead_id}",
            )
            messages.success(request, "Follow-up scheduled.")
    return redirect("leads:detail", pk=pk)


@login_required
def complete_followup(request, pk):
    followup = get_object_or_404(FollowUp.objects.visible_detail(request.user), pk=pk)
    followup.mark_completed()
    log_action(
        actor=request.user,
        action="followup.completed",
        entity="FollowUp",
        entity_id=followup.pk,
        detail=f"Lead {followup.lead.lead_id}",
    )
    messages.success(request, "Follow-up marked complete.")
    return redirect(request.META.get("HTTP_REFERER") or "leads:followup_queue")


@login_required
def followup_queue(request):
    now = timezone.now()
    today_end = timezone.localtime(now).replace(hour=23, minute=59, second=59, microsecond=999999)
    base = FollowUp.objects.visible_detail(request.user).filter(status=FollowUpStatus.OPEN).select_related(
        "lead", "lead__client"
    )

    bucket = request.GET.get("bucket", "overdue")
    buckets = {
        "overdue": base.filter(scheduled_at__lt=now),
        "today": base.filter(scheduled_at__gte=now, scheduled_at__lte=today_end),
        "upcoming": base.filter(scheduled_at__gt=today_end),
    }
    context = {
        "bucket": bucket,
        "followups": buckets.get(bucket, buckets["overdue"]).order_by("scheduled_at"),
        "counts": {name: qs.count() for name, qs in buckets.items()},
    }
    template = "leads/partials/followup_list.html" if request.htmx else "leads/followup_queue.html"
    return render(request, template, context)
