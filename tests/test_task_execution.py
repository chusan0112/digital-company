"""
任务执行系统测试
"""

import json
import sys
import os

# 添加项目根目录路径
PROJECT_ROOT = r"C:\Users\Administrator\.openclaw\skills\digital-company"
sys.path.insert(0, PROJECT_ROOT)

from core.task_execution import (
    create_task,
    create_tasks_from_conclusion,
    assign_task,
    set_task_priority,
    set_task_due_date,
    start_task,
    update_task_progress,
    add_task_log,
    complete_task,
    fail_task,
    get_task_status,
    get_all_tasks,
    get_task_statistics,
    TASK_STATUS_PENDING,
    TASK_STATUS_IN_PROGRESS,
    TASK_STATUS_COMPLETED,
    TASK_STATUS_FAILED,
    PRIORITY_LOW,
    PRIORITY_MEDIUM,
    PRIORITY_HIGH,
    PRIORITY_URGENT
)
from db.sqlite_repository import EmployeeRepository, ProjectRepository


def print_result(title, result):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print('='*50)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def main():
    print("=" * 60)
    print("  任务执行系统测试")
    print("=" * 60)
    
    # 1. 测试从会议结论提取任务
    print("\n【测试1】从会议结论提取任务")
    test_conclusion = """
    经讨论，该项目可行性评估为75%，整体风险可控。建议推进执行。
    关键行动项：
    1. 做市场调研，了解竞争对手情况
    2. 开发小程序，实现核心功能
    3. 分析数据，优化运营策略
    4. 制定推广计划
    """
    
    from core.task_execution import get_task_system
    system = get_task_system()
    extracted = system.extract_tasks_from_conclusion(test_conclusion)
    print_result("提取的任务", {"success": True, "tasks": extracted})
    
    # 2. 测试创建任务
    print("\n【测试2】创建任务")
    task1 = create_task(
        name="市场调研",
        description="调研竞争对手情况和市场需求",
        priority=PRIORITY_HIGH,
        due_date="2026-03-30"
    )
    print_result("创建任务", task1)
    
    # 3. 创建更多任务
    task2 = create_task(
        name="开发小程序",
        description="开发微信小程序核心功能",
        priority=PRIORITY_MEDIUM,
        due_date="2026-04-15"
    )
    task3 = create_task(
        name="数据分析",
        description="分析用户行为数据",
        priority=PRIORITY_LOW,
        due_date="2026-04-01"
    )
    print_result("创建更多任务", {"tasks_created": 3})
    
    # 4. 测试从会议结论创建任务
    print("\n【测试4】从会议结论批量创建任务")
    tasks_from_conclusion = create_tasks_from_conclusion(
        conclusion=test_conclusion,
        project_id=None,
        default_assignee_id=None
    )
    print_result("批量创建任务", {"success": True, "tasks": tasks_from_conclusion, "count": len(tasks_from_conclusion)})
    
    # 5. 测试分配任务
    print("\n【测试5】分配任务")
    # 先创建一个测试员工
    employees = EmployeeRepository.get_all()
    if employees:
        employee = employees[0]
        assign_result = assign_task(task1["task_id"], employee["id"])
        print_result("分配任务", assign_result)
    else:
        print("暂无员工，跳过分配测试")
    
    # 6. 测试设置优先级
    print("\n【测试6】设置优先级")
    priority_result = set_task_priority(task1["task_id"], PRIORITY_URGENT)
    print_result("设置优先级", priority_result)
    
    # 7. 测试开始任务
    print("\n【测试7】开始任务")
    start_result = start_task(task1["task_id"])
    print_result("开始任务", start_result)
    
    # 8. 测试更新进度
    print("\n【测试8】更新进度")
    progress_result = update_task_progress(task1["task_id"], 50, "完成市场调研问卷设计")
    print_result("更新进度", progress_result)
    
    # 9. 添加执行日志
    print("\n【测试9】添加执行日志")
    log_result = add_task_log(task1["task_id"], "与竞品A进行对比分析")
    print_result("添加日志", log_result)
    
    # 10. 完成任务
    print("\n【测试10】完成任务")
    complete_result = complete_task(task1["task_id"], "市场调研报告已完成")
    print_result("完成任务", complete_result)
    
    # 11. 获取任务状态
    print("\n【测试11】获取任务状态")
    status_result = get_task_status(task1["task_id"])
    print_result("任务状态", status_result)
    
    # 12. 获取所有任务
    print("\n【测试12】获取所有任务")
    all_tasks = get_all_tasks()
    print_result("所有任务", {"success": True, "tasks": all_tasks, "count": len(all_tasks)})
    
    # 13. 获取任务统计
    print("\n【测试13】获取任务统计")
    stats = get_task_statistics()
    print_result("任务统计", stats)
    
    # 14. 测试失败任务
    print("\n【测试14】测试失败任务")
    fail_result = fail_task(task3["task_id"], "数据无法获取")
    print_result("标记失败", fail_result)
    
    # 15. 再次获取统计
    print("\n【测试15】更新后的任务统计")
    stats = get_task_statistics()
    print_result("更新后统计", stats)
    
    print("\n" + "=" * 60)
    print("  测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
