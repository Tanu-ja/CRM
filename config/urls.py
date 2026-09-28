from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from apps.whatsapp.views import webhook as whatsapp_webhook

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", RedirectView.as_view(pattern_name="dashboard:home", permanent=False)),
    path("", include("apps.accounts.urls", namespace="accounts")),
    path("clients/", include("apps.clients.urls", namespace="clients")),
    path("campaigns/", include("apps.campaigns.urls", namespace="campaigns")),
    path("leads/", include("apps.leads.urls", namespace="leads")),
    path("admissions/", include("apps.admissions.urls", namespace="admissions")),
    path("dashboard/", include("apps.dashboard.urls", namespace="dashboard")),
    path("audit/", include("apps.audit.urls", namespace="audit")),
    path("import/", include("apps.csv_import.urls", namespace="csv_import")),
    path("whatsapp/", include("apps.whatsapp.urls", namespace="whatsapp")),
    path("webhooks/whatsapp/", whatsapp_webhook, name="whatsapp_webhook"),
]
