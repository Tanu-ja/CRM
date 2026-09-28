from django.urls import path

from . import views

app_name = "csv_import"

urlpatterns = [
    path("", views.ImportUploadView.as_view(), name="upload"),
    path("history/", views.ImportHistoryView.as_view(), name="history"),
]
