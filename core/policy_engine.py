"""Governance policy engine for approval boundaries."""

import json
import os


DEFAULT_CONFIG = {
    "approval": {
        "budget_threshold": 200000,
        "high_risk_budget_threshold": 500000,
        "always_require_approval_intents": ["launch_new_business"],
    }
}


def _load_governance_config() -> dict:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(root, "governance_config.json")

    if not os.path.exists(config_path):
        return DEFAULT_CONFIG

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
    except Exception:
        pass

    return DEFAULT_CONFIG


def evaluate_policy(intent_payload: dict) -> dict:
    """Return governance decision for incoming intent."""
    cfg = _load_governance_config().get("approval", {})

    budget_threshold = int(cfg.get("budget_threshold", 200000))
    high_risk_budget_threshold = int(cfg.get("high_risk_budget_threshold", 500000))
    always_approval_intents = set(cfg.get("always_require_approval_intents", ["launch_new_business"]))

    budget_cap = int(intent_payload.get("budget_cap") or 0)
    intent = intent_payload.get("intent", "unknown")

    requires_approval = bool(intent_payload.get("requires_approval", True))
    reasons = []

    if intent in always_approval_intents:
        requires_approval = True
        reasons.append("intent_requires_board_approval")

    if budget_cap > budget_threshold:
        requires_approval = True
        reasons.append("budget_above_threshold")

    risk_level = "medium"
    if budget_cap > high_risk_budget_threshold:
        risk_level = "high"

    reason_messages_map = {
        "intent_requires_board_approval": "该事项属于公司级战略动作，必须提交董事长审批。",
        "budget_above_threshold": f"预算超过阈值（{budget_threshold}元），需走审批流程。",
    }
    reason_messages = [reason_messages_map.get(r, r) for r in reasons]

    suggested_action = "proceed_with_controls"
    if risk_level == "high":
        suggested_action = "require_stage_gate_and_finance_review"

    return {
        "requires_approval": requires_approval,
        "risk_level": risk_level,
        "policy_reasons": reasons,
        "policy_reason_messages": reason_messages,
        "suggested_action": suggested_action,
        "policy_config": {
            "budget_threshold": budget_threshold,
            "high_risk_budget_threshold": high_risk_budget_threshold,
        },
    }
