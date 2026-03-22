#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Digital Company SQLite Repository
提供所有数据表的CRUD操作
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from contextlib import contextmanager


# 数据库文件路径
DB_PATH = os.path.join(os.path.dirname(__file__), 'company.db')


@contextmanager
def get_connection():
    """获取数据库连接的上下文管理器"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def dict_from_row(row: sqlite3.Row) -> dict:
    """将sqlite3.Row转换为字典"""
    if row is None:
        return None
    return dict(row)


def parse_json_field(value: str) -> Any:
    """解析JSON字段"""
    if value is None or value == "":
        return None
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value


def serialize_json_field(value: Any) -> str:
    """序列化JSON字段"""
    if value is None:
        return None
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


# ============== UserRepository ==============

class UserRepository:
    """用户管理Repository"""
    
    @staticmethod
    def create(username: str, password_hash: str, role: str = "user") -> int:
        """创建用户"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (username, password_hash, role)
            )
            conn.commit()
            return cursor.lastrowid
    
    @staticmethod
    def get_by_id(user_id: int) -> Optional[dict]:
        """根据ID获取用户"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            return dict_from_row(cursor.fetchone())
    
    @staticmethod
    def get_by_username(username: str) -> Optional[dict]:
        """根据用户名获取用户"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            return dict_from_row(cursor.fetchone())
    
    @staticmethod
    def get_all() -> List[dict]:
        """获取所有用户"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
            return [dict_from_row(row) for row in cursor.fetchall()]
    
    @staticmethod
    def update(user_id: int, **kwargs) -> bool:
        """更新用户"""
        allowed_fields = ["username", "password_hash", "role"]
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not updates:
            return False
        
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [user_id]
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE users SET {set_clause} WHERE id = ?", values)
            conn.commit()
            return cursor.rowcount > 0
    
    @staticmethod
    def delete(user_id: int) -> bool:
        """删除用户"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            return cursor.rowcount > 0


# ============== DepartmentRepository ==============

class DepartmentRepository:
    """部门管理Repository"""
    
    @staticmethod
    def create(name: str, description: str = "", parent_id: int = None) -> int:
        """创建部门"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO departments (name, description, parent_id) VALUES (?, ?, ?)",
                (name, description, parent_id)
            )
            conn.commit()
            return cursor.lastrowid
    
    @staticmethod
    def get_by_id(dept_id: int) -> Optional[dict]:
        """根据ID获取部门"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM departments WHERE id = ?", (dept_id,))
            return dict_from_row(cursor.fetchone())
    
    @staticmethod
    def get_all() -> List[dict]:
        """获取所有部门"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM departments ORDER BY id")
            return [dict_from_row(row) for row in cursor.fetchall()]
    
    @staticmethod
    def get_children(parent_id: int) -> List[dict]:
        """获取子部门"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM departments WHERE parent_id = ?", (parent_id,))
            return [dict_from_row(row) for row in cursor.fetchall()]
    
    @staticmethod
    def update(dept_id: int, **kwargs) -> bool:
        """更新部门"""
        allowed_fields = ["name", "description", "parent_id"]
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not updates:
            return False
        
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [dept_id]
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE departments SET {set_clause} WHERE id = ?", values)
            conn.commit()
            return cursor.rowcount > 0
    
    @staticmethod
    def delete(dept_id: int) -> bool:
        """删除部门"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM departments WHERE id = ?", (dept_id,))
            conn.commit()
            return cursor.rowcount > 0


# ============== EmployeeRepository ==============

class EmployeeRepository:
    """员工管理Repository"""
    
    @staticmethod
    def create(name: str, role: str, department_id: int = None, 
               skills: List[str] = None, status: str = "active",
               hire_date: str = None, salary: float = 0, performance: float = 100) -> int:
        """创建员工"""
        skills_json = serialize_json_field(skills)
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO employees 
                   (name, role, department_id, skills, status, hire_date, salary, performance) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (name, role, department_id, skills_json, status, hire_date, salary, performance)
            )
            conn.commit()
            return cursor.lastrowid
    
    @staticmethod
    def get_by_id(emp_id: int) -> Optional[dict]:
        """根据ID获取员工"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM employees WHERE id = ?", (emp_id,))
            row = cursor.fetchone()
            if row:
                result = dict(row)
                result["skills"] = parse_json_field(result.get("skills"))
                return result
            return None
    
    @staticmethod
    def get_all(department_id: int = None, status: str = None) -> List[dict]:
        """获取所有员工，可按部门或状态过滤"""
        with get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM employees WHERE 1=1"
            params = []
            
            if department_id:
                query += " AND department_id = ?"
                params.append(department_id)
            if status:
                query += " AND status = ?"
                params.append(status)
            
            query += " ORDER BY id"
            cursor.execute(query, params)
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                result["skills"] = parse_json_field(result.get("skills"))
                results.append(result)
            return results
    
    @staticmethod
    def update(emp_id: int, **kwargs) -> bool:
        """更新员工"""
        allowed_fields = ["name", "role", "department_id", "skills", "status", "hire_date", "salary", "performance"]
        updates = {}
        for k, v in kwargs.items():
            if k in allowed_fields:
                if k == "skills":
                    updates[k] = serialize_json_field(v)
                else:
                    updates[k] = v
        
        if not updates:
            return False
        
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [emp_id]
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE employees SET {set_clause} WHERE id = ?", values)
            conn.commit()
            return cursor.rowcount > 0
    
    @staticmethod
    def delete(emp_id: int) -> bool:
        """删除员工"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM employees WHERE id = ?", (emp_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    @staticmethod
    def count(department_id: int = None, status: str = None) -> int:
        """统计员工数量"""
        with get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT COUNT(*) FROM employees WHERE 1=1"
            params = []
            
            if department_id:
                query += " AND department_id = ?"
                params.append(department_id)
            if status:
                query += " AND status = ?"
                params.append(status)
            
            cursor.execute(query, params)
            return cursor.fetchone()[0]


# ============== ProjectRepository ==============

class ProjectRepository:
    """项目管理Repository"""
    
    @staticmethod
    def create(name: str, description: str = "", status: str = "planning",
               priority: str = "medium", department_id: int = None,
               start_date: str = None, end_date: str = None,
               budget: float = 0, progress: float = 0) -> int:
        """创建项目"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO projects 
                   (name, description, status, priority, department_id, start_date, end_date, budget, progress) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (name, description, status, priority, department_id, start_date, end_date, budget, progress)
            )
            conn.commit()
            return cursor.lastrowid
    
    @staticmethod
    def get_by_id(proj_id: int) -> Optional[dict]:
        """根据ID获取项目"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects WHERE id = ?", (proj_id,))
            return dict_from_row(cursor.fetchone())
    
    @staticmethod
    def get_all(department_id: int = None, status: str = None) -> List[dict]:
        """获取所有项目"""
        with get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM projects WHERE 1=1"
            params = []
            
            if department_id:
                query += " AND department_id = ?"
                params.append(department_id)
            if status:
                query += " AND status = ?"
                params.append(status)
            
            query += " ORDER BY id"
            cursor.execute(query, params)
            return [dict_from_row(row) for row in cursor.fetchall()]
    
    @staticmethod
    def update(proj_id: int, **kwargs) -> bool:
        """更新项目"""
        allowed_fields = ["name", "description", "status", "priority", "department_id", 
                         "start_date", "end_date", "budget", "progress"]
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not updates:
            return False
        
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [proj_id]
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE projects SET {set_clause} WHERE id = ?", values)
            conn.commit()
            return cursor.rowcount > 0
    
    @staticmethod
    def delete(proj_id: int) -> bool:
        """删除项目"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM projects WHERE id = ?", (proj_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    @staticmethod
    def count(status: str = None) -> dict:
        """统计项目数量"""
        with get_connection() as conn:
            cursor = conn.cursor()
            
            result = {"total": 0, "planning": 0, "active": 0, "completed": 0, "archived": 0}
            
            cursor.execute("SELECT COUNT(*) FROM projects")
            result["total"] = cursor.fetchone()[0]
            
            for s in ["planning", "active", "completed", "archived"]:
                cursor.execute("SELECT COUNT(*) FROM projects WHERE status = ?", (s,))
                result[s] = cursor.fetchone()[0]
            
            return result


# ============== TaskRepository ==============

class TaskRepository:
    """任务管理Repository"""
    
    @staticmethod
    def create(name: str, description: str = "", project_id: int = None,
               assignee_id: int = None, status: str = "pending",
               priority: str = "medium", due_date: str = None) -> int:
        """创建任务"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO tasks 
                   (name, description, project_id, assignee_id, status, priority, due_date) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (name, description, project_id, assignee_id, status, priority, due_date)
            )
            conn.commit()
            return cursor.lastrowid
    
    @staticmethod
    def get_by_id(task_id: int) -> Optional[dict]:
        """根据ID获取任务"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            return dict_from_row(cursor.fetchone())
    
    @staticmethod
    def get_all(project_id: int = None, assignee_id: int = None, 
                status: str = None) -> List[dict]:
        """获取所有任务"""
        with get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM tasks WHERE 1=1"
            params = []
            
            if project_id:
                query += " AND project_id = ?"
                params.append(project_id)
            if assignee_id:
                query += " AND assignee_id = ?"
                params.append(assignee_id)
            if status:
                query += " AND status = ?"
                params.append(status)
            
            query += " ORDER BY created_at DESC"
            cursor.execute(query, params)
            return [dict_from_row(row) for row in cursor.fetchall()]
    
    @staticmethod
    def update(task_id: int, **kwargs) -> bool:
        """更新任务"""
        allowed_fields = ["name", "description", "project_id", "assignee_id", 
                         "status", "priority", "due_date"]
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not updates:
            return False
        
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [task_id]
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", values)
            conn.commit()
            return cursor.rowcount > 0
    
    @staticmethod
    def delete(task_id: int) -> bool:
        """删除任务"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    @staticmethod
    def count(status: str = None) -> dict:
        """统计任务数量"""
        with get_connection() as conn:
            cursor = conn.cursor()
            
            result = {"total": 0, "pending": 0, "in_progress": 0, "review": 0, "completed": 0}
            
            cursor.execute("SELECT COUNT(*) FROM tasks")
            result["total"] = cursor.fetchone()[0]
            
            for s in ["pending", "in_progress", "review", "completed"]:
                cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = ?", (s,))
                result[s] = cursor.fetchone()[0]
            
            return result


# ============== DecisionRepository ==============

class DecisionRepository:
    """决策管理Repository"""
    
    @staticmethod
    def create(intent: str, policy: dict = None, executive_panel: list = None,
               options: list = None, summary: str = "", status: str = "pending") -> int:
        """创建决策"""
        policy_json = serialize_json_field(policy)
        executive_json = serialize_json_field(executive_panel)
        options_json = serialize_json_field(options)
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO decisions 
                   (intent, policy, executive_panel, options, summary, status) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (intent, policy_json, executive_json, options_json, summary, status)
            )
            conn.commit()
            return cursor.lastrowid
    
    @staticmethod
    def get_by_id(decision_id: int) -> Optional[dict]:
        """根据ID获取决策"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM decisions WHERE id = ?", (decision_id,))
            row = cursor.fetchone()
            if row:
                result = dict(row)
                result["policy"] = parse_json_field(result.get("policy"))
                result["executive_panel"] = parse_json_field(result.get("executive_panel"))
                result["options"] = parse_json_field(result.get("options"))
                result["execution_result"] = parse_json_field(result.get("execution_result"))
                return result
            return None
    
    @staticmethod
    def get_all(status: str = None, limit: int = 100) -> List[dict]:
        """获取所有决策"""
        with get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM decisions"
            params = []
            
            if status:
                query += " WHERE status = ?"
                params.append(status)
            
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                result["policy"] = parse_json_field(result.get("policy"))
                result["executive_panel"] = parse_json_field(result.get("executive_panel"))
                result["options"] = parse_json_field(result.get("options"))
                result["execution_result"] = parse_json_field(result.get("execution_result"))
                results.append(result)
            return results
    
    @staticmethod
    def update(decision_id: int, **kwargs) -> bool:
        """更新决策"""
        allowed_fields = ["intent", "policy", "executive_panel", "options", 
                         "summary", "status", "execution_result"]
        updates = {}
        for k, v in kwargs.items():
            if k in allowed_fields:
                if k in ["policy", "executive_panel", "options", "execution_result"]:
                    updates[k] = serialize_json_field(v)
                else:
                    updates[k] = v
        
        if not updates:
            return False
        
        updates["updated_at"] = datetime.now().isoformat()
        
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [decision_id]
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE decisions SET {set_clause} WHERE id = ?", values)
            conn.commit()
            return cursor.rowcount > 0
    
    @staticmethod
    def delete(decision_id: int) -> bool:
        """删除决策"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM decisions WHERE id = ?", (decision_id,))
            conn.commit()
            return cursor.rowcount > 0


# ============== ApprovalRepository ==============

class ApprovalRepository:
    """审批管理Repository"""
    
    @staticmethod
    def create(title: str, payload: dict = None, status: str = "pending") -> int:
        """创建审批"""
        payload_json = serialize_json_field(payload)
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO approvals (title, payload, status) VALUES (?, ?, ?)",
                (title, payload_json, status)
            )
            conn.commit()
            return cursor.lastrowid
    
    @staticmethod
    def get_by_id(approval_id: int) -> Optional[dict]:
        """根据ID获取审批"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM approvals WHERE id = ?", (approval_id,))
            row = cursor.fetchone()
            if row:
                result = dict(row)
                result["payload"] = parse_json_field(result.get("payload"))
                result["governance_conditions"] = parse_json_field(result.get("governance_conditions"))
                return result
            return None
    
    @staticmethod
    def get_all(status: str = None, limit: int = 100) -> List[dict]:
        """获取所有审批"""
        with get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM approvals"
            params = []
            
            if status:
                query += " WHERE status = ?"
                params.append(status)
            
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                result["payload"] = parse_json_field(result.get("payload"))
                result["governance_conditions"] = parse_json_field(result.get("governance_conditions"))
                results.append(result)
            return results
    
    @staticmethod
    def update(approval_id: int, **kwargs) -> bool:
        """更新审批"""
        allowed_fields = ["title", "payload", "status", "decision", "comments", "governance_conditions"]
        updates = {}
        for k, v in kwargs.items():
            if k in allowed_fields:
                if k in ["payload", "governance_conditions"]:
                    updates[k] = serialize_json_field(v)
                else:
                    updates[k] = v
        
        if not updates:
            return False
        
        updates["updated_at"] = datetime.now().isoformat()
        if kwargs.get("status") in ["approved", "rejected"]:
            updates["decided_at"] = datetime.now().isoformat()
        
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [approval_id]
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE approvals SET {set_clause} WHERE id = ?", values)
            conn.commit()
            return cursor.rowcount > 0
    
    @staticmethod
    def delete(approval_id: int) -> bool:
        """删除审批"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM approvals WHERE id = ?", (approval_id,))
            conn.commit()
            return cursor.rowcount > 0


# ============== MeetingRepository ==============

class MeetingRepository:
    """会议管理Repository"""
    
    @staticmethod
    def create(title: str, host_id: int, start_time: str, end_time: str,
               status: str = "scheduled", notes: str = None, 
               action_items: list = None, meeting_room_id: int = None) -> int:
        """创建会议"""
        action_items_json = serialize_json_field(action_items)
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO meetings 
                   (title, host_id, start_time, end_time, status, notes, action_items, meeting_room_id) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (title, host_id, start_time, end_time, status, notes, action_items_json, meeting_room_id)
            )
            conn.commit()
            return cursor.lastrowid
    
    @staticmethod
    def get_by_id(meeting_id: int) -> Optional[dict]:
        """根据ID获取会议"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM meetings WHERE id = ?", (meeting_id,))
            row = cursor.fetchone()
            if row:
                result = dict(row)
                result["action_items"] = parse_json_field(result.get("action_items"))
                return result
            return None
    
    @staticmethod
    def get_all(host_id: int = None, status: str = None) -> List[dict]:
        """获取所有会议"""
        with get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM meetings WHERE 1=1"
            params = []
            
            if host_id:
                query += " AND host_id = ?"
                params.append(host_id)
            if status:
                query += " AND status = ?"
                params.append(status)
            
            query += " ORDER BY start_time DESC"
            cursor.execute(query, params)
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                result["action_items"] = parse_json_field(result.get("action_items"))
                results.append(result)
            return results
    
    @staticmethod
    def update(meeting_id: int, **kwargs) -> bool:
        """更新会议"""
        allowed_fields = ["title", "host_id", "start_time", "end_time", "status", "notes", "action_items", "meeting_room_id"]
        updates = {}
        for k, v in kwargs.items():
            if k in allowed_fields:
                if k == "action_items":
                    updates[k] = serialize_json_field(v)
                else:
                    updates[k] = v
        
        if not updates:
            return False
        
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [meeting_id]
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE meetings SET {set_clause} WHERE id = ?", values)
            conn.commit()
            return cursor.rowcount > 0
    
    @staticmethod
    def check_conflict(room_id: int, start_time: str, end_time: str, exclude_meeting_id: int = None) -> List[dict]:
        """检查会议室在指定时间段是否有冲突"""
        with get_connection() as conn:
            cursor = conn.cursor()
            # 冲突条件：新会议的开始时间 < 已有会议的结束时间 AND 新会议的结束时间 > 已有会议的开始时间
            query = """SELECT * FROM meetings 
                       WHERE meeting_room_id = ? 
                       AND status != 'cancelled'
                       AND start_time < ? 
                       AND end_time > ?"""
            params = [room_id, end_time, start_time]
            
            if exclude_meeting_id:
                query += " AND id != ?"
                params.append(exclude_meeting_id)
            
            cursor.execute(query, params)
            return [dict_from_row(row) for row in cursor.fetchall()]
    
    @staticmethod
    def delete(meeting_id: int) -> bool:
        """删除会议"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM meetings WHERE id = ?", (meeting_id,))
            conn.commit()
            return cursor.rowcount > 0


# ============== MeetingRoomRepository ==============

class MeetingRoomRepository:
    """会议室管理Repository"""
    
    @staticmethod
    def create(name: str, capacity: int, location: str = None, 
               status: str = "available") -> int:
        """创建会议室"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO meeting_rooms (name, capacity, location, status) VALUES (?, ?, ?, ?)",
                (name, capacity, location, status)
            )
            conn.commit()
            return cursor.lastrowid
    
    @staticmethod
    def get_by_id(room_id: int) -> Optional[dict]:
        """根据ID获取会议室"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM meeting_rooms WHERE id = ?", (room_id,))
            return dict_from_row(cursor.fetchone())
    
    @staticmethod
    def get_all(status: str = None) -> List[dict]:
        """获取所有会议室"""
        with get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM meeting_rooms"
            params = []
            
            if status:
                query += " WHERE status = ?"
                params.append(status)
            
            cursor.execute(query, params)
            return [dict_from_row(row) for row in cursor.fetchall()]
    
    @staticmethod
    def update(room_id: int, **kwargs) -> bool:
        """更新会议室"""
        allowed_fields = ["name", "capacity", "location", "status"]
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not updates:
            return False
        
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [room_id]
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE meeting_rooms SET {set_clause} WHERE id = ?", values)
            conn.commit()
            return cursor.rowcount > 0
    
    @staticmethod
    def delete(room_id: int) -> bool:
        """删除会议室"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM meeting_rooms WHERE id = ?", (room_id,))
            conn.commit()
            return cursor.rowcount > 0


# ============== AuditLogRepository ==============

class AuditLogRepository:
    """审计日志Repository"""
    
    @staticmethod
    def create(event_type: str, actor: str = None, target: str = None, 
               details: dict = None) -> int:
        """创建审计日志"""
        details_json = serialize_json_field(details)
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO audit_logs (event_type, actor, target, details) VALUES (?, ?, ?, ?)",
                (event_type, actor, target, details_json)
            )
            conn.commit()
            return cursor.lastrowid
    
    @staticmethod
    def get_all(event_type: str = None, limit: int = 100) -> List[dict]:
        """获取所有审计日志"""
        with get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM audit_logs"
            params = []
            
            if event_type:
                query += " WHERE event_type = ?"
                params.append(event_type)
            
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                result["details"] = parse_json_field(result.get("details"))
                results.append(result)
            return results


# ============== 便捷函数 ==============

def init_database():
    """初始化数据库（运行表创建脚本）"""
    import init_db
    init_db.main()


if __name__ == "__main__":
    # 测试代码
    print("Testing SQLite Repository...")
    
    # 初始化数据库
    init_database()
    
    # 测试 UserRepository
    print("\n=== Testing UserRepository ===")
    user_id = UserRepository.create("test_user", "password123", "user")
    print(f"Created user: {user_id}")
    user = UserRepository.get_by_id(user_id)
    print(f"Get user: {user}")
    users = UserRepository.get_all()
    print(f"All users: {len(users)}")
    
    # 测试 DepartmentRepository
    print("\n=== Testing DepartmentRepository ===")
    dept_id = DepartmentRepository.create("Test Dept", "Test Description")
    print(f"Created department: {dept_id}")
    dept = DepartmentRepository.get_by_id(dept_id)
    print(f"Get department: {dept}")
    departments = DepartmentRepository.get_all()
    print(f"All departments: {len(departments)}")
    
    # 测试 EmployeeRepository
    print("\n=== Testing EmployeeRepository ===")
    emp_id = EmployeeRepository.create("Zhang San", "Engineer", department_id=1, skills=["Python", "SQL"])
    print(f"Created employee: {emp_id}")
    emp = EmployeeRepository.get_by_id(emp_id)
    print(f"Get employee: {emp}")
    employees = EmployeeRepository.get_all()
    print(f"All employees: {len(employees)}")
    
    # 测试 ProjectRepository
    print("\n=== Testing ProjectRepository ===")
    proj_id = ProjectRepository.create("Test Project", "Description", department_id=1, budget=10000)
    print(f"Created project: {proj_id}")
    proj = ProjectRepository.get_by_id(proj_id)
    print(f"Get project: {proj}")
    projects = ProjectRepository.get_all()
    print(f"All projects: {len(projects)}")
    
    # 测试 TaskRepository
    print("\n=== Testing TaskRepository ===")
    task_id = TaskRepository.create("Test Task", "Description", project_id=1, assignee_id=1)
    print(f"Created task: {task_id}")
    task = TaskRepository.get_by_id(task_id)
    print(f"Get task: {task}")
    tasks = TaskRepository.get_all()
    print(f"All tasks: {len(tasks)}")
    
    # 测试 DecisionRepository
    print("\n=== Testing DecisionRepository ===")
    decision_id = DecisionRepository.create("Test Decision", {"risk_level": "low"}, ["CEO", "CFO"])
    print(f"Created decision: {decision_id}")
    decision = DecisionRepository.get_by_id(decision_id)
    print(f"Get decision: {decision}")
    decisions = DecisionRepository.get_all()
    print(f"All decisions: {len(decisions)}")
    
    # 测试 ApprovalRepository
    print("\n=== Testing ApprovalRepository ===")
    approval_id = ApprovalRepository.create("Test Approval", {"amount": 1000})
    print(f"Created approval: {approval_id}")
    approval = ApprovalRepository.get_by_id(approval_id)
    print(f"Get approval: {approval}")
    approvals = ApprovalRepository.get_all()
    print(f"All approvals: {len(approvals)}")
    
    # 测试 MeetingRepository
    print("\n=== Testing MeetingRepository ===")
    meeting_id = MeetingRepository.create("Test Meeting", 1, "2024-01-01 10:00", "2024-01-01 11:00")
    print(f"Created meeting: {meeting_id}")
    meeting = MeetingRepository.get_by_id(meeting_id)
    print(f"Get meeting: {meeting}")
    meetings = MeetingRepository.get_all()
    print(f"All meetings: {len(meetings)}")
    
    # 测试 MeetingRoomRepository
    print("\n=== Testing MeetingRoomRepository ===")
    room_id = MeetingRoomRepository.create("Room 101", 10, "Floor 1")
    print(f"Created meeting room: {room_id}")
    room = MeetingRoomRepository.get_by_id(room_id)
    print(f"Get meeting room: {room}")
    rooms = MeetingRoomRepository.get_all()
    print(f"All meeting rooms: {len(rooms)}")
    
    print("\n=== All tests passed! ===")
