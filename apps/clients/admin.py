from django.contrib import admin

from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "commission_per_admission", "is_active", "created_at"]
    search_fields = ["name", "code"]
    list_filter = ["is_active"]
