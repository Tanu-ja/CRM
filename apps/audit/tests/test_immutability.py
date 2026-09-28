import pytest
from django.core.exceptions import PermissionDenied

from apps.audit.services import log_action
from apps.audit.models import AuditLog

pytestmark = pytest.mark.django_db


def test_log_action_creates_a_row():
    entry = log_action(actor=None, action="lead.created", entity="Lead", entity_id=1, detail="test")
    assert AuditLog.objects.filter(pk=entry.pk).exists()


def test_existing_entry_cannot_be_updated():
    entry = log_action(actor=None, action="lead.created", entity="Lead", entity_id=1)
    entry.detail = "tampered"
    with pytest.raises(RuntimeError):
        entry.save()


def test_entry_cannot_be_deleted():
    entry = log_action(actor=None, action="lead.created", entity="Lead", entity_id=1)
    with pytest.raises(PermissionDenied):
        entry.delete()
