from django.db import models

from apps.leads.models import Lead


class WhatsAppInboundMessage(models.Model):
    """Reserved architecture only — no auto lead-creation logic yet.
    Real integration (auto-create leads, richer payload handling) is future
    work; this stub just proves out the idempotent-storage shape."""

    message_id = models.CharField(max_length=128, unique=True)
    from_number = models.CharField(max_length=32)
    text = models.TextField(blank=True)
    raw_payload = models.JSONField(default=dict, blank=True)
    received_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    lead = models.ForeignKey(Lead, null=True, blank=True, on_delete=models.SET_NULL, related_name="whatsapp_messages")

    class Meta:
        ordering = ["-received_at"]

    def __str__(self):
        return f"WhatsApp msg {self.message_id} from {self.from_number}"
