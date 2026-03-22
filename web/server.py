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
    </style>
</head>
<body>
    <div class="header">
        <h1>🏢 金库集团</h1>
        <div class="time">董事长驾驶舱 | <span id="updateTime"></span></div>
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
    
    <script>
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
    server_address = ('', port)
    httpd = HTTPServer(server_address, DashboardHandler)
    print(f"驾驶舱已启动: http://localhost:{port}")
    httpd.serve_forever()


if __name__ == '__main__':
    start_server()
