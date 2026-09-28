from django.conf import settings
from django.db import models

from apps.accounts.models import Role
from apps.leads.models import Lead


class CallOutcome(models.TextChoices):
    CONNECTED = "CONNECTED", "Connected"
    NO_ANSWER = "NO_ANSWER", "No Answer"
    BUSY = "BUSY", "Busy"
    SWITCHED_OFF = "SWITCHED_OFF", "Switched Off"
    WRONG_NUMBER = "WRONG_NUMBER", "Wrong Number"
    CALL_BACK = "CALL_BACK", "Call Back Requested"
    INTERESTED = "INTERESTED", "Interested"
    NOT_INTERESTED = "NOT_INTERESTED", "Not Interested"


class CallQuerySet(models.QuerySet):
    def visible_detail(self, user):
        if user.role == Role.SUPER_ADMIN:
            return self
        if user.role == Role.CLIENT_ADMIN:
            return self.filter(lead__client=user.client)
        return self.filter(lead__client=user.client, lead__assigned_to=user)

    def scoped_to_client(self, user):
        if user.role == Role.SUPER_ADMIN:
            return self
        return self.filter(lead__client=user.client)


class Call(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.PROTECT, related_name="calls")
    staff = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="calls_logged")
    outcome = models.CharField(max_length=32, choices=CallOutcome.choices)
    duration_seconds = models.PositiveIntegerField(default=0)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = CallQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["lead", "created_at"])]

    def __str__(self):
        return f"Call on {self.lead.lead_id} - {self.outcome}"
