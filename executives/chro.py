"""CHRO executive advisor."""


def evaluate(intent_payload: dict) -> dict:
    business = intent_payload.get("business_name", "新业务")
    return {
        "role": "CHRO",
        "feasibility": 0.74,
        "risks": ["关键岗位招聘周期不确定"],
        "recommendations": [f"先确定{business}岗位编制，再分批招聘"],
    }
