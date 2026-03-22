"""Simple JSON repository for governance data persistence."""

import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, "storage", "governance_data.json")


def _default_data() -> dict:
    return {
        "version": 1,
        "updated_at": datetime.now().isoformat(),
        "decisions": {},
        "approvals": {},
    }


def load_governance_data() -> dict:
    if not os.path.exists(DATA_FILE):
        return _default_data()

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return _default_data()
        data.setdefault("decisions", {})
        data.setdefault("approvals", {})
        data.setdefault("version", 1)
        data.setdefault("updated_at", datetime.now().isoformat())
        return data
    except Exception:
        return _default_data()


def save_governance_data(data: dict):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    data["updated_at"] = datetime.now().isoformat()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def upsert_decision(decision: dict):
    data = load_governance_data()
    decisions = data.get("decisions", {})
    decisions[decision["id"]] = decision
    data["decisions"] = decisions
    save_governance_data(data)


def get_decision(decision_id: str):
    data = load_governance_data()
    return data.get("decisions", {}).get(decision_id)


def list_recent_decisions(limit: int = 10):
    data = load_governance_data()
    items = list(data.get("decisions", {}).values())
    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return items[:limit]


def upsert_approval(approval: dict):
    data = load_governance_data()
    approvals = data.get("approvals", {})
    approvals[approval["id"]] = approval
    data["approvals"] = approvals
    save_governance_data(data)


def get_approval(approval_id: str):
    data = load_governance_data()
    return data.get("approvals", {}).get(approval_id)


def list_recent_approvals(limit: int = 10):
    data = load_governance_data()
    items = list(data.get("approvals", {}).values())
    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return items[:limit]
