"""Finance domain service."""


def allocate_initial_budget(budget_cap: int) -> dict:
    phase1 = min(200000, budget_cap)
    reserve = max(0, budget_cap - phase1)
    return {
        "budget_cap": budget_cap,
        "phase1_release": phase1,
        "reserve": reserve,
        "rule": "分阶段拨付，里程碑达成后解锁后续预算",
    }
