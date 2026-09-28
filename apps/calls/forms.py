from django import forms

from .models import Call


class CallForm(forms.ModelForm):
    """Duration is deliberately excluded — the lead-detail template supplies
    it via a hidden field bound to the Alpine.js call-timer, not a visible
    form field, so there is only ever one source of truth for it."""

    class Meta:
        model = Call
        fields = ["outcome", "remarks"]
