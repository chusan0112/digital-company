"""CTO executive advisor."""


def evaluate(intent_payload: dict) -> dict:
    business = intent_payload.get("business_name", "新业务")
    return {
        "role": "CTO",
        "feasibility": 0.76,
        "risks": ["关键技术能力尚需补齐"],
        "recommendations": [f"先组建{business}技术小组，完成基础架构验证"],
    }
