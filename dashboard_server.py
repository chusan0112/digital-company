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

app = Flask(__name__)

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


if __name__ == '__main__':
    print("=" * 50)
    print("[Dashboard] JinKu Group Digital Company")
    print("=" * 50)
    print("[OpenClaw] Connecting to real-time data...")
    print("[Web] Access: http://127.0.0.1:8080")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)
