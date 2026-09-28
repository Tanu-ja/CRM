from django import forms

from .models import Campaign


class CampaignForm(forms.ModelForm):
    class Meta:
        model = Campaign
        fields = ["client", "name", "course", "commission_per_admission", "is_active"]

    def __init__(self, *args, actor=None, **kwargs):
        super().__init__(*args, **kwargs)
        if actor and actor.is_client_admin:
            self.fields["client"].initial = actor.client
            self.fields["client"].widget = forms.HiddenInput()
