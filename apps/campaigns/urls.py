from django.urls import path

from . import views

app_name = "campaigns"

urlpatterns = [
    path("", views.CampaignListView.as_view(), name="list"),
    path("add/", views.CampaignCreateView.as_view(), name="add"),
]
