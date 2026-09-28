"""
Central place for role-check predicates. Every permission decision in the
project should route through here (or through the queryset methods in each
app's managers.py) rather than inline ``if role == ...`` checks scattered
across views/templates.
"""

from apps.accounts.models import Role


def is_super_admin(user) -> bool:
    return user.is_authenticated and user.role == Role.SUPER_ADMIN


def is_client_admin(user) -> bool:
    return user.is_authenticated and user.role == Role.CLIENT_ADMIN


def is_telecaller(user) -> bool:
    return user.is_authenticated and user.role == Role.TELECALLER


def can_manage_client_staff(actor, target_client) -> bool:
    """Can `actor` add/disable/reset-password for staff of `target_client`?"""
    if not actor.is_authenticated:
        return False
    if actor.role == Role.SUPER_ADMIN:
        return True
    if actor.role == Role.CLIENT_ADMIN:
        return actor.client_id == getattr(target_client, "id", target_client)
    return False


def can_reset_password(actor, target) -> bool:
    """Can `actor` reset `target` user's password?"""
    if not actor.is_authenticated:
        return False
    if actor.role == Role.SUPER_ADMIN:
        return target.role in (Role.CLIENT_ADMIN, Role.TELECALLER)
    if actor.role == Role.CLIENT_ADMIN:
        return target.role == Role.TELECALLER and target.client_id == actor.client_id
    return False


def can_manage_clients(actor) -> bool:
    return is_super_admin(actor)


def can_import_csv(actor) -> bool:
    return is_super_admin(actor)


def can_access_whatsapp(actor) -> bool:
    return is_super_admin(actor)
