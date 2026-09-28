import json

from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView

from apps.accounts.models import Role
from apps.core.mixins import RoleRequiredMixin

from .models import WhatsAppInboundMessage


class WhatsAppInboxView(RoleRequiredMixin, ListView):
    allowed_roles = (Role.SUPER_ADMIN,)
    model = WhatsAppInboundMessage
    template_name = "whatsapp/inbox.html"
    context_object_name = "messages_list"
    paginate_by = 25


@csrf_exempt
def webhook(request):
    if request.method == "GET":
        # Meta webhook verification handshake.
        if request.GET.get("hub.verify_token") == settings.WHATSAPP_VERIFY_TOKEN:
            return HttpResponse(request.GET.get("hub.challenge", ""))
        return HttpResponseForbidden()

    if request.method == "POST":
        payload = json.loads(request.body or "{}")
        message_id = payload.get("message_id") or payload.get("id")
        if message_id and not WhatsAppInboundMessage.objects.filter(message_id=message_id).exists():
            WhatsAppInboundMessage.objects.create(
                message_id=message_id,
                from_number=payload.get("from", ""),
                text=payload.get("text", ""),
                raw_payload=payload,
            )
        # Idempotent either way — Meta retries on anything but a 200.
        return JsonResponse({"status": "ok"})

    return HttpResponseForbidden()
