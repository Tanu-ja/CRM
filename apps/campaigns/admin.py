from django.contrib import admin

from .models import Campaign


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ["name", "client", "course", "commission_per_admission", "is_active"]
    list_filter = ["client", "is_active"]
    search_fields = ["name", "course"]
