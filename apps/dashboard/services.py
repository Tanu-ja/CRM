from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncWeek
from django.utils import timezone

from apps.accounts.models import Role
from apps.admissions.models import Admission, AdmissionStatus
from apps.audit.models import AuditLog
from apps.leads.models import FollowUp, FollowUpStatus, Lead, LeadStatus


def status_kpis(queryset):
    """One conditional-aggregation query for the whole KPI card row,
    instead of one .filter().count() per status."""
    return queryset.aggregate(
        total=Count("id"),
        **{status.lower(): Count("id", filter=Q(status=status)) for status in LeadStatus.values},
    )


def followup_bucket_counts(user):
    now = timezone.now()
    today_end = timezone.localtime(now).replace(hour=23, minute=59, second=59, microsecond=999999)
    open_followups = FollowUp.objects.visible_detail(user).filter(status=FollowUpStatus.OPEN)
    return {
        "overdue": open_followups.filter(scheduled_at__lt=now).count(),
        "today": open_followups.filter(scheduled_at__gte=now, scheduled_at__lte=today_end).count(),
        "upcoming": open_followups.filter(scheduled_at__gt=today_end).count(),
    }


def super_admin_context():
    leads = Lead.objects.all()
    kpis = status_kpis(leads)
    per_client = (
        leads.values("client__name")
        .annotate(
            total=Count("id"),
            confirmed=Count("id", filter=Q(status=LeadStatus.ADMISSION_CONFIRMED)),
        )
        .order_by("-total")
    )
    trend = (
        leads.annotate(week=TruncWeek("created_at"))
        .values("week")
        .annotate(count=Count("id"))
        .order_by("week")
    )
    recent_audit = AuditLog.objects.select_related("actor").all()[:20]
    return {"kpis": kpis, "per_client": per_client, "trend": trend, "recent_audit": recent_audit}


def client_admin_context(user):
    leads = Lead.objects.filter(client=user.client)
    kpis = status_kpis(leads)
    per_telecaller = (
        leads.values("assigned_to__first_name", "assigned_to__last_name", "assigned_to__email")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    admissions_summary = Admission.objects.filter(lead__client=user.client).aggregate(
        confirmed_commission=Sum("commission", filter=Q(status=AdmissionStatus.CONFIRMED)),
        confirmed_count=Count("id", filter=Q(status=AdmissionStatus.CONFIRMED)),
        pending_count=Count("id", filter=Q(status=AdmissionStatus.PENDING)),
    )
    return {
        "kpis": kpis,
        "per_telecaller": per_telecaller,
        "admissions_summary": admissions_summary,
        "followup_counts": followup_bucket_counts(user),
    }


def telecaller_context(user):
    my_leads = Lead.objects.visible_detail(user)  # already own-only for a Telecaller
    kpis = status_kpis(my_leads)

    team_totals = (
        Lead.objects.scoped_to_client(user)
        .values("assigned_to__first_name", "assigned_to__last_name", "assigned_to_id")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    return {
        "kpis": kpis,
        "team_totals": team_totals,
        "followup_counts": followup_bucket_counts(user),
    }


def dashboard_context(user):
    if user.role == Role.SUPER_ADMIN:
        return super_admin_context()
    if user.role == Role.CLIENT_ADMIN:
        return client_admin_context(user)
    return telecaller_context(user)
