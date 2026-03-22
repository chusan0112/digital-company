"""COO executive advisor."""


def evaluate(intent_payload: dict) -> dict:
    deadline = intent_payload.get("deadline", "T+90d")
    return {
        "role": "COO",
        "feasibility": 0.78,
        "risks": ["执行排期受资源调度影响"],
        "recommendations": [f"按双周里程碑推进，目标截止{deadline}"],
    }
