from django.conf import settings
from django.db import models

from apps.accounts.models import Role
from apps.leads.models import Lead


class AdmissionStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    CONFIRMED = "CONFIRMED", "Confirmed"
    REJECTED = "REJECTED", "Rejected"
    CANCELLED = "CANCELLED", "Cancelled"


class AdmissionQuerySet(models.QuerySet):
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


class Admission(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.PROTECT, related_name="admissions")
    student_name = models.CharField(max_length=255, blank=True)
    admission_phone = models.CharField(max_length=20, db_index=True)
    alternate_phone = models.CharField(max_length=20, blank=True)
    guardian_phone = models.CharField(max_length=20, blank=True)
    course = models.CharField(max_length=255, blank=True)
    admission_date = models.DateField(null=True, blank=True)
    admission_number = models.CharField(max_length=64, unique=True, db_index=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=16, choices=AdmissionStatus.choices, default=AdmissionStatus.PENDING)
    commission = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+"
    )
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = AdmissionQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Admission {self.admission_number} ({self.status})"

    def _effective_rate(self):
        rate = self.lead.campaign.effective_commission if self.lead.campaign_id else None
        return rate if rate is not None else self.lead.client.commission_per_admission

    def save(self, *args, **kwargs):
        self.commission = self._effective_rate() if self.status == AdmissionStatus.CONFIRMED else 0
        super().save(*args, **kwargs)
