"""
数字公司插件 - 核心数据模型（持久化版）
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional
import uuid
import json
import os

# OpenClaw集成
try:
    from integrations.openclaw_client import get_openclaw_client, AgentInfo
    OPENCLAW_ENABLED = True
except ImportError:
    OPENCLAW_ENABLED = False
    AgentInfo = None


DATA_FILE = os.path.join(os.path.dirname(__file__), "company_data.json")


# ============== 部门 ==============

@dataclass
class Department:
    """部门"""
    id: str
    name: str
    description: str = ""
    parent_id: str = ""
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self):
        return asdict(self)
    
    @staticmethod
    def from_dict(d):
        return Department(**d)


# ============== 员工 ==============

@dataclass
class Employee:
    """员工（子Agent）"""
    id: str
    name: str
    role: str
    department_id: str
    skills: List[str] = field(default_factory=list)
    status: str = "idle"  # idle, working, discussing, resting
    hire_date: str = ""
    salary: float = 0
    performance: float = 100
    openclaw_agent_id: str = ""  # OpenClaw子Agent ID
    current_task_id: str = ""  # 当前执行的任务ID
    current_task_name: str = ""  # 当前任务名称
    
    def __post_init__(self):
        if not self.hire_date:
            self.hire_date = datetime.now().isoformat()
    
    def to_dict(self):
        return asdict(self)
    
    @staticmethod
    def from_dict(d):
        return Employee(**d)


# ============== 项目 ==============

@dataclass
class Meeting:
    """会议"""
    id: str
    title: str
    participants: List[str] = field(default_factory=list)  # 员工ID列表
    current_speaker_id: str = ""
    current_speech: str = ""
    progress: int = 0  # 0-100
    status: str = "waiting"  # waiting, in_progress, completed
    agenda: List[str] = field(default_factory=list)  # 议程列表
    started_at: str = ""
    ended_at: str = ""
    
    def __post_init__(self):
        if not self.started_at:
            self.started_at = datetime.now().isoformat()
    
    def to_dict(self):
        return asdict(self)
    
    @staticmethod
    def from_dict(d):
        return Meeting(**d)


@dataclass
class Project:
    """项目"""
    id: str
    name: str
    description: str
    status: str = "planning"
    priority: int = 1
    department_id: str = ""
    start_date: str = ""
    end_date: str = ""
    budget: float = 0
    progress: int = 0
    
    def __post_init__(self):
        if not self.start_date:
            self.start_date = datetime.now().isoformat()
    
    def to_dict(self):
        return asdict(self)
    
    @staticmethod
    def from_dict(d):
        return Project(**d)


# ============== 任务 ==============

@dataclass
class TaskLog:
    """任务执行日志"""
    id: str
    task_id: str
    message: str
    timestamp: str = ""
    level: str = "info"  # info, warning, error, success
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self):
        return asdict(self)
    
    @staticmethod
    def from_dict(d):
        return TaskLog(**d)


@dataclass
class Task:
    """任务"""
    id: str
    name: str
    description: str
    project_id: str = ""
    assignee_id: str = ""
    status: str = "pending"
    priority: int = 1
    created_at: str = ""
    due_date: str = ""
    progress: int = 0  # 0-100
    logs: List[TaskLog] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self):
        return asdict(self)
    
    @staticmethod
    def from_dict(d):
        logs = [TaskLog.from_dict(l) for l in d.get('logs', [])]
        d['logs'] = logs
        return Task(**d)
    
    def add_log(self, message: str, level: str = "info"):
        """添加执行日志"""
        log = TaskLog(
            id=str(uuid.uuid4())[:8],
            task_id=self.id,
            message=message,
            level=level
        )
        self.logs.append(log)
        return log


# ============== 公司 ==============

class Company:
    """公司 - 核心管理类"""
    
    def __init__(self, name: str = "金库集团"):
        self.id = str(uuid.uuid4())[:8]
        self.name = name
        self.founded_at = datetime.now().isoformat()
        
        self.departments: List[Department] = []
        self.employees: List[Employee] = []
        self.projects: List[Project] = []
        self.tasks: List[Task] = []
        self.meetings: List[Meeting] = []  # 会议列表
        
        self.budget = 1000
        self.spent = 0
        
        # OpenClaw集成
        self.openclaw_client = None
        if OPENCLAW_ENABLED:
            try:
                self.openclaw_client = get_openclaw_client()
            except Exception as e:
                print(f"OpenClaw client init warning: {e}")
        
        # 加载或初始化
        self.load()
    
    # ---------- 数据持久化 ----------
    
    def save(self):
        """保存数据到文件"""
        data = {
            "id": self.id,
            "name": self.name,
            "founded_at": self.founded_at,
            "budget": self.budget,
            "spent": self.spent,
            "departments": [d.to_dict() for d in self.departments],
            "employees": [e.to_dict() for e in self.employees],
            "projects": [p.to_dict() for p in self.projects],
            "tasks": [t.to_dict() for t in self.tasks],
            "meetings": [m.to_dict() for m in self.meetings]
        }
        
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load(self):
        """从文件加载数据"""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                self.id = data.get("id", self.id)
                self.name = data.get("name", self.name)
                self.founded_at = data.get("founded_at", self.founded_at)
                self.budget = data.get("budget", 1000)
                self.spent = data.get("spent", 0)
                
                self.departments = [Department.from_dict(d) for d in data.get("departments", [])]
                self.employees = [Employee.from_dict(e) for e in data.get("employees", [])]
                self.projects = [Project.from_dict(p) for p in data.get("projects", [])]
                self.tasks = [Task.from_dict(t) for t in data.get("tasks", [])]
                self.meetings = [Meeting.from_dict(m) for m in data.get("meetings", [])]
            except:
                self._init_default()
        else:
            self._init_default()
    
    def _init_default(self):
        """初始化默认数据"""
        # 创建默认部门
        self.add_department("总经办", "公司最高管理层")
        self.add_department("研发部", "技术研发")
        self.add_department("运营部", "日常运营")
        self.add_department("财务部", "财务管理")
        self.add_department("市场部", "市场营销")
        
        # 雇佣6位高管
        self.hire_employee("金小创", "首席创意官 CCO", "总经办", ["创意", "策划"], 0)
        self.hire_employee("金小运", "首席运营官 COO", "运营部", ["运营", "项目管理"], 0)
        self.hire_employee("金小财", "首席财务官 CFO", "财务部", ["财务", "分析"], 0)
        self.hire_employee("金小码", "首席技术官 CTO", "研发部", ["技术", "架构"], 0)
        self.hire_employee("金小产", "首席产品官 CPO", "研发部", ["产品", "设计"], 0)
        self.hire_employee("金小市", "首席市场官 CMO", "市场部", ["市场", "销售"], 0)
        
        # 创建演示数据
        self._create_demo_data()
        
        self.save()
    
    def _create_demo_data(self):
        """创建演示数据（用于实时可视化测试）"""
        if not self.employees:
            return
        
        # 创建一些演示任务
        emp_ids = [e.id for e in self.employees]
        
        # 任务1：进行中
        task1 = self.create_task(
            name="开发可视化驾驶舱",
            description="开发实时可视化界面",
            assignee_id=emp_ids[3] if len(emp_ids) > 3 else emp_ids[0],
            priority=5
        )
        self.assign_task(task1.id, emp_ids[3] if len(emp_ids) > 3 else emp_ids[0])
        self.update_task_progress(task1.id, 65)
        self.add_task_log(task1.id, "开始开发实时可视化界面", "info")
        self.add_task_log(task1.id, "完成员工状态模块", "success")
        self.add_task_log(task1.id, "正在开发任务进度模块", "info")
        
        # 更新员工当前任务
        emp = self.get_employee(emp_ids[3] if len(emp_ids) > 3 else emp_ids[0])
        if emp:
            emp.current_task_id = task1.id
            emp.current_task_name = task1.name
            emp.status = "working"
        
        # 任务2：待处理
        task2 = self.create_task(
            name="优化系统性能",
            description="提升系统响应速度",
            assignee_id=emp_ids[4] if len(emp_ids) > 4 else emp_ids[0],
            priority=3
        )
        
        # 任务3：已完成
        task3 = self.create_task(
            name="完成UI设计",
            description="完成驾驶舱界面设计",
            assignee_id=emp_ids[4] if len(emp_ids) > 4 else emp_ids[0],
            priority=4
        )
        self.assign_task(task3.id, emp_ids[4] if len(emp_ids) > 4 else emp_ids[0])
        self.complete_task(task3.id)
        self.add_task_log(task3.id, "完成界面设计初稿", "success")
        self.add_task_log(task3.id, "通过评审", "success")
        
        # 创建一个演示会议
        meeting = self.create_meeting(
            title="周例会",
            participants=emp_ids[:4],
            agenda=["汇报上周工作", "讨论本周计划", "问题协调", "总结"]
        )
        self.start_meeting(meeting.id)
        self.update_meeting_speaker(meeting.id, emp_ids[0], "大家好，我来汇报上周的工作进展...")
        self.update_meeting_progress(meeting.id, 35)
        
        # 设置部分员工状态
        if len(emp_ids) > 1:
            self.update_employee_status(emp_ids[1], "discussing")
        if len(emp_ids) > 2:
            self.update_employee_status(emp_ids[2], "resting")
        
        self.save()
    
    # ---------- 部门管理 ----------
    
    def add_department(self, name: str, description: str = "", parent_id: str = "") -> Department:
        dept = Department(
            id=str(uuid.uuid4())[:8],
            name=name,
            description=description,
            parent_id=parent_id
        )
        self.departments.append(dept)
        self.save()
        return dept
    
    def get_department(self, dept_id: str) -> Optional[Department]:
        for dept in self.departments:
            if dept.id == dept_id:
                return dept
        return None
    
    def list_departments(self) -> List[Department]:
        return self.departments
    
    # ---------- 员工管理 ----------
    
    def hire_employee(self, name: str, role: str, department_id: str, 
                     skills: List[str] = None, salary: float = 0,
                     create_openclaw_agent: bool = True) -> Employee:
        """
        雇佣员工
        
        Args:
            name: 员工姓名
            role: 职位
            department_id: 部门ID
            skills: 技能列表
            salary: 薪资
            create_openclaw_agent: 是否在OpenClaw中创建对应Agent
        """
        emp = Employee(
            id=str(uuid.uuid4())[:8],
            name=name,
            role=role,
            department_id=department_id,
            skills=skills or [],
            salary=salary
        )
        
        # 如果启用OpenClaw，创建对应的Agent
        if create_openclaw_agent and self.openclaw_client and OPENCLAW_ENABLED:
            try:
                agent = self.openclaw_client.sync_employee_to_agent(
                    employee_id=emp.id,
                    name=name,
                    role=role,
                    skills=skills or []
                )
                emp.openclaw_agent_id = agent.agent_id
            except Exception as e:
                print(f"Failed to create OpenClaw agent: {e}")
        
        self.employees.append(emp)
        self.save()
        return emp
    
    def fire_employee(self, emp_id: str) -> bool:
        """解雇员工"""
        emp = self.get_employee(emp_id)
        
        # 如果有OpenClaw Agent，一并删除
        if emp and emp.openclaw_agent_id and self.openclaw_client:
            try:
                self.openclaw_client.delete_agent(emp.openclaw_agent_id)
            except Exception as e:
                print(f"Failed to delete OpenClaw agent: {e}")
        
        for i, emp in enumerate(self.employees):
            if emp.id == emp_id:
                self.employees.pop(i)
                self.save()
                return True
        return False
    
    def get_employee(self, emp_id: str) -> Optional[Employee]:
        for emp in self.employees:
            if emp.id == emp_id:
                return emp
        return None
    
    def list_employees(self, department_id: str = None) -> List[Employee]:
        if department_id:
            return [e for e in self.employees if e.department_id == department_id]
        return self.employees
    
    def update_employee_status(self, emp_id: str, status: str):
        emp = self.get_employee(emp_id)
        if emp:
            emp.status = status
            self.save()
    
    # ---------- OpenClaw集成 ----------
    
    def dispatch_task_to_employee(self, emp_id: str, task_description: str) -> str:
        """
        分配任务给员工（通过OpenClaw Agent）
        
        Args:
            emp_id: 员工ID
            task_description: 任务描述
        
        Returns:
            task_id: 任务ID
        """
        emp = self.get_employee(emp_id)
        if not emp:
            raise ValueError(f"Employee {emp_id} not found")
        
        if not emp.openclaw_agent_id:
            raise ValueError(f"Employee {emp_id} has no OpenClaw agent")
        
        if not self.openclaw_client:
            raise RuntimeError("OpenClaw client not initialized")
        
        # 创建任务
        task = self.create_task(
            name=task_description[:50],
            description=task_description,
            assignee_id=emp_id
        )
        
        # 通过OpenClaw执行任务
        def task_callback(result):
            """任务完成回调"""
            if result.status == "completed":
                self.complete_task(task.id)
            # 同步Agent状态到员工
            self.sync_agent_status(emp.openclaw_agent_id)
        
        task_id = self.openclaw_client.dispatch_task(
            agent_id=emp.openclaw_agent_id,
            task=task_description,
            callback=task_callback
        )
        
        # 更新员工状态
        self.update_employee_status(emp_id, "working")
        
        return task.id
    
    def sync_agent_status(self, agent_id: str = None, emp_id: str = None):
        """
        同步OpenClaw Agent状态到员工
        
        Args:
            agent_id: Agent ID (二选一)
            emp_id: 员工ID (二选一)
        """
        if not self.openclaw_client:
            return
        
        # 根据Agent ID查找员工
        if agent_id:
            for emp in self.employees:
                if emp.openclaw_agent_id == agent_id:
                    emp_id = emp.id
                    break
        
        if not emp_id:
            return
        
        emp = self.get_employee(emp_id)
        if not emp or not emp.openclaw_agent_id:
            return
        
        # 获取Agent状态
        agent = self.openclaw_client.get_agent(emp.openclaw_agent_id)
        if agent:
            status_map = {
                "created": "idle",
                "running": "working",
                "idle": "idle",
                "working": "working",
                "completed": "idle",
                "failed": "idle"
            }
            emp.status = status_map.get(agent.status, "idle")
            self.save()
    
    def get_employee_agent(self, emp_id: str) -> Optional[AgentInfo]:
        """获取员工的OpenClaw Agent信息"""
        emp = self.get_employee(emp_id)
        if not emp or not emp.openclaw_agent_id:
            return None
        
        if not self.openclaw_client:
            return None
        
        return self.openclaw_client.get_agent(emp.openclaw_agent_id)
    
    # ---------- 项目管理 ----------
    
    def create_project(self, name: str, description: str, 
                     department_id: str = "", budget: float = 0) -> Project:
        proj = Project(
            id=str(uuid.uuid4())[:8],
            name=name,
            description=description,
            department_id=department_id,
            budget=budget
        )
        self.projects.append(proj)
        self.save()
        return proj
    
    def get_project(self, proj_id: str) -> Optional[Project]:
        for p in self.projects:
            if p.id == proj_id:
                return p
        return None
    
    def list_projects(self, status: str = None) -> List[Project]:
        if status:
            return [p for p in self.projects if p.status == status]
        return self.projects
    
    def update_project_progress(self, proj_id: str, progress: int):
        proj = self.get_project(proj_id)
        if proj:
            proj.progress = min(100, max(0, progress))
            if proj.progress == 100:
                proj.status = "completed"
            self.save()
    
    # ---------- 任务管理 ----------
    
    def create_task(self, name: str, description: str, 
                   project_id: str = "", assignee_id: str = "",
                   priority: int = 1) -> Task:
        task = Task(
            id=str(uuid.uuid4())[:8],
            name=name,
            description=description,
            project_id=project_id,
            assignee_id=assignee_id,
            priority=priority
        )
        self.tasks.append(task)
        self.save()
        return task
    
    def assign_task(self, task_id: str, emp_id: str) -> bool:
        task = self.get_task(task_id)
        if task:
            task.assignee_id = emp_id
            task.status = "in_progress"
            self.save()
            return True
        return False
    
    def complete_task(self, task_id: str) -> bool:
        task = self.get_task(task_id)
        if task:
            task.status = "completed"
            self.save()
            return True
        return False
    
    def get_task(self, task_id: str) -> Optional[Task]:
        for t in self.tasks:
            if t.id == task_id:
                return t
        return None
    
    def list_tasks(self, status: str = None, assignee_id: str = None) -> List[Task]:
        result = self.tasks
        if status:
            result = [t for t in result if t.status == status]
        if assignee_id:
            result = [t for t in result if t.assignee_id == assignee_id]
        return result
    
    def update_task_progress(self, task_id: str, progress: int):
        """更新任务进度"""
        task = self.get_task(task_id)
        if task:
            task.progress = min(100, max(0, progress))
            if task.progress == 100:
                task.status = "completed"
            self.save()
    
    def add_task_log(self, task_id: str, message: str, level: str = "info"):
        """添加任务执行日志"""
        task = self.get_task(task_id)
        if task:
            task.add_log(message, level)
            self.save()
            return task.logs[-1]
        return None
    
    def get_task_logs(self, task_id: str) -> List[TaskLog]:
        """获取任务的所有日志"""
        task = self.get_task(task_id)
        if task:
            return task.logs
        return []
    
    # ---------- 会议管理 ----------
    
    def create_meeting(self, title: str, participants: List[str], agenda: List[str] = None) -> Meeting:
        """创建会议"""
        meeting = Meeting(
            id=str(uuid.uuid4())[:8],
            title=title,
            participants=participants,
            agenda=agenda or [],
            status="waiting"
        )
        self.meetings.append(meeting)
        self.save()
        return meeting
    
    def start_meeting(self, meeting_id: str) -> bool:
        """开始会议"""
        meeting = self.get_meeting(meeting_id)
        if meeting:
            meeting.status = "in_progress"
            self.save()
            return True
        return False
    
    def get_meeting(self, meeting_id: str) -> Optional[Meeting]:
        for m in self.meetings:
            if m.id == meeting_id:
                return m
        return None
    
    def update_meeting_speaker(self, meeting_id: str, speaker_id: str, speech: str = ""):
        """更新会议发言人"""
        meeting = self.get_meeting(meeting_id)
        if meeting:
            meeting.current_speaker_id = speaker_id
            meeting.current_speech = speech
            self.save()
    
    def update_meeting_progress(self, meeting_id: str, progress: int):
        """更新会议进度"""
        meeting = self.get_meeting(meeting_id)
        if meeting:
            meeting.progress = min(100, max(0, progress))
            if meeting.progress == 100:
                meeting.status = "completed"
                meeting.ended_at = datetime.now().isoformat()
            self.save()
    
    def list_meetings(self, status: str = None) -> List[Meeting]:
        if status:
            return [m for m in self.meetings if m.status == status]
        return self.meetings
    
    def get_current_meeting(self) -> Optional[Meeting]:
        """获取当前进行中的会议"""
        for m in self.meetings:
            if m.status == "in_progress":
                return m
        return None
    
    # ---------- 财务 ----------
    
    def spend(self, amount: float, description: str = "") -> bool:
        if amount > self.budget - self.spent:
            return False
        self.spent += amount
        self.save()
        return True
    
    def get_balance(self) -> float:
        return self.budget - self.spent
    
    # ---------- 统计 ----------
    
    def get_dashboard(self) -> dict:
        # 获取当前会议
        current_meeting = self.get_current_meeting()
        meeting_data = None
        if current_meeting:
            speaker = self.get_employee(current_meeting.current_speaker_id)
            meeting_data = {
                "id": current_meeting.id,
                "title": current_meeting.title,
                "current_speaker": speaker.name if speaker else "未知",
                "current_speech": current_meeting.current_speech,
                "progress": current_meeting.progress,
                "agenda": current_meeting.agenda,
                "participants_count": len(current_meeting.participants)
            }
        
        return {
            "company_name": self.name,
            "founded_at": self.founded_at,
            "departments": len(self.departments),
            "employees": len(self.employees),
            "employees_by_status": {
                "working": len([e for e in self.employees if e.status == "working"]),
                "idle": len([e for e in self.employees if e.status == "idle"]),
                "discussing": len([e for e in self.employees if e.status == "discussing"]),
                "resting": len([e for e in self.employees if e.status == "resting"])
            },
            "projects": {
                "total": len(self.projects),
                "planning": len([p for p in self.projects if p.status == "planning"]),
                "running": len([p for p in self.projects if p.status == "running"]),
                "completed": len([p for p in self.projects if p.status == "completed"])
            },
            "tasks": {
                "total": len(self.tasks),
                "pending": len([t for t in self.tasks if t.status == "pending"]),
                "in_progress": len([t for t in self.tasks if t.status == "in_progress"]),
                "completed": len([t for t in self.tasks if t.status == "completed"])
            },
            "financial": {
                "budget": self.budget,
                "spent": self.spent,
                "balance": self.get_balance()
            },
            "meeting": meeting_data,
            "meetings_count": len(self.meetings)
        }


# ============== 全局实例 =============

_company: Optional[Company] = None


def get_company() -> Company:
    global _company
    if _company is None:
        _company = Company()
    return _company


def reset_company():
    """重置公司（测试用）"""
    global _company
    _company = None
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
