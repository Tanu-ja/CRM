import pytest

from apps.admissions.models import Admission, AdmissionStatus
from apps.campaigns.models import Campaign
from tests.factories import LeadFactory

pytestmark = pytest.mark.django_db


def _make_admission(status, commission_rate=5000):
    lead = LeadFactory()
    lead.client.commission_per_admission = commission_rate
    lead.client.save()
    return Admission.objects.create(
        lead=lead,
        admission_phone=lead.phone,
        admission_number=f"ADM-{lead.pk}",
        amount=10000,
        status=status,
    )


def test_commission_is_zero_when_pending():
    admission = _make_admission(AdmissionStatus.PENDING)
    assert admission.commission == 0


def test_commission_equals_client_rate_when_confirmed():
    admission = _make_admission(AdmissionStatus.CONFIRMED, commission_rate=4500)
    assert admission.commission == 4500


def test_commission_resets_to_zero_when_rejected_after_being_confirmed():
    admission = _make_admission(AdmissionStatus.CONFIRMED, commission_rate=3000)
    assert admission.commission == 3000
    admission.status = AdmissionStatus.REJECTED
    admission.save()
    assert admission.commission == 0


def test_campaign_commission_overrides_client_commission():
    lead = LeadFactory()
    lead.client.commission_per_admission = 5000
    lead.client.save()
    campaign = Campaign.objects.create(client=lead.client, name="Special Drive", commission_per_admission=7000)
    lead.campaign = campaign
    lead.save()

    admission = Admission.objects.create(
        lead=lead,
        admission_phone=lead.phone,
        admission_number=f"ADM-{lead.pk}",
        amount=10000,
        status=AdmissionStatus.CONFIRMED,
    )
    assert admission.commission == 7000
