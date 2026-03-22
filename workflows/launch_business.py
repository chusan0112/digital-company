"""Launch-new-business workflow."""

from datetime import datetime, timedelta

from domains.org_service import create_business_unit
from domains.hr_service import generate_hiring_plan
from domains.project_service import create_launch_project
from domains.finance_service import allocate_initial_budget
from domains.risk_service import evaluate_risks


def _build_t7_milestone_check(project_bundle: dict) -> dict:
    project = project_bundle.get("project", {})
    project_id = project.get("id", "")
    due_at = (datetime.now() + timedelta(days=7)).isoformat()
    return {
        "name": "T+7里程碑检查",
        "project_id": project_id,
        "due_at": due_at,
        "check_items": [
            "关键岗位到岗率",
            "里程碑任务启动率",
            "预算首期执行偏差",
            "风险处置状态",
        ],
    }


def execute_launch(decision_packet: dict) -> dict:
    intent = decision_packet.get("intent", {})
    policy = decision_packet.get("policy", {})
    business_name = intent.get("business_name", "新业务")
    budget_cap = int(intent.get("budget_cap") or 200000)

    unit = create_business_unit(name=f"{business_name}事业部")
    hiring_plan = generate_hiring_plan(business_name)
    project_bundle = create_launch_project(
        business_name=business_name,
        department_id=unit.get("id", ""),
        budget=budget_cap,
    )
    budget_plan = allocate_initial_budget(budget_cap)
    risks = evaluate_risks(intent)

    governance_controls = {
        "risk_level": policy.get("risk_level", "medium"),
        "suggested_action": policy.get("suggested_action", "proceed_with_controls"),
        "required_controls": [],
    }

    if policy.get("risk_level") == "high":
        governance_controls["required_controls"] = [
            "分阶段拨款（Stage-Gate）",
            "财务周审",
            "里程碑达成后再释放预算",
        ]

    t7_check = _build_t7_milestone_check(project_bundle)

    return {
        "business_unit": unit,
        "hiring_plan": hiring_plan,
        "project_bundle": project_bundle,
        "budget_plan": budget_plan,
        "risks": risks,
        "governance_controls": governance_controls,
        "milestone_checks": [t7_check],
    }
