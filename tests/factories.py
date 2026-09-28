import factory

from apps.accounts.models import Role, User
from apps.campaigns.models import Campaign
from apps.clients.models import Client
from apps.leads.models import Lead
from apps.leads.services import next_lead_id


class ClientFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Client

    name = factory.Sequence(lambda n: f"Client {n}")
    code = factory.Sequence(lambda n: f"CLI{n}")
    commission_per_admission = 5000


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    role = Role.TELECALLER
    client = factory.SubFactory(ClientFactory)

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        self.set_password(extracted or "testpass123")
        if create:
            self.save()


class CampaignFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Campaign

    client = factory.SubFactory(ClientFactory)
    name = factory.Sequence(lambda n: f"Campaign {n}")


class LeadFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Lead

    client = factory.SubFactory(ClientFactory)
    phone = factory.Sequence(lambda n: f"90000{n:05d}")
    name = factory.Sequence(lambda n: f"Lead {n}")

    @factory.lazy_attribute
    def lead_id(self):
        return next_lead_id(self.client)
