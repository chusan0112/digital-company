"""CEO executive advisor."""


def evaluate(intent_payload: dict) -> dict:
    business = intent_payload.get("business_name", "新业务")
    return {
        "role": "CEO",
        "feasibility": 0.8,
        "risks": ["跨部门协同复杂度上升"],
        "recommendations": [f"建议以90天试点方式启动{business}"],
    }
