import pytest
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404

from apps.accounts.models import Role
from apps.leads.models import Lead
from apps.leads.utils import normalize_phone
from tests.factories import ClientFactory, LeadFactory, UserFactory

pytestmark = pytest.mark.django_db


def test_super_admin_sees_every_lead():
    lead_a = LeadFactory()
    lead_b = LeadFactory()
    super_admin = UserFactory(role=Role.SUPER_ADMIN, client=None)

    visible = set(Lead.objects.visible_detail(super_admin).values_list("pk", flat=True))
    assert {lead_a.pk, lead_b.pk} <= visible


def test_client_admin_sees_only_their_client():
    client_a = ClientFactory()
    client_b = ClientFactory()
    lead_a = LeadFactory(client=client_a)
    LeadFactory(client=client_b)
    admin_a = UserFactory(role=Role.CLIENT_ADMIN, client=client_a)

    visible = Lead.objects.visible_detail(admin_a)
    assert list(visible) == [lead_a]


def test_telecaller_sees_only_own_assigned_leads():
    client = ClientFactory()
    telecaller = UserFactory(role=Role.TELECALLER, client=client)
    other_telecaller = UserFactory(role=Role.TELECALLER, client=client)
    own_lead = LeadFactory(client=client, assigned_to=telecaller)
    LeadFactory(client=client, assigned_to=other_telecaller)

    visible = Lead.objects.visible_detail(telecaller)
    assert list(visible) == [own_lead]


def test_telecaller_team_totals_are_counts_only_never_lead_objects():
    client = ClientFactory()
    telecaller = UserFactory(role=Role.TELECALLER, client=client)
    other_telecaller = UserFactory(role=Role.TELECALLER, client=client)
    LeadFactory(client=client, assigned_to=telecaller)
    LeadFactory.create_batch(2, client=client, assigned_to=other_telecaller)

    team_totals = list(
        Lead.objects.scoped_to_client(telecaller).values("assigned_to_id").annotate(count=Count("id"))
    )
    # Every row is a plain dict of id/count -- never a Lead instance a template could pull PII from.
    assert all(set(row.keys()) == {"assigned_to_id", "count"} for row in team_totals)


def test_cross_client_lead_lookup_404s_not_leaks():
    client_a = ClientFactory()
    client_b = ClientFactory()
    lead_b = LeadFactory(client=client_b)
    admin_a = UserFactory(role=Role.CLIENT_ADMIN, client=client_a)

    with pytest.raises(Http404):
        get_object_or_404(Lead.objects.visible_detail(admin_a), pk=lead_b.pk)


def test_duplicate_detection_is_scoped_within_a_client_not_across_clients():
    client_a = ClientFactory()
    client_b = ClientFactory()
    LeadFactory(client=client_a, phone="9876543210")
    LeadFactory(client=client_b, phone="9876543210")

    dupes_in_a = Lead.duplicate_query(client_a, normalize_phone("9876543210"))
    assert dupes_in_a.count() == 1
    assert dupes_in_a.first().client == client_a
