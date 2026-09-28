from django import forms

from .models import Admission


class AdmissionForm(forms.ModelForm):
    class Meta:
        model = Admission
        fields = [
            "student_name",
            "admission_phone",
            "alternate_phone",
            "guardian_phone",
            "course",
            "admission_date",
            "admission_number",
            "amount",
            "status",
        ]
        widgets = {"admission_date": forms.DateInput(attrs={"type": "date"})}
