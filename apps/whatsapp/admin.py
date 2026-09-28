from django.contrib import admin

from .models import WhatsAppInboundMessage


@admin.register(WhatsAppInboundMessage)
class WhatsAppInboundMessageAdmin(admin.ModelAdmin):
    list_display = ["message_id", "from_number", "received_at", "processed", "lead"]
    list_filter = ["processed"]
