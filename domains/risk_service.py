"""Risk domain service."""


def evaluate_risks(intent_payload: dict) -> list:
    business_name = intent_payload.get("business_name", "新业务")
    risks = [
        {"type": "execution", "level": "medium", "message": f"{business_name}跨部门协同复杂"},
        {"type": "talent", "level": "medium", "message": "关键岗位招聘周期不确定"},
    ]

    if int(intent_payload.get("budget_cap") or 0) > 500000:
        risks.append({"type": "financial", "level": "high", "message": "预算体量较大，需加强阶段审计"})

    return risks
