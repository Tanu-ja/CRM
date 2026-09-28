from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.utils import timezone


@receiver(user_logged_in)
def stamp_login_time(sender, request, user, **kwargs):
    """Record when this session started, so SessionValidAfterMiddleware can
    tell whether it predates a later forced password reset."""
    request.session["login_at"] = timezone.now().isoformat()
