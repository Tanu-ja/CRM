from django.urls import path

from . import views

app_name = "admissions"

urlpatterns = [
    path("", views.AdmissionListView.as_view(), name="list"),
]
