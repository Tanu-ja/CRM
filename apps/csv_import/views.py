from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.generic import ListView

from apps.accounts.models import Role
from apps.core.mixins import RoleRequiredMixin

from .forms import CsvUploadForm
from .models import ImportBatch
from .services import CsvImportError, process_csv


class ImportUploadView(RoleRequiredMixin, ListView):
    """Combines the upload form with a peek at recent batches on one page."""

    allowed_roles = (Role.SUPER_ADMIN,)
    model = ImportBatch
    template_name = "csv_import/upload.html"
    context_object_name = "recent_batches"
    queryset = ImportBatch.objects.select_related("client", "uploaded_by")[:10]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = CsvUploadForm()
        return ctx

    def post(self, request, *args, **kwargs):
        form = CsvUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                batch = process_csv(
                    file_obj=form.cleaned_data["file"].file,
                    client=form.cleaned_data["client"],
                    uploaded_by=request.user,
                    filename=form.cleaned_data["file"].name,
                )
                messages.success(
                    request,
                    f"Import complete: {batch.created_count} created, "
                    f"{batch.duplicate_count} duplicates, {batch.invalid_count} invalid.",
                )
                return redirect("csv_import:history")
            except CsvImportError as exc:
                messages.error(request, str(exc))
        else:
            messages.error(request, "Please correct the errors below.")
        return render(request, self.template_name, {"form": form, "recent_batches": self.get_queryset()})


class ImportHistoryView(RoleRequiredMixin, ListView):
    allowed_roles = (Role.SUPER_ADMIN,)
    model = ImportBatch
    template_name = "csv_import/history.html"
    context_object_name = "batches"
    paginate_by = 25
    queryset = ImportBatch.objects.select_related("client", "uploaded_by")
