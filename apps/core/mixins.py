"""
Reusable view-layer guards. A CBV uses `RoleRequiredMixin`; an FBV uses the
`role_required` decorator. Both share `_role_allowed` so the two entry points
can never drift apart.
"""

from functools import wraps

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404


def _role_allowed(user, allowed_roles) -> bool:
    return user.is_authenticated and user.role in allowed_roles


def role_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not _role_allowed(request.user, allowed_roles):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator


class RoleRequiredMixin(LoginRequiredMixin):
    allowed_roles: tuple = ()

    def get(self, request, *args, **kwargs):
        if not _role_allowed(request.user, self.allowed_roles):
            raise PermissionDenied
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if not _role_allowed(request.user, self.allowed_roles):
            raise PermissionDenied
        return super().post(request, *args, **kwargs)


class ScopedQuerysetMixin:
    """
    For ListView/DetailView on a tenant-scoped model whose manager exposes
    `visible_detail(user)`. An out-of-scope pk correctly 404s (not 403),
    since `get_object_or_404` filters against the already-scoped queryset.
    """

    def get_queryset(self):
        return self.model.objects.visible_detail(self.request.user)

    def get_object(self, queryset=None):
        queryset = queryset or self.get_queryset()
        return get_object_or_404(queryset, pk=self.kwargs["pk"])
