from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class Client(TimeStampedModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=16, unique=True, help_text="Short code, e.g. 'NURSE'. Feeds lead IDs.")
    commission_per_admission = models.DecimalField(max_digits=12, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.code = self.code.upper()
        super().save(*args, **kwargs)
