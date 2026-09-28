from django.contrib import admin

from .models import FollowUp, Lead, LeadCounter


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ["lead_id", "name", "phone", "client", "status", "temperature", "assigned_to", "created_at"]
    list_filter = ["client", "status", "temperature"]
    search_fields = ["lead_id", "name", "phone", "email"]
    readonly_fields = ["lead_id", "phone_normalized", "whatsapp_phone_normalized", "alternate_phone_normalized"]


@admin.register(FollowUp)
class FollowUpAdmin(admin.ModelAdmin):
    list_display = ["lead", "scheduled_at", "type", "status", "assigned_to"]
    list_filter = ["status", "type"]


@admin.register(LeadCounter)
class LeadCounterAdmin(admin.ModelAdmin):
    list_display = ["client", "year", "last_sequence"]
