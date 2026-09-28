from django.contrib import admin

from .models import ImportBatch


@admin.register(ImportBatch)
class ImportBatchAdmin(admin.ModelAdmin):
    list_display = ["filename", "client", "row_count", "created_count", "duplicate_count", "invalid_count", "created_at"]
    list_filter = ["client"]
