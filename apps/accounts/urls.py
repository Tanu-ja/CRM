from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.EmailLoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path(
        "password/change/",
        auth_views.PasswordChangeView.as_view(template_name="accounts/password_change.html"),
        name="password_change",
    ),
    path(
        "password/change/done/",
        auth_views.PasswordChangeDoneView.as_view(template_name="accounts/password_change_done.html"),
        name="password_change_done",
    ),
    path("users/", views.StaffListView.as_view(), name="staff_list"),
    path("users/add/", views.StaffCreateView.as_view(), name="staff_add"),
    path("users/<int:pk>/toggle-active/", views.staff_toggle_active, name="staff_toggle_active"),
    path("users/<int:pk>/reset-password/", views.staff_reset_password, name="staff_reset_password"),
]
