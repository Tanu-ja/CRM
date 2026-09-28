from django.urls import path

from . import views

app_name = "whatsapp"

urlpatterns = [
    path("", views.WhatsAppInboxView.as_view(), name="inbox"),
]
