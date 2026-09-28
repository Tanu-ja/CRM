from django import forms

from apps.accounts.models import Role, User
from apps.campaigns.models import Campaign

from .models import FollowUp, Lead


class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = [
            "campaign",
            "name",
            "phone",
            "whatsapp_phone",
            "alternate_phone",
            "email",
            "temperature",
            "original_source",
            "original_campaign",
            "original_ad",
            "original_ad_set",
            "assigned_to",
        ]

    def __init__(self, *args, actor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.actor = actor
        if actor is not None:
            client = actor.client
            self.fields["campaign"].queryset = Campaign.objects.filter(client=client)
            self.fields["assigned_to"].queryset = User.objects.filter(client=client, role=Role.TELECALLER)
            if actor.is_telecaller:
                self.fields["assigned_to"].initial = actor
                self.fields["assigned_to"].widget = forms.HiddenInput()


class LeadStatusForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ["status", "temperature"]


class LeadReassignForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ["assigned_to"]

    def __init__(self, *args, client=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assigned_to"].queryset = User.objects.filter(client=client, role=Role.TELECALLER)


class FollowUpForm(forms.ModelForm):
    class Meta:
        model = FollowUp
        fields = ["scheduled_at", "type", "note", "assigned_to"]
        widgets = {"scheduled_at": forms.DateTimeInput(attrs={"type": "datetime-local"})}

    def __init__(self, *args, client=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assigned_to"].queryset = User.objects.filter(client=client, role=Role.TELECALLER)
