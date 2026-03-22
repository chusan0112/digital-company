"""
数字公司插件 - API接口
"""

import json
from datetime import datetime
from company import get_company
from core.orchestrator import submit_chairman_command, preview_chairman_command, get_decision, approve_and_execute
from core.approval_center import approve as approve_record, reject as reject_record, get_approval
from workflows.weekly_review import generate_weekly_report
from storage.repository import list_recent_decisions, list_recent_approvals


def handle_request(path, method="GET", body=None):
    """处理API请求"""
    company = get_company()
    
    # 路由
    if path == "/api/health":
        return {"success": True, "service": "digital-company", "status": "ok"}

    if path == "/api/dashboard":
        return company.get_dashboard()
    
    elif path == "/api/employees":
        return [e.__dict__ for e in company.list_employees()]
    
    elif path == "/api/departments":
        return [d.__dict__ for d in company.list_departments()]
    
    elif path == "/api/projects":
        return [p.__dict__ for p in company.list_projects()]
    
    elif path == "/api/tasks":
        return [t.__dict__ for t in company.list_tasks()]
    
    # 创建部门
    elif path == "/api/department" and method == "POST":
        data = json.loads(body) if body else {}
        dept = company.add_department(
            name=data.get("name", ""),
            description=data.get("description", ""),
            parent_id=data.get("parent_id", "")
        )
        return {"success": True, "id": dept.id}
    
    # 雇佣员工
    elif path == "/api/employee" and method == "POST":
        data = json.loads(body) if body else {}
        emp = company.hire_employee(
            name=data.get("name", ""),
            role=data.get("role", ""),
            department_id=data.get("department_id", ""),
            skills=data.get("skills", []),
            salary=data.get("salary", 0)
        )
        return {"success": True, "id": emp.id}
    
    # 解雇员工
    elif path == "/api/employee" and method == "DELETE":
        data = json.loads(body) if body else {}
        success = company.fire_employee(data.get("id", ""))
        return {"success": success}
    
    # 更新员工状态
    elif path == "/api/employee/status" and method == "POST":
        data = json.loads(body) if body else {}
        company.update_employee_status(
            data.get("id", ""),
            data.get("status", "idle")
        )
        return {"success": True}
    
    # 创建项目
    elif path == "/api/project" and method == "POST":
        data = json.loads(body) if body else {}
        proj = company.create_project(
            name=data.get("name", ""),
            description=data.get("description", ""),
            department_id=data.get("department_id", ""),
            budget=data.get("budget", 0)
        )
        return {"success": True, "id": proj.id}
    
    # 创建任务
    elif path == "/api/task" and method == "POST":
        data = json.loads(body) if body else {}
        task = company.create_task(
            name=data.get("name", ""),
            description=data.get("description", ""),
            project_id=data.get("project_id", ""),
            assignee_id=data.get("assignee_id", ""),
            priority=data.get("priority", 1)
        )
        return {"success": True, "id": task.id}
    
    # 分配任务
    elif path == "/api/task/assign" and method == "POST":
        data = json.loads(body) if body else {}
        success = company.assign_task(
            data.get("task_id", ""),
            data.get("employee_id", "")
        )
        return {"success": success}
    
    # 完成任务
    elif path == "/api/task/complete" and method == "POST":
        data = json.loads(body) if body else {}
        success = company.complete_task(data.get("task_id", ""))
        return {"success": success}
    
    # 财务支出
    elif path == "/api/spend" and method == "POST":
        data = json.loads(body) if body else {}
        success = company.spend(
            amount=data.get("amount", 0),
            description=data.get("description", "")
        )
        return {"success": success}

    # 董事长指令入口（MVP）
    elif path == "/api/chairman/command" and method == "POST":
        data = json.loads(body) if body else {}
        command = data.get("command", "")
        if not command:
            return {"success": False, "error": "command_required"}
        packet = submit_chairman_command(command)
        return {"success": True, "decision": packet}

    elif path == "/api/chairman/command/preview" and method == "POST":
        data = json.loads(body) if body else {}
        command = data.get("command", "")
        if not command:
            return {"success": False, "error": "command_required"}
        packet = preview_chairman_command(command)
        return {
            "success": True,
            "preview": packet,
            "chairman_recommendation": {
                "execute_now": packet.get("summary", {}).get("recommended_to_execute_now", False),
                "suggested_action": packet.get("summary", {}).get("suggested_action"),
                "reason_messages": packet.get("summary", {}).get("policy_reason_messages", []),
            },
        }

    elif path.startswith("/api/decisions/") and method == "GET":
        decision_id = path.replace("/api/decisions/", "")
        decision = get_decision(decision_id)
        if not decision:
            return {"success": False, "error": "decision_not_found"}
        return {"success": True, "decision": decision}

    elif path.startswith("/api/approvals/") and path.endswith("/approve") and method == "POST":
        approval_id = path.replace("/api/approvals/", "").replace("/approve", "")
        data = json.loads(body) if body else {}
        comments = data.get("comments", "")
        reason = data.get("reason", "战略匹配，批准执行")
        governance_conditions = data.get("governance_conditions", [])
        final_comments = comments if comments else reason

        # P0-3: 不再拼接字符串，改为结构化落库
        # final_comments = f"{final_comments} | 治理条件: {'; '.join(governance_conditions)}"

        approve_result = approve_record(approval_id, final_comments, governance_conditions)
        if not approve_result.get("success"):
            return approve_result
        execution = approve_and_execute(approval_id, final_comments)
        return {
            "success": True,
            "reason_template": reason,
            "governance_conditions": governance_conditions,
            "approval": approve_result.get("approval"),
            "execution": execution,
        }

    elif path.startswith("/api/approvals/") and path.endswith("/reject") and method == "POST":
        approval_id = path.replace("/api/approvals/", "").replace("/reject", "")
        data = json.loads(body) if body else {}
        comments = data.get("comments", "")
        reason = data.get("reason", "风险过高，暂不批准")
        final_comments = comments if comments else reason

        reject_result = reject_record(approval_id, final_comments)
        if isinstance(reject_result, dict):
            reject_result["reason_template"] = reason
        return reject_result

    elif path.startswith("/api/approvals/") and method == "GET":
        approval_id = path.replace("/api/approvals/", "")
        approval = get_approval(approval_id)
        if not approval:
            return {"success": False, "error": "approval_not_found"}
        return {"success": True, "approval": approval}

    elif path == "/api/reports/weekly/latest" and method == "GET":
        return {"success": True, "report": generate_weekly_report()}

    elif path == "/api/dashboard/executive" and method == "GET":
        dashboard = company.get_dashboard()
        recent_decisions = list_recent_decisions(8)
        recent_approvals = list_recent_approvals(8)
        pending_approvals = [a for a in recent_approvals if a.get("status") == "pending"]

        return {
            "success": True,
            "dashboard": {
                "company": {
                    "name": dashboard.get("company_name"),
                    "departments": dashboard.get("departments"),
                    "employees": dashboard.get("employees"),
                },
                "operations": {
                    "projects_total": dashboard.get("projects", {}).get("total", 0),
                    "tasks_total": dashboard.get("tasks", {}).get("total", 0),
                    "tasks_completed": dashboard.get("tasks", {}).get("completed", 0),
                },
                "finance": dashboard.get("financial", {}),
                "governance": {
                    "recent_decisions": recent_decisions,
                    "recent_approvals": recent_approvals,
                    "pending_approvals_count": len(pending_approvals),
                },
            },
        }

    elif path == "/api/chairman/snapshot" and method == "GET":
        dashboard = company.get_dashboard()
        recent_decisions = list_recent_decisions(20)
        recent_approvals = list_recent_approvals(20)

        pending_approvals = [a for a in recent_approvals if a.get("status") == "pending"]
        pending_approvals.sort(key=lambda a: a.get("created_at", ""), reverse=True)

        high_risk_decisions = [
            d for d in recent_decisions
            if d.get("policy", {}).get("risk_level") == "high"
        ]

        top_risk = None
        if high_risk_decisions:
            top = high_risk_decisions[0]
            biz = top.get("intent", {}).get("business_name", "未命名业务")
            reason = (top.get("summary", {}).get("policy_reason_messages") or [""])[0]
            top_risk = {
                "decision_id": top.get("id"),
                "business": biz,
                "risk_level": "high",
                "reason": reason,
            }

        milestone_alerts = []
        for d in recent_decisions:
            exec_result = d.get("execution_result", {}) if isinstance(d, dict) else {}
            checks = exec_result.get("milestone_checks", []) if isinstance(exec_result, dict) else []
            for check in checks[:2]:
                milestone_alerts.append({
                    "decision_id": d.get("id"),
                    "business": d.get("intent", {}).get("business_name", "未命名业务"),
                    "name": check.get("name"),
                    "due_at": check.get("due_at"),
                })

        next_actions = []
        if pending_approvals:
            next_actions.append("优先处理待审批事项")
        if milestone_alerts:
            next_actions.append("关注本周里程碑检查")
        if dashboard.get("tasks", {}).get("pending", 0) > 0:
            next_actions.append("推动待处理任务转入执行")
        if not next_actions:
            next_actions.append("保持当前节奏，按周复盘")

        return {
            "success": True,
            "snapshot": {
                "company": {
                    "name": dashboard.get("company_name"),
                    "employees": dashboard.get("employees"),
                    "projects_total": dashboard.get("projects", {}).get("total", 0),
                },
                "pending_approvals_count": len(pending_approvals),
                "pending_approvals": [
                    {
                        "id": a.get("id"),
                        "title": a.get("title"),
                        "status": a.get("status"),
                        "governance_conditions": a.get("governance_conditions", []),  # P0-3: 结构化条件
                    }
                    for a in pending_approvals[:5]
                ],
                "top_risk": top_risk,
                "milestone_alerts": milestone_alerts[:5],
                "next_actions": next_actions,
            },
        }
    
    return {"error": "Not found"}
