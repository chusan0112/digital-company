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

# Import auth module
try:
    from auth.jwt_auth import (
        create_token, verify_token, authenticate_user,
        blacklist_token, init_default_users
    )
    # Initialize default users
    init_default_users()
    AUTH_ENABLED = True
except ImportError:
    AUTH_ENABLED = False

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
    
    return {"error": "Not found"}
