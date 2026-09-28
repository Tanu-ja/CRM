from django import forms
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm
from django.utils.translation import gettext_lazy as _

from .models import Role, User


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label=_("Email"))


class StaffCreateForm(forms.ModelForm):
    """Used by both Super Admin (creating a Client Manager) and a Client
    Manager (creating a Telecaller) — `role` choices and `client` field are
    narrowed by the view based on who's submitting it."""

    password = forms.CharField(widget=forms.PasswordInput, min_length=8)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "role", "client", "employee_id", "phone"]

    def __init__(self, *args, actor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.actor = actor
        if actor and actor.is_client_admin:
            self.fields["role"].choices = [(Role.TELECALLER, Role.TELECALLER.label)]
            self.fields["client"].initial = actor.client
            self.fields["client"].widget = forms.HiddenInput()
        elif actor and actor.is_super_admin:
            self.fields["role"].choices = [
                (Role.CLIENT_ADMIN, Role.CLIENT_ADMIN.label),
                (Role.TELECALLER, Role.TELECALLER.label),
            ]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if self.actor and self.actor.is_client_admin:
            user.client = self.actor.client
        if commit:
            user.save()
        return user


class AdminSetPasswordForm(SetPasswordForm):
    """Wraps Django's SetPasswordForm; the view is responsible for calling
    `target.mark_sessions_stale()` after save so the reset also logs the
    target out of any other active session."""
