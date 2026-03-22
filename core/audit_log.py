"""Simple audit logging helper."""

from datetime import datetime

MAX_AUDIT_EVENTS = 1000  # 最大保留事件数量
_AUDIT_EVENTS = []


def log_event(action: str, actor: str, payload: dict = None):
    """记录审计事件，自动清理超过容量限制的旧事件"""
    _AUDIT_EVENTS.append(
        {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "actor": actor,
            "payload": payload or {},
        }
    )
    # 自动清理：保留最近 MAX_AUDIT_EVENTS 条
    if len(_AUDIT_EVENTS) > MAX_AUDIT_EVENTS:
        _AUDIT_EVENTS[:] = _AUDIT_EVENTS[-MAX_AUDIT_EVENTS:]


def list_events(limit: int = 50):
    """获取最近的审计事件"""
    if limit <= 0:
        return []
    return _AUDIT_EVENTS[-limit:]


def get_total_count() -> int:
    """获取当前审计事件总数"""
    return len(_AUDIT_EVENTS)


def clear_events():
    """清空所有审计事件（用于测试）"""
    _AUDIT_EVENTS.clear()
