"""
任务执行系统 - 从会议结论创建任务并执行
"""

import uuid
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from db.sqlite_repository import TaskRepository, EmployeeRepository, ProjectRepository


# 任务状态
TASK_STATUS_PENDING = "pending"       # 待处理
TASK_STATUS_IN_PROGRESS = "in_progress" # 进行中
TASK_STATUS_COMPLETED = "completed"    # 完成
TASK_STATUS_FAILED = "failed"           # 失败

# 优先级
PRIORITY_LOW = "low"
PRIORITY_MEDIUM = "medium"
PRIORITY_HIGH = "high"
PRIORITY_URGENT = "urgent"


class TaskExecutionSystem:
    """任务执行系统"""
    
    def __init__(self):
        self.tasks = {}  # task_id -> task_info
    
    def extract_tasks_from_conclusion(self, conclusion: str) -> List[str]:
        """
        从会议结论中提取任务
        
        Args:
            conclusion: 会议结论文本
        
        Returns:
            提取出的任务列表
        """
        tasks = []
        
        # 常见的任务关键词模式
        task_patterns = [
            r"做(.+?调研)",       # 做市场调研
            r"开发(.+?程序|.+?系统|.+?小程序)",  # 开发小程序
            r"分析(.+?数据|.+?报告)",  # 分析数据
            r"完成(.+?任务)",    # 完成任务
            r"推进(.+?项目)",    # 推进项目
            r"制定(.+?计划)",    # 制定计划
            r"优化(.+?流程)",    # 优化流程
            r"更新(.+?系统)",    # 更新系统
            r"创建(.+?文档)",    # 创建文档
            r"准备(.+?材料)",    # 准备材料
            r"开展(.+?活动)",    # 开展活动
            r"进行(.+?培训)",    # 进行培训
            r"落实(.+?措施)",    # 落实措施
            r"跟进(.+?进度)",    # 跟进进度
            r"检查(.+?情况)",    # 检查情况
            r"撰写(.+?报告)",    # 撰写报告
            r"整理(.+?资料)",    # 整理资料
            r"协调(.+?资源)",    # 协调资源
            r"维护(.+?关系)",    # 维护关系
        ]
        
        # 使用正则表达式提取
        for pattern in task_patterns:
            matches = re.findall(pattern, conclusion)
            for match in matches:
                task_name = match.strip()
                if task_name and len(task_name) > 1:
                    # 避免重复
                    if task_name not in tasks:
                        tasks.append(task_name)
        
        # 如果没有匹配到，尝试提取整个句子中的动词短语
        if not tasks:
            verb_patterns = [
                r"建议(.+?)执行",
                r"需要(.+?)完成",
                r"应该(.+?)处理",
                r"尽快(.+?)",
            ]
            for pattern in verb_patterns:
                matches = re.findall(pattern, conclusion)
                for match in matches:
                    task = match.strip()
                    if task and len(task) > 2:
                        if task not in tasks:
                            tasks.append(task)
        
        return tasks
    
    def create_task(self, name: str, description: str = "", project_id: int = None,
                    assignee_id: int = None, priority: str = PRIORITY_MEDIUM,
                    due_date: str = None, source: str = "manual") -> Dict:
        """
        创建任务
        
        Args:
            name: 任务名称
            description: 任务描述
            project_id: 所属项目ID
            assignee_id: 执行员工ID
            priority: 优先级
            due_date: 截止日期
            source: 任务来源（manual/manual_conclusion）
        
        Returns:
            创建的任务信息
        """
        task_id = TaskRepository.create(
            name=name,
            description=description,
            project_id=project_id,
            assignee_id=assignee_id,
            status=TASK_STATUS_PENDING,
            priority=priority,
            due_date=due_date
        )
        
        task_info = {
            "task_id": task_id,
            "name": name,
            "description": description,
            "project_id": project_id,
            "assignee_id": assignee_id,
            "status": TASK_STATUS_PENDING,
            "priority": priority,
            "due_date": due_date,
            "source": source,
            "created_at": datetime.now().isoformat(),
            "progress": 0,
            "logs": [{
                "timestamp": datetime.now().isoformat(),
                "action": "task_created",
                "message": f"任务 '{name}' 已创建"
            }],
            "result": None
        }
        
        self.tasks[task_id] = task_info
        return task_info
    
    def create_tasks_from_conclusion(self, conclusion: str, project_id: int = None,
                                     default_assignee_id: int = None) -> List[Dict]:
        """
        从会议结论创建多个任务
        
        Args:
            conclusion: 会议结论
            project_id: 所属项目ID
            default_assignee_id: 默认执行人ID
        
        Returns:
            创建的任务列表
        """
        task_names = self.extract_tasks_from_conclusion(conclusion)
        created_tasks = []
        
        for task_name in task_names:
            task = self.create_task(
                name=task_name,
                description=f"从会议结论提取的任务：{task_name}",
                project_id=project_id,
                assignee_id=default_assignee_id,
                priority=PRIORITY_MEDIUM,
                source="meeting_conclusion"
            )
            created_tasks.append(task)
        
        return created_tasks
    
    def assign_task(self, task_id: int, employee_id: int) -> Dict:
        """
        分配任务给员工
        
        Args:
            task_id: 任务ID
            employee_id: 员工ID
        
        Returns:
            更新后的任务信息
        """
        task = TaskRepository.get_by_id(task_id)
        if not task:
            return {"success": False, "error": "task_not_found"}
        
        employee = EmployeeRepository.get_by_id(employee_id)
        if not employee:
            return {"success": False, "error": "employee_not_found"}
        
        # 更新任务
        TaskRepository.update(task_id, assignee_id=employee_id)
        
        # 记录日志
        self._add_log(task_id, "task_assigned", f"任务分配给员工: {employee.get('name')}")
        
        task = TaskRepository.get_by_id(task_id)
        return {"success": True, "task": task}
    
    def set_priority(self, task_id: int, priority: str) -> Dict:
        """
        设置任务优先级
        
        Args:
            task_id: 任务ID
            priority: 优先级
        
        Returns:
            更新后的任务信息
        """
        if priority not in [PRIORITY_LOW, PRIORITY_MEDIUM, PRIORITY_HIGH, PRIORITY_URGENT]:
            return {"success": False, "error": "invalid_priority"}
        
        TaskRepository.update(task_id, priority=priority)
        
        priority_text = {"low": "低", "medium": "中", "high": "高", "urgent": "紧急"}
        self._add_log(task_id, "priority_changed", f"优先级设置为: {priority_text.get(priority)}")
        
        task = TaskRepository.get_by_id(task_id)
        return {"success": True, "task": task}
    
    def set_due_date(self, task_id: int, due_date: str) -> Dict:
        """
        设置任务截止日期
        
        Args:
            task_id: 任务ID
            due_date: 截止日期 (YYYY-MM-DD)
        
        Returns:
            更新后的任务信息
        """
        TaskRepository.update(task_id, due_date=due_date)
        
        self._add_log(task_id, "due_date_changed", f"截止日期设置为: {due_date}")
        
        task = TaskRepository.get_by_id(task_id)
        return {"success": True, "task": task}
    
    def start_task(self, task_id: int) -> Dict:
        """
        开始执行任务
        
        Args:
            task_id: 任务ID
        
        Returns:
            更新后的任务信息
        """
        task = TaskRepository.get_by_id(task_id)
        if not task:
            return {"success": False, "error": "task_not_found"}
        
        if task.get("status") == TASK_STATUS_COMPLETED:
            return {"success": False, "error": "task_already_completed"}
        
        # 更新状态为进行中
        TaskRepository.update(task_id, status=TASK_STATUS_IN_PROGRESS)
        
        # 记录日志
        self._add_log(task_id, "task_started", "任务开始执行")
        
        task = TaskRepository.get_by_id(task_id)
        return {"success": True, "task": task}
    
    def update_progress(self, task_id: int, progress: int, message: str = "") -> Dict:
        """
        更新任务进度
        
        Args:
            task_id: 任务ID
            progress: 进度 (0-100)
            message: 进度说明
        
        Returns:
            更新后的任务信息
        """
        if progress < 0 or progress > 100:
            return {"success": False, "error": "invalid_progress"}
        
        task = TaskRepository.get_by_id(task_id)
        if not task:
            return {"success": False, "error": "task_not_found"}
        
        # 记录进度日志
        log_message = f"进度更新: {task.get('progress', 0)}% → {progress}%"
        if message:
            log_message += f" - {message}"
        
        self._add_log(task_id, "progress_updated", log_message)
        
        # 如果进度达到100%，自动完成任务
        if progress == 100:
            return self.complete_task(task_id, message or "任务已完成")
        
        task = TaskRepository.get_by_id(task_id)
        return {"success": True, "task": task}
    
    def add_execution_log(self, task_id: int, log: str) -> Dict:
        """
        添加执行日志
        
        Args:
            task_id: 任务ID
            log: 日志内容
        
        Returns:
            结果
        """
        return self._add_log(task_id, "execution_log", log)
    
    def complete_task(self, task_id: int, result: str = None) -> Dict:
        """
        完成任务
        
        Args:
            task_id: 任务ID
            result: 任务结果
        
        Returns:
            更新后的任务信息
        """
        task = TaskRepository.get_by_id(task_id)
        if not task:
            return {"success": False, "error": "task_not_found"}
        
        # 更新状态为完成
        TaskRepository.update(task_id, status=TASK_STATUS_COMPLETED)
        
        # 记录完成日志
        self._add_log(task_id, "task_completed", result or "任务已完成")
        
        task = TaskRepository.get_by_id(task_id)
        return {"success": True, "task": task, "result": result}
    
    def fail_task(self, task_id: int, reason: str) -> Dict:
        """
        标记任务失败
        
        Args:
            task_id: 任务ID
            reason: 失败原因
        
        Returns:
            更新后的任务信息
        """
        task = TaskRepository.get_by_id(task_id)
        if not task:
            return {"success": False, "error": "task_not_found"}
        
        # 更新状态为失败
        TaskRepository.update(task_id, status=TASK_STATUS_FAILED)
        
        # 记录失败日志
        self._add_log(task_id, "task_failed", f"任务失败: {reason}")
        
        task = TaskRepository.get_by_id(task_id)
        return {"success": True, "task": task}
    
    def get_task_status(self, task_id: int) -> Dict:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
        
        Returns:
            任务信息
        """
        task = TaskRepository.get_by_id(task_id)
        if not task:
            return {"success": False, "error": "task_not_found"}
        
        # 获取任务日志
        task_info = self.tasks.get(task_id, {})
        logs = task_info.get("logs", [])
        
        return {
            "success": True,
            "task": task,
            "logs": logs
        }
    
    def get_all_tasks(self, status: str = None, assignee_id: int = None) -> List[Dict]:
        """
        获取所有任务
        
        Args:
            status: 任务状态过滤
            assignee_id: 执行人ID过滤
        
        Returns:
            任务列表
        """
        tasks = TaskRepository.get_all(status=status, assignee_id=assignee_id)
        return tasks
    
    def get_task_statistics(self) -> Dict:
        """
        获取任务统计信息
        
        Returns:
            统计信息
        """
        all_tasks = TaskRepository.get_all()
        
        stats = {
            "total": len(all_tasks),
            "pending": 0,
            "in_progress": 0,
            "completed": 0,
            "failed": 0
        }
        
        for task in all_tasks:
            status = task.get("status", "pending")
            if status in stats:
                stats[status] += 1
        
        return stats
    
    def _add_log(self, task_id: int, action: str, message: str) -> Dict:
        """
        添加任务日志
        
        Args:
            task_id: 任务ID
            action: 操作类型
            message: 日志消息
        
        Returns:
            结果
        """
        if task_id not in self.tasks:
            # 从数据库加载任务
            task = TaskRepository.get_by_id(task_id)
            if not task:
                return {"success": False, "error": "task_not_found"}
            self.tasks[task_id] = {
                "task_id": task_id,
                "logs": []
            }
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "message": message
        }
        
        self.tasks[task_id]["logs"].append(log_entry)
        
        return {"success": True, "log": log_entry}


# 全局实例
_task_execution_system = None


def get_task_system() -> TaskExecutionSystem:
    """获取任务执行系统实例"""
    global _task_execution_system
    if _task_execution_system is None:
        _task_execution_system = TaskExecutionSystem()
    return _task_execution_system


def create_task(name: str, description: str = "", project_id: int = None,
               assignee_id: int = None, priority: str = "medium",
               due_date: str = None) -> Dict:
    """创建任务"""
    system = get_task_system()
    return system.create_task(name, description, project_id, assignee_id, priority, due_date)


def create_tasks_from_conclusion(conclusion: str, project_id: int = None,
                                 default_assignee_id: int = None) -> List[Dict]:
    """从会议结论创建任务"""
    system = get_task_system()
    return system.create_tasks_from_conclusion(conclusion, project_id, default_assignee_id)


def assign_task(task_id: int, employee_id: int) -> Dict:
    """分配任务"""
    system = get_task_system()
    return system.assign_task(task_id, employee_id)


def set_task_priority(task_id: int, priority: str) -> Dict:
    """设置任务优先级"""
    system = get_task_system()
    return system.set_priority(task_id, priority)


def set_task_due_date(task_id: int, due_date: str) -> Dict:
    """设置任务截止日期"""
    system = get_task_system()
    return system.set_due_date(task_id, due_date)


def start_task(task_id: int) -> Dict:
    """开始任务"""
    system = get_task_system()
    return system.start_task(task_id)


def update_task_progress(task_id: int, progress: int, message: str = "") -> Dict:
    """更新任务进度"""
    system = get_task_system()
    return system.update_progress(task_id, progress, message)


def add_task_log(task_id: int, log: str) -> Dict:
    """添加任务日志"""
    system = get_task_system()
    return system.add_execution_log(task_id, log)


def complete_task(task_id: int, result: str = None) -> Dict:
    """完成任务"""
    system = get_task_system()
    return system.complete_task(task_id, result)


def fail_task(task_id: int, reason: str) -> Dict:
    """标记任务失败"""
    system = get_task_system()
    return system.fail_task(task_id, reason)


def get_task_status(task_id: int) -> Dict:
    """获取任务状态"""
    system = get_task_system()
    return system.get_task_status(task_id)


def get_all_tasks(status: str = None, assignee_id: int = None) -> List[Dict]:
    """获取所有任务"""
    system = get_task_system()
    return system.get_all_tasks(status, assignee_id)


def get_task_statistics() -> Dict:
    """获取任务统计"""
    system = get_task_system()
    return system.get_task_statistics()
