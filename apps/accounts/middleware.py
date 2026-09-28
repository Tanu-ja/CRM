from django.contrib.auth import logout
from django.utils.dateparse import parse_datetime


class SessionValidAfterMiddleware:
    """
    Forces logout of any session established before the user's
    `session_valid_after` timestamp — i.e. before an admin last reset their
    password. Stock Django session auth has no user-indexed session store,
    so this is the mechanism that makes "reset password" also end that
    user's other active sessions.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            login_at_raw = request.session.get("login_at")
            login_at = parse_datetime(login_at_raw) if login_at_raw else None
            if login_at is None or login_at < user.session_valid_after:
                logout(request)
        return self.get_response(request)
