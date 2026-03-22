"""CFO executive advisor."""


def evaluate(intent_payload: dict) -> dict:
    budget = int(intent_payload.get("budget_cap") or 0)
    return {
        "role": "CFO",
        "feasibility": 0.72,
        "risks": ["前期投入回收周期不确定"],
        "recommendations": [f"建议分阶段拨付预算，首期拨付不超过{min(200000, budget)}元"],
    }
