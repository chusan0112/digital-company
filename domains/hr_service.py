"""HR domain service."""


def generate_hiring_plan(business_name: str) -> list:
    return [
        {"role": f"{business_name}项目经理", "count": 1, "priority": "high"},
        {"role": f"{business_name}研究员", "count": 2, "priority": "high"},
        {"role": f"{business_name}运营专员", "count": 1, "priority": "medium"},
    ]
