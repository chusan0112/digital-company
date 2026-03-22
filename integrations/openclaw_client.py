"""
数字公司 OpenClaw 客户端
实现与OpenClaw API的深度集成，支持子Agent创建、任务调度和状态查询
"""

import json
import os
import subprocess
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional, Callable
import threading
import time


# OpenClaw配置
DEFAULT_OPENCLAW_DIR = os.path.expanduser("~/.openclaw")
DEFAULT_AGENT_PREFIX = "dc-"  # digital-company agent prefix


@dataclass
class AgentInfo:
    """OpenClaw子Agent信息"""
    agent_id: str
    name: str
    workspace: str
    status: str = "created"  # created, running, idle, working, completed, failed
    skills: List[str] = field(default_factory=list)
    created_at: str = ""
    last_active: str = ""
    task_id: str = ""  # 当前执行的任务ID
    
    def to_dict(self):
        return asdict(self)
    
    @staticmethod
    def from_dict(d):
        return AgentInfo(**d)


@dataclass
class TaskResult:
    """任务执行结果"""
    task_id: str
    agent_id: str
    status: str  # pending, running, completed, failed
    result: str = ""
    error: str = ""
    created_at: str = ""
    completed_at: str = ""
    
    def to_dict(self):
        return asdict(self)


class OpenClawClient:
    """OpenClaw API客户端"""
    
    def __init__(self, openclaw_dir: str = None):
        self.openclaw_dir = openclaw_dir or DEFAULT_OPENCLAW_DIR
        self.agents: Dict[str, AgentInfo] = {}
        self.tasks: Dict[str, TaskResult] = {}
        self.webhook_callbacks: List[Callable] = []
        self._lock = threading.Lock()
        
    def _run_command(self, args: List[str], timeout: int = 30) -> dict:
        """执行OpenClaw CLI命令"""
        try:
            result = subprocess.run(
                ["openclaw"] + args,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8'
            )
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
    
    def _generate_agent_id(self, name: str) -> str:
        """生成Agent ID"""
        sanitized = "".join(c for c in name.lower() if c.isalnum() or c == '-')
        return f"{DEFAULT_AGENT_PREFIX}{sanitized}-{uuid.uuid4().hex[:6]}"
    
    def _generate_workspace(self, agent_id: str) -> str:
        """生成Agent工作目录"""
        return os.path.join(self.openclaw_dir, "agents", agent_id)
    
    # ============== Agent管理 ==============
    
    def create_agent(self, name: str, skills: List[str] = None, 
                     system_prompt: str = None) -> AgentInfo:
        """
        创建OpenClaw子Agent
        
        Args:
            name: Agent名称
            skills: 技能列表
            system_prompt: 系统提示词
        
        Returns:
            AgentInfo: 创建的Agent信息
        """
        agent_id = self._generate_agent_id(name)
        workspace = self._generate_workspace(agent_id)
        
        # 创建workspace目录
        os.makedirs(workspace, exist_ok=True)
        
        # 创建Agent配置文件
        agent_config = {
            "name": name,
            "id": agent_id,
            "skills": skills or [],
            "created_at": datetime.now().isoformat(),
            "system_prompt": system_prompt or f"你是数字公司的员工 {name}。"
        }
        
        config_path = os.path.join(workspace, "AGENTS.md")
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(f"# {name}\n\n")
            f.write(f"ID: {agent_id}\n\n")
            f.write(f"技能: {', '.join(skills or [])}\n\n")
            if system_prompt:
                f.write(f"## 系统提示\n{system_prompt}\n")
        
        # 使用openclaw agents add创建agent
        cmd_result = self._run_command([
            "agents", "add", agent_id,
            "--agent-dir", workspace,
            "--non-interactive"
        ])
        
        with self._lock:
            agent = AgentInfo(
                agent_id=agent_id,
                name=name,
                workspace=workspace,
                status="created",
                skills=skills or [],
                created_at=datetime.now().isoformat()
            )
            self.agents[agent_id] = agent
            
        return agent
    
    def get_agent(self, agent_id: str) -> Optional[AgentInfo]:
        """获取Agent信息"""
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[AgentInfo]:
        """列出所有Agent"""
        return list(self.agents.values())
    
    def update_agent_status(self, agent_id: str, status: str) -> bool:
        """更新Agent状态"""
        with self._lock:
            if agent_id in self.agents:
                self.agents[agent_id].status = status
                self.agents[agent_id].last_active = datetime.now().isoformat()
                return True
        return False
    
    def delete_agent(self, agent_id: str) -> bool:
        """删除Agent"""
        cmd_result = self._run_command(["agents", "delete", agent_id])
        
        with self._lock:
            if agent_id in self.agents:
                del self.agents[agent_id]
                return True
        return False
    
    # ============== 任务调度 ==============
    
    def dispatch_task(self, agent_id: str, task: str, 
                     callback: Callable = None) -> str:
        """
        向Agent分配任务
        
        Args:
            agent_id: Agent ID
            task: 任务描述
            callback: 任务完成回调
        
        Returns:
            task_id: 任务ID
        """
        task_id = f"task-{uuid.uuid4().hex[:8]}"
        
        # 更新Agent状态
        self.update_agent_status(agent_id, "working")
        
        # 创建任务记录
        with self._lock:
            self.tasks[task_id] = TaskResult(
                task_id=task_id,
                agent_id=agent_id,
                status="running",
                created_at=datetime.now().isoformat()
            )
            if agent_id in self.agents:
                self.agents[agent_id].task_id = task_id
        
        # 在后台执行任务
        thread = threading.Thread(
            target=self._execute_task,
            args=(task_id, agent_id, task, callback)
        )
        thread.daemon = True
        thread.start()
        
        return task_id
    
    def _execute_task(self, task_id: str, agent_id: str, task: str, 
                     callback: Callable):
        """执行任务（后台线程）"""
        try:
            # 使用sessions_send发送任务
            result = self._run_command([
                "sessions_send",
                "--agent", agent_id,
                "--message", task,
                "--expect-final"
            ], timeout=300)
            
            with self._lock:
                if task_id in self.tasks:
                    if result.get("success"):
                        self.tasks[task_id].status = "completed"
                        self.tasks[task_id].result = result.get("stdout", "")
                        self.tasks[task_id].completed_at = datetime.now().isoformat()
                    else:
                        self.tasks[task_id].status = "failed"
                        self.tasks[task_id].error = result.get("stderr", result.get("error", ""))
                        self.tasks[task_id].completed_at = datetime.now().isoformat()
            
            # 更新Agent状态
            self.update_agent_status(agent_id, "idle")
            
            # 触发回调
            if callback:
                callback(self.tasks[task_id])
            
            # 触发webhook
            self._trigger_webhooks(self.tasks[task_id])
            
        except Exception as e:
            with self._lock:
                if task_id in self.tasks:
                    self.tasks[task_id].status = "failed"
                    self.tasks[task_id].error = str(e)
                    self.tasks[task_id].completed_at = datetime.now().isoformat()
            
            self.update_agent_status(agent_id, "idle")
    
    def get_task_status(self, task_id: str) -> Optional[TaskResult]:
        """获取任务状态"""
        return self.tasks.get(task_id)
    
    def list_tasks(self, agent_id: str = None, 
                   status: str = None) -> List[TaskResult]:
        """列出任务"""
        tasks = list(self.tasks.values())
        if agent_id:
            tasks = [t for t in tasks if t.agent_id == agent_id]
        if status:
            tasks = [t for t in tasks if t.status == status]
        return tasks
    
    # ============== Webhook回调 ==============
    
    def register_webhook(self, callback: Callable):
        """注册Webhook回调"""
        self.webhook_callbacks.append(callback)
    
    def unregister_webhook(self, callback: Callable):
        """注销Webhook回调"""
        if callback in self.webhook_callbacks:
            self.webhook_callbacks.remove(callback)
    
    def _trigger_webhooks(self, task_result: TaskResult):
        """触发Webhook回调"""
        for callback in self.webhook_callbacks:
            try:
                callback(task_result)
            except Exception as e:
                print(f"Webhook callback error: {e}")
    
    # ============== 同步方法 ==============
    
    def sync_employee_to_agent(self, employee_id: str, name: str, 
                               role: str, skills: List[str]) -> AgentInfo:
        """
        将员工同步到OpenClaw Agent
        
        Args:
            employee_id: 员工ID
            name: 员工姓名
            role: 职位
            skills: 技能列表
        
        Returns:
            AgentInfo: 对应的Agent信息
        """
        agent_name = f"{name}({role})"
        system_prompt = f"""你是数字公司的员工 {name}，担任 {role}。
你的职责包括：
- 服从公司安排的任务
- 及时汇报工作进度
- 保持专业的工作态度

技能：{', '.join(skills)}

当完成工作时，请返回任务结果摘要。"""
        
        agent = self.create_agent(
            name=agent_name,
            skills=skills,
            system_prompt=system_prompt
        )
        
        # 保存员工ID映射
        with self._lock:
            agent.employee_id = employee_id
        
        return agent
    
    def sync_agent_to_employee_status(self, agent_id: str) -> str:
        """
        同步Agent状态到员工状态
        
        Returns:
            员工状态字符串
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return "unknown"
        
        status_map = {
            "created": "idle",
            "running": "working",
            "idle": "idle",
            "working": "working",
            "completed": "idle",
            "failed": "idle"
        }
        
        return status_map.get(agent.status, "idle")


# 全局客户端实例
_client: Optional[OpenClawClient] = None


def get_openclaw_client() -> OpenClawClient:
    """获取OpenClaw客户端单例"""
    global _client
    if _client is None:
        _client = OpenClawClient()
    return _client
