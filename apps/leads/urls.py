from django.urls import path

from apps.admissions.views import add_admission
from apps.calls.views import add_call

from . import views

app_name = "leads"

urlpatterns = [
    path("", views.LeadListView.as_view(), name="list"),
    path("add/", views.LeadCreateView.as_view(), name="add"),
    path("followups/", views.followup_queue, name="followup_queue"),
    path("followups/<int:pk>/complete/", views.complete_followup, name="followup_complete"),
    path("<int:pk>/", views.LeadDetailView.as_view(), name="detail"),
    path("<int:pk>/update-status/", views.update_status, name="update_status"),
    path("<int:pk>/reassign/", views.reassign, name="reassign"),
    path("<int:pk>/followups/add/", views.add_followup, name="add_followup"),
    path("<int:lead_pk>/calls/add/", add_call, name="add_call"),
    path("<int:lead_pk>/admission/add/", add_admission, name="add_admission"),
]
