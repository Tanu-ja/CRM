from django.db import models

from apps.accounts.models import Role
from apps.clients.models import Client
from apps.core.models import TimeStampedModel


class CampaignQuerySet(models.QuerySet):
    def scoped_to_client(self, user):
        if user.role == Role.SUPER_ADMIN:
            return self
        return self.filter(client=user.client)


class Campaign(TimeStampedModel):
    objects = CampaignQuerySet.as_manager()
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name="campaigns")
    name = models.CharField(max_length=255)
    course = models.CharField(max_length=255, blank=True)
    commission_per_admission = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Overrides the client's default commission when set.",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["client", "name"]
        indexes = [models.Index(fields=["client", "is_active"])]

    def __str__(self):
        return f"{self.name} ({self.client.code})"

    @property
    def effective_commission(self):
        return self.commission_per_admission if self.commission_per_admission is not None else self.client.commission_per_admission
