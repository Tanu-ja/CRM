from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="home"),
    path("kpi-fragment/", views.kpi_fragment, name="kpi_fragment"),
]
