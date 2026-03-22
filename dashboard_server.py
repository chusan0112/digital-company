# -*- coding: utf-8 -*-
"""
Flask-based Digital Company Dashboard Server
连接OpenClaw真实数据的实时驾驶舱
"""
import sys
import os

os.chdir(r'C:\Users\Administrator\.openclaw\skills\digital-company')
sys.path.insert(0, r'C:\Users\Administrator\.openclaw\skills\digital-company')

from flask import Flask, jsonify, request, send_from_directory, Response
import json
from datetime import datetime

# 导入OpenClaw实时数据模块
from integrations.openclaw_realtime import get_realtime, OpenClawRealtime

# 导入生命周期服务
from domains.project_lifecycle_service import get_lifecycle_service

app = Flask(__name__)

# 初始化生命周期服务
lifecycle = get_lifecycle_service()

# 初始化实时数据获取器
realtime = get_realtime()
realtime.start_auto_update()


@app.route('/')
def index():
    """主页 - 驾驶舱"""
    return send_from_directory('.', 'dashboard.html')


# ============== 实时数据API ==============

@app.route('/api/realtime/dashboard')
def api_realtime_dashboard():
    """获取实时驾驶舱数据"""
    return jsonify(realtime.get_dashboard_data())


@app.route('/api/realtime/agents')
def api_realtime_agents():
    """获取所有Agent列表"""
    return jsonify(realtime.list_agents())


@app.route('/api/realtime/agents/<agent_id>')
def api_realtime_agent(agent_id):
    """获取单个Agent详情"""
    agent = realtime.get_agent_detail(agent_id)
    if agent:
        return jsonify(agent)
    return jsonify({"error": "Agent not found"}), 404


@app.route('/api/realtime/agents/<agent_id>/sessions')
def api_realtime_sessions(agent_id):
    """获取Agent的会话历史"""
    sessions = realtime.get_sessions(agent_id)
    return jsonify({"sessions": sessions})


@app.route('/api/realtime/agents/<agent_id>/messages')
def api_realtime_messages(agent_id):
    """获取Agent的最近消息"""
    limit = request.args.get('limit', 10, type=int)
    messages = realtime.get_recent_messages(agent_id, limit)
    return jsonify({"messages": messages})


@app.route('/api/realtime/task', methods=['POST'])
def api_realtime_task():
    """向Agent发送任务"""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Invalid request body"}), 400
    
    agent_id = data.get("agent_id")
    task = data.get("task")
    
    if not agent_id or not task:
        return jsonify({"success": False, "error": "agent_id and task required"}), 400
    
    try:
        task_id = realtime.send_task(agent_id, task)
        return jsonify({"success": True, "task_id": task_id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============== 会议发言API ==============

@app.route('/api/realtime/meeting/speak', methods=['POST'])
def api_meeting_speak():
    """让员工发言"""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Invalid request body"}), 400
    
    agent_id = data.get("agent_id")
    topic = data.get("topic")
    
    if not agent_id or not topic:
        return jsonify({"success": False, "error": "agent_id and topic required"}), 400
    
    try:
        speech = realtime.request_speech(agent_id, topic)
        return jsonify({
            "success": True,
            "agent_id": agent_id,
            "speech": speech
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============== SSE - Server Sent Events ==============

@app.route('/api/realtime/stream')
def api_realtime_stream():
    """SSE流 - 实时推送数据更新"""
    import queue
    
    def generate():
        q = queue.Queue()
        
        def callback(agents, tasks):
            try:
                q.put_nowait({
                    "agents": [a.to_dict() for a in agents.values()],
                    "tasks": {k: v.to_dict() for k, v in tasks.items()},
                    "timestamp": datetime.now().isoformat()
                })
            except:
                pass
        
        realtime.register_callback(callback)
        
        try:
            while True:
                try:
                    data = q.get(timeout=30)
                    yield f"data: {json.dumps(data)}\n\n"
                except queue.Empty:
                    yield f"data: {json.dumps({'keepalive': True})}\n\n"
        finally:
            pass
    
    return Response(generate(), mimetype='text/event-stream')


# ============== 健康检查 ==============

@app.route('/api/health')
def health():
    return jsonify({
        "success": True,
        "service": "digital-company-dashboard",
        "status": "ok",
        "openclaw_connected": True,
        "realtime_mode": True
    })


# ============== 生命周期API ==============

# POST /api/lifecycle/project - 创建项目
@app.route('/api/lifecycle/project', methods=['POST'])
def api_create_project():
    """创建项目"""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Invalid request body"}), 400
    
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"success": False, "error": "name_required"}), 400
    
    try:
        project = lifecycle.create_project(
            name=name,
            description=data.get("description", ""),
            department_id=data.get("department_id", ""),
            budget=data.get("budget", 0),
            owner=data.get("owner", ""),
            tags=data.get("tags", [])
        )
        return jsonify({"success": True, "project": project})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# GET /api/lifecycle/projects - 列出所有项目
@app.route('/api/lifecycle/projects', methods=['GET'])
def api_list_projects():
    """列出所有项目"""
    status = request.args.get('status')
    try:
        projects = lifecycle.list_projects(status=status)
        return jsonify({"success": True, "projects": projects, "count": len(projects)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# GET /api/lifecycle/project/<project_id> - 获取项目信息
@app.route('/api/lifecycle/project/<project_id>', methods=['GET'])
def api_get_project(project_id):
    """获取项目信息"""
    try:
        project = lifecycle.get_project(project_id)
        if not project:
            return jsonify({"success": False, "error": "project_not_found"}), 404
        return jsonify({"success": True, "project": project})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# POST /api/lifecycle/kickoff/<project_id> - 发起立项会议
@app.route('/api/lifecycle/kickoff/<project_id>', methods=['POST'])
def api_kickoff_meeting(project_id):
    """发起立项会议"""
    data = request.get_json() or {}
    context = {
        "budget": data.get("budget", 1000),
        "deadline": data.get("deadline", "T+30d"),
        "priority": data.get("priority", "high"),
        "target": data.get("target", "日入1000元")
    }
    
    try:
        result = lifecycle.run_kickoff_meeting(project_id, context)
        return jsonify({"success": True, "result": result})
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# GET /api/lifecycle/meetings/<project_id> - 列出项目会议
@app.route('/api/lifecycle/meetings/<project_id>', methods=['GET'])
def api_list_meetings(project_id):
    """列出项目会议"""
    meeting_type = request.args.get('type')
    try:
        meetings = lifecycle.list_meetings(project_id, meeting_type=meeting_type)
        return jsonify({"success": True, "meetings": meetings, "count": len(meetings)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# GET /api/lifecycle/meeting/<project_id>/<meeting_id> - 获取会议信息
@app.route('/api/lifecycle/meeting/<project_id>/<meeting_id>', methods=['GET'])
def api_get_meeting(project_id, meeting_id):
    """获取会议信息"""
    try:
        meeting = lifecycle.get_meeting(project_id, meeting_id)
        if not meeting:
            return jsonify({"success": False, "error": "meeting_not_found"}), 404
        return jsonify({"success": True, "meeting": meeting})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# GET /api/lifecycle/tasks/<project_id> - 列出项目任务
@app.route('/api/lifecycle/tasks/<project_id>', methods=['GET'])
def api_list_tasks(project_id):
    """列出项目任务"""
    status = request.args.get('status')
    assignee_id = request.args.get('assignee_id')
    try:
        tasks = lifecycle.list_tasks(project_id, status=status, assignee_id=assignee_id)
        return jsonify({"success": True, "tasks": tasks, "count": len(tasks)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# GET /api/lifecycle/milestones/<project_id> - 获取项目里程碑
@app.route('/api/lifecycle/milestones/<project_id>', methods=['GET'])
def api_get_milestones(project_id):
    """获取项目里程碑"""
    try:
        milestones = lifecycle.get_milestones(project_id)
        return jsonify({"success": True, "milestones": milestones})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# GET /api/lifecycle/statistics - 获取项目统计
@app.route('/api/lifecycle/statistics', methods=['GET'])
def api_lifecycle_statistics():
    """获取项目统计"""
    try:
        stats = lifecycle.get_project_statistics()
        return jsonify({"success": True, "statistics": stats})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# GET /api/lifecycle/active-meeting - 获取当前进行中的会议
@app.route('/api/lifecycle/active-meeting', methods=['GET'])
def api_active_meeting():
    """获取当前进行中的会议"""
    try:
        # 获取所有项目中的会议
        projects = lifecycle.list_projects()
        for project in projects:
            meetings = lifecycle.list_meetings(project.get("id"))
            for meeting in meetings:
                if meeting.get("status") == "in_progress":
                    return jsonify({
                        "success": True,
                        "meeting": meeting,
                        "project": project
                    })
        return jsonify({"success": True, "meeting": None})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# GET /api/dashboard/meeting - 获取大屏会议实时数据
@app.route('/api/dashboard/meeting', methods=['GET'])
def api_dashboard_meeting():
    """获取大屏会议实时数据"""
    try:
        # 获取所有项目，查找最近完成的会议（优先显示立项会议）
        all_projects = lifecycle.list_projects()
        latest_meeting = None
        latest_project = None
        
        for proj in all_projects:
            proj_meetings = proj.get("meetings", [])
            for meeting_id in proj_meetings:
                meeting = lifecycle.get_meeting(proj["id"], meeting_id)
                if meeting and meeting.get("type") == "kickoff":
                    if not latest_meeting or meeting.get("start_time", "") > latest_meeting.get("start_time", ""):
                        latest_meeting = meeting
                        latest_project = proj
        
        # 如果没有找到kickoff会议，找最近的任何会议
        if not latest_meeting:
            for proj in all_projects:
                proj_meetings = proj.get("meetings", [])
                for meeting_id in proj_meetings:
                    meeting = lifecycle.get_meeting(proj["id"], meeting_id)
                    if meeting:
                        if not latest_meeting or meeting.get("start_time", "") > latest_meeting.get("start_time", ""):
                            latest_meeting = meeting
                            latest_project = proj
        
        # 构建返回数据
        meeting_data = {
            "has_active_meeting": latest_meeting is not None,
            "project_name": latest_project.get("name", "") if latest_project else "",
            "meeting_title": latest_meeting.get("title", "") if latest_meeting else "",
            "status": latest_meeting.get("status", "") if latest_meeting else "",
            "progress": "",
            "speeches": latest_meeting.get("speeches", []) if latest_meeting else [],
            "participants": latest_meeting.get("participants", []) if latest_meeting else [],
            "summary": latest_meeting.get("summary", {}) if latest_meeting else {}
        }
        
        # 计算进度
        if latest_meeting:
            speeches = latest_meeting.get("speeches", [])
            if speeches:
                meeting_data["progress"] = f"{len(speeches)}/{len(latest_meeting.get('participants', []))}"
                
                # 格式化speeches供前端使用
                formatted_speeches = []
                for speech in speeches:
                    # 兼容新旧格式
                    role = speech.get("speaker_role") or speech.get("role", "")
                    title = speech.get("speaker_title") or speech.get("title", "")
                    content = speech.get("speech_content") or speech.get("content", "")
                    is_real = speech.get("is_real_ai", False)
                    agent_id = speech.get("agent_id", "")
                    timestamp = speech.get("timestamp", "")
                    
                    formatted_speeches.append({
                        "role": role,
                        "title": title,
                        "content": content,
                        "is_real_ai": is_real,
                        "agent_id": agent_id,
                        "timestamp": timestamp
                    })
                meeting_data["speeches"] = formatted_speeches
            else:
                meeting_data["progress"] = "已完成"
        
        return jsonify({"success": True, "meeting": meeting_data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == '__main__':
    print("=" * 50)
    print("[Dashboard] JinKu Group Digital Company")
    print("=" * 50)
    print("[OpenClaw] Connecting to real-time data...")
    print("[Web] Access: http://127.0.0.1:8080")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)
