"""Simple audit logging helper."""

from datetime import datetime

_AUDIT_EVENTS = []


def log_event(action: str, actor: str, payload: dict = None):
    _AUDIT_EVENTS.append(
        {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "actor": actor,
            "payload": payload or {},
        }
    )


def list_events(limit: int = 50):
    if limit <= 0:
        return []
    return _AUDIT_EVENTS[-limit:]
