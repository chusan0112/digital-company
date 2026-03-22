"""Chairman command orchestration."""

from datetime import datetime
import uuid

from core.intent_parser import parse_chairman_command
from core.policy_engine import evaluate_policy
from core.approval_center import create_approval, get_approval
from core.audit_log import log_event
from storage.repository import upsert_decision, get_decision as repo_get_decision

from executives.ceo import evaluate as ceo_evaluate
from executives.cfo import evaluate as cfo_evaluate
from executives.cto import evaluate as cto_evaluate
from executives.coo import evaluate as coo_evaluate
from executives.chro import evaluate as chro_evaluate

from workflows.launch_business import execute_launch
from workflows.weekly_review import generate_weekly_report


def _build_options(intent_payload: dict) -> list:
    budget = int(intent_payload.get("budget_cap") or 200000)
    return [
        {"name": "保守方案", "budget": int(budget * 0.5), "timeline": "T+120d"},
        {"name": "平衡方案", "budget": int(budget * 0.8), "timeline": "T+90d", "recommended": True},
        {"name": "激进方案", "budget": budget, "timeline": "T+60d"},
    ]


def _build_summary(intent_payload: dict, policy: dict, executive_panel: list, options: list) -> dict:
    best_option = None
    for option in options:
        if option.get("recommended"):
            best_option = option
            break
    if not best_option and options:
        best_option = options[0]

    avg_feasibility = 0.0
    if executive_panel:
        avg_feasibility = round(sum(float(x.get("feasibility", 0)) for x in executive_panel) / len(executive_panel), 2)

    auto_execute_recommended = (
        policy.get("risk_level") != "high"
        and avg_feasibility >= 0.75
        and not policy.get("requires_approval", True)
    )

    return {
        "title": f"{intent_payload.get('business_name', '新业务')}立项建议",
        "intent": intent_payload.get("intent"),
        "priority": intent_payload.get("priority", "medium"),
        "budget_cap": intent_payload.get("budget_cap"),
        "deadline": intent_payload.get("deadline"),
        "risk_level": policy.get("risk_level", "unknown"),
        "requires_approval": policy.get("requires_approval", True),
        "policy_reason_messages": policy.get("policy_reason_messages", []),
        "suggested_action": policy.get("suggested_action", "proceed_with_controls"),
        "avg_feasibility": avg_feasibility,
        "recommended_option": best_option,
        "recommended_to_execute_now": auto_execute_recommended,
        "executive_consensus": [
            {
                "role": x.get("role"),
                "feasibility": x.get("feasibility"),
                "top_risk": (x.get("risks") or [None])[0],
            }
            for x in executive_panel
        ],
    }


def _build_decision_packet(command_text: str) -> dict:
    intent_payload = parse_chairman_command(command_text)
    policy = evaluate_policy(intent_payload)

    executive_panel = [
        ceo_evaluate(intent_payload),
        cfo_evaluate(intent_payload),
        cto_evaluate(intent_payload),
        coo_evaluate(intent_payload),
        chro_evaluate(intent_payload),
    ]

    options = _build_options(intent_payload)

    decision_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    return {
        "id": decision_id,
        "created_at": now,
        "updated_at": now,
        "intent": intent_payload,
        "policy": policy,
        "executive_panel": executive_panel,
        "options": options,
        "summary": _build_summary(intent_payload, policy, executive_panel, options),
        "status": "pending_approval" if policy.get("requires_approval") else "approved",
    }


def preview_chairman_command(command_text: str) -> dict:
    """Build decision packet for preview without persistence side effects."""
    decision_packet = _build_decision_packet(command_text)
    decision_packet["preview"] = True
    decision_packet["id"] = "preview-" + decision_packet["id"]
    return decision_packet


def submit_chairman_command(command_text: str) -> dict:
    decision_packet = _build_decision_packet(command_text)

    policy = decision_packet.get("policy", {})
    intent_payload = decision_packet.get("intent", {})

    if policy.get("requires_approval"):
        approval = create_approval(
            title=f"立项审批: {intent_payload.get('business_name', '新业务')}",
            payload=decision_packet,
        )
        decision_packet["approval_id"] = approval["id"]

    upsert_decision(decision_packet)
    log_event("submit_command", "chairman", {"decision_id": decision_packet.get("id")})

    return decision_packet


def get_decision(decision_id: str) -> dict:
    return repo_get_decision(decision_id)


def approve_and_execute(approval_id: str, comments: str = "") -> dict:
    approval = get_approval(approval_id)
    if not approval:
        return {"success": False, "error": "approval_not_found"}

    decision_packet = approval.get("payload", {})
    intent_name = decision_packet.get("intent", {}).get("intent")

    result = {}
    if intent_name == "launch_new_business":
        result = execute_launch(decision_packet)
    elif intent_name == "weekly_review":
        result = generate_weekly_report()

    decision_packet["status"] = "executed"
    decision_packet["execution_result"] = result
    decision_packet["updated_at"] = datetime.now().isoformat()
    upsert_decision(decision_packet)

    log_event("approve_and_execute", "chairman", {"approval_id": approval_id})

    return {
        "success": True,
        "approval_id": approval_id,
        "execution_result": result,
    }
