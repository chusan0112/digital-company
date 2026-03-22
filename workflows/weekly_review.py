"""Weekly review workflow."""

from company import get_company


def generate_weekly_report() -> dict:
    company = get_company()
    dashboard = company.get_dashboard()

    return {
        "summary": {
            "company": dashboard["company_name"],
            "projects_total": dashboard["projects"]["total"],
            "tasks_total": dashboard["tasks"]["total"],
            "tasks_completed": dashboard["tasks"]["completed"],
            "balance": dashboard["financial"]["balance"],
        },
        "focus_next_week": [
            "推进关键里程碑交付",
            "补齐高优先级岗位招聘",
            "跟踪预算执行偏差",
        ],
    }
