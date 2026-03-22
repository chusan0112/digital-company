# -*- coding: utf-8 -*-
"""
Flask-based Digital Company Server
With JWT Authentication
"""
import sys
import os

os.chdir(r'C:\Users\Administrator\.openclaw\skills\digital-company')
sys.path.insert(0, r'C:\Users\Administrator\.openclaw\skills\digital-company')

from flask import Flask, jsonify, request, send_from_directory
from company import get_company

# Import auth module
from auth.jwt_auth import (
    create_token, verify_token, authenticate_user,
    blacklist_token, is_token_blacklisted, init_default_users,
    require_auth
)

app = Flask(__name__)

# Initialize default users on startup
init_default_users()


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


# ============== Authentication Endpoints ==============

@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login - returns JWT token"""
    data = request.get_json()
    
    if not data:
        return jsonify({"success": False, "error": "Invalid request body"}), 400
    
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({
            "success": False, 
            "error": "Username and password are required"
        }), 400
    
    # Authenticate user
    user = authenticate_user(username, password)
    
    if not user:
        return jsonify({
            "success": False, 
            "error": "Invalid username or password"
        }), 401
    
    # Create JWT token
    token = create_token(user['id'], user['username'], user['role'])
    
    return jsonify({
        "success": True,
        "message": "Login successful",
        "token": token,
        "user": {
            "id": user['id'],
            "username": user['username'],
            "role": user['role']
        }
    })


@app.route('/api/auth/logout', methods=['POST'])
@require_auth
def logout():
    """User logout - blacklists the token"""
    # Get token from header
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        blacklist_token(token)
    
    return jsonify({
        "success": True,
        "message": "Logout successful"
    })


@app.route('/api/auth/verify', methods=['GET'])
@require_auth
def verify():
    """Verify token - returns user info if valid"""
    user = request.user
    
    return jsonify({
        "success": True,
        "user": {
            "id": user.get('user_id'),
            "username": user.get('username'),
            "role": user.get('role')
        }
    })


# ============== Public API Endpoints ==============

@app.route('/api/dashboard')
def dashboard():
    return jsonify(get_company().get_dashboard())


@app.route('/api/employees')
def employees():
    return jsonify([e.__dict__ for e in get_company().list_employees()])


@app.route('/api/departments')
def departments():
    return jsonify([d.__dict__ for d in get_company().list_departments()])


@app.route('/api/projects')
def projects():
    return jsonify([p.__dict__ for p in get_company().list_projects()])


@app.route('/api/tasks')
def tasks():
    return jsonify([t.__dict__ for t in get_company().list_tasks()])


@app.route('/api/governance')
def governance():
    return jsonify([])


# ============== Protected API Endpoints ==============

@app.route('/api/protected/dashboard', methods=['GET'])
@require_auth
def protected_dashboard():
    """Protected dashboard endpoint"""
    return jsonify({
        "success": True,
        "data": get_company().get_dashboard(),
        "user": request.user
    })


@app.route('/api/protected/employees', methods=['GET'])
@require_auth
def protected_employees():
    """Protected employees endpoint"""
    return jsonify({
        "success": True,
        "data": [e.__dict__ for e in get_company().list_employees()],
        "user": request.user
    })


# ============== Health Check ==============

@app.route('/api/health')
def health():
    return jsonify({
        "success": True,
        "service": "digital-company",
        "status": "ok",
        "auth_enabled": True
    })


# ============== Meeting Room API ==============

@app.route('/api/meeting-rooms', methods=['GET'])
def get_meeting_rooms():
    """获取所有会议室"""
    from db.sqlite_repository import MeetingRoomRepository
    status = request.args.get('status')
    rooms = MeetingRoomRepository.get_all(status=status)
    return jsonify({"success": True, "meeting_rooms": rooms})


@app.route('/api/meeting-rooms', methods=['POST'])
def create_meeting_room():
    """创建会议室"""
    from db.sqlite_repository import MeetingRoomRepository
    data = request.get_json()
    
    if not data:
        return jsonify({"success": False, "error": "Invalid request body"}), 400
    
    name = data.get('name', '').strip()
    capacity = data.get('capacity', 0)
    location = data.get('location', '')
    status = data.get('status', 'available')
    
    if not name:
        return jsonify({"success": False, "error": "name_required"}), 400
    if capacity <= 0:
        return jsonify({"success": False, "error": "capacity_required"}), 400
    
    room_id = MeetingRoomRepository.create(name=name, capacity=capacity, location=location, status=status)
    return jsonify({"success": True, "id": room_id, "message": "Meeting room created"})


@app.route('/api/meeting-rooms/<int:room_id>', methods=['PUT'])
def update_meeting_room(room_id):
    """更新会议室"""
    from db.sqlite_repository import MeetingRoomRepository
    data = request.get_json()
    
    if not data:
        return jsonify({"success": False, "error": "Invalid request body"}), 400
    
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
        return jsonify({"success": False, "error": "no_fields_to_update"}), 400
    
    success = MeetingRoomRepository.update(room_id, **updates)
    return jsonify({"success": success, "message": "Meeting room updated" if success else "Meeting room not found"})


@app.route('/api/meeting-rooms/<int:room_id>', methods=['DELETE'])
def delete_meeting_room(room_id):
    """删除会议室"""
    from db.sqlite_repository import MeetingRoomRepository
    success = MeetingRoomRepository.delete(room_id)
    return jsonify({"success": success, "message": "Meeting room deleted" if success else "Meeting room not found"})


# ============== Meeting API ==============

@app.route('/api/meetings', methods=['GET'])
def get_meetings():
    """获取会议列表"""
    from db.sqlite_repository import MeetingRepository
    host_id = request.args.get('host_id', type=int)
    status = request.args.get('status')
    meeting_room_id = request.args.get('meeting_room_id', type=int)
    
    meetings = MeetingRepository.get_all(host_id=host_id, status=status)
    
    # 过滤会议室
    if meeting_room_id:
        meetings = [m for m in meetings if m.get("meeting_room_id") == meeting_room_id]
    
    return jsonify({"success": True, "meetings": meetings})


@app.route('/api/meetings', methods=['POST'])
def create_meeting():
    """预订会议"""
    from db.sqlite_repository import MeetingRepository
    data = request.get_json()
    
    if not data:
        return jsonify({"success": False, "error": "Invalid request body"}), 400
    
    title = data.get('title', '').strip()
    host_id = data.get('host_id')
    start_time = data.get('start_time', '').strip()
    end_time = data.get('end_time', '').strip()
    meeting_room_id = data.get('meeting_room_id')
    notes = data.get('notes', '')
    
    if not title:
        return jsonify({"success": False, "error": "title_required"}), 400
    if not host_id:
        return jsonify({"success": False, "error": "host_id_required"}), 400
    if not start_time or not end_time:
        return jsonify({"success": False, "error": "start_time_and_end_time_required"}), 400
    
    # 如果指定了会议室，检查冲突
    if meeting_room_id:
        conflicts = MeetingRepository.check_conflict(meeting_room_id, start_time, end_time)
        if conflicts:
            return jsonify({
                "success": False,
                "error": "room_conflict",
                "conflicts": conflicts,
                "message": "会议室在该时间段已被占用"
            }), 409
    
    meeting_id = MeetingRepository.create(
        title=title,
        host_id=host_id,
        start_time=start_time,
        end_time=end_time,
        meeting_room_id=meeting_room_id,
        notes=notes,
        status="scheduled"
    )
    return jsonify({"success": True, "id": meeting_id, "message": "Meeting scheduled"})


@app.route('/api/meetings/<int:meeting_id>', methods=['PUT'])
def update_meeting(meeting_id):
    """更新会议"""
    from db.sqlite_repository import MeetingRepository
    data = request.get_json()
    
    if not data:
        return jsonify({"success": False, "error": "Invalid request body"}), 400
    
    updates = {}
    allowed_fields = ["title", "host_id", "start_time", "end_time", "status", "notes", "meeting_room_id"]
    
    for field in allowed_fields:
        if field in data:
            updates[field] = data[field]
    
    if not updates:
        return jsonify({"success": False, "error": "no_fields_to_update"}), 400
    
    # 如果更新了会议室或时间，检查冲突
    if updates.get("meeting_room_id") or updates.get("start_time") or updates.get("end_time"):
        meeting = MeetingRepository.get_by_id(meeting_id)
        if meeting:
            room_id = updates.get("meeting_room_id", meeting.get("meeting_room_id"))
            start_time = updates.get("start_time", meeting.get("start_time"))
            end_time = updates.get("end_time", meeting.get("end_time"))
            
            if room_id:
                conflicts = MeetingRepository.check_conflict(room_id, start_time, end_time, exclude_meeting_id=meeting_id)
                if conflicts:
                    return jsonify({
                        "success": False,
                        "error": "room_conflict",
                        "conflicts": conflicts,
                        "message": "会议室在该时间段已被占用"
                    }), 409
    
    success = MeetingRepository.update(meeting_id, **updates)
    return jsonify({"success": success, "message": "Meeting updated" if success else "Meeting not found"})


@app.route('/api/meetings/<int:meeting_id>', methods=['DELETE'])
def cancel_meeting(meeting_id):
    """取消会议"""
    from db.sqlite_repository import MeetingRepository
    # 软删除：将状态设为cancelled
    success = MeetingRepository.update(meeting_id, status="cancelled")
    return jsonify({"success": success, "message": "Meeting cancelled" if success else "Meeting not found"})


if __name__ == '__main__':
    print("Starting Flask server on http://127.0.0.1:8080")
    print("Authentication enabled")
    print("Default admin credentials: admin / admin123")
    
    # 导入任务执行API
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
        get_task_statistics
    )
    
    @app.route('/api/task', methods=['POST'])
    def api_create_task():
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Invalid request body"}), 400
        task = create_task(
            name=data.get("name", ""),
            description=data.get("description", ""),
            project_id=data.get("project_id"),
            assignee_id=data.get("assignee_id"),
            priority=data.get("priority", "medium"),
            due_date=data.get("due_date")
        )
        return jsonify({"success": True, "task": task})
    
    @app.route('/api/tasks/from-conclusion', methods=['POST'])
    def api_tasks_from_conclusion():
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Invalid request body"}), 400
        conclusion = data.get("conclusion", "")
        if not conclusion:
            return jsonify({"success": False, "error": "conclusion_required"}), 400
        tasks = create_tasks_from_conclusion(
            conclusion=conclusion,
            project_id=data.get("project_id"),
            default_assignee_id=data.get("assignee_id")
        )
        return jsonify({"success": True, "tasks": tasks, "count": len(tasks)})
    
    @app.route('/api/task/<int:task_id>/assign', methods=['POST'])
    def api_task_assign(task_id):
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Invalid request body"}), 400
        employee_id = data.get("employee_id")
        if not employee_id:
            return jsonify({"success": False, "error": "employee_id_required"}), 400
        result = assign_task(task_id, employee_id)
        return jsonify(result)
    
    @app.route('/api/task/<int:task_id>/priority', methods=['POST'])
    def api_task_priority(task_id):
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Invalid request body"}), 400
        priority = data.get("priority", "medium")
        if priority not in ["low", "medium", "high", "urgent"]:
            return jsonify({"success": False, "error": "invalid_priority"}), 400
        result = set_task_priority(task_id, priority)
        return jsonify(result)
    
    @app.route('/api/task/<int:task_id>/due-date', methods=['POST'])
    def api_task_due_date(task_id):
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Invalid request body"}), 400
        due_date = data.get("due_date")
        if not due_date:
            return jsonify({"success": False, "error": "due_date_required"}), 400
        result = set_task_due_date(task_id, due_date)
        return jsonify(result)
    
    @app.route('/api/task/<int:task_id>/start', methods=['POST'])
    def api_task_start(task_id):
        result = start_task(task_id)
        return jsonify(result)
    
    @app.route('/api/task/<int:task_id>/progress', methods=['POST'])
    def api_task_progress(task_id):
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Invalid request body"}), 400
        progress = data.get("progress", 0)
        message = data.get("message", "")
        if progress < 0 or progress > 100:
            return jsonify({"success": False, "error": "invalid_progress"}), 400
        result = update_task_progress(task_id, progress, message)
        return jsonify(result)
    
    @app.route('/api/task/<int:task_id>/log', methods=['POST'])
    def api_task_log(task_id):
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Invalid request body"}), 400
        log = data.get("log", "")
        if not log:
            return jsonify({"success": False, "error": "log_required"}), 400
        result = add_task_log(task_id, log)
        return jsonify(result)
    
    @app.route('/api/task/<int:task_id>/complete', methods=['POST'])
    def api_task_complete(task_id):
        data = request.get_json() or {}
        result_text = data.get("result")
        result = complete_task(task_id, result_text)
        return jsonify(result)
    
    @app.route('/api/task/<int:task_id>/fail', methods=['POST'])
    def api_task_fail(task_id):
        data = request.get_json() or {}
        reason = data.get("reason", "未知原因")
        result = fail_task(task_id, reason)
        return jsonify(result)
    
    @app.route('/api/task/<int:task_id>/status', methods=['GET'])
    def api_task_status(task_id):
        result = get_task_status(task_id)
        return jsonify(result)
    
    @app.route('/api/tasks', methods=['GET'])
    def api_tasks_list():
        status = request.args.get("status")
        assignee_id = request.args.get("assignee_id", type=int)
        tasks = get_all_tasks(status=status, assignee_id=assignee_id)
        return jsonify({"success": True, "tasks": tasks, "count": len(tasks)})
    
    @app.route('/api/tasks/statistics', methods=['GET'])
    def api_tasks_statistics():
        stats = get_task_statistics()
        return jsonify({"success": True, "statistics": stats})
    
    @app.route('/api/meeting/extract-tasks', methods=['POST'])
    def api_extract_tasks():
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Invalid request body"}), 400
        conclusion = data.get("conclusion", "")
        if not conclusion:
            return jsonify({"success": False, "error": "conclusion_required"}), 400
        from core.task_execution import get_task_system
        system = get_task_system()
        extracted = system.extract_tasks_from_conclusion(conclusion)
        return jsonify({"success": True, "extracted_tasks": extracted, "count": len(extracted)})
    
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)
