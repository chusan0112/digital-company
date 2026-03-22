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

# Import extended modules
from domains.finance_extended import get_finance_service
from domains.market_service import get_market_service
from domains.satisfaction_service import get_satisfaction_service
from domains.project_lifecycle_service import get_lifecycle_service

# Import meeting module
from core.meeting import (
    start_meeting,
    next_speaker,
    end_meeting,
    get_current_meeting,
    run_full_discussion,
    ROLE_SPEECH_STYLES
)

# Import task execution module
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

# Import OpenClaw integration
try:
    from integrations.openclaw_client import get_openclaw_client
    OPENCLAW_ENABLED = True
except ImportError:
    OPENCLAW_ENABLED = False

# Token storage for API-based auth (simple in-memory)
_token_store = {}


def _extract_token(headers=None, body=None):
    """Extract token from headers or body"""
    if headers:
        auth_header = headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            return auth_header[7:]
    
    if body:
        try:
            data = json.loads(body) if isinstance(body, str) else body
            return data.get('token', '')
        except:
            pass
    
    return None


def _verify_request(headers=None, body=None):
    """Verify authentication for protected endpoints"""
    if not AUTH_ENABLED:
        return {"authenticated": False, "error": "Auth not enabled"}
    
    token = _extract_token(headers, body)
    if not token:
        return {"authenticated": False, "error": "No token provided"}
    
    if token in _token_store.get('blacklist', set()):
        return {"authenticated": False, "error": "Token revoked"}
    
    payload = verify_token(token)
    if not payload:
        return {"authenticated": False, "error": "Invalid or expired token"}
    
    return {"authenticated": True, "user": payload}


def handle_request(path, method="GET", body=None, headers=None):
    """处理API请求"""
    company = get_company()
    
    # ============== 认证接口 ==============
    # POST /api/auth/login - 用户登录
    if path == "/api/auth/login" and method == "POST":
        data = json.loads(body) if body else {}
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return {"success": False, "error": "Username and password are required"}
        
        user = authenticate_user(username, password)
        
        if not user:
            return {"success": False, "error": "Invalid username or password"}
        
        token = create_token(user['id'], user['username'], user['role'])
        
        return {
            "success": True,
            "message": "Login successful",
            "token": token,
            "user": {
                "id": user['id'],
                "username": user['username'],
                "role": user['role']
            }
        }
    
    # POST /api/auth/logout - 用户登出
    elif path == "/api/auth/logout" and method == "POST":
        auth_result = _verify_request(headers, body)
        
        if not auth_result.get('authenticated'):
            return {"success": False, "error": auth_result.get('error', 'Authentication failed')}
        
        token = _extract_token(headers, body)
        if token:
            if 'blacklist' not in _token_store:
                _token_store['blacklist'] = set()
            _token_store['blacklist'].add(token)
        
        return {"success": True, "message": "Logout successful"}
    
    # GET /api/auth/verify - 验证token
    elif path == "/api/auth/verify" and method == "GET":
        auth_result = _verify_request(headers, body)
        
        if not auth_result.get('authenticated'):
            return {"success": False, "error": auth_result.get('error', 'Authentication failed')}
        
        user = auth_result.get('user', {})
        return {
            "success": True,
            "user": {
                "id": user.get('user_id'),
                "username": user.get('username'),
                "role": user.get('role')
            }
        }
    
    # ============== 公开接口 ==============
    # 路由
    if path == "/api/health":
        return {"success": True, "service": "digital-company", "status": "ok", "auth_enabled": AUTH_ENABLED}

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
    
    # ============== OpenClaw集成接口 ==============
    
    # POST /api/openclaw/enable - 启用/禁用OpenClaw集成
    elif path == "/api/openclaw/enable" and method == "POST":
        if not OPENCLAW_ENABLED:
            return {"success": False, "error": "OpenClaw integration not available"}
        return {"success": True, "enabled": True}
    
    # POST /api/employee/recruit - 招聘AI员工（自动创建OpenClaw Agent）
    elif path == "/api/employee/recruit" and method == "POST":
        if not OPENCLAW_ENABLED:
            return {"success": False, "error": "OpenClaw integration not available"}
        
        data = json.loads(body) if body else {}
        name = data.get("name", "").strip()
        role = data.get("role", "").strip()
        department_id = data.get("department_id", "").strip()
        skills = data.get("skills", [])
        
        if not name:
            return {"success": False, "error": "name_required"}
        if not role:
            return {"success": False, "error": "role_required"}
        
        # 创建员工（同时创建OpenClaw Agent）
        emp = company.hire_employee(
            name=name,
            role=role,
            department_id=department_id,
            skills=skills,
            create_openclaw_agent=True
        )
        
        return {
            "success": True,
            "employee": emp.to_dict(),
            "openclaw_agent_id": emp.openclaw_agent_id,
            "message": f"员工 {name} 已入职，OpenClaw Agent 已创建"
        }
    
    # GET /api/employee/{id}/agent - 获取员工对应的OpenClaw Agent
    elif path.startswith("/api/employee/") and path.endswith("/agent") and method == "GET":
        if not OPENCLAW_ENABLED:
            return {"success": False, "error": "OpenClaw integration not available"}
        
        emp_id = path.replace("/api/employee/", "").replace("/agent", "")
        agent_info = company.get_employee_agent(emp_id)
        
        if not agent_info:
            return {"success": False, "error": "agent_not_found"}
        
        return {"success": True, "agent": agent_info.to_dict()}
    
    # POST /api/employee/{id}/task - 给员工分配任务（通过OpenClaw执行）
    elif path.startswith("/api/employee/") and path.endswith("/task") and method == "POST":
        if not OPENCLAW_ENABLED:
            return {"success": False, "error": "OpenClaw integration not available"}
        
        emp_id = path.replace("/api/employee/", "").replace("/task", "")
        data = json.loads(body) if body else {}
        task_description = data.get("description", "").strip()
        
        if not task_description:
            return {"success": False, "error": "task_description_required"}
        
        try:
            task_id = company.dispatch_task_to_employee(emp_id, task_description)
            return {
                "success": True,
                "task_id": task_id,
                "message": "任务已分配给员工"
            }
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except RuntimeError as e:
            return {"success": False, "error": str(e)}
    
    # POST /api/employee/{id}/sync - 同步OpenClaw Agent状态到员工
    elif path.startswith("/api/employee/") and path.endswith("/sync") and method == "POST":
        if not OPENCLAW_ENABLED:
            return {"success": False, "error": "OpenClaw integration not available"}
        
        emp_id = path.replace("/api/employee/", "").replace("/sync", "")
        company.sync_agent_status(emp_id=emp_id)
        
        emp = company.get_employee(emp_id)
        return {
            "success": True,
            "employee_status": emp.status if emp else "unknown"
        }
    
    # GET /api/openclaw/agents - 列出所有OpenClaw Agents
    elif path == "/api/openclaw/agents" and method == "GET":
        if not OPENCLAW_ENABLED:
            return {"success": False, "error": "OpenClaw integration not available"}
        
        client = get_openclaw_client()
        agents = client.list_agents()
        
        return {
            "success": True,
            "agents": [a.to_dict() for a in agents]
        }
    
    # GET /api/openclaw/tasks - 列出所有任务
    elif path == "/api/openclaw/tasks" and method == "GET":
        if not OPENCLAW_ENABLED:
            return {"success": False, "error": "OpenClaw integration not available"}
        
        client = get_openclaw_client()
        data = json.loads(body) if body else {}
        
        tasks = client.list_tasks(
            agent_id=data.get("agent_id"),
            status=data.get("status")
        )
        
        return {
            "success": True,
            "tasks": [t.to_dict() for t in tasks]
        }
    
    # GET /api/openclaw/task/{id} - 获取任务状态
    elif path.startswith("/api/openclaw/task/") and method == "GET":
        if not OPENCLAW_ENABLED:
            return {"success": False, "error": "OpenClaw integration not available"}
        
        task_id = path.replace("/api/openclaw/task/", "")
        client = get_openclaw_client()
        task_result = client.get_task_status(task_id)
        
        if not task_result:
            return {"success": False, "error": "task_not_found"}
        
        return {"success": True, "task": task_result.to_dict()}
    
    # POST /api/openclaw/webhook/register - 注册Webhook回调
    elif path == "/api/openclaw/webhook/register" and method == "POST":
        if not OPENCLAW_ENABLED:
            return {"success": False, "error": "OpenClaw integration not available"}
        
        data = json.loads(body) if body else {}
        callback_url = data.get("callback_url", "").strip()
        
        if not callback_url:
            return {"success": False, "error": "callback_url_required"}
        
        # 注册webhook（这里简单存储URL，实际实现需要web服务器支持）
        if not hasattr(company, '_webhooks'):
            company._webhooks = []
        company._webhooks.append(callback_url)
        
        return {
            "success": True,
            "message": "Webhook已注册",
            "callback_url": callback_url
        }
    
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
    
    # ============== 会议室管理API ==============
    from db.sqlite_repository import MeetingRoomRepository, MeetingRepository
    
    # GET /api/meeting-rooms - 获取所有会议室
    if path == "/api/meeting-rooms" and method == "GET":
        status_filter = None
        if body:
            data = json.loads(body) if isinstance(body, str) else body
            status_filter = data.get("status")
        rooms = MeetingRoomRepository.get_all(status=status_filter)
        return {"success": True, "meeting_rooms": rooms}
    
    # POST /api/meeting-rooms - 创建会议室
    if path == "/api/meeting-rooms" and method == "POST":
        data = json.loads(body) if body else {}
        name = data.get("name", "").strip()
        capacity = data.get("capacity", 0)
        location = data.get("location", "")
        status = data.get("status", "available")
        
        if not name:
            return {"success": False, "error": "name_required"}
        if capacity <= 0:
            return {"success": False, "error": "capacity_required"}
        
        room_id = MeetingRoomRepository.create(name=name, capacity=capacity, location=location, status=status)
        return {"success": True, "id": room_id, "message": "Meeting room created"}
    
    # PUT /api/meeting-rooms/{id} - 更新会议室
    if path.startswith("/api/meeting-rooms/") and method == "PUT":
        room_id = path.replace("/api/meeting-rooms/", "")
        if not room_id.isdigit():
            return {"success": False, "error": "invalid_id"}
        
        data = json.loads(body) if body else {}
        updates = {}
        if "name" in data:
            updates["name"] = data["name"]
        if "capacity" in data:
            updates["capacity"] = data["capacity"]
        if "location" in data:
            updates["location"] = data["location"]
        if "status" in data:
            updates["status"] = data["status"]
        
        if not updates:
            return {"success": False, "error": "no_fields_to_update"}
        
        success = MeetingRoomRepository.update(int(room_id), **updates)
        return {"success": success, "message": "Meeting room updated" if success else "Meeting room not found"}
    
    # DELETE /api/meeting-rooms/{id} - 删除会议室
    if path.startswith("/api/meeting-rooms/") and method == "DELETE":
        room_id = path.replace("/api/meeting-rooms/", "")
        if not room_id.isdigit():
            return {"success": False, "error": "invalid_id"}
        
        success = MeetingRoomRepository.delete(int(room_id))
        return {"success": success, "message": "Meeting room deleted" if success else "Meeting room not found"}
    
    # POST /api/meeting-rooms/book - 预订会议室
    if path == "/api/meeting-rooms/book" and method == "POST":
        from domains.meeting_room_service import BookingService
        
        data = json.loads(body) if body else {}
        title = data.get("title", "").strip()
        host_id = data.get("host_id")
        meeting_room_id = data.get("meeting_room_id")
        start_time = data.get("start_time", "").strip()
        end_time = data.get("end_time", "").strip()
        notes = data.get("notes", "")
        
        if not title:
            return {"success": False, "error": "title_required"}
        if not host_id:
            return {"success": False, "error": "host_id_required"}
        if not meeting_room_id:
            return {"success": False, "error": "meeting_room_id_required"}
        if not start_time or not end_time:
            return {"success": False, "error": "start_time_and_end_time_required"}
        
        result = BookingService.book_room(
            title=title,
            host_id=host_id,
            meeting_room_id=meeting_room_id,
            start_time=start_time,
            end_time=end_time,
            notes=notes
        )
        return result
    
    # GET /api/meeting-rooms/availability - 查询可用会议室
    if path == "/api/meeting-rooms/availability" and method == "GET":
        from domains.meeting_room_service import BookingService, get_availability
        
        # 解析查询参数
        start_time = None
        end_time = None
        min_capacity = None
        date = None
        
        if body:
            data = json.loads(body) if isinstance(body, str) else body
            start_time = data.get("start_time")
            end_time = data.get("end_time")
            min_capacity = data.get("min_capacity")
            date = data.get("date")
        
        # 如果提供了具体时间段，查询可用会议室
        if start_time and end_time:
            available_rooms = BookingService.get_available_rooms(
                start_time=start_time,
                end_time=end_time,
                min_capacity=min_capacity
            )
            return {
                "success": True,
                "start_time": start_time,
                "end_time": end_time,
                "available_rooms": available_rooms,
                "count": len(available_rooms)
            }
        else:
            # 否则返回会议室可用性概览
            availability = get_availability(date=date)
            return {"success": True, "availability": availability}
    
    # ============== 会议预订API ==============
    
    # POST /api/meetings - 预订会议
    elif path == "/api/meetings" and method == "POST":
        data = json.loads(body) if body else {}
        title = data.get("title", "").strip()
        host_id = data.get("host_id")
        start_time = data.get("start_time", "").strip()
        end_time = data.get("end_time", "").strip()
        meeting_room_id = data.get("meeting_room_id")
        notes = data.get("notes", "")
        
        if not title:
            return {"success": False, "error": "title_required"}
        if not host_id:
            return {"success": False, "error": "host_id_required"}
        if not start_time or not end_time:
            return {"success": False, "error": "start_time_and_end_time_required"}
        
        # 如果指定了会议室，检查冲突
        if meeting_room_id:
            conflicts = MeetingRepository.check_conflict(meeting_room_id, start_time, end_time)
            if conflicts:
                return {
                    "success": False,
                    "error": "room_conflict",
                    "conflicts": conflicts,
                    "message": "会议室在该时间段已被占用"
                }
        
        meeting_id = MeetingRepository.create(
            title=title,
            host_id=host_id,
            start_time=start_time,
            end_time=end_time,
            meeting_room_id=meeting_room_id,
            notes=notes,
            status="scheduled"
        )
        return {"success": True, "id": meeting_id, "message": "Meeting scheduled"}
    
    # GET /api/meetings - 获取会议列表
    elif path == "/api/meetings" and method == "GET":
        host_id = None
        status = None
        meeting_room_id = None
        # 支持查询参数
        if body:
            data = json.loads(body) if isinstance(body, str) else body
            host_id = data.get("host_id")
            status = data.get("status")
            meeting_room_id = data.get("meeting_room_id")
        
        meetings = MeetingRepository.get_all(host_id=host_id, status=status)
        # 过滤会议室
        if meeting_room_id:
            meetings = [m for m in meetings if m.get("meeting_room_id") == meeting_room_id]
        return {"success": True, "meetings": meetings}
    
    # PUT /api/meetings/{id} - 更新会议
    elif path.startswith("/api/meetings/") and method == "PUT":
        meeting_id = path.replace("/api/meetings/", "")
        if not meeting_id.isdigit():
            return {"success": False, "error": "invalid_id"}
        
        data = json.loads(body) if body else {}
        updates = {}
        allowed_fields = ["title", "host_id", "start_time", "end_time", "status", "notes", "meeting_room_id"]
        
        for field in allowed_fields:
            if field in data:
                updates[field] = data[field]
        
        if not updates:
            return {"success": False, "error": "no_fields_to_update"}
        
        # 如果更新了会议室或时间，检查冲突
        if updates.get("meeting_room_id") or updates.get("start_time") or updates.get("end_time"):
            meeting = MeetingRepository.get_by_id(int(meeting_id))
            if meeting:
                room_id = updates.get("meeting_room_id", meeting.get("meeting_room_id"))
                start_time = updates.get("start_time", meeting.get("start_time"))
                end_time = updates.get("end_time", meeting.get("end_time"))
                
                if room_id:
                    conflicts = MeetingRepository.check_conflict(room_id, start_time, end_time, exclude_meeting_id=int(meeting_id))
                    if conflicts:
                        return {
                            "success": False,
                            "error": "room_conflict",
                            "conflicts": conflicts,
                            "message": "会议室在该时间段已被占用"
                        }
        
        success = MeetingRepository.update(int(meeting_id), **updates)
        return {"success": success, "message": "Meeting updated" if success else "Meeting not found"}
    
    # DELETE /api/meetings/{id} - 取消会议
    elif path.startswith("/api/meetings/") and method == "DELETE":
        meeting_id = path.replace("/api/meetings/", "")
        if not meeting_id.isdigit():
            return {"success": False, "error": "invalid_id"}
        
        # 软删除：将状态设为cancelled
        success = MeetingRepository.update(int(meeting_id), status="cancelled")
        return {"success": success, "message": "Meeting cancelled" if success else "Meeting not found"}
    # GET /api/finance/summary - 财务汇总
    if path == "/api/finance/summary" and method == "GET":
        finance = get_finance_service()
        return {"success": True, "summary": finance.get_financial_summary()}
    
    # POST /api/finance/budget - 创建预算
    elif path == "/api/finance/budget" and method == "POST":
        data = json.loads(body) if body else {}
        finance = get_finance_service()
        budget = finance.create_budget(
            name=data.get("name", ""),
            department_id=data.get("department_id", ""),
            fiscal_year=data.get("fiscal_year", 2026),
            amount=data.get("amount", 0),
            category=data.get("category", "general")
        )
        return {"success": True, "budget": budget.to_dict()}
    
    # POST /api/finance/budget/{id}/submit - 提交预算审批
    elif path.startswith("/api/finance/budget/") and path.endswith("/submit") and method == "POST":
        budget_id = path.replace("/api/finance/budget/", "").replace("/submit", "")
        finance = get_finance_service()
        success = finance.submit_budget(budget_id)
        return {"success": success, "message": "Budget submitted" if success else "Budget not found"}
    
    # POST /api/finance/budget/{id}/approve - 审批预算
    elif path.startswith("/api/finance/budget/") and path.endswith("/approve") and method == "POST":
        budget_id = path.replace("/api/finance/budget/", "").replace("/approve", "")
        data = json.loads(body) if body else {}
        approved_by = data.get("approved_by", "admin")
        finance = get_finance_service()
        success = finance.approve_budget(budget_id, approved_by)
        return {"success": success, "message": "Budget approved" if success else "Budget not found"}
    
    # GET /api/finance/budgets - 获取预算列表
    elif path == "/api/finance/budgets" and method == "GET":
        finance = get_finance_service()
        budgets = finance.list_budgets(
            department_id=body.get("department_id") if body else None,
            status=body.get("status") if body else None,
            fiscal_year=body.get("fiscal_year") if body else None
        )
        return {"success": True, "budgets": [b.to_dict() for b in budgets]}
    
    # POST /api/finance/cost - 添加成本记录
    elif path == "/api/finance/cost" and method == "POST":
        data = json.loads(body) if body else {}
        finance = get_finance_service()
        cost = finance.add_cost(
            date=data.get("date", datetime.now().strftime("%Y-%m-%d")),
            department_id=data.get("department_id", ""),
            category=data.get("category", "other"),
            amount=data.get("amount", 0),
            description=data.get("description", ""),
            project_id=data.get("project_id", ""),
            vendor=data.get("vendor", "")
        )
        return {"success": True, "cost": cost.to_dict()}
    
    # GET /api/finance/costs - 获取成本记录
    elif path == "/api/finance/costs" and method == "GET":
        data = json.loads(body) if body else {}
        finance = get_finance_service()
        costs = finance.get_costs(
            department_id=data.get("department_id"),
            category=data.get("category"),
            start_date=data.get("start_date"),
            end_date=data.get("end_date")
        )
        return {"success": True, "costs": [c.to_dict() for c in costs]}
    
    # GET /api/finance/costs/summary - 成本汇总
    elif path == "/api/finance/costs/summary" and method == "GET":
        data = json.loads(body) if body else {}
        finance = get_finance_service()
        summary = finance.get_cost_summary(
            department_id=data.get("department_id"),
            start_date=data.get("start_date"),
            end_date=data.get("end_date")
        )
        return {"success": True, "summary": summary}
    
    # POST /api/finance/income-statement - 生成利润表
    elif path == "/api/finance/income-statement" and method == "POST":
        data = json.loads(body) if body else {}
        finance = get_finance_service()
        statement = finance.generate_income_statement(
            period=data.get("period", "monthly"),
            start_date=data.get("start_date", ""),
            end_date=data.get("end_date", ""),
            revenue=data.get("revenue", 0),
            cost_of_goods_sold=data.get("cost_of_goods_sold", 0),
            operating_expenses=data.get("operating_expenses", 0),
            other_income=data.get("other_income", 0),
            other_expenses=data.get("other_expenses", 0)
        )
        return {"success": True, "income_statement": statement.to_dict()}
    
    # GET /api/finance/income-statements - 获取利润表
    elif path == "/api/finance/income-statements" and method == "GET":
        finance = get_finance_service()
        statements = finance.get_income_statements()
        return {"success": True, "income_statements": [s.to_dict() for s in statements]}
    
    # POST /api/finance/balance-sheet - 生成资产负债表
    elif path == "/api/finance/balance-sheet" and method == "POST":
        data = json.loads(body) if body else {}
        finance = get_finance_service()
        sheet = finance.generate_balance_sheet(
            period=data.get("period", "monthly"),
            end_date=data.get("end_date", ""),
            cash=data.get("cash", 0),
            accounts_receivable=data.get("accounts_receivable", 0),
            inventory=data.get("inventory", 0),
            accounts_payable=data.get("accounts_payable", 0),
            short_term_debt=data.get("short_term_debt", 0),
            long_term_debt=data.get("long_term_debt", 0),
            owner_equity=data.get("owner_equity", 0),
            retained_earnings=data.get("retained_earnings", 0)
        )
        return {"success": True, "balance_sheet": sheet.to_dict()}
    
    # GET /api/finance/balance-sheets - 获取资产负债表
    elif path == "/api/finance/balance-sheets" and method == "GET":
        finance = get_finance_service()
        sheets = finance.get_balance_sheets()
        return {"success": True, "balance_sheets": [s.to_dict() for s in sheets]}
    # POST /api/market/data - 采集市场数据
    elif path == "/api/market/data" and method == "POST":
        data = json.loads(body) if body else {}
        market = get_market_service()
        market_data = market.collect_market_data(
            market_name=data.get("market_name", ""),
            industry=data.get("industry", "tech"),
            total_market_size=data.get("total_market_size", 1000000)
        )
        return {"success": True, "market_data": market_data.to_dict()}
    
    # GET /api/market/data - 获取市场数据
    elif path == "/api/market/data" and method == "GET":
        market = get_market_service()
        data = market.get_market_data()
        return {"success": True, "market_data": [m.to_dict() for m in data]}
    
    # GET /api/market/overview - 市场概览
    elif path == "/api/market/overview" and method == "GET":
        data = json.loads(body) if body else {}
        market = get_market_service()
        overview = market.get_market_overview(data.get("market_name", ""))
        return {"success": True, "overview": overview}
    
    # POST /api/market/competitor - 添加竞争对手
    elif path == "/api/market/competitor" and method == "POST":
        data = json.loads(body) if body else {}
        market = get_market_service()
        competitor = market.add_competitor(
            name=data.get("name", ""),
            industry=data.get("industry", ""),
            market_share=data.get("market_share", 0),
            revenue=data.get("revenue", 0),
            strength_score=data.get("strength_score", 50),
            weakness=data.get("weakness", []),
            threat_level=data.get("threat_level", "medium"),
            description=data.get("description", "")
        )
        return {"success": True, "competitor": competitor.to_dict()}
    
    # GET /api/market/competitors - 获取竞争对手列表
    elif path == "/api/market/competitors" and method == "GET":
        data = json.loads(body) if body else {}
        market = get_market_service()
        competitors = market.list_competitors(
            industry=data.get("industry"),
            min_threat=data.get("min_threat")
        )
        return {"success": True, "competitors": [c.to_dict() for c in competitors]}
    
    # POST /api/market/share - 更新市场份额
    elif path == "/api/market/share" and method == "POST":
        data = json.loads(body) if body else {}
        market = get_market_service()
        share = market.update_market_share(
            market_name=data.get("market_name", ""),
            company_name=data.get("company_name", ""),
            period=data.get("period", datetime.now().strftime("%Y-%m")),
            share=data.get("share", 0),
            revenue=data.get("revenue", 0)
        )
        return {"success": True, "market_share": share.to_dict()}
    
    # GET /api/market/shares - 获取市场份额
    elif path == "/api/market/shares" and method == "GET":
        data = json.loads(body) if body else {}
        market = get_market_service()
        shares = market.get_market_shares(
            market_name=data.get("market_name"),
            period=data.get("period")
        )
        return {"success": True, "market_shares": [s.to_dict() for s in shares]}
    
    # POST /api/market/simulate - 模拟市场份额变化
    elif path == "/api/market/simulate" and method == "POST":
        data = json.loads(body) if body else {}
        market = get_market_service()
        result = market.simulate_market_share_change(
            company_name=data.get("company_name", ""),
            market_name=data.get("market_name", ""),
            marketing_budget=data.get("marketing_budget", 0),
            product_quality=data.get("product_quality", 50)
        )
        return {"success": True, "simulation": result}
    
    # POST /api/market/report - 生成市场报告
    elif path == "/api/market/report" and method == "POST":
        data = json.loads(body) if body else {}
        market = get_market_service()
        report = market.generate_market_report(
            market_name=data.get("market_name", ""),
            period=data.get("period", datetime.now().strftime("%Y-%m"))
        )
        return {"success": True, "report": report.to_dict()}
    # POST /api/satisfaction/survey - 创建满意度调查
    elif path == "/api/satisfaction/survey" and method == "POST":
        data = json.loads(body) if body else {}
        satisfaction = get_satisfaction_service()
        survey = satisfaction.create_survey(
            title=data.get("title", ""),
            department_id=data.get("department_id", ""),
            start_date=data.get("start_date", ""),
            end_date=data.get("end_date", "")
        )
        return {"success": True, "survey": survey.to_dict()}
    
    # POST /api/satisfaction/survey/{id}/activate - 激活问卷
    elif path.startswith("/api/satisfaction/survey/") and path.endswith("/activate") and method == "POST":
        survey_id = path.replace("/api/satisfaction/survey/", "").replace("/activate", "")
        satisfaction = get_satisfaction_service()
        success = satisfaction.activate_survey(survey_id)
        return {"success": success, "message": "Survey activated" if success else "Survey not found"}
    
    # POST /api/satisfaction/survey/{id}/close - 关闭问卷
    elif path.startswith("/api/satisfaction/survey/") and path.endswith("/close") and method == "POST":
        survey_id = path.replace("/api/satisfaction/survey/", "").replace("/close", "")
        satisfaction = get_satisfaction_service()
        success = satisfaction.close_survey(survey_id)
        return {"success": success, "message": "Survey closed" if success else "Survey not found"}
    
    # GET /api/satisfaction/surveys - 获取问卷列表
    elif path == "/api/satisfaction/surveys" and method == "GET":
        data = json.loads(body) if body else {}
        satisfaction = get_satisfaction_service()
        surveys = satisfaction.list_surveys(
            department_id=data.get("department_id"),
            status=data.get("status")
        )
        return {"success": True, "surveys": [s.to_dict() for s in surveys]}
    
    # POST /api/satisfaction/response - 提交问卷响应
    elif path == "/api/satisfaction/response" and method == "POST":
        data = json.loads(body) if body else {}
        satisfaction = get_satisfaction_service()
        try:
            response = satisfaction.submit_response(
                survey_id=data.get("survey_id", ""),
                employee_id=data.get("employee_id", ""),
                responses=data.get("responses", {}),
                comments=data.get("comments", "")
            )
            return {"success": True, "response": response.to_dict()}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # GET /api/satisfaction/responses - 获取问卷响应
    elif path == "/api/satisfaction/responses" and method == "GET":
        data = json.loads(body) if body else {}
        satisfaction = get_satisfaction_service()
        responses = satisfaction.get_responses(
            survey_id=data.get("survey_id"),
            employee_id=data.get("employee_id")
        )
        return {"success": True, "responses": [r.to_dict() for r in responses]}
    
    # POST /api/satisfaction/metrics - 计算满意度指标
    elif path == "/api/satisfaction/metrics" and method == "POST":
        data = json.loads(body) if body else {}
        satisfaction = get_satisfaction_service()
        try:
            metrics = satisfaction.calculate_metrics(
                survey_id=data.get("survey_id", ""),
                department_id=data.get("department_id", "")
            )
            return {"success": True, "metrics": metrics.to_dict()}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # GET /api/satisfaction/metrics - 获取满意度指标历史
    elif path == "/api/satisfaction/metrics" and method == "GET":
        data = json.loads(body) if body else {}
        satisfaction = get_satisfaction_service()
        metrics = satisfaction.get_metrics_history(department_id=data.get("department_id"))
        return {"success": True, "metrics": [m.to_dict() for m in metrics]}
    
    # POST /api/satisfaction/insights - 生成满意度洞察
    elif path == "/api/satisfaction/insights" and method == "POST":
        data = json.loads(body) if body else {}
        satisfaction = get_satisfaction_service()
        try:
            insight = satisfaction.generate_insights(
                department_id=data.get("department_id", "")
            )
            return {"success": True, "insight": insight.to_dict()}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # GET /api/satisfaction/overview - 满意度概览
    elif path == "/api/satisfaction/overview" and method == "GET":
        data = json.loads(body) if body else {}
        satisfaction = get_satisfaction_service()
        overview = satisfaction.get_satisfaction_overview(department_id=data.get("department_id"))
        return {"success": True, "overview": overview}
    
    # POST /api/satisfaction/simulate - 模拟满意度数据
    elif path == "/api/satisfaction/simulate" and method == "POST":
        data = json.loads(body) if body else {}
        satisfaction = get_satisfaction_service()
        result = satisfaction.simulate_satisfaction_data(
            department_id=data.get("department_id", ""),
            employee_count=data.get("employee_count", 10)
        )
        return {"success": True, "simulation": result}
    
    # ============== 会议讨论系统接口 ==============
    
    # POST /api/meeting/start - 开始新会议
    elif path == "/api/meeting/start" and method == "POST":
        data = json.loads(body) if body else {}
        result = start_meeting(
            topic=data.get("topic", ""),
            participants=data.get("participants")  # 可选，默认全部
        )
        return {"success": True, "meeting": result}
    
    # POST /api/meeting/next - 下一位发言人
    elif path == "/api/meeting/next" and method == "POST":
        data = json.loads(body) if body else {}
        result = next_speaker(context=data.get("context"))
        return {"success": True, "turn": result}
    
    # POST /api/meeting/end - 结束会议
    elif path == "/api/meeting/end" and method == "POST":
        result = end_meeting()
        return {"success": True, "meeting": result}
    
    # GET /api/meeting/status - 获取当前会议状态
    elif path == "/api/meeting/status" and method == "GET":
        result = get_current_meeting()
        if result.get("success") == False:
            return {"success": False, "error": result.get("error")}
        return {"success": True, "meeting": result}
    
    # GET /api/meeting/roles - 获取角色发言风格
    elif path == "/api/meeting/roles" and method == "GET":
        return {"success": True, "roles": ROLE_SPEECH_STYLES}
    
    # POST /api/meeting/run - 一键运行完整讨论
    elif path == "/api/meeting/run" and method == "POST":
        data = json.loads(body) if body else {}
        result = run_full_discussion(
            topic=data.get("topic", ""),
            context=data.get("context")
        )
        return {"success": True, "meeting": result}
    
    # ============== 任务执行系统接口 ==============
    
    # POST /api/task - 创建任务
    elif path == "/api/task" and method == "POST":
        data = json.loads(body) if body else {}
        task = create_task(
            name=data.get("name", ""),
            description=data.get("description", ""),
            project_id=data.get("project_id"),
            assignee_id=data.get("assignee_id"),
            priority=data.get("priority", "medium"),
            due_date=data.get("due_date")
        )
        return {"success": True, "task": task}
    
    # POST /api/tasks/from-conclusion - 从会议结论创建任务
    elif path == "/api/tasks/from-conclusion" and method == "POST":
        data = json.loads(body) if body else {}
        conclusion = data.get("conclusion", "")
        if not conclusion:
            return {"success": False, "error": "conclusion_required"}
        
        tasks = create_tasks_from_conclusion(
            conclusion=conclusion,
            project_id=data.get("project_id"),
            default_assignee_id=data.get("assignee_id")
        )
        return {"success": True, "tasks": tasks, "count": len(tasks)}
    
    # POST /api/task/{id}/assign - 分配任务
    elif path.startswith("/api/task/") and path.endswith("/assign") and method == "POST":
        task_id = path.replace("/api/task/", "").replace("/assign", "")
        if not task_id.isdigit():
            return {"success": False, "error": "invalid_id"}
        
        data = json.loads(body) if body else {}
        employee_id = data.get("employee_id")
        if not employee_id:
            return {"success": False, "error": "employee_id_required"}
        
        result = assign_task(int(task_id), employee_id)
        return result
    
    # POST /api/task/{id}/priority - 设置优先级
    elif path.startswith("/api/task/") and path.endswith("/priority") and method == "POST":
        task_id = path.replace("/api/task/", "").replace("/priority", "")
        if not task_id.isdigit():
            return {"success": False, "error": "invalid_id"}
        
        data = json.loads(body) if body else {}
        priority = data.get("priority", "medium")
        if priority not in ["low", "medium", "high", "urgent"]:
            return {"success": False, "error": "invalid_priority"}
        
        result = set_task_priority(int(task_id), priority)
        return result
    
    # POST /api/task/{id}/due-date - 设置截止日期
    elif path.startswith("/api/task/") and path.endswith("/due-date") and method == "POST":
        task_id = path.replace("/api/task/", "").replace("/due-date", "")
        if not task_id.isdigit():
            return {"success": False, "error": "invalid_id"}
        
        data = json.loads(body) if body else {}
        due_date = data.get("due_date")
        if not due_date:
            return {"success": False, "error": "due_date_required"}
        
        result = set_task_due_date(int(task_id), due_date)
        return result
    
    # POST /api/task/{id}/start - 开始任务
    elif path.startswith("/api/task/") and path.endswith("/start") and method == "POST":
        task_id = path.replace("/api/task/", "").replace("/start", "")
        if not task_id.isdigit():
            return {"success": False, "error": "invalid_id"}
        
        result = start_task(int(task_id))
        return result
    
    # POST /api/task/{id}/progress - 更新进度
    elif path.startswith("/api/task/") and path.endswith("/progress") and method == "POST":
        task_id = path.replace("/api/task/", "").replace("/progress", "")
        if not task_id.isdigit():
            return {"success": False, "error": "invalid_id"}
        
        data = json.loads(body) if body else {}
        progress = data.get("progress", 0)
        message = data.get("message", "")
        
        if progress < 0 or progress > 100:
            return {"success": False, "error": "invalid_progress"}
        
        result = update_task_progress(int(task_id), progress, message)
        return result
    
    # POST /api/task/{id}/log - 添加执行日志
    elif path.startswith("/api/task/") and path.endswith("/log") and method == "POST":
        task_id = path.replace("/api/task/", "").replace("/log", "")
        if not task_id.isdigit():
            return {"success": False, "error": "invalid_id"}
        
        data = json.loads(body) if body else {}
        log = data.get("log", "")
        if not log:
            return {"success": False, "error": "log_required"}
        
        result = add_task_log(int(task_id), log)
        return result
    
    # POST /api/task/{id}/complete - 完成任务
    elif path.startswith("/api/task/") and path.endswith("/complete") and method == "POST":
        task_id = path.replace("/api/task/", "").replace("/complete", "")
        if not task_id.isdigit():
            return {"success": False, "error": "invalid_id"}
        
        data = json.loads(body) if body else {}
        result_text = data.get("result")
        
        result = complete_task(int(task_id), result_text)
        return result
    
    # POST /api/task/{id}/fail - 标记任务失败
    elif path.startswith("/api/task/") and path.endswith("/fail") and method == "POST":
        task_id = path.replace("/api/task/", "").replace("/fail", "")
        if not task_id.isdigit():
            return {"success": False, "error": "invalid_id"}
        
        data = json.loads(body) if body else {}
        reason = data.get("reason", "未知原因")
        
        result = fail_task(int(task_id), reason)
        return result
    
    # GET /api/task/{id} - 获取任务状态
    elif path.startswith("/api/task/") and path.endswith("/status") and method == "GET":
        task_id = path.replace("/api/task/", "").replace("/status", "")
        if not task_id.isdigit():
            return {"success": False, "error": "invalid_id"}
        
        result = get_task_status(int(task_id))
        return result
    
    # GET /api/tasks - 获取任务列表
    elif path == "/api/tasks" and method == "GET":
        status = None
        assignee_id = None
        
        if body:
            data = json.loads(body) if isinstance(body, str) else body
            status = data.get("status")
            assignee_id = data.get("assignee_id")
        
        tasks = get_all_tasks(status=status, assignee_id=assignee_id)
        return {"success": True, "tasks": tasks, "count": len(tasks)}
    
    # GET /api/tasks/statistics - 获取任务统计
    elif path == "/api/tasks/statistics" and method == "GET":
        stats = get_task_statistics()
        return {"success": True, "statistics": stats}
    
    # ============== 提取会议结论中的任务（便捷接口）==============
    
    # POST /api/meeting/extract-tasks - 从会议结论提取任务
    elif path == "/api/meeting/extract-tasks" and method == "POST":
        data = json.loads(body) if body else {}
        conclusion = data.get("conclusion", "")
        if not conclusion:
            return {"success": False, "error": "conclusion_required"}
        
        from core.task_execution import get_task_system
        system = get_task_system()
        extracted = system.extract_tasks_from_conclusion(conclusion)
        
        return {"success": True, "extracted_tasks": extracted, "count": len(extracted)}
    
    # ============== 项目生命周期管理系统API ==============
    
    # 导入项目生命周期服务
    from domains.project_lifecycle_service import (
        get_lifecycle_service,
        ProjectStatus,
        MeetingType
    )
    
    lifecycle = get_lifecycle_service()
    
    # ---- 项目管理 ----
    
    # POST /api/lifecycle/project - 创建项目
    if path == "/api/lifecycle/project" and method == "POST":
        data = json.loads(body) if body else {}
        name = data.get("name", "").strip()
        if not name:
            return {"success": False, "error": "name_required"}
        
        project = lifecycle.create_project(
            name=name,
            description=data.get("description", ""),
            department_id=data.get("department_id", ""),
            budget=data.get("budget", 0),
            owner=data.get("owner", ""),
            tags=data.get("tags", [])
        )
        return {"success": True, "project": project}
    
    # GET /api/lifecycle/project/{id} - 获取项目信息
    if path.startswith("/api/lifecycle/project/") and method == "GET":
        project_id = path.replace("/api/lifecycle/project/", "")
        project = lifecycle.get_project(project_id)
        if not project:
            return {"success": False, "error": "project_not_found"}
        return {"success": True, "project": project}
    
    # GET /api/lifecycle/projects - 列出所有项目
    if path == "/api/lifecycle/projects" and method == "GET":
        status = None
        if body:
            data = json.loads(body) if isinstance(body, str) else body
            status = data.get("status")
        
        projects = lifecycle.list_projects(status=status)
        return {"success": True, "projects": projects, "count": len(projects)}
    
    # PUT /api/lifecycle/project/{id} - 更新项目
    if path.startswith("/api/lifecycle/project/") and method == "PUT":
        project_id = path.replace("/api/lifecycle/project/", "")
        data = json.loads(body) if body else {}
        
        success = lifecycle.update_project(project_id, **data)
        if not success:
            return {"success": False, "error": "project_not_found"}
        return {"success": True, "message": "Project updated"}
    
    # ---- 会议管理 ----
    
    # POST /api/lifecycle/meeting - 创建会议
    if path == "/api/lifecycle/meeting" and method == "POST":
        data = json.loads(body) if body else {}
        project_id = data.get("project_id", "").strip()
        if not project_id:
            return {"success": False, "error": "project_id_required"}
        
        meeting_type = data.get("type", "regular")
        title = data.get("title", "").strip()
        if not title:
            return {"success": False, "error": "title_required"}
        
        meeting = lifecycle.create_meeting(
            project_id=project_id,
            meeting_type=meeting_type,
            title=title,
            host=data.get("host", ""),
            participants=data.get("participants", []),
            agenda=data.get("agenda", ""),
            start_time=data.get("start_time"),
            end_time=data.get("end_time")
        )
        return {"success": True, "meeting": meeting}
    
    # GET /api/lifecycle/meeting/{project_id}/{meeting_id} - 获取会议信息
    if path.startswith("/api/lifecycle/meeting/") and method == "GET":
        parts = path.replace("/api/lifecycle/meeting/", "").split("/")
        if len(parts) != 2:
            return {"success": False, "error": "invalid_path"}
        
        project_id, meeting_id = parts
        meeting = lifecycle.get_meeting(project_id, meeting_id)
        if not meeting:
            return {"success": False, "error": "meeting_not_found"}
        return {"success": True, "meeting": meeting}
    
    # GET /api/lifecycle/meetings/{project_id} - 列出项目会议
    if path.startswith("/api/lifecycle/meetings/") and method == "GET":
        project_id = path.replace("/api/lifecycle/meetings/", "")
        meeting_type = None
        if body:
            data = json.loads(body) if isinstance(body, str) else body
            meeting_type = data.get("type")
        
        meetings = lifecycle.list_meetings(project_id, meeting_type=meeting_type)
        return {"success": True, "meetings": meetings, "count": len(meetings)}
    
    # ---- 立项会议（AI高管辩论）----
    
    # POST /api/lifecycle/kickoff/{project_id} - 发起立项会议
    if path.startswith("/api/lifecycle/kickoff/") and method == "POST":
        project_id = path.replace("/api/lifecycle/kickoff/", "")
        
        context = {}
        if body:
            data = json.loads(body) if isinstance(body, str) else body
            context = {
                "budget": data.get("budget", 200000),
                "deadline": data.get("deadline", "T+90d"),
                "priority": data.get("priority", "medium")
            }
        
        try:
            result = lifecycle.run_kickoff_meeting(project_id, context)
            return {"success": True, "result": result}
        except ValueError as e:
            return {"success": False, "error": str(e)}
    
    # ---- 任务管理 ----
    
    # POST /api/lifecycle/task - 创建任务
    if path == "/api/lifecycle/task" and method == "POST":
        data = json.loads(body) if body else {}
        project_id = data.get("project_id", "").strip()
        if not project_id:
            return {"success": False, "error": "project_id_required"}
        
        name = data.get("name", "").strip()
        if not name:
            return {"success": False, "error": "name_required"}
        
        try:
            task = lifecycle.create_task(
                project_id=project_id,
                name=name,
                description=data.get("description", ""),
                assignee_id=data.get("assignee_id", ""),
                priority=data.get("priority", "medium"),
                due_date=data.get("due_date"),
                milestone_id=data.get("milestone_id")
            )
            return {"success": True, "task": task}
        except ValueError as e:
            return {"success": False, "error": str(e)}
    
    # GET /api/lifecycle/task/{project_id}/{task_id} - 获取任务信息
    if path.startswith("/api/lifecycle/task/") and method == "GET":
        parts = path.replace("/api/lifecycle/task/", "").split("/")
        if len(parts) != 2:
            return {"success": False, "error": "invalid_path"}
        
        project_id, task_id = parts
        task = lifecycle.get_task(project_id, task_id)
        if not task:
            return {"success": False, "error": "task_not_found"}
        return {"success": True, "task": task}
    
    # GET /api/lifecycle/tasks/{project_id} - 列出项目任务
    if path.startswith("/api/lifecycle/tasks/") and method == "GET":
        project_id = path.replace("/api/lifecycle/tasks/", "")
        
        status = None
        assignee_id = None
        if body:
            data = json.loads(body) if isinstance(body, str) else body
            status = data.get("status")
            assignee_id = data.get("assignee_id")
        
        tasks = lifecycle.list_tasks(project_id, status=status, assignee_id=assignee_id)
        return {"success": True, "tasks": tasks, "count": len(tasks)}
    
    # PUT /api/lifecycle/task/{project_id}/{task_id} - 更新任务
    if path.startswith("/api/lifecycle/task/") and method == "PUT":
        parts = path.replace("/api/lifecycle/task/", "").split("/")
        if len(parts) != 2:
            return {"success": False, "error": "invalid_path"}
        
        project_id, task_id = parts
        data = json.loads(body) if body else {}
        
        success = lifecycle.update_task(project_id, task_id, **data)
        if not success:
            return {"success": False, "error": "task_not_found"}
        return {"success": True, "message": "Task updated"}
    
    # ---- 里程碑 ----
    
    # GET /api/lifecycle/milestones/{project_id} - 获取项目里程碑
    if path.startswith("/api/lifecycle/milestones/") and method == "GET":
        project_id = path.replace("/api/lifecycle/milestones/", "")
        milestones = lifecycle.get_milestones(project_id)
        return {"success": True, "milestones": milestones}
    
    # ---- 复盘总结 ----
    
    # POST /api/lifecycle/retrospective - 创建复盘会议
    if path == "/api/lifecycle/retrospective" and method == "POST":
        data = json.loads(body) if body else {}
        project_id = data.get("project_id", "").strip()
        if not project_id:
            return {"success": False, "error": "project_id_required"}
        
        retrospective = lifecycle.create_retrospective(
            project_id=project_id,
            title=data.get("title", "项目复盘"),
            host=data.get("host", ""),
            participants=data.get("participants", []),
            what_went_well=data.get("what_went_well", []),
            what_could_improve=data.get("what_could_improve", []),
            lessons_learned=data.get("lessons_learned", [])
        )
        return {"success": True, "retrospective": retrospective}
    
    # POST /api/lifecycle/complete - 完成项目
    if path == "/api/lifecycle/complete" and method == "POST":
        data = json.loads(body) if body else {}
        project_id = data.get("project_id", "").strip()
        if not project_id:
            return {"success": False, "error": "project_id_required"}
        
        conclusion = data.get("conclusion", "")
        
        try:
            summary = lifecycle.complete_project(project_id, conclusion)
            return {"success": True, "summary": summary}
        except ValueError as e:
            return {"success": False, "error": str(e)}
    
    # ---- 知识库 ----
    
    # GET /api/lifecycle/knowledge/lessons - 获取经验教训
    if path == "/api/lifecycle/knowledge/lessons" and method == "GET":
        lessons = lifecycle.get_knowledge_lessons()
        return {"success": True, "lessons": lessons, "count": len(lessons)}
    
    # GET /api/lifecycle/knowledge/summaries - 获取项目总结
    if path == "/api/lifecycle/knowledge/summaries" and method == "GET":
        summaries = lifecycle.get_knowledge_summaries()
        return {"success": True, "summaries": summaries, "count": len(summaries)}
    
    # ---- 统计 ----
    
    # GET /api/lifecycle/statistics - 获取项目统计
    if path == "/api/lifecycle/statistics" and method == "GET":
        stats = lifecycle.get_project_statistics()
        return {"success": True, "statistics": stats}
    
    # ---- 大屏会议实时数据 ----
    
    # GET /api/dashboard/meeting - 获取大屏会议实时数据
    if path == "/api/dashboard/meeting" and method == "GET":
        # 获取lifecycle服务
        lifecycle = get_lifecycle_service()
        
        # 获取当前进行中的会议（内存中的）
        meeting_result = get_current_meeting()
        
        # 获取所有项目，查找正在进行中的
        all_projects = lifecycle.list_projects()
        active_project = None
        active_meeting = None
        
        for proj in all_projects:
            # 查找该项目下状态为进行中的会议
            proj_meetings = proj.get("meetings", [])
            for meeting_id in proj_meetings:
                meeting = lifecycle.get_meeting(proj["id"], meeting_id)
                if meeting and meeting.get("status") == "in_progress":
                    active_project = proj
                    active_meeting = meeting
                    break
            if active_meeting:
                break
        
        # 构建返回数据
        meeting_data = {
            "has_active_meeting": False,
            "project_name": "",
            "meeting_title": "",
            "status": "",
            "progress": "",
            "speeches": [],
            "participants": []
        }
        
        # 如果有正在进行中的会议（内存中的会议优先）
        if meeting_result.get("success"):
            meeting_data["has_active_meeting"] = True
            meeting_data["meeting_title"] = meeting_result.get("topic", "")
            meeting_data["status"] = meeting_result.get("status", "")
            
            # 计算进度
            participants = meeting_result.get("participants", [])
            current_turn = meeting_result.get("current_turn", 0)
            if participants:
                meeting_data["progress"] = f"{current_turn}/{len(participants)}"
            else:
                meeting_data["progress"] = "0/0"
            
            # 获取发言内容
            speeches = meeting_result.get("speeches", [])
            for speech in speeches:
                meeting_data["speeches"].append({
                    "role": speech.get("speaker_role", ""),
                    "title": speech.get("speaker_title", ""),
                    "content": speech.get("speech_content", ""),
                    "timestamp": speech.get("timestamp", "")
                })
        
        # 如果有正在进行中的项目会议
        elif active_meeting:
            meeting_data["has_active_meeting"] = True
            meeting_data["project_name"] = active_project.get("name", "") if active_project else ""
            meeting_data["meeting_title"] = active_meeting.get("title", "")
            meeting_data["status"] = active_meeting.get("status", "")
            
            # 读取speeches
            speeches = active_meeting.get("speeches", [])
            for speech in speeches:
                meeting_data["speeches"].append({
                    "role": speech.get("speaker_role", ""),
                    "title": speech.get("speaker_title", ""),
                    "content": speech.get("speech_content", ""),
                    "timestamp": speech.get("timestamp", "")
                })
            
            # 进度
            total = len(active_meeting.get("participants", []))
            done = len(speeches)
            meeting_data["progress"] = f"{done}/{total}"
        
        return {"success": True, "meeting": meeting_data}
    
    return {"error": "Not found"}
