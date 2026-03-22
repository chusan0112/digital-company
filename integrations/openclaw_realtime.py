"""
OpenClaw 实时数据获取模块
直接从OpenClaw CLI获取真实Agent、任务和会话数据
"""

import json
import os
import subprocess
import threading
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional, Dict, Callable

# OpenClaw Agents配置目录
OPENCLAW_AGENTS_DIR = os.path.expanduser("~/.openclaw/agents")

# 数字公司员工映射
EMPLOYEE_MAPPING = {
    "jxchuang": {"name": "金小创", "role": "首席创意官 CCO", "department": "总经办", "skills": ["创意", "策划", "内容"]},
    "jxyun": {"name": "金小运", "role": "首席运营官 COO", "department": "运营部", "skills": ["运营", "项目管理"]},
    "jxcai": {"name": "金小财", "role": "首席财务官 CFO", "department": "财务部", "skills": ["财务", "分析"]},
    "jxchma": {"name": "金小码", "role": "首席技术官 CTO", "department": "研发部", "skills": ["技术", "架构"]},
    "jxsc": {"name": "金小产", "role": "首席产品官 CPO", "department": "研发部", "skills": ["产品", "设计"]},
    "jxshi": {"name": "金小市", "role": "首席市场官 CMO", "department": "市场部", "skills": ["市场", "销售"]},
}


@dataclass
class RealtimeAgent:
    """实时Agent信息"""
    agent_id: str
    name: str
    role: str
    department: str
    skills: List[str]
    status: str = "idle"  # idle, working, discussing, resting
    current_task: str = ""
    current_task_id: str = ""
    sessions_count: int = 0
    last_active: str = ""
    workspace: str = ""
    
    def to_dict(self):
        return asdict(self)


@dataclass
class RealtimeTask:
    """实时任务信息"""
    task_id: str
    agent_id: str
    description: str
    status: str  # pending, running, completed, failed
    created_at: str
    result: str = ""
    error: str = ""
    
    def to_dict(self):
        return asdict(self)


class OpenClawRealtime:
    """OpenClaw实时数据获取器"""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._last_update = None
        self._agents_cache: Dict[str, RealtimeAgent] = {}
        self._tasks_cache: Dict[str, RealtimeTask] = {}
        self._update_interval = 5  # 5秒刷新一次
        self._running = False
        self._update_thread: Optional[threading.Thread] = None
        self._callbacks: List[Callable] = []
        
    def start_auto_update(self):
        """启动自动更新"""
        if self._running:
            return
        self._running = True
        self._update_thread = threading.Thread(target=self._auto_update_loop, daemon=True)
        self._update_thread.start()
        
    def stop_auto_update(self):
        """停止自动更新"""
        self._running = False
        if self._update_thread:
            self._update_thread.join(timeout=2)
    
    def _auto_update_loop(self):
        """自动更新循环"""
        while self._running:
            try:
                self.update_all()
                self._notify_callbacks()
            except Exception as e:
                print(f"Auto update error: {e}")
            time.sleep(self._update_interval)
    
    def register_callback(self, callback: Callable):
        """注册数据更新回调"""
        self._callbacks.append(callback)
    
    def _notify_callbacks(self):
        """通知回调"""
        for callback in self._callbacks:
            try:
                callback(self._agents_cache, self._tasks_cache)
            except Exception as e:
                print(f"Callback error: {e}")
    
    def _run_command(self, args: List[str], timeout: int = 30) -> dict:
        """执行OpenClaw CLI命令"""
        try:
            result = subprocess.run(
                ["openclaw"] + args,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8',
                shell=True
            )
            # 解析JSON输出（忽略插件加载信息）
            stdout_lines = []
            in_json = False
            json_buffer = []
            
            for line in result.stdout.split('\n'):
                # 检测JSON开始
                if line.strip().startswith('{'):
                    in_json = True
                    json_buffer = [line]
                elif in_json:
                    json_buffer.append(line)
                    if line.strip() == '}' or line.strip().endswith('}') and line.strip().count('}') == 1:
                        try:
                            json_str = '\n'.join(json_buffer)
                            data = json.loads(json_str)
                            return {"success": True, "data": data}
                        except:
                            pass
                            in_json = False
            
            # 尝试解析整个stdout
            try:
                data = json.loads(result.stdout)
                return {"success": True, "data": data}
            except:
                pass
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timeout", "returncode": -1}
        except Exception as e:
            return {"success": False, "error": str(e), "returncode": -1}
    
    def list_agents(self) -> List[RealtimeAgent]:
        """获取所有数字公司Agent列表"""
        agents = []
        
        # 遍历Agents目录
        if not os.path.exists(OPENCLAW_AGENTS_DIR):
            return agents
        
        for agent_id in os.listdir(OPENCLAW_AGENTS_DIR):
            # 只处理数字公司的Agent
            if agent_id not in EMPLOYEE_MAPPING:
                continue
            
            mapping = EMPLOYEE_MAPPING[agent_id]
            workspace = os.path.join(OPENCLAW_AGENTS_DIR, agent_id, "workspace")
            
            # 读取Agent配置文件
            status = "idle"
            current_task = ""
            
            # 检查是否有活跃的sessions
            sessions_path = os.path.join(OPENCLAW_AGENTS_DIR, agent_id, "sessions", "sessions.json")
            sessions_count = 0
            if os.path.exists(sessions_path):
                try:
                    with open(sessions_path, 'r', encoding='utf-8') as f:
                        sessions_data = json.load(f)
                        sessions = sessions_data.get("sessions", [])
                        sessions_count = len(sessions)
                        
                        # 检查最新session的状态
                        if sessions:
                            # 最近活跃的session
                            latest = sessions[0] if sessions else {}
                            # 如果有活跃的message，视为工作中
                            if latest.get("messages", []):
                                status = "working"
                except:
                    pass
            
            # 尝试读取心跳文件
            heartbeat_path = os.path.join(workspace, "HEARTBEAT.md")
            if os.path.exists(heartbeat_path):
                try:
                    with open(heartbeat_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if "idle" in content.lower():
                            status = "idle"
                        elif "working" in content.lower() or "running" in content.lower():
                            status = "working"
                except:
                    pass
            
            # 尝试读取当前任务
            task_file = os.path.join(workspace, ".openclaw", "current_task.txt")
            if os.path.exists(task_file):
                try:
                    with open(task_file, 'r', encoding='utf-8') as f:
                        current_task = f.read().strip()
                except:
                    pass
            
            agent = RealtimeAgent(
                agent_id=agent_id,
                name=mapping["name"],
                role=mapping["role"],
                department=mapping["department"],
                skills=mapping["skills"],
                status=status,
                current_task=current_task,
                sessions_count=sessions_count,
                workspace=workspace
            )
            agents.append(agent)
        
        with self._lock:
            self._agents_cache = {a.agent_id: a for a in agents}
        
        return agents
    
    def get_agent_detail(self, agent_id: str) -> Optional[RealtimeAgent]:
        """获取单个Agent详细信息"""
        if agent_id in self._agents_cache:
            return self._agents_cache[agent_id]
        
        # 刷新并返回
        self.list_agents()
        return self._agents_cache.get(agent_id)
    
    def get_sessions(self, agent_id: str) -> List[dict]:
        """获取Agent的会话历史"""
        sessions_path = os.path.join(OPENCLAW_AGENTS_DIR, agent_id, "sessions", "sessions.json")
        if os.path.exists(sessions_path):
            try:
                with open(sessions_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("sessions", [])
            except:
                pass
        return []
    
    def get_latest_session(self, agent_id: str) -> Optional[dict]:
        """获取最新会话"""
        sessions = self.get_sessions(agent_id)
        return sessions[0] if sessions else None
    
    def get_recent_messages(self, agent_id: str, limit: int = 10) -> List[dict]:
        """获取最近的对话消息"""
        latest = self.get_latest_session(agent_id)
        if latest:
            messages = latest.get("messages", [])
            return messages[-limit:] if messages else []
        return []
    
    def send_task(self, agent_id: str, task: str) -> str:
        """向Agent发送任务"""
        if agent_id not in EMPLOYEE_MAPPING:
            raise ValueError(f"Unknown agent: {agent_id}")
        
        # 使用openclaw sessions_send发送任务
        task_id = f"task-{int(time.time())}"
        
        # 在后台执行
        thread = threading.Thread(
            target=self._send_task_background,
            args=(agent_id, task, task_id),
            daemon=True
        )
        thread.start()
        
        return task_id
    
    def _send_task_background(self, agent_id: str, task: str, task_id: str):
        """后台发送任务"""
        result = self._run_command([
            "sessions_send",
            "--agent", agent_id,
            "--message", task
        ], timeout=120)
        
        # 更新任务缓存
        with self._lock:
            task_obj = RealtimeTask(
                task_id=task_id,
                agent_id=agent_id,
                description=task,
                status="completed" if result.get("success") else "failed",
                created_at=datetime.now().isoformat(),
                result=result.get("stdout", ""),
                error=result.get("stderr", "")
            )
            self._tasks_cache[task_id] = task_obj
    
    def update_all(self):
        """更新所有数据"""
        self.list_agents()
        self._last_update = datetime.now()
    
    def get_dashboard_data(self) -> dict:
        """获取驾驶舱数据"""
        agents = self.list_agents()
        
        # 统计
        status_counts = {
            "working": len([a for a in agents if a.status == "working"]),
            "idle": len([a for a in agents if a.status == "idle"]),
            "discussing": len([a for a in agents if a.status == "discussing"]),
            "resting": len([a for a in agents if a.status == "resting"])
        }
        
        # 准备员工列表
        employees = []
        for agent in agents:
            # 获取最近的任务/消息
            recent_messages = self.get_recent_messages(agent.agent_id, limit=3)
            last_message = recent_messages[-1] if recent_messages else {}
            
            employees.append({
                "agent_id": agent.agent_id,
                "name": agent.name,
                "role": agent.role,
                "department": agent.department,
                "skills": agent.skills,
                "status": agent.status,
                "current_task": agent.current_task,
                "sessions_count": agent.sessions_count,
                "workspace": agent.workspace,
                "last_message": last_message.get("content", "")[:100] if last_message else ""
            })
        
        return {
            "company_name": "金库集团",
            "departments": 5,
            "employees_count": len(agents),
            "employees_by_status": status_counts,
            "employees": employees,
            "projects": {
                "total": 3,
                "active": 2,
                "completed": 1
            },
            "tasks": {
                "total": len(self._tasks_cache),
                "pending": len([t for t in self._tasks_cache.values() if t.status == "pending"]),
                "running": len([t for t in self._tasks_cache.values() if t.status == "running"]),
                "completed": len([t for t in self._tasks_cache.values() if t.status == "completed"])
            },
            "financial": {
                "budget": 1000,
                "spent": 0,
                "balance": 1000
            },
            "last_update": self._last_update.isoformat() if self._last_update else ""
        }


# 全局实例
_realtime: Optional[OpenClawRealtime] = None


def get_realtime() -> OpenClawRealtime:
    """获取实时数据获取器单例"""
    global _realtime
    if _realtime is None:
        _realtime = OpenClawRealtime()
    return _realtime
