from django import forms

from apps.clients.models import Client


class CsvUploadForm(forms.Form):
    client = forms.ModelChoiceField(queryset=Client.objects.filter(is_active=True))
    file = forms.FileField()

    def clean_file(self):
        file = self.cleaned_data["file"]
        if not file.name.lower().endswith(".csv"):
            raise forms.ValidationError("Please upload a .csv file.")
        return file
