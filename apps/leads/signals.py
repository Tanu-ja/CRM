from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import FollowUp
from .services import schedule_followup_and_sync_lead


@receiver(post_save, sender=FollowUp)
@receiver(post_delete, sender=FollowUp)
def sync_lead_next_followup(sender, instance, **kwargs):
    schedule_followup_and_sync_lead(instance)
