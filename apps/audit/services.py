from .models import AuditLog


def log_action(*, actor, action, entity, entity_id, old_value=None, new_value=None, detail=""):
    """The only sanctioned way to write an AuditLog row — keeps every
    caller's shape consistent and the immutability guarantee centralized."""
    return AuditLog.objects.create(
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        action=action,
        entity=entity,
        entity_id=str(entity_id),
        old_value=old_value,
        new_value=new_value,
        detail=detail,
    )
