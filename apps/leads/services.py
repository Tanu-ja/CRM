from django.db import transaction
from django.db.models import F
from django.utils import timezone

from .models import FollowUpStatus, Lead, LeadCounter
from .utils import make_lead_id


def allocate_lead_id_block(client, count: int) -> list[str]:
    """Reserve `count` sequential lead-id numbers for `client` in the
    current year, race-safe under concurrent inserts (simultaneous CSV
    import + manual add). Returns the formatted lead_ids in order."""
    if count <= 0:
        return []
    year = timezone.localdate().year
    with transaction.atomic():
        counter, _ = LeadCounter.objects.select_for_update().get_or_create(
            client=client, year=year, defaults={"last_sequence": 0}
        )
        start = counter.last_sequence + 1
        counter.last_sequence = F("last_sequence") + count
        counter.save(update_fields=["last_sequence"])
    return [make_lead_id(client.code, year, seq) for seq in range(start, start + count)]


def next_lead_id(client) -> str:
    return allocate_lead_id_block(client, 1)[0]


def create_lead(*, client, created_by=None, **fields) -> Lead:
    lead = Lead(client=client, created_by=created_by, lead_id=next_lead_id(client), **fields)
    lead.save()
    return lead


def schedule_followup_and_sync_lead(followup_instance) -> None:
    """Keep Lead.next_follow_up_at denormalized so dashboard/list queries
    avoid a join to FollowUp on every load."""
    lead = followup_instance.lead
    earliest_open = (
        lead.followups.filter(status=FollowUpStatus.OPEN).order_by("scheduled_at").values_list("scheduled_at", flat=True).first()
    )
    lead.next_follow_up_at = earliest_open
    lead.save(update_fields=["next_follow_up_at"])
