"""
数字公司 - 驾驶舱 Web界面 - 单屏版
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import os
import sys

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


def start_server(port=8080):
    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, DashboardHandler)
    print(f"驾驶舱已启动: http://localhost:{port}")
    httpd.serve_forever()


if __name__ == '__main__':
    start_server()
