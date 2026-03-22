"""周报生成工作流"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
from company import get_company


def get_week_range() -> tuple:
    """获取本周的日期范围（周一到周日）"""
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    return start_of_week, end_of_week


def get_employee_status_summary(company) -> Dict[str, Any]:
    """获取员工状态汇总"""
    employees = company.list_employees()
    status_count = {
        "working": 0,
        "idle": 0,
        "meeting": 0
    }
    
    dept_count = {}
    for emp in employees:
        status_count[emp.status] = status_count.get(emp.status, 0) + 1
        dept = emp.department_id
        if dept not in dept_count:
            dept_count[dept] = {"total": 0, "working": 0, "idle": 0}
        dept_count[dept]["total"] += 1
        if emp.status == "working":
            dept_count[dept]["working"] += 1
        elif emp.status == "idle":
            dept_count[dept]["idle"] += 1
    
    return {
        "total": len(employees),
        "status": status_count,
        "by_department": dept_count
    }


def get_project_summary(company) -> Dict[str, Any]:
    """获取项目状态汇总"""
    projects = company.list_projects()
    
    status_count = {
        "planning": 0,
        "running": 0,
        "completed": 0,
        "on_hold": 0
    }
    
    total_progress = 0
    total_budget = 0
    
    project_list = []
    for p in projects:
        status_count[p.status] = status_count.get(p.status, 0) + 1
        total_progress += p.progress
        total_budget += p.budget
        project_list.append({
            "id": p.id,
            "name": p.name,
            "status": p.status,
            "priority": p.priority,
            "progress": p.progress,
            "budget": p.budget
        })
    
    avg_progress = total_progress / len(projects) if projects else 0
    
    return {
        "total": len(projects),
        "status": status_count,
        "average_progress": round(avg_progress, 1),
        "total_budget": total_budget,
        "projects": project_list
    }


def get_task_summary(company) -> Dict[str, Any]:
    """获取任务状态汇总"""
    tasks = company.list_tasks()
    
    status_count = {
        "pending": 0,
        "in_progress": 0,
        "completed": 0
    }
    
    priority_count = {1: 0, 2: 0, 3: 0}
    
    for t in tasks:
        status_count[t.status] = status_count.get(t.status, 0) + 1
        priority_count[t.priority] = priority_count.get(t.priority, 0) + 1
    
    return {
        "total": len(tasks),
        "status": status_count,
        "priority": priority_count,
        "completion_rate": round(status_count["completed"] / len(tasks) * 100, 1) if tasks else 0
    }


def get_financial_summary(company) -> Dict[str, Any]:
    """获取财务状况汇总"""
    return {
        "budget": company.budget,
        "spent": company.spent,
        "balance": company.get_balance(),
        "usage_rate": round(company.spent / company.budget * 100, 1) if company.budget > 0 else 0
    }


def generate_markdown_report(data: dict) -> str:
    """生成 Markdown 格式的周报"""
    start_date, end_date = get_week_range()
    
    md = f"""# 📊 周报 - {data['company_name']}

**报告周期**: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}  
**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 📈 一、核心指标概览

| 指标 | 数值 |
|------|------|
| 员工总数 | {data['employee']['total']} 人 |
| 项目总数 | {data['project']['total']} 个 |
| 任务总数 | {data['task']['total']} 个 |
| 资金余额 | ¥{data['financial']['balance']:.2f} |

---

## 👥 二、员工状态

### 2.1 整体状态

| 状态 | 人数 |
|------|------|
| 🟢工作中 | {data['employee']['status']['working']} 人 |
| 🟡空闲 | {data['employee']['status']['idle']} 人 |
| 🔵会议中 | {data['employee']['status']['meeting']} 人 |

### 2.2 部门分布

| 部门 | 总人数 | 工作中 | 空闲 |
|------|--------|--------|------|
"""
    
    for dept, stats in data['employee']['by_department'].items():
        md += f"| {dept} | {stats['total']} | {stats['working']} | {stats['idle']} |\n"
    
    md += f"""
---

## 📁 三、项目进度

### 3.1 项目概览

| 状态 | 数量 |
|------|------|
| 📋 规划中 | {data['project']['status']['planning']} 个 |
| 🚀 进行中 | {data['project']['status']['running']} 个 |
| ✅ 已完成 | {data['project']['status']['completed']} 个 |
| ⏸️ 暂停 | {data['project']['status']['on_hold']} 个 |

**平均进度**: {data['project']['average_progress']}%  
**总预算**: ¥{data['project']['total_budget']:.2f}

### 3.2 项目详情

"""
    
    if data['project']['projects']:
        md += "| 项目名称 | 状态 | 优先级 | 进度 | 预算 |\n"
        md += "|----------|------|--------|------|------|\n"
        for p in data['project']['projects']:
            status_icon = {"planning": "📋", "running": "🚀", "completed": "✅", "on_hold": "⏸️"}.get(p['status'], "❓")
            priority_label = {1: "低", 2: "中", 3: "高"}.get(p['priority'], "未知")
            md += f"| {p['name']} | {status_icon}{p['status']} | {priority_label} | {p['progress']}% | ¥{p['budget']:.2f} |\n"
    else:
        md += "暂无项目数据\n"
    
    md += f"""
---

## ✅ 四、任务状态

| 状态 | 数量 |
|------|------|
| ⏳ 待处理 | {data['task']['status']['pending']} 个 |
| 🔄 进行中 | {data['task']['status']['in_progress']} 个 |
| ✅ 已完成 | {data['task']['status']['completed']} 个 |

**任务完成率**: {data['task']['completion_rate']}%

---

## 💰 五、财务状况

| 项目 | 金额 |
|------|------|
| 💵 预算总额 | ¥{data['financial']['budget']:.2f} |
| 💸 已支出 | ¥{data['financial']['spent']:.2f} |
| 💰 剩余余额 | ¥{data['financial']['balance']:.2f} |
| 📊 资金使用率 | {data['financial']['usage_rate']}% |

---

## 🎯 六、下周重点工作计划

"""
    
    for i, item in enumerate(data['focus_next_week'], 1):
        md += f"{i}. {item}\n"
    
    md += f"""
---

## 📝 七、问题与建议

- 空闲员工: {data['employee']['status']['idle']} 人，需要合理分配任务
- 待处理任务: {data['task']['status']['pending']} 个，需要尽快安排

---

*本报告由数字公司插件自动生成*
"""
    
    return md


def generate_weekly_report() -> dict:
    """
    生成完整的周报数据
    
    Returns:
        dict: 包含所有周报数据的字典
    """
    company = get_company()
    dashboard = company.get_dashboard()
    
    # 获取各项详细数据
    employee_data = get_employee_status_summary(company)
    project_data = get_project_summary(company)
    task_data = get_task_summary(company)
    financial_data = get_financial_summary(company)
    
    # 获取本周日期范围
    start_date, end_date = get_week_range()
    
    # 生成下周重点工作计划
    focus_next_week = _generate_focus_next_week(
        employee_data, project_data, task_data, financial_data
    )
    
    # 组装完整周报数据
    report_data = {
        "week_start": start_date.isoformat(),
        "week_end": end_date.isoformat(),
        "generated_at": datetime.now().isoformat(),
        "company_name": company.name,
        "summary": {
            "employees_total": employee_data['total'],
            "projects_total": project_data['total'],
            "tasks_total": task_data['total'],
            "balance": financial_data['balance'],
        },
        "employee": employee_data,
        "project": project_data,
        "task": task_data,
        "financial": financial_data,
        "focus_next_week": focus_next_week,
    }
    
    return report_data


def _generate_focus_next_week(
    employee_data: dict,
    project_data: dict,
    task_data: dict,
    financial_data: dict
) -> List[str]:
    """根据当前状态自动生成下周重点工作计划"""
    focus = []
    
    # 项目相关
    if project_data['status']['planning'] > 0:
        focus.append(f"推进 {project_data['status']['planning']} 个规划中项目的启动")
    if project_data['status']['running'] > 0:
        focus.append(f"跟进 {project_data['status']['running']} 个进行中项目的进度")
    if project_data['average_progress'] < 50:
        focus.append("提升项目整体进度")
    
    # 任务相关
    if task_data['status']['pending'] > 0:
        focus.append(f"处理 {task_data['status']['pending']} 个待处理任务")
    if task_data['completion_rate'] < 50:
        focus.append("提高任务完成率")
    
    # 员工相关
    idle_count = employee_data['status']['idle']
    if idle_count > 0:
        focus.append(f"合理分配 {idle_count} 位空闲员工的工作任务")
    
    # 财务相关
    if financial_data['usage_rate'] > 80:
        focus.append("关注预算使用情况，避免超支")
    elif financial_data['balance'] < 200:
        focus.append("关注资金余额，考虑增收节支")
    
    # 确保至少有3项计划
    default_plans = [
        "推进关键里程碑交付",
        "补齐高优先级岗位招聘",
        "跟踪预算执行偏差",
    ]
    
    for plan in default_plans:
        if len(focus) >= 5:
            break
        if plan not in focus:
            focus.append(plan)
    
    return focus[:5]


def save_weekly_report_to_file(report_data: dict = None, file_path: str = None) -> str:
    """
    保存周报到文件
    
    Args:
        report_data: 周报数据，如果为None则重新生成
        file_path: 文件保存路径，如果为None则自动生成
    
    Returns:
        str: 保存的文件路径
    """
    if report_data is None:
        report_data = generate_weekly_report()
    
    # 生成 Markdown 格式报告
    markdown_report = generate_markdown_report(report_data)
    
    # 确定保存路径
    if file_path is None:
        # 使用周报目录
        week_dir = os.path.join(os.path.dirname(__file__), "..", "reports", "weekly")
        os.makedirs(week_dir, exist_ok=True)
        
        # 生成文件名：weekly_2026-03-16.md
        start_date = datetime.fromisoformat(report_data['week_start']).strftime('%Y-%m-%d')
        file_path = os.path.join(week_dir, f"weekly_{start_date}.md")
    
    # 写入文件
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(markdown_report)
    
    return file_path


def run_weekly_review() -> dict:
    """
    运行完整的周报生成流程
    
    Returns:
        dict: 包含周报数据 和 文件保存路径
    """
    # 1. 生成周报数据
    report_data = generate_weekly_report()
    
    # 2. 保存到文件
    file_path = save_weekly_report_to_file(report_data)
    
    # 3. 返回结果
    return {
        "success": True,
        "report_data": report_data,
        "file_path": file_path,
        "markdown": generate_markdown_report(report_data)
    }


# ============ 测试代码 ============
if __name__ == "__main__":
    print("=" * 50)
    print("开始生成周报...")
    print("=" * 50)
    
    result = run_weekly_review()
    
    print(f"\n✅ 周报生成成功！")
    print(f"📁 文件保存路径: {result['file_path']}")
    print(f"\n{'=' * 50}")
    print("周报预览:")
    print('=' * 50)
    print(result['markdown'])
