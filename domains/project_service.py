"""Project domain service."""

from company import get_company


def create_launch_project(business_name: str, department_id: str, budget: int) -> dict:
    company = get_company()
    project = company.create_project(
        name=f"{business_name}试点项目",
        description=f"{business_name}从0到1试点落地",
        department_id=department_id,
        budget=budget,
    )

    milestones = [
        "完成市场与竞品分析",
        "完成技术架构与数据方案",
        "完成MVP并启动试运行",
    ]

    tasks = []
    for i, milestone in enumerate(milestones, start=1):
        task = company.create_task(
            name=f"里程碑{i}: {milestone}",
            description=milestone,
            project_id=project.id,
            priority=1,
        )
        tasks.append(task.to_dict())

    return {
        "project": project.to_dict(),
        "milestones": milestones,
        "tasks": tasks,
    }
