"""Approval center with JSON persistence."""

from datetime import datetime
import uuid

from storage.repository import upsert_approval, get_approval as repo_get_approval


def create_approval(title: str, payload: dict, governance_conditions: list = None) -> dict:
    approval_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    record = {
        "id": approval_id,
        "title": title,
        "status": "pending",
        "payload": payload,
        "governance_conditions": governance_conditions or [],  # P0-3: 结构化存储
        "created_at": now,
        "updated_at": now,
        "comments": "",
    }
    upsert_approval(record)
    return record


def get_approval(approval_id: str) -> dict:
    return repo_get_approval(approval_id)


def approve(approval_id: str, comments: str = "", governance_conditions: list = None) -> dict:
    item = repo_get_approval(approval_id)
    if not item:
        return {"success": False, "error": "approval_not_found"}

    item["status"] = "approved"
    item["comments"] = comments
    # P0-3: 结构化落库，不拼接字符串
    if governance_conditions:
        item["governance_conditions"] = governance_conditions
    elif "governance_conditions" not in item:
        item["governance_conditions"] = []
    item["updated_at"] = datetime.now().isoformat()
    upsert_approval(item)
    return {"success": True, "approval": item}


def reject(approval_id: str, comments: str = "") -> dict:
    item = repo_get_approval(approval_id)
    if not item:
        return {"success": False, "error": "approval_not_found"}

    item["status"] = "rejected"
    item["comments"] = comments
    item["updated_at"] = datetime.now().isoformat()
    upsert_approval(item)
    return {"success": True, "approval": item}
