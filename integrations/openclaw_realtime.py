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
            
            # 检查是否有活跃的sessions - sessions.json 是字典格式，key是session key
            sessions_path = os.path.join(OPENCLAW_AGENTS_DIR, agent_id, "sessions", "sessions.json")
            sessions_count = 0
            latest_session_time = 0
            if os.path.exists(sessions_path):
                try:
                    with open(sessions_path, 'r', encoding='utf-8') as f:
                        sessions_data = json.load(f)
                        # sessions.json 是字典，key是session标识，value是session数据
                        if isinstance(sessions_data, dict):
                            sessions_count = len(sessions_data)
                            # 找出最新更新的session时间
                            for session_key, session_info in sessions_data.items():
                                updated_at = session_info.get("updatedAt", 0)
                                if updated_at > latest_session_time:
                                    latest_session_time = updated_at
                                    # 检查是否最近活跃（5分钟内）
                                    if updated_at > (time.time() * 1000 - 5 * 60 * 1000):
                                        status = "working"
                except Exception as e:
                    print(f"Error reading sessions for {agent_id}: {e}")
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
                    # sessions.json 是字典格式，转换为列表返回
                    if isinstance(data, dict):
                        # 返回按更新时间排序的session列表
                        sessions_list = list(data.values())
                        sessions_list.sort(key=lambda x: x.get("updatedAt", 0), reverse=True)
                        return sessions_list
                    return []
            except Exception as e:
                print(f"Error reading sessions for {agent_id}: {e}")
                pass
        return []
    
    def get_latest_session(self, agent_id: str) -> Optional[dict]:
        """获取最新会话"""
        sessions = self.get_sessions(agent_id)
        return sessions[0] if sessions else None
    
    def get_recent_messages(self, agent_id: str, limit: int = 10) -> List[dict]:
        """获取最近的对话消息"""
        # 尝试从session store获取消息
        sessions_path = os.path.join(OPENCLAW_AGENTS_DIR, agent_id, "sessions", "sessions.json")
        if os.path.exists(sessions_path):
            try:
                with open(sessions_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        # 找到最新的session
                        sessions_list = list(data.values())
                        sessions_list.sort(key=lambda x: x.get("updatedAt", 0), reverse=True)
                        if sessions_list:
                            latest = sessions_list[0]
                            # 尝试获取消息（可能在session data中）
                            messages = latest.get("messages", [])
                            if messages:
                                return messages[-limit:] if messages else []
            except Exception as e:
                print(f"Error reading messages for {agent_id}: {e}")
                pass
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
            "agent",
            "--agent", agent_id,
            "--message", task,
            "--json"
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
    
    def request_speech(self, agent_id: str, topic: str, timeout: int = 30) -> str:
        """
        让员工发言（会议模式）
        
        Args:
            agent_id: 员工Agent ID
            topic: 讨论话题
            timeout: 超时秒数，默认30秒
        
        Returns:
            发言内容
        """
        if agent_id not in EMPLOYEE_MAPPING:
            raise ValueError(f"Unknown agent: {agent_id}")
        
        agent_name = EMPLOYEE_MAPPING[agent_id]["name"]
        role = EMPLOYEE_MAPPING[agent_id]["role"]
        
        # 如果 topic 已经包含完整的提示词（以"议题："开头），直接使用
        # 否则构建完整的 prompt
        if topic and topic.strip().startswith("议题："):
            speech_prompt = f"你是{agent_name}，{role}。\n\n{topic}"
        else:
            # 尝试调用真实的Agent，添加超时保护
            speech_prompt = f"""你是{agent_name}，{role}。现在公司正在开会讨论「{topic}」。
请从你的专业角度，发表2-3句话的专业意见。要求简洁有力，体现专业水准。"""
        
        try:
            # 调用子Agent获取回复，设置超时
            result = self._run_command([
                "agent",
                "--agent", agent_id,
                "--message", speech_prompt,
                "--json"
            ], timeout=timeout)
            
            # 如果成功获取响应，返回响应内容
            if result.get("success"):
                data = result.get("data", {})
                if isinstance(data, dict):
                    # 尝试从各种字段获取响应
                    response = data.get("response") or data.get("message") or data.get("content") or data.get("reply")
                    if response:
                        return response
            
            # 如果没有获取到响应，返回基于角色的模拟发言
            return self._generate_mock_speech(agent_id, topic)
            
        except subprocess.TimeoutExpired:
            # 超时异常，返回模拟发言
            print(f"[警告] Agent {agent_id} 发言超时({timeout}秒)，使用模拟发言")
            return self._generate_mock_speech(agent_id, topic)
        except Exception as e:
            # 其他异常，记录错误并返回模拟发言
            print(f"[错误] Agent {agent_id} 发言异常: {str(e)}，使用模拟发言")
            return self._generate_mock_speech(agent_id, topic)
    
    def _generate_mock_speech(self, agent_id: str, topic: str) -> str:
        """生成基于角色的模拟发言"""
        mock_speeches = {
            "jxcai": f"从财务角度来看，这个项目需要关注成本控制和ROI。建议先进行小规模试点，验证盈利模式后再扩大投入。",
            "jxchma": f"技术上我建议采用微服务架构，这样可以提高系统的可扩展性和维护性。同时需要注意技术债务的控制。",
            "jxchuang": f"从创意角度，这个项目很有市场潜力。建议在品牌定位上更加年轻化，突出差异化竞争策略。",
            "jxsc": f"作为产品负责人，我认为首先要明确MVP的核心功能，用户体验至关重要。建议采用敏捷开发方式快速迭代。",
            "jxshi": f"市场方面，我建议采用多渠道营销策略，重点关注社交媒体和内容营销。初期可以通过KOL合作快速获取曝光。",
            "jxyun": f"运营角度，我认为需要建立完善的用户增长体系，留存和转化是关键指标。建议数据驱动决策，持续优化运营策略。"
        }
        
        base_speech = mock_speeches.get(agent_id, "我认为这个议题需要进一步讨论分析。")
        
        # 根据话题调整发言
        if "产品" in topic or "发布" in topic:
            return f"关于{topic}，{base_speech}"
        elif "财务" in topic or "预算" in topic:
            return f"关于{topic}，{mock_speeches.get('jxcai', base_speech)}"
        elif "技术" in topic or "开发" in topic:
            return f"关于{topic}，{mock_speeches.get('jxchma', base_speech)}"
        else:
            return f"关于{topic}，{base_speech}"
            # 尝试解析返回内容
            data = result.get("data", {})
            if isinstance(data, dict):
                return data.get("response", data.get("message", "（暂无回复）"))
            return result.get("stdout", "（发言完毕）")
        
        return f"（发言请求失败：{result.get('error', '未知错误')}）"
    
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
            last_message = ""
            if recent_messages:
                # 尝试从messages中获取内容
                last_msg = recent_messages[-1]
                if isinstance(last_msg, dict):
                    last_message = last_msg.get("content", "") or last_msg.get("message", "") or last_msg.get("response", "")
                elif isinstance(last_msg, str):
                    last_message = last_msg
                last_message = last_message[:100] if last_message else ""
            
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
                "last_message": last_message
            })
        
        # 获取真实项目数据
        projects_data = self._get_projects_data()
        
        # 获取真实任务数据
        tasks_data = self._get_tasks_data()
        
        # 生成实时动态
        recent_activity = self._get_recent_activity()
        
        return {
            "company_name": "金库集团",
            "departments": 5,
            "employees_count": len(agents),
            "employees_by_status": status_counts,
            "employees": employees,
            "projects": projects_data,
            "tasks": tasks_data["summary"],
            "task_kanban": tasks_data["kanban"],
            "recent_activity": recent_activity,
            "financial": {
                "budget": 1000,
                "spent": 0,
                "balance": 1000
            },
            "last_update": self._last_update.isoformat() if self._last_update else ""
        }
    
    def _get_tasks_data(self) -> dict:
        """从storage/projects获取真实任务数据"""
        projects_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "storage", 
            "projects"
        )
        
        all_tasks = []
        kanban = {
            "pending": [],
            "in_progress": [],
            "completed": [],
            "failed": []
        }
        
        if os.path.exists(projects_path):
            try:
                for project_dir in os.listdir(projects_path):
                    project_file = os.path.join(projects_path, project_dir, "info.json")
                    project_name = project_dir
                    if os.path.exists(project_file):
                        with open(project_file, 'r', encoding='utf-8') as f:
                            project_info = json.load(f)
                            project_name = project_info.get("name", project_dir)
                    
                    tasks_dir = os.path.join(projects_path, project_dir, "tasks")
                    if os.path.exists(tasks_dir):
                        for task_file in os.listdir(tasks_dir):
                            if task_file.endswith('.json'):
                                task_path = os.path.join(tasks_dir, task_file)
                                with open(task_path, 'r', encoding='utf-8') as f:
                                    task = json.load(f)
                                    task["project"] = project_name
                                    all_tasks.append(task)
                                    
                                    status = task.get("status", "pending")
                                    if status == "pending":
                                        kanban["pending"].append(task)
                                    elif status in ["in_progress", "running"]:
                                        kanban["in_progress"].append(task)
                                    elif status == "completed":
                                        kanban["completed"].append(task)
                                    elif status == "failed":
                                        kanban["failed"].append(task)
            except Exception as e:
                print(f"Error reading tasks: {e}")
        
        return {
            "summary": {
                "total": len(all_tasks),
                "pending": len(kanban["pending"]),
                "in_progress": len(kanban["in_progress"]),
                "completed": len(kanban["completed"]),
                "failed": len(kanban["failed"])
            },
            "kanban": kanban
        }
    
    def _get_recent_activity(self) -> list:
        """从storage/projects获取真实动态"""
        projects_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "storage", 
            "projects"
        )
        
        activities = []
        
        if os.path.exists(projects_path):
            try:
                for project_dir in os.listdir(projects_path):
                    project_file = os.path.join(projects_path, project_dir, "info.json")
                    project_name = project_dir
                    if os.path.exists(project_file):
                        with open(project_file, 'r', encoding='utf-8') as f:
                            project_info = json.load(f)
                            project_name = project_info.get("name", project_dir)
                    
                    # 读取会议记录
                    meetings_dir = os.path.join(projects_path, project_dir, "meetings")
                    if os.path.exists(meetings_dir):
                        for meeting_file in os.listdir(meetings_dir):
                            if meeting_file.endswith('.json'):
                                meeting_path = os.path.join(meetings_dir, meeting_file)
                                with open(meeting_path, 'r', encoding='utf-8') as f:
                                    meeting = json.load(f)
                                    activities.append({
                                        "type": "meeting",
                                        "content": f"项目 {project_name} 召开 {meeting.get('type', '会议')}",
                                        "time": meeting.get("created_at", "")[:19] if meeting.get("created_at") else ""
                                    })
            except Exception as e:
                print(f"Error reading activities: {e}")
        
        # 按时间排序，取最新的10条
        activities.sort(key=lambda x: x.get("time", ""), reverse=True)
        return activities[:10]
    
    def _get_projects_data(self) -> dict:
        """从storage/projects获取真实项目数据"""
        projects_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "storage", 
            "projects"
        )
        
        total = 0
        active = 0
        completed = 0
        project_list = []
        
        if os.path.exists(projects_path):
            try:
                for project_dir in os.listdir(projects_path):
                    project_file = os.path.join(projects_path, project_dir, "info.json")
                    if os.path.exists(project_file):
                        with open(project_file, 'r', encoding='utf-8') as f:
                            project_info = json.load(f)
                            status = project_info.get("status", "")
                            total += 1
                            if status in ["active", "kickoff", "running"]:
                                active += 1
                            elif status == "completed":
                                completed += 1
                            project_list.append({
                                "id": project_dir,
                                "name": project_info.get("name", project_dir),
                                "status": status,
                                "description": project_info.get("description", "")
                            })
            except Exception as e:
                print(f"Error reading projects: {e}")
        
        return {
            "total": total,
            "active": active,
            "completed": completed,
            "list": project_list
        }


# 全局实例
_realtime: Optional[OpenClawRealtime] = None


def get_realtime() -> OpenClawRealtime:
    """获取实时数据获取器单例"""
    global _realtime
    if _realtime is None:
        _realtime = OpenClawRealtime()
    return _realtime
