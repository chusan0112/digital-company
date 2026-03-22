"""
数字公司插件 - 核心数据模型（持久化版）
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional
import uuid
import json
import os


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
    status: str = "idle"
    hire_date: str = ""
    salary: float = 0
    performance: float = 100
    
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
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self):
        return asdict(self)
    
    @staticmethod
    def from_dict(d):
        return Task(**d)


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
        
        self.budget = 1000
        self.spent = 0
        
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
            "tasks": [t.to_dict() for t in self.tasks]
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
                     skills: List[str] = None, salary: float = 0) -> Employee:
        emp = Employee(
            id=str(uuid.uuid4())[:8],
            name=name,
            role=role,
            department_id=department_id,
            skills=skills or [],
            salary=salary
        )
        self.employees.append(emp)
        self.save()
        return emp
    
    def fire_employee(self, emp_id: str) -> bool:
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
        return {
            "company_name": self.name,
            "founded_at": self.founded_at,
            "departments": len(self.departments),
            "employees": len(self.employees),
            "employees_by_status": {
                "working": len([e for e in self.employees if e.status == "working"]),
                "idle": len([e for e in self.employees if e.status == "idle"]),
                "meeting": len([e for e in self.employees if e.status == "meeting"])
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
            }
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
