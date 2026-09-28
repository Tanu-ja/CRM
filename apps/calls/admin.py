from django.contrib import admin

from .models import Call


@admin.register(Call)
class CallAdmin(admin.ModelAdmin):
    list_display = ["lead", "staff", "outcome", "duration_seconds", "created_at"]
    list_filter = ["outcome"]
    readonly_fields = [f.name for f in Call._meta.fields]

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
