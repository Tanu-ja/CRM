from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.accounts.models import Role
from apps.campaigns.models import Campaign
from apps.clients.models import Client

from .utils import normalize_phone


class LeadStatus(models.TextChoices):
    NEW = "NEW", "New"
    ASSIGNED = "ASSIGNED", "Assigned"
    CONTACT_ATTEMPTED = "CONTACT_ATTEMPTED", "Contact Attempted"
    CONNECTED = "CONNECTED", "Connected"
    FOLLOW_UP = "FOLLOW_UP", "Follow Up"
    COUNSELLING = "COUNSELLING", "Counselling"
    VISIT_SCHEDULED = "VISIT_SCHEDULED", "Visit Scheduled"
    VISITED = "VISITED", "Visited"
    ADMISSION_PENDING = "ADMISSION_PENDING", "Admission Pending"
    ADMISSION_CONFIRMED = "ADMISSION_CONFIRMED", "Admission Confirmed"
    NOT_INTERESTED = "NOT_INTERESTED", "Not Interested"
    WRONG_NUMBER = "WRONG_NUMBER", "Wrong Number"
    DUPLICATE = "DUPLICATE", "Duplicate"
    LOST = "LOST", "Lost"


class Temperature(models.TextChoices):
    HOT = "HOT", "Hot"
    WARM = "WARM", "Warm"
    COLD = "COLD", "Cold"
    UNQUALIFIED = "UNQUALIFIED", "Unqualified"


class LeadQuerySet(models.QuerySet):
    def visible_detail(self, user):
        """Rows this user may see individually, in full detail."""
        if user.role == Role.SUPER_ADMIN:
            return self
        if user.role == Role.CLIENT_ADMIN:
            return self.filter(client=user.client)
        return self.filter(client=user.client, assigned_to=user)

    def scoped_to_client(self, user):
        """Full client-wide queryset for AGGREGATION ONLY. Callers must not
        serialize individual rows from this to a Telecaller — only
        .values(...).annotate(...) results."""
        if user.role == Role.SUPER_ADMIN:
            return self
        return self.filter(client=user.client)


class Lead(models.Model):
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name="leads")
    campaign = models.ForeignKey(Campaign, null=True, blank=True, on_delete=models.SET_NULL, related_name="leads")

    lead_id = models.CharField(max_length=32, unique=True, editable=False)

    name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20)
    whatsapp_phone = models.CharField(max_length=20, blank=True)
    alternate_phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    phone_normalized = models.CharField(max_length=20, db_index=True, editable=False)
    whatsapp_phone_normalized = models.CharField(max_length=20, db_index=True, blank=True, editable=False)
    alternate_phone_normalized = models.CharField(max_length=20, db_index=True, blank=True, editable=False)

    status = models.CharField(max_length=32, choices=LeadStatus.choices, default=LeadStatus.NEW)
    temperature = models.CharField(max_length=16, choices=Temperature.choices, default=Temperature.WARM)

    original_source = models.CharField(max_length=100, blank=True)
    original_campaign = models.CharField(max_length=255, blank=True)
    original_ad = models.CharField(max_length=255, blank=True)
    original_ad_set = models.CharField(max_length=255, blank=True)

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_leads"
    )
    next_follow_up_at = models.DateTimeField(null=True, blank=True, db_index=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    first_touch_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LeadQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["client", "status"]),
            models.Index(fields=["client", "assigned_to"]),
            models.Index(fields=["client", "temperature"]),
        ]

    def __str__(self):
        return f"{self.lead_id} - {self.name or self.phone}"

    def save(self, *args, **kwargs):
        self.phone_normalized = normalize_phone(self.phone)
        self.whatsapp_phone_normalized = normalize_phone(self.whatsapp_phone)
        self.alternate_phone_normalized = normalize_phone(self.alternate_phone)
        super().save(*args, **kwargs)

    @property
    def current_admission(self):
        return self.admissions.order_by("-created_at").first()

    @staticmethod
    def duplicate_query(client, phone_normalized, whatsapp_normalized="", alternate_normalized=""):
        candidates = {v for v in (phone_normalized, whatsapp_normalized, alternate_normalized) if v}
        if not candidates:
            return Lead.objects.none()
        return Lead.objects.filter(client=client).filter(
            Q(phone_normalized__in=candidates)
            | Q(whatsapp_phone_normalized__in=candidates)
            | Q(alternate_phone_normalized__in=candidates)
        )


class LeadCounter(models.Model):
    """Backs concurrency-safe lead_id sequence generation — see
    apps.leads.services.next_lead_id."""

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="lead_counters")
    year = models.PositiveIntegerField()
    last_sequence = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["client", "year"], name="unique_counter_per_client_year")]


class FollowUpType(models.TextChoices):
    CALL = "CALL", "Call"
    WHATSAPP = "WHATSAPP", "WhatsApp"
    VISIT = "VISIT", "Visit"
    COUNSELLING = "COUNSELLING", "Counselling"
    DOCUMENT_COLLECTION = "DOCUMENT_COLLECTION", "Document Collection"
    ADMISSION = "ADMISSION", "Admission"
    OTHER = "OTHER", "Other"


class FollowUpStatus(models.TextChoices):
    OPEN = "OPEN", "Open"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"


class FollowUpQuerySet(models.QuerySet):
    def visible_detail(self, user):
        if user.role == Role.SUPER_ADMIN:
            return self
        if user.role == Role.CLIENT_ADMIN:
            return self.filter(lead__client=user.client)
        return self.filter(lead__client=user.client, assigned_to=user)

    def scoped_to_client(self, user):
        if user.role == Role.SUPER_ADMIN:
            return self
        return self.filter(lead__client=user.client)


class FollowUp(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="followups")
    scheduled_at = models.DateTimeField()
    type = models.CharField(max_length=32, choices=FollowUpType.choices, default=FollowUpType.CALL)
    note = models.TextField(blank=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="followups")
    status = models.CharField(max_length=16, choices=FollowUpStatus.choices, default=FollowUpStatus.OPEN)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    objects = FollowUpQuerySet.as_manager()

    class Meta:
        ordering = ["scheduled_at"]
        indexes = [
            models.Index(fields=["assigned_to", "status", "scheduled_at"]),
            models.Index(fields=["lead", "status"]),
        ]

    def __str__(self):
        return f"Follow-up for {self.lead.lead_id} @ {self.scheduled_at:%Y-%m-%d %H:%M}"

    def mark_completed(self):
        self.status = FollowUpStatus.COMPLETED
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "completed_at"])
