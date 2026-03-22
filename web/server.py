"""
数字公司 - 驾驶舱 Web界面 - 单屏版
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from company import get_company


def get_dashboard_data():
    company = get_company()
    return company.get_dashboard()


def get_employees_data():
    company = get_company()
    return [
        {
            "id": e.id,
            "name": e.name,
            "role": e.role,
            "status": e.status,
            "skills": e.skills,
            "department_id": e.department_id
        }
        for e in company.list_employees()
    ]


def get_departments_data():
    company = get_company()
    return [
        {
            "id": d.id,
            "name": d.name,
            "employee_count": len([e for e in company.employees if e.department_id == d.id])
        }
        for d in company.list_departments()
    ]


def get_projects_data():
    company = get_company()
    return [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "status": p.status,
            "progress": p.progress
        }
        for p in company.list_projects()
    ]


def get_tasks_data():
    company = get_company()
    return [
        {
            "id": t.id,
            "name": t.name,
            "status": t.status,
            "priority": t.priority,
            "assignee_id": t.assignee_id
        }
        for t in company.list_tasks()
    ]


def get_executive_governance_data():
    """从插件API读取治理数据（容错）"""
    try:
        from api import handle_request
        result = handle_request('/api/dashboard/executive', 'GET', None)
        if isinstance(result, dict) and result.get('success'):
            governance = result.get('dashboard', {}).get('governance', {})
            return {
                "pending_approvals_count": governance.get("pending_approvals_count", 0),
                "recent_decisions": governance.get("recent_decisions", []),
                "recent_approvals": governance.get("recent_approvals", []),
            }
    except Exception:
        pass

    return {
        "pending_approvals_count": 0,
        "recent_decisions": [],
        "recent_approvals": [],
    }


# ============== 实时可视化 API =============

def get_realtime_data():
    """获取实时数据（员工状态、任务进度、会议）"""
    company = get_company()
    
    # 员工实时状态
    employees = []
    for e in company.list_employees():
        # 获取当前任务信息
        current_task = None
        if e.current_task_id:
            task = company.get_task(e.current_task_id)
            if task:
                current_task = {
                    "id": task.id,
                    "name": task.name,
                    "progress": task.progress,
                    "logs": [{"message": l.message, "level": l.level, "timestamp": l.timestamp} for l in task.logs[-5:]]  # 最近5条日志
                }
        
        employees.append({
            "id": e.id,
            "name": e.name,
            "role": e.role,
            "status": e.status,
            "current_task": current_task,
            "skills": e.skills
        })
    
    # 任务进度
    tasks = []
    for t in company.list_tasks():
        assignee = company.get_employee(t.assignee_id)
        tasks.append({
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "status": t.status,
            "priority": t.priority,
            "progress": t.progress,
            "assignee_name": assignee.name if assignee else "未分配",
            "logs": [{"message": l.message, "level": l.level, "timestamp": l.timestamp} for l in t.logs]
        })
    
    # 会议实时画面
    current_meeting = company.get_current_meeting()
    meeting = None
    if current_meeting:
        speaker = company.get_employee(current_meeting.current_speaker_id)
        participants = []
        for pid in current_meeting.participants:
            p = company.get_employee(pid)
            if p:
                participants.append({"id": p.id, "name": p.name, "role": p.role})
        
        meeting = {
            "id": current_meeting.id,
            "title": current_meeting.title,
            "status": current_meeting.status,
            "progress": current_meeting.progress,
            "current_speaker": {"id": speaker.id, "name": speaker.name} if speaker else None,
            "current_speech": current_meeting.current_speech,
            "agenda": current_meeting.agenda,
            "participants": participants
        }
    
    return {
        "employees": employees,
        "tasks": tasks,
        "meeting": meeting,
        "timestamp": datetime.now().isoformat()
    }


def get_employee_realtime(emp_id: str):
    """获取单个员工实时状态"""
    company = get_company()
    emp = company.get_employee(emp_id)
    if not emp:
        return None
    
    current_task = None
    if emp.current_task_id:
        task = company.get_task(emp.current_task_id)
        if task:
            current_task = {
                "id": task.id,
                "name": task.name,
                "status": task.status,
                "progress": task.progress,
                "logs": [{"message": l.message, "level": l.level, "timestamp": l.timestamp} for l in task.logs]
            }
    
    return {
        "id": emp.id,
        "name": emp.name,
        "role": emp.role,
        "status": emp.status,
        "current_task": current_task,
        "skills": emp.skills
    }


def get_tasks_realtime():
    """获取任务实时进度"""
    company = get_company()
    tasks = []
    for t in company.list_tasks():
        assignee = company.get_employee(t.assignee_id)
        tasks.append({
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "status": t.status,
            "priority": t.priority,
            "progress": t.progress,
            "assignee_name": assignee.name if assignee else "未分配",
            "logs": [{"message": l.message, "level": l.level, "timestamp": l.timestamp} for l in t.logs]
        })
    return tasks


def get_meeting_realtime():
    """获取会议实时画面"""
    company = get_company()
    current_meeting = company.get_current_meeting()
    if not current_meeting:
        return None
    
    speaker = company.get_employee(current_meeting.current_speaker_id)
    participants = []
    for pid in current_meeting.participants:
        p = company.get_employee(pid)
        if p:
            participants.append({"id": p.id, "name": p.name, "role": p.role})
    
    return {
        "id": current_meeting.id,
        "title": current_meeting.title,
        "status": current_meeting.status,
        "progress": current_meeting.progress,
        "current_speaker": {"id": speaker.id, "name": speaker.name} if speaker else None,
        "current_speech": current_meeting.current_speech,
        "agenda": current_meeting.agenda,
        "participants": participants
    }


# ============== 交互功能 API =============

def validate_task_data(data: dict) -> tuple:
    """验证任务数据"""
    if not data:
        return False, "请求体不能为空"
    
    name = data.get('name', '').strip()
    if not name:
        return False, "任务名称不能为空"
    if len(name) > 100:
        return False, "任务名称不能超过100个字符"
    
    priority = data.get('priority', 1)
    try:
        priority = int(priority)
        if priority < 1 or priority > 5:
            return False, "优先级必须在1-5之间"
    except (ValueError, TypeError):
        return False, "优先级必须是数字"
    
    return True, None


def validate_employee_status_data(data: dict) -> tuple:
    """验证员工状态更新数据"""
    if not data:
        return False, "请求体不能为空"
    
    emp_id = data.get('employee_id', '').strip()
    if not emp_id:
        return False, "员工ID不能为空"
    
    status = data.get('status', '').strip()
    valid_statuses = ['working', 'idle', 'meeting']
    if status not in valid_statuses:
        return False, f"状态必须是: {', '.join(valid_statuses)}"
    
    return True, None


def validate_expense_data(data: dict) -> tuple:
    """验证支出数据"""
    if not data:
        return False, "请求体不能为空"
    
    amount = data.get('amount')
    if amount is None:
        return False, "支出金额不能为空"
    
    try:
        amount = float(amount)
        if amount <= 0:
            return False, "支出金额必须大于0"
        if amount > 1000000:
            return False, "单笔支出不能超过100万元"
    except (ValueError, TypeError):
        return False, "支出金额必须是有效数字"
    
    description = data.get('description', '').strip()
    if not description:
        return False, "支出描述不能为空"
    if len(description) > 200:
        return False, "支出描述不能超过200个字符"
    
    return True, None


class DashboardHandler(SimpleHTTPRequestHandler):

    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML.encode('utf-8'))
        
        elif self.path == '/realtime.html' or self.path == '/realtime':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(REALTIME_HTML.encode('utf-8'))
        
        elif self.path == '/api/dashboard':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(get_dashboard_data(), ensure_ascii=False).encode('utf-8'))
        
        elif self.path == '/api/employees':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(get_employees_data(), ensure_ascii=False).encode('utf-8'))
        
        elif self.path == '/api/departments':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(get_departments_data(), ensure_ascii=False).encode('utf-8'))
        
        elif self.path == '/api/projects':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(get_projects_data(), ensure_ascii=False).encode('utf-8'))
        
        elif self.path == '/api/tasks':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(get_tasks_data(), ensure_ascii=False).encode('utf-8'))

        elif self.path == '/api/governance':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(get_executive_governance_data(), ensure_ascii=False).encode('utf-8'))

        elif self.path in ['/api/health', '/api/health/']:
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "service": "digital-company-web", "status": "ok"}, ensure_ascii=False).encode('utf-8'))
        
        # ========== 实时可视化 API ==========
        elif self.path == '/api/realtime':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(get_realtime_data(), ensure_ascii=False).encode('utf-8'))
        
        elif self.path == '/api/realtime/tasks':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(get_tasks_realtime(), ensure_ascii=False).encode('utf-8'))
        
        elif self.path == '/api/realtime/meeting':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            meeting = get_meeting_realtime()
            self.wfile.write(json.dumps(meeting if meeting else {}, ensure_ascii=False).encode('utf-8'))
        
        elif self.path.startswith('/api/realtime/employee/'):
            emp_id = self.path.split('/')[-1]
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            emp = get_employee_realtime(emp_id)
            self.wfile.write(json.dumps(emp if emp else {}, ensure_ascii=False).encode('utf-8'))
        
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        """处理POST请求 - 交互功能"""
        if self.path == '/api/tasks/create':
            self.handle_create_task()
        elif self.path == '/api/employees/update-status':
            self.handle_update_employee_status()
        elif self.path == '/api/expenses/add':
            self.handle_add_expense()
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": False, "error": "未找到该接口"}, ensure_ascii=False).encode('utf-8'))

    def handle_create_task(self):
        """创建新任务"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)
        except (json.JSONDecodeError, ValueError):
            self.send_error_response("请求体必须是有效的JSON")
            return

        # 验证数据
        valid, error = validate_task_data(data)
        if not valid:
            self.send_error_response(error)
            return

        # 创建任务
        try:
            company = get_company()
            task = company.create_task(
                name=data['name'].strip(),
                description=data.get('description', '').strip(),
                project_id=data.get('project_id', '').strip(),
                assignee_id=data.get('assignee_id', '').strip(),
                priority=int(data.get('priority', 1))
            )
            
            self.send_response(201)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "message": "任务创建成功",
                "task": {
                    "id": task.id,
                    "name": task.name,
                    "status": task.status,
                    "priority": task.priority
                }
            }, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.send_error_response(f"创建任务失败: {str(e)}")

    def handle_update_employee_status(self):
        """更新员工状态"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)
        except (json.JSONDecodeError, ValueError):
            self.send_error_response("请求体必须是有效的JSON")
            return

        # 验证数据
        valid, error = validate_employee_status_data(data)
        if not valid:
            self.send_error_response(error)
            return

        # 更新状态
        try:
            company = get_company()
            emp = company.get_employee(data['employee_id'])
            if not emp:
                self.send_error_response("员工不存在")
                return
            
            company.update_employee_status(data['employee_id'], data['status'])
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "message": "员工状态更新成功",
                "employee": {
                    "id": emp.id,
                    "name": emp.name,
                    "status": data['status']
                }
            }, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.send_error_response(f"更新员工状态失败: {str(e)}")

    def handle_add_expense(self):
        """添加支出记录"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)
        except (json.JSONDecodeError, ValueError):
            self.send_error_response("请求体必须是有效的JSON")
            return

        # 验证数据
        valid, error = validate_expense_data(data)
        if not valid:
            self.send_error_response(error)
            return

        # 添加支出
        try:
            company = get_company()
            balance = company.get_balance()
            amount = float(data['amount'])
            
            if amount > balance:
                self.send_error_response(f"余额不足，当前余额: ¥{balance}")
                return
            
            success = company.spend(amount, data['description'].strip())
            if not success:
                self.send_error_response("支出失败")
                return
            
            self.send_response(201)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "message": "支出记录添加成功",
                "expense": {
                    "amount": amount,
                    "description": data['description'].strip(),
                    "new_balance": company.get_balance()
                }
            }, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.send_error_response(f"添加支出失败: {str(e)}")

    def send_error_response(self, message: str, status_code: int = 400):
        """发送错误响应"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({
            "success": False,
            "error": message
        }, ensure_ascii=False).encode('utf-8'))


HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>金库集团 - 董事长驾驶舱</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
            min-height: 100vh;
            color: #fff;
            padding: 15px;
        }
        
        .header { text-align: center; padding: 15px 0; }
        .header h1 { font-size: 1.8rem; margin-bottom: 5px; }
        .header .time { color: #888; font-size: 0.8rem; }
        
        /* 单屏布局 */
        .dashboard { 
            display: grid; 
            grid-template-columns: repeat(4, 1fr); 
            gap: 12px;
            max-width: 1400px;
            margin: 0 auto;
        }
        
        /* 卡片 */
        .card {
            background: rgba(255,255,255,0.08);
            border-radius: 12px;
            padding: 15px;
            backdrop-filter: blur(10px);
        }
        
        .card h3 { 
            font-size: 0.85rem; 
            color: #aaa; 
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        /* 统计卡片 */
        .stat-card { text-align: center; }
        .stat-card .value { font-size: 2rem; font-weight: bold; }
        .stat-card .label { color: #888; font-size: 0.75rem; }
        .stat-card.blue .value { color: #4fc3f7; }
        .stat-card.green .value { color: #81c784; }
        .stat-card.orange .value { color: #ffb74d; }
        .stat-card.red .value { color: #e57373; }
        .stat-card.purple .value { color: #ba68c8; }
        
        /* 资金卡片 */
        .money { font-size: 1.8rem; font-weight: bold; }
        .money.green { color: #81c784; }
        .money.red { color: #e57373; }
        
        /* 员工卡片 */
        .employee-list { display: flex; flex-direction: column; gap: 8px; max-height: 280px; overflow-y: auto; }
        .employee { 
            display: flex; 
            align-items: center; 
            gap: 10px; 
            padding: 8px;
            background: rgba(255,255,255,0.05);
            border-radius: 8px;
        }
        .emp-avatar {
            width: 36px; height: 36px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 0.9rem;
        }
        .emp-info { flex: 1; }
        .emp-name { font-weight: bold; font-size: 0.9rem; }
        .emp-role { color: #888; font-size: 0.7rem; }
        
        .status-dot {
            width: 8px; height: 8px;
            border-radius: 50%;
        }
        .status-working { background: #81c784; box-shadow: 0 0 8px #81c784; }
        .status-idle { background: #757575; }
        .status-meeting { background: #ba68c8; box-shadow: 0 0 8px #ba68c8; }
        
        /* 项目/任务 */
        .item-list { display: flex; flex-direction: column; gap: 8px; max-height: 200px; overflow-y: auto; }
        .item { 
            padding: 10px; 
            background: rgba(255,255,255,0.05); 
            border-radius: 8px;
            font-size: 0.85rem;
        }
        .item-name { font-weight: bold; margin-bottom: 4px; }
        .item-desc { color: #888; font-size: 0.75rem; }
        
        .progress-bar {
            height: 6px;
            background: rgba(255,255,255,0.1);
            border-radius: 3px;
            margin-top: 8px;
            overflow: hidden;
        }
        .progress-fill { height: 100%; background: linear-gradient(90deg, #4fc3f7, #81c784); border-radius: 3px; }
        
        .status-tag {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.65rem;
        }
        .tag-planning { background: #ffb74d; color: #000; }
        .tag-running { background: #81c784; color: #000; }
        .tag-completed { background: #4fc3f7; color: #000; }
        .tag-pending { background: #ffb74d; color: #000; }
        .tag-in_progress { background: #81c784; color: #000; }
        
        /* 部门 */
        .dept-list { display: flex; flex-wrap: wrap; gap: 8px; }
        .dept-tag {
            padding: 6px 12px;
            background: rgba(255,255,255,0.1);
            border-radius: 20px;
            font-size: 0.8rem;
        }
        .dept-tag span { color: #4fc3f7; font-weight: bold; }
        
        /* 响应式 */
        @media (max-width: 1200px) {
            .dashboard { grid-template-columns: repeat(2, 1fr); }
        }
        @media (max-width: 600px) {
            .dashboard { grid-template-columns: 1fr; }
        }

        /* 交互按钮 */
        .action-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            color: white;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.8rem;
            margin: 5px;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .action-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        .action-btn.green {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        }
        .action-btn.orange {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }

        /* 模态框 */
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.7);
            backdrop-filter: blur(5px);
        }
        .modal.active { display: flex; align-items: center; justify-content: center; }
        .modal-content {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border-radius: 16px;
            padding: 25px;
            width: 90%;
            max-width: 450px;
            border: 1px solid rgba(255,255,255,0.1);
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
        }
        .modal h3 {
            margin-bottom: 20px;
            font-size: 1.2rem;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .modal-close {
            float: right;
            cursor: pointer;
            font-size: 1.5rem;
            color: #888;
        }
        .modal-close:hover { color: #fff; }

        /* 表单 */
        .form-group { margin-bottom: 15px; }
        .form-group label {
            display: block;
            margin-bottom: 6px;
            color: #aaa;
            font-size: 0.85rem;
        }
        .form-group input, .form-group select, .form-group textarea {
            width: 100%;
            padding: 10px 12px;
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 8px;
            color: #fff;
            font-size: 0.9rem;
        }
        .form-group input:focus, .form-group select:focus, .form-group textarea:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102,126,234,0.2);
        }
        .form-group textarea { resize: vertical; min-height: 80px; }
        .form-group select option { background: #1a1a2e; }

        .form-error {
            color: #e57373;
            font-size: 0.75rem;
            margin-top: 5px;
            display: none;
        }
        .form-group.error input { border-color: #e57373; }
        .form-group.error .form-error { display: block; }

        .form-actions {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
        .form-actions button {
            flex: 1;
            padding: 12px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: all 0.2s;
        }
        .btn-submit {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .btn-submit:hover { transform: translateY(-2px); box-shadow: 0 4px 15px rgba(102,126,234,0.4); }
        .btn-cancel {
            background: rgba(255,255,255,0.1);
            color: #aaa;
        }
        .btn-cancel:hover { background: rgba(255,255,255,0.15); color: #fff; }

        /* Toast 提示 */
        .toast {
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 12px 24px;
            border-radius: 8px;
            color: white;
            font-size: 0.9rem;
            z-index: 2000;
            transform: translateY(100px);
            opacity: 0;
            transition: all 0.3s ease;
        }
        .toast.show { transform: translateY(0); opacity: 1; }
        .toast.success { background: linear-gradient(135deg, #11998e, #38ef7d); }
        .toast.error { background: linear-gradient(135deg, #eb3349, #f45c43); }

        /* 操作按钮区域 */
        .actions-bar {
            display: flex;
            gap: 8px;
            margin-bottom: 10px;
            flex-wrap: wrap;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏢 金库集团</h1>
        <div class="time">董事长驾驶舱 | <span id="updateTime"></span></div>
        <div class="actions-bar">
            <button class="action-btn green" onclick="openModal('taskModal')">➕ 新建任务</button>
            <button class="action-btn orange" onclick="openModal('employeeModal')">👤 员工状态</button>
            <button class="action-btn" onclick="openModal('expenseModal')">💸 添加支出</button>
            <a href="/realtime.html" class="action-btn" style="text-decoration:none;display:inline-block;">🔴 实时驾驶舱</a>
        </div>
    </div>
    
    <div class="dashboard">
        <!-- 财务 -->
        <div class="card">
            <h3>💰 资金状况</h3>
            <div class="money green" id="balance">¥1000</div>
            <div style="color:#888;font-size:0.75rem;margin-top:5px">
                预算 ¥<span id="budget">1000</span> | 已用 ¥<span id="spent">0</span>
            </div>
        </div>
        
        <!-- 员工 -->
        <div class="card">
            <h3>👥 员工 (<span id="empTotal">6</span>人)</h3>
            <div class="employee-list" id="employeeList"></div>
        </div>
        
        <!-- 项目 -->
        <div class="card">
            <h3>📊 项目 (<span id="projTotal">0</span>)</h3>
            <div class="item-list" id="projectList"></div>
        </div>
        
        <!-- 任务 -->
        <div class="card">
            <h3>✅ 任务 (<span id="taskTotal">0</span>)</h3>
            <div class="item-list" id="taskList"></div>
        </div>
        
        <!-- 部门 -->
        <div class="card" style="grid-column: span 2;">
            <h3>🏢 组织架构</h3>
            <div class="dept-list" id="deptList"></div>
        </div>
        
        <!-- 统计 -->
        <div class="card" style="grid-column: span 2;">
            <h3>📈 概览</h3>
            <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;text-align:center">
                <div class="stat-card blue"><div class="value" id="statEmp">6</div><div class="label">员工</div></div>
                <div class="stat-card green"><div class="value" id="statWorking">0</div><div class="label">工作中</div></div>
                <div class="stat-card orange"><div class="value" id="statProj">0</div><div class="label">项目</div></div>
                <div class="stat-card purple"><div class="value" id="statTask">0</div><div class="label">任务</div></div>
            </div>
        </div>

        <!-- 治理 -->
        <div class="card" style="grid-column: span 4;">
            <h3>⚖️ 治理中心</h3>
            <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:10px">
                <div class="dept-tag">待审批 <span id="pendingApprovals">0</span> 项</div>
                <div class="dept-tag">最近决策 <span id="recentDecisionsCount">0</span> 条</div>
                <div class="dept-tag">最近审批 <span id="recentApprovalsCount">0</span> 条</div>
            </div>
            <div class="item-list" id="governanceList"></div>
        </div>

    </div>
    
    <!-- 模态框: 创建任务 -->
    <div id="taskModal" class="modal">
        <div class="modal-content">
            <span class="modal-close" onclick="closeModal('taskModal')">&times;</span>
            <h3>➕ 创建新任务</h3>
            <form id="taskForm" onsubmit="submitTask(event)">
                <div class="form-group">
                    <label>任务名称 *</label>
                    <input type="text" id="taskName" name="name" required maxlength="100" placeholder="输入任务名称">
                    <div class="form-error">任务名称不能为空</div>
                </div>
                <div class="form-group">
                    <label>任务描述</label>
                    <textarea id="taskDesc" name="description" placeholder="描述任务内容（可选）"></textarea>
                </div>
                <div class="form-group">
                    <label>优先级 (1-5)</label>
                    <select id="taskPriority" name="priority">
                        <option value="1">1 - 最低</option>
                        <option value="2">2 - 较低</option>
                        <option value="3" selected>3 - 普通</option>
                        <option value="4">4 - 较高</option>
                        <option value="5">5 - 最高</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>分配员工</label>
                    <select id="taskAssignee" name="assignee_id">
                        <option value="">-- 未分配 --</option>
                    </select>
                </div>
                <div class="form-actions">
                    <button type="button" class="btn-cancel" onclick="closeModal('taskModal')">取消</button>
                    <button type="submit" class="btn-submit">创建任务</button>
                </div>
            </form>
        </div>
    </div>

    <!-- 模态框: 更新员工状态 -->
    <div id="employeeModal" class="modal">
        <div class="modal-content">
            <span class="modal-close" onclick="closeModal('employeeModal')">&times;</span>
            <h3>👤 更新员工状态</h3>
            <form id="employeeForm" onsubmit="submitEmployeeStatus(event)">
                <div class="form-group">
                    <label>选择员工 *</label>
                    <select id="employeeSelect" name="employee_id" required>
                        <option value="">-- 请选择员工 --</option>
                    </select>
                    <div class="form-error">请选择员工</div>
                </div>
                <div class="form-group">
                    <label>新状态 *</label>
                    <select id="employeeStatus" name="status" required>
                        <option value="working">工作中</option>
                        <option value="idle">闲置</option>
                        <option value="meeting">会议中</option>
                    </select>
                    <div class="form-error">请选择状态</div>
                </div>
                <div class="form-actions">
                    <button type="button" class="btn-cancel" onclick="closeModal('employeeModal')">取消</button>
                    <button type="submit" class="btn-submit">更新状态</button>
                </div>
            </form>
        </div>
    </div>

    <!-- 模态框: 添加支出 -->
    <div id="expenseModal" class="modal">
        <div class="modal-content">
            <span class="modal-close" onclick="closeModal('expenseModal')">&times;</span>
            <h3>💸 添加支出记录</h3>
            <form id="expenseForm" onsubmit="submitExpense(event)">
                <div class="form-group">
                    <label>支出金额 (¥) *</label>
                    <input type="number" id="expenseAmount" name="amount" required min="0.01" step="0.01" placeholder="输入金额">
                    <div class="form-error">请输入有效金额</div>
                </div>
                <div class="form-group">
                    <label>支出描述 *</label>
                    <textarea id="expenseDesc" name="description" required maxlength="200" placeholder="描述支出用途"></textarea>
                    <div class="form-error">支出描述不能为空</div>
                </div>
                <div class="form-actions">
                    <button type="button" class="btn-cancel" onclick="closeModal('expenseModal')">取消</button>
                    <button type="submit" class="btn-submit">添加支出</button>
                </div>
            </form>
        </div>
    </div>

    <!-- Toast 提示 -->
    <div id="toast" class="toast"></div>

    <script>
        // ============== 模态框交互 ==============
        let cachedEmployees = [];

        function openModal(modalId) {
            document.getElementById(modalId).classList.add('active');
            
            // 如果是员工选择框，填充员工列表
            if (modalId === 'employeeModal') {
                populateEmployeeSelect();
            }
            // 如果是任务分配框，填充员工列表
            if (modalId === 'taskModal') {
                populateTaskAssigneeSelect();
            }
        }

        function closeModal(modalId) {
            document.getElementById(modalId).classList.remove('active');
            // 重置表单
            const form = document.querySelector(`#${modalId} form`);
            if (form) form.reset();
        }

        // 点击模态框外部关闭
        document.addEventListener('click', function(e) {
            if (e.target.classList.contains('modal')) {
                e.target.classList.remove('active');
            }
        });

        function populateEmployeeSelect() {
            const select = document.getElementById('employeeSelect');
            if (cachedEmployees.length > 0) {
                select.innerHTML = '<option value="">-- 请选择员工 --</option>' + 
                    cachedEmployees.map(e => `<option value="${e.id}">${e.name} (${e.role})</option>`).join('');
            } else {
                fetch('/api/employees').then(r => r.json()).then(emps => {
                    cachedEmployees = emps;
                    select.innerHTML = '<option value="">-- 请选择员工 --</option>' + 
                        emps.map(e => `<option value="${e.id}">${e.name} (${e.role})</option>`).join('');
                });
            }
        }

        function populateTaskAssigneeSelect() {
            const select = document.getElementById('taskAssignee');
            if (cachedEmployees.length > 0) {
                select.innerHTML = '<option value="">-- 未分配 --</option>' + 
                    cachedEmployees.map(e => `<option value="${e.id}">${e.name}</option>`).join('');
            } else {
                fetch('/api/employees').then(r => r.json()).then(emps => {
                    cachedEmployees = emps;
                    select.innerHTML = '<option value="">-- 未分配 --</option>' + 
                        emps.map(e => `<option value="${e.id}">${e.name}</option>`).join('');
                });
            }
        }

        // ============== 表单提交 ==============
        async function submitTask(e) {
            e.preventDefault();
            const form = e.target;
            const data = {
                name: form.name.value.trim(),
                description: form.description.value.trim(),
                priority: parseInt(form.priority.value),
                assignee_id: form.assignee_id.value
            };

            try {
                const res = await fetch('/api/tasks/create', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                const result = await res.json();
                
                if (result.success) {
                    showToast('任务创建成功: ' + result.task.name, 'success');
                    closeModal('taskModal');
                    loadData(); // 刷新数据
                } else {
                    showToast(result.error || '创建失败', 'error');
                }
            } catch(err) {
                showToast('请求失败: ' + err.message, 'error');
            }
        }

        async function submitEmployeeStatus(e) {
            e.preventDefault();
            const form = e.target;
            const data = {
                employee_id: form.employee_id.value,
                status: form.status.value
            };

            if (!data.employee_id) {
                showToast('请选择员工', 'error');
                return;
            }

            try {
                const res = await fetch('/api/employees/update-status', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                const result = await res.json();
                
                if (result.success) {
                    showToast(`员工状态已更新为: ${result.employee.status === 'working' ? '工作中' : result.employee.status === 'idle' ? '闲置' : '会议中'}`, 'success');
                    closeModal('employeeModal');
                    loadData(); // 刷新数据
                } else {
                    showToast(result.error || '更新失败', 'error');
                }
            } catch(err) {
                showToast('请求失败: ' + err.message, 'error');
            }
        }

        async function submitExpense(e) {
            e.preventDefault();
            const form = e.target;
            const data = {
                amount: parseFloat(form.amount.value),
                description: form.description.value.trim()
            };

            if (!data.amount || data.amount <= 0) {
                showToast('请输入有效金额', 'error');
                return;
            }

            try {
                const res = await fetch('/api/expenses/add', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                const result = await res.json();
                
                if (result.success) {
                    showToast(`支出 ¥${data.amount} 添加成功，余额: ¥${result.expense.new_balance}`, 'success');
                    closeModal('expenseModal');
                    loadData(); // 刷新数据
                } else {
                    showToast(result.error || '添加失败', 'error');
                }
            } catch(err) {
                showToast('请求失败: ' + err.message, 'error');
            }
        }

        // ============== Toast 提示 ==============
        function showToast(message, type = 'success') {
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.className = 'toast ' + type + ' show';
            
            setTimeout(() => {
                toast.classList.remove('show');
            }, 3500);
        }

        // ============== 数据加载 ==============
        async function loadData() {
            try {
                const [dash, emps, depts, projs, tasks, governance] = await Promise.all([
                    fetch('/api/dashboard').then(r=>r.json()),
                    fetch('/api/employees').then(r=>r.json()),
                    fetch('/api/departments').then(r=>r.json()),
                    fetch('/api/projects').then(r=>r.json()),
                    fetch('/api/tasks').then(r=>r.json()),
                    fetch('/api/governance').then(r=>r.json())
                ]);
                
                // 缓存员工数据
                cachedEmployees = emps;
                
                // 时间
                document.getElementById('updateTime').textContent = new Date().toLocaleTimeString();
                
                // 财务
                document.getElementById('balance').textContent = '¥' + dash.financial.balance;
                document.getElementById('budget').textContent = dash.financial.budget;
                document.getElementById('spent').textContent = dash.financial.spent;
                
                // 统计
                document.getElementById('empTotal').textContent = dash.employees;
                document.getElementById('projTotal').textContent = dash.projects.total;
                document.getElementById('taskTotal').textContent = dash.tasks.total;
                document.getElementById('statEmp').textContent = dash.employees;
                document.getElementById('statWorking').textContent = dash.employees_by_status.working;
                document.getElementById('statProj').textContent = dash.projects.running;
                document.getElementById('statTask').textContent = dash.tasks.in_progress;
                
                // 部门
                document.getElementById('deptList').innerHTML = depts.map(d => 
                    '<div class="dept-tag">' + d.name + ' <span>' + d.employee_count + '</span>人</div>'
                ).join('');
                
                // 员工
                const statusMap = {working:'工作中',idle:'闲置',meeting:'会议中'};
                const statusClassMap = {working:'status-working',idle:'status-idle',meeting:'status-meeting'};
                document.getElementById('employeeList').innerHTML = emps.map(e => 
                    '<div class="employee">' +
                        '<div class="emp-avatar">' + e.name.charAt(0) + '</div>' +
                        '<div class="emp-info"><div class="emp-name">' + e.name + '</div><div class="emp-role">' + e.role + '</div></div>' +
                        '<div class="status-dot ' + statusClassMap[e.status] + '" title="' + statusMap[e.status] + '"></div>' +
                    '</div>'
                ).join('');
                
                // 项目
                const projStatusMap = {planning:'规划中',running:'进行中',completed:'已完成'};
                document.getElementById('projectList').innerHTML = projs.length ? projs.map(p => 
                    '<div class="item">' +
                        '<div class="item-name">' + p.name + ' <span class="status-tag tag-' + p.status + '">' + projStatusMap[p.status] + '</span></div>' +
                        '<div class="item-desc">' + p.description + '</div>' +
                        '<div class="progress-bar"><div class="progress-fill" style="width:' + p.progress + '%"></div></div>' +
                    '</div>'
                ).join('') : '<div style="color:#666;text-align:center;padding:20px">暂无项目</div>';
                
                // 任务
                const taskStatusMap = {pending:'待处理',in_progress:'进行中',completed:'已完成'};
                document.getElementById('taskList').innerHTML = tasks.length ? tasks.map(t => 
                    '<div class="item">' +
                        '<div class="item-name">' + t.name + ' <span class="status-tag tag-' + t.status + '">' + taskStatusMap[t.status] + '</span></div>' +
                    '</div>'
                ).join('') : '<div style="color:#666;text-align:center;padding:20px">暂无任务</div>';

                // 治理
                const pending = governance.pending_approvals_count || 0;
                const decisionsRaw = governance.recent_decisions || [];
                const approvalsRaw = governance.recent_approvals || [];

                // 排序：高风险优先
                const decisions = decisionsRaw.slice().sort((a, b) => {
                    const ar = (a.policy && a.policy.risk_level) === 'high' ? 1 : 0;
                    const br = (b.policy && b.policy.risk_level) === 'high' ? 1 : 0;
                    return br - ar;
                });

                // 排序：待审批优先
                const approvals = approvalsRaw.slice().sort((a, b) => {
                    const ap = a.status === 'pending' ? 1 : 0;
                    const bp = b.status === 'pending' ? 1 : 0;
                    return bp - ap;
                });

                document.getElementById('pendingApprovals').textContent = pending;
                document.getElementById('recentDecisionsCount').textContent = decisions.length;
                document.getElementById('recentApprovalsCount').textContent = approvals.length;

                const governanceItems = [];
                decisions.slice(0, 4).forEach(d => {
                    const biz = d.intent && d.intent.business_name ? d.intent.business_name : '未命名业务';
                    const summary = d.summary || {};
                    const rec = summary.recommended_option || null;
                    const recText = rec ? ('推荐：' + rec.name + '（预算' + rec.budget + '，周期' + rec.timeline + '）') : '推荐方案：暂无';
                    const policyReasons = (summary.policy_reason_messages || []).join('；');
                    const recStatus = summary.recommended_to_execute_now ? '建议立即执行' : '建议先审批';
                    const riskTag = (d.policy && d.policy.risk_level === 'high') ? '【高风险】' : '';
                    const detail = [recText, recStatus, policyReasons].filter(Boolean).join(' ｜ ');
                    governanceItems.push('<div class="item"><div class="item-name">' + riskTag + ' 决策：' + biz + '</div><div class="item-desc">状态：' + (d.status || 'unknown') + (detail ? ' ｜ ' + detail : '') + '</div></div>');
                });
                approvals.slice(0, 4).forEach(a => {
                    const pendingTag = a.status === 'pending' ? '【待审批】' : '';
                    governanceItems.push('<div class="item"><div class="item-name">' + pendingTag + ' 审批：' + (a.title || '审批单') + '</div><div class="item-desc">状态：' + (a.status || 'unknown') + '</div></div>');
                });

                document.getElementById('governanceList').innerHTML = governanceItems.length
                    ? governanceItems.join('')
                    : '<div style="color:#666;text-align:center;padding:20px">暂无治理记录</div>';
                
            } catch(e) { console.error(e); }
        }
        
        loadData();
        setInterval(loadData, 5000);
    </script>
</body>
</html>"""

# ============== 实时可视化界面 HTML ==============
REALTIME_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>金库集团 - 实时驾驶舱</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0a0a1a 0%, #1a1a2e 50%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
            padding: 15px;
        }
        
        .header { 
            text-align: center; 
            padding: 15px 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            max-width: 1600px;
            margin: 0 auto;
        }
        .header h1 { font-size: 1.8rem; margin-bottom: 5px; }
        .header .time { color: #888; font-size: 0.8rem; }
        .header .live-badge {
            background: linear-gradient(135deg, #e53935, #d32f2f);
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.8rem;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        
        /* 三栏布局 */
        .dashboard { 
            display: grid; 
            grid-template-columns: 1fr 1.2fr 1fr;
            gap: 15px;
            max-width: 1600px;
            margin: 0 auto;
        }
        
        /* 卡片 */
        .card {
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.08);
        }
        
        .card h3 { 
            font-size: 1rem; 
            color: #aaa; 
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        /* 实时状态指示器 */
        .status-dot-lg {
            width: 12px; height: 12px;
            border-radius: 50%;
            display: inline-block;
        }
        .status-idle { background: #757575; }
        .status-working { background: #4caf50; box-shadow: 0 0 12px #4caf50; }
        .status-discussing { background: #2196f3; box-shadow: 0 0 12px #2196f3; }
        .status-resting { background: #ff9800; }
        
        /* 员工卡片 */
        .employee-list { display: flex; flex-direction: column; gap: 10px; max-height: 500px; overflow-y: auto; }
        .employee { 
            display: flex; 
            align-items: center; 
            gap: 12px; 
            padding: 12px;
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            transition: all 0.3s;
        }
        .employee:hover { background: rgba(255,255,255,0.1); }
        .emp-avatar {
            width: 44px; height: 44px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 1.1rem;
            flex-shrink: 0;
        }
        .emp-info { flex: 1; min-width: 0; }
        .emp-name { font-weight: bold; font-size: 0.95rem; }
        .emp-role { color: #888; font-size: 0.75rem; }
        .emp-task { 
            color: #4fc3f7; 
            font-size: 0.75rem; 
            margin-top: 4px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        /* 任务进度 */
        .task-list { display: flex; flex-direction: column; gap: 12px; max-height: 500px; overflow-y: auto; }
        .task { 
            padding: 15px; 
            background: rgba(255,255,255,0.05); 
            border-radius: 12px;
            transition: all 0.3s;
        }
        .task:hover { background: rgba(255,255,255,0.1); }
        .task-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
        .task-name { font-weight: bold; font-size: 0.95rem; }
        .task-status {
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.7rem;
            font-weight: bold;
        }
        .task-pending { background: #ff9800; color: #000; }
        .task-in_progress { background: #4caf50; color: #fff; }
        .task-completed { background: #2196f3; color: #fff; }
        
        .progress-bar {
            height: 8px;
            background: rgba(255,255,255,0.1);
            border-radius: 4px;
            overflow: hidden;
            margin: 10px 0;
        }
        .progress-fill { 
            height: 100%; 
            background: linear-gradient(90deg, #667eea, #4caf50); 
            border-radius: 4px;
            transition: width 0.5s ease;
        }
        
        .task-logs {
            margin-top: 10px;
            padding: 8px;
            background: rgba(0,0,0,0.3);
            border-radius: 8px;
            font-size: 0.7rem;
            max-height: 80px;
            overflow-y: auto;
        }
        .log-item { padding: 2px 0; }
        .log-info { color: #aaa; }
        .log-success { color: #4caf50; }
        .log-warning { color: #ff9800; }
        .log-error { color: #f44336; }
        
        /* 会议实时画面 */
        .meeting-card { 
            grid-column: 3;
            grid-row: 1 / 3;
        }
        .meeting-current {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 15px;
        }
        .meeting-title { font-size: 1.2rem; font-weight: bold; margin-bottom: 15px; }
        .speaker-section {
            display: flex;
            align-items: center;
            gap: 15px;
            padding: 15px;
            background: rgba(0,0,0,0.2);
            border-radius: 10px;
            margin-bottom: 15px;
        }
        .speaker-avatar {
            width: 50px; height: 50px;
            border-radius: 50%;
            background: linear-gradient(135deg, #f093fb, #f5576c);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.3rem;
        }
        .speaker-info { flex: 1; }
        .speaker-name { font-weight: bold; font-size: 1rem; }
        .speaker-label { color: #aaa; font-size: 0.75rem; }
        
        .speech-bubble {
            background: rgba(255,255,255,0.1);
            padding: 15px;
            border-radius: 12px;
            font-size: 0.9rem;
            line-height: 1.5;
            min-height: 60px;
        }
        
        .meeting-progress { margin-top: 15px; }
        .progress-text { 
            display: flex; 
            justify-content: space-between; 
            font-size: 0.75rem; 
            color: #aaa;
            margin-bottom: 5px;
        }
        
        .agenda-list { margin-top: 15px; }
        .agenda-item {
            padding: 8px 12px;
            margin: 5px 0;
            border-radius: 8px;
            font-size: 0.85rem;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .agenda-done { background: rgba(76,175,80,0.2); color: #81c784; }
        .agenda-current { background: rgba(33,150,243,0.3); color: #64b5f6; }
        .agenda-pending { background: rgba(255,255,255,0.05); color: #888; }
        
        .no-meeting {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        
        .nav-tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
        }
        .nav-tab {
            padding: 8px 16px;
            background: rgba(255,255,255,0.05);
            border: none;
            color: #aaa;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.85rem;
            transition: all 0.3s;
        }
        .nav-tab.active {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: #fff;
        }
        
        /* 统计栏 */
        .stats-row {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
            margin-bottom: 15px;
        }
        .stat-box {
            text-align: center;
            padding: 12px;
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
        }
        .stat-value { font-size: 1.5rem; font-weight: bold; }
        .stat-label { color: #888; font-size: 0.7rem; }
        
        /* 滚动条样式 */
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: rgba(255,255,255,0.05); border-radius: 3px; }
        ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.2); border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.3); }
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1>🏢 金库集团 - 实时驾驶舱</h1>
            <div class="time">实时更新 | <span id="updateTime"></span></div>
        </div>
        <div class="live-badge">🔴 LIVE</div>
    </div>
    
    <div class="dashboard">
        <!-- 左侧：员工实时状态 -->
        <div class="card">
            <h3>👥 员工实时状态 <span class="status-dot-lg status-working"></span></h3>
            <div class="stats-row">
                <div class="stat-box">
                    <div class="stat-value" id="statIdle">0</div>
                    <div class="stat-label">空闲</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value" id="statWorking" style="color:#4caf50">0</div>
                    <div class="stat-label">工作中</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value" id="statDiscussing" style="color:#2196f3">0</div>
                    <div class="stat-label">讨论中</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value" id="statResting" style="color:#ff9800">0</div>
                    <div class="stat-label">休息中</div>
                </div>
            </div>
            <div class="employee-list" id="employeeList"></div>
        </div>
        
        <!-- 中间：任务进度 -->
        <div class="card">
            <h3>📋 任务进度</h3>
            <div class="nav-tabs">
                <button class="nav-tab active" onclick="filterTasks('all')">全部</button>
                <button class="nav-tab" onclick="filterTasks('pending')">待处理</button>
                <button class="nav-tab" onclick="filterTasks('in_progress')">进行中</button>
                <button class="nav-tab" onclick="filterTasks('completed')">已完成</button>
            </div>
            <div class="task-list" id="taskList"></div>
        </div>
        
        <!-- 右侧：会议实时画面 -->
        <div class="card meeting-card">
            <h3>🎙️ 会议实时画面</h3>
            <div id="meetingContent">
                <div class="no-meeting">暂无进行中的会议</div>
            </div>
        </div>
    </div>
    
    <script>
        let allTasks = [];
        
        // 状态映射
        const statusMap = {
            'idle': { text: '空闲', class: 'status-idle' },
            'working': { text: '工作中', class: 'status-working' },
            'discussing': { text: '讨论中', class: 'status-discussing' },
            'resting': { text: '休息中', class: 'status-resting' }
        };
        
        const taskStatusMap = {
            'pending': { text: '待处理', class: 'task-pending' },
            'in_progress': { text: '进行中', class: 'task-in_progress' },
            'completed': { text: '已完成', class: 'task-completed' }
        };
        
        async function loadRealtimeData() {
            try {
                const [realtime] = await Promise.all([
                    fetch('/api/realtime').then(r => r.json())
                ]);
                
                // 更新时间
                document.getElementById('updateTime').textContent = new Date().toLocaleTimeString();
                
                // 更新员工统计
                const statusCounts = { idle: 0, working: 0, discussing: 0, resting: 0 };
                realtime.employees.forEach(e => {
                    if (statusCounts[e.status] !== undefined) {
                        statusCounts[e.status]++;
                    }
                });
                document.getElementById('statIdle').textContent = statusCounts.idle;
                document.getElementById('statWorking').textContent = statusCounts.working;
                document.getElementById('statDiscussing').textContent = statusCounts.discussing;
                document.getElementById('statResting').textContent = statusCounts.resting;
                
                // 更新员工列表
                const empHtml = realtime.employees.map(e => {
                    const s = statusMap[e.status] || statusMap.idle;
                    const taskInfo = e.current_task ? 
                        `<div class="emp-task">📌 任务: ${e.current_task.name} (${e.current_task.progress}%)</div>` : 
                        '';
                    return `
                        <div class="employee">
                            <div class="emp-avatar">${e.name.charAt(0)}</div>
                            <div class="emp-info">
                                <div class="emp-name">${e.name}</div>
                                <div class="emp-role">${e.role}</div>
                                ${taskInfo}
                            </div>
                            <span class="status-dot-lg ${s.class}" title="${s.text}"></span>
                        </div>
                    `;
                }).join('');
                document.getElementById('employeeList').innerHTML = empHtml;
                
                // 更新任务列表
                allTasks = realtime.tasks;
                renderTasks(allTasks);
                
                // 更新会议
                if (realtime.meeting) {
                    updateMeetingUI(realtime.meeting);
                } else {
                    document.getElementById('meetingContent').innerHTML = 
                        '<div class="no-meeting">暂无进行中的会议</div>';
                }
                
            } catch(e) { 
                console.error('Load realtime data error:', e); 
            }
        }
        
        function renderTasks(tasks) {
            const taskHtml = tasks.map(t => {
                const s = taskStatusMap[t.status] || taskStatusMap.pending;
                const logsHtml = t.logs.slice(-3).map(l => 
                    `<div class="log-item log-${l.level}">${l.message}</div>`
                ).join('');
                
                return `
                    <div class="task">
                        <div class="task-header">
                            <div class="task-name">${t.name}</div>
                            <span class="task-status ${s.class}">${s.text}</span>
                        </div>
                        <div style="color:#888;font-size:0.75rem">👤 ${t.assignee_name}</div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width:${t.progress}%"></div>
                        </div>
                        <div style="display:flex;justify-content:space-between;font-size:0.7rem;color:#aaa">
                            <span>优先级: ${t.priority}</span>
                            <span>进度: ${t.progress}%</span>
                        </div>
                        ${logsHtml ? `<div class="task-logs">${logsHtml}</div>` : ''}
                    </div>
                `;
            }).join('');
            document.getElementById('taskList').innerHTML = taskHtml || '<div class="no-meeting">暂无任务</div>';
        }
        
        function filterTasks(status) {
            // 更新tab状态
            document.querySelectorAll('.nav-tab').forEach(tab => {
                tab.classList.remove('active');
            });
            event.target.classList.add('active');
            
            // 过滤任务
            if (status === 'all') {
                renderTasks(allTasks);
            } else {
                renderTasks(allTasks.filter(t => t.status === status));
            }
        }
        
        function updateMeetingUI(m) {
            const speaker = m.current_speaker || { name: '等待发言' };
            const agendaHtml = m.agenda.map((item, idx) => {
                let cls = 'agenda-pending';
                if (idx < Math.floor(m.progress / 100 * m.agenda.length)) {
                    cls = 'agenda-done';
                } else if (idx === Math.floor(m.progress / 100 * m.agenda.length)) {
                    cls = 'agenda-current';
                }
                return `<div class="agenda-item ${cls}">✓ ${item}</div>`;
            }).join('');
            
            document.getElementById('meetingContent').innerHTML = `
                <div class="meeting-current">
                    <div class="meeting-title">${m.title}</div>
                    
                    <div class="speaker-section">
                        <div class="speaker-avatar">${speaker.name.charAt(0)}</div>
                        <div class="speaker-info">
                            <div class="speaker-name">${speaker.name}</div>
                            <div class="speaker-label">正在发言</div>
                        </div>
                    </div>
                    
                    <div class="speech-bubble">${m.current_speech || '...'}</div>
                    
                    <div class="meeting-progress">
                        <div class="progress-text">
                            <span>讨论进度</span>
                            <span>${m.progress}%</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width:${m.progress}%"></div>
                        </div>
                    </div>
                </div>
                
                <h4 style="color:#aaa;margin-bottom:10px;font-size:0.9rem">📋 会议议程</h4>
                <div class="agenda-list">${agendaHtml}</div>
                
                <h4 style="color:#aaa;margin:15px 0 10px;font-size:0.9rem">👥 参会人员 (${m.participants.length})</h4>
                <div style="display:flex;flex-wrap:wrap;gap:8px">
                    ${m.participants.map(p => 
                        `<div style="padding:5px 12px;background:rgba(255,255,255,0.1);border-radius:15px;font-size:0.8rem">
                            ${p.name}
                        </div>`
                    ).join('')}
                </div>
            `;
        }
        
        // 初始加载
        loadRealtimeData();
        
        // 每2秒更新一次（实时）
        setInterval(loadRealtimeData, 2000);
    </script>
</body>
</html>"""


def start_server(port=8080):
    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, DashboardHandler)
    print(f"驾驶舱已启动: http://localhost:{port}")
    httpd.serve_forever()


if __name__ == '__main__':
    start_server()
