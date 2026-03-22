#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目生命周期管理系统
包含：项目立项、会议系统、项目执行、复盘总结、知识库
"""

import json
import os
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from enum import Enum

# 数据存储路径
STORAGE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage", "projects")
KNOWLEDGE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage", "knowledge")


class ProjectStatus(Enum):
    """项目状态"""
    PLANNING = "planning"       # 规划中
    KICKOFF = "kickoff"         # 立项中
    ACTIVE = "active"           # 执行中
    REVIEW = "review"           # 中期复盘
    COMPLETED = "completed"     # 已完成
    ARCHIVED = "archived"       # 已归档


class MeetingType(Enum):
    """会议类型"""
    KICKOFF = "kickoff"         # 立项会议（头脑风暴）
    STANDUP = "standup"          # 晨会/例会
    REVIEW = "review"           # 中期复盘会
    RETROSPECTIVE = "retrospective"  # 项目总结会
    REGULAR = "regular"         # 常规会议


class ProjectLifecycleService:
    """项目生命周期服务"""
    
    def __init__(self):
        self._ensure_directories()
        self._projects_cache = {}
        self._load_projects()
    
    def _ensure_directories(self):
        """确保目录结构存在"""
        os.makedirs(STORAGE_PATH, exist_ok=True)
        os.makedirs(KNOWLEDGE_PATH, exist_ok=True)
        os.makedirs(os.path.join(KNOWLEDGE_PATH, "lessons"), exist_ok=True)
        os.makedirs(os.path.join(KNOWLEDGE_PATH, "summaries"), exist_ok=True)
    
    def _load_projects(self):
        """加载所有项目"""
        if not os.path.exists(STORAGE_PATH):
            return
        
        for project_dir in os.listdir(STORAGE_PATH):
            project_path = os.path.join(STORAGE_PATH, project_dir)
            if os.path.isdir(project_path):
                info_file = os.path.join(project_path, "info.json")
                if os.path.exists(info_file):
                    with open(info_file, 'r', encoding='utf-8') as f:
                        self._projects_cache[project_dir] = json.load(f)
    
    def _save_project(self, project_id: str, project_data: Dict):
        """保存项目数据"""
        project_path = os.path.join(STORAGE_PATH, project_id)
        os.makedirs(project_path, exist_ok=True)
        
        # 创建子目录
        os.makedirs(os.path.join(project_path, "meetings"), exist_ok=True)
        os.makedirs(os.path.join(project_path, "tasks"), exist_ok=True)
        os.makedirs(os.path.join(project_path, "lessons"), exist_ok=True)
        
        info_file = os.path.join(project_path, "info.json")
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(project_data, f, ensure_ascii=False, indent=2)
        
        self._projects_cache[project_id] = project_data
    
    def _get_project_path(self, project_id: str) -> str:
        """获取项目路径"""
        return os.path.join(STORAGE_PATH, project_id)
    
    # ============== 项目立项 ==============
    
    def create_project(self, name: str, description: str = "", 
                       department_id: str = "", budget: float = 0,
                       owner: str = "", tags: List[str] = None) -> Dict:
        """
        创建新项目
        
        Args:
            name: 项目名称
            description: 项目描述
            department_id: 部门ID
            budget: 预算
            owner: 项目负责人
            tags: 项目标签
        
        Returns:
            项目信息
        """
        project_id = f"proj_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:6]}"
        
        project_data = {
            "id": project_id,
            "name": name,
            "description": description,
            "department_id": department_id,
            "budget": budget,
            "owner": owner,
            "tags": tags or [],
            "status": ProjectStatus.PLANNING.value,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "start_date": None,
            "end_date": None,
            "kickoff_meeting_id": None,
            "meetings": [],
            "tasks": [],
            "lessons": [],
            "milestones": [],
            "team_members": [],
            "progress": 0,
            "conclusion": None,  # 项目最终结论
        }
        
        self._save_project(project_id, project_data)
        
        return project_data
    
    def get_project(self, project_id: str) -> Optional[Dict]:
        """获取项目信息"""
        return self._projects_cache.get(project_id)
    
    def list_projects(self, status: str = None) -> List[Dict]:
        """列出所有项目"""
        projects = list(self._projects_cache.values())
        
        if status:
            projects = [p for p in projects if p.get("status") == status]
        
        # 按创建时间排序
        projects.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return projects
    
    def update_project(self, project_id: str, **kwargs) -> bool:
        """更新项目信息"""
        project = self._projects_cache.get(project_id)
        if not project:
            return False
        
        allowed_fields = ["name", "description", "department_id", "budget", 
                         "owner", "tags", "status", "start_date", "end_date",
                         "progress", "conclusion", "team_members", "milestones"]
        
        for key, value in kwargs.items():
            if key in allowed_fields:
                project[key] = value
        
        project["updated_at"] = datetime.now().isoformat()
        
        self._save_project(project_id, project)
        return True
    
    # ============== 会议系统 ==============
    
    def create_meeting(self, project_id: str, meeting_type: str,
                       title: str, host: str, participants: List[str] = None,
                       agenda: str = "", start_time: str = None,
                       end_time: str = None) -> Dict:
        """
        创建会议
        
        Args:
            project_id: 项目ID
            meeting_type: 会议类型 (kickoff/standup/review/retrospective/regular)
            title: 会议标题
            host: 主持人
            participants: 参会人
            agenda: 议程
            start_time: 开始时间
            end_time: 结束时间
        
        Returns:
            会议信息
        """
        project = self._projects_cache.get(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        meeting_id = f"meet_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:6]}"
        
        meeting_data = {
            "id": meeting_id,
            "type": meeting_type,
            "title": title,
            "host": host,
            "participants": participants or [],
            "agenda": agenda,
            "start_time": start_time or datetime.now().isoformat(),
            "end_time": end_time,
            "status": "scheduled",  # scheduled/in_progress/completed/cancelled
            "created_at": datetime.now().isoformat(),
            "summary": None,      # 会议纪要
            "decisions": [],      # 决议事项
            "action_items": [],   # 行动项
            "speeches": [],       # 发言记录（用于立项会议）
        }
        
        # 保存会议到项目目录
        meeting_file = os.path.join(
            self._get_project_path(project_id), 
            "meetings", 
            f"{meeting_id}.json"
        )
        with open(meeting_file, 'w', encoding='utf-8') as f:
            json.dump(meeting_data, f, ensure_ascii=False, indent=2)
        
        # 更新项目的会议列表
        project.setdefault("meetings", []).append(meeting_id)
        
        # 如果是立项会议，记录到项目信息
        if meeting_type == MeetingType.KICKOFF.value:
            project["kickoff_meeting_id"] = meeting_id
            project["status"] = ProjectStatus.KICKOFF.value
        
        self._save_project(project_id, project)
        
        return meeting_data
    
    def get_meeting(self, project_id: str, meeting_id: str) -> Optional[Dict]:
        """获取会议信息"""
        meeting_file = os.path.join(
            self._get_project_path(project_id),
            "meetings",
            f"{meeting_id}.json"
        )
        
        if not os.path.exists(meeting_file):
            return None
        
        with open(meeting_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def update_meeting(self, project_id: str, meeting_id: str, **kwargs) -> bool:
        """更新会议信息"""
        meeting = self.get_meeting(project_id, meeting_id)
        if not meeting:
            return False
        
        allowed_fields = ["title", "host", "participants", "agenda", 
                         "start_time", "end_time", "status", 
                         "summary", "decisions", "action_items", "speeches"]
        
        for key, value in kwargs.items():
            if key in allowed_fields:
                meeting[key] = value
        
        meeting_file = os.path.join(
            self._get_project_path(project_id),
            "meetings",
            f"{meeting_id}.json"
        )
        
        with open(meeting_file, 'w', encoding='utf-8') as f:
            json.dump(meeting, f, ensure_ascii=False, indent=2)
        
        return True
    
    def list_meetings(self, project_id: str, meeting_type: str = None) -> List[Dict]:
        """列出项目的所有会议"""
        project = self._projects_cache.get(project_id)
        if not project:
            return []
        
        meetings = []
        project_path = self._get_project_path(project_id)
        meetings_dir = os.path.join(project_path, "meetings")
        
        if not os.path.exists(meetings_dir):
            return []
        
        for meeting_file in os.listdir(meetings_dir):
            if meeting_file.endswith(".json"):
                with open(os.path.join(meetings_dir, meeting_file), 'r', encoding='utf-8') as f:
                    meeting = json.load(f)
                    if meeting_type is None or meeting.get("type") == meeting_type:
                        meetings.append(meeting)
        
        meetings.sort(key=lambda x: x.get("start_time", ""), reverse=True)
        
        return meetings
    
    # ============== AI高管辩论（立项会议）==============
    
    def run_kickoff_meeting(self, project_id: str, context: Dict = None) -> Dict:
        """
        运行立项会议（AI高管头脑风暴）
        
        Args:
            project_id: 项目ID
            context: 额外上下文（预算、截止日期等）
        
        Returns:
            会议结果（含辩论记录和结论）
        """
        project = self._projects_cache.get(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        # 创建立项会议
        meeting = self.create_meeting(
            project_id=project_id,
            meeting_type=MeetingType.KICKOFF.value,
            title=f"立项会议: {project['name']}",
            host="CEO",
            participants=["CEO", "CFO", "CTO", "COO", "CHRO"]
        )
        
        # 导入会议讨论系统
        from core.meeting import run_full_discussion
        
        # 运行AI高管辩论
        topic = f"项目: {project['name']} - {project['description']}"
        discussion_result = run_full_discussion(topic, context)
        
        # 提取关键信息（从summary中获取）
        summary = discussion_result.get("summary", {})
        speeches = summary.get("detailed_speeches", [])
        conclusion = summary.get("conclusion", "")
        avg_feasibility = summary.get("average_feasibility", 0)
        
        # 保存发言记录
        self.update_meeting(
            project_id, 
            meeting["id"],
            speeches=speeches,
            summary={
                "conclusion": conclusion,
                "feasibility": avg_feasibility,
                "participants": ["CEO", "CFO", "CTO", "COO", "CHRO"]
            },
            decisions=[{"type": "feasibility", "value": avg_feasibility}],
            status="completed"
        )
        
        # 根据可行性评分更新项目状态
        if avg_feasibility >= 0.75:
            project_status = ProjectStatus.ACTIVE.value
            # 自动创建里程碑
            milestones = self._generate_default_milestones(project_id, project["name"])
        else:
            project_status = ProjectStatus.PLANNING.value
            milestones = []
        
        self.update_project(
            project_id,
            status=project_status,
            kickoff_meeting_id=meeting["id"],
            milestones=milestones
        )
        
        return {
            "meeting": self.get_meeting(project_id, meeting["id"]),
            "project_status": project_status,
            "milestones": milestones,
            "feasibility_score": avg_feasibility
        }
    
    def _generate_default_milestones(self, project_id: str, project_name: str) -> List[Dict]:
        """生成默认里程碑"""
        milestones = [
            {
                "id": f"ms_{uuid.uuid4().hex[:6]}",
                "name": "Phase 1: 规划与设计",
                "description": "完成项目规划和系统设计",
                "due_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
                "status": "pending",
                "tasks": []
            },
            {
                "id": f"ms_{uuid.uuid4().hex[:6]}",
                "name": "Phase 2: 开发与实现",
                "description": "完成核心功能开发",
                "due_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
                "status": "pending",
                "tasks": []
            },
            {
                "id": f"ms_{uuid.uuid4().hex[:6]}",
                "name": "Phase 3: 测试与上线",
                "description": "完成测试并上线",
                "due_date": (datetime.now() + timedelta(days=45)).strftime("%Y-%m-%d"),
                "status": "pending",
                "tasks": []
            }
        ]
        
        # 保存里程碑
        project_path = self._get_project_path(project_id)
        milestones_file = os.path.join(project_path, "milestones.json")
        with open(milestones_file, 'w', encoding='utf-8') as f:
            json.dump(milestones, f, ensure_ascii=False, indent=2)
        
        return milestones
    
    # ============== 项目执行 - 任务管理 ==============
    
    def create_task(self, project_id: str, name: str, description: str = "",
                    assignee_id: str = "", priority: str = "medium",
                    due_date: str = None, milestone_id: str = None) -> Dict:
        """
        创建项目任务
        
        Args:
            project_id: 项目ID
            name: 任务名称
            description: 任务描述
            assignee_id: 负责人ID
            priority: 优先级 (low/medium/high/urgent)
            due_date: 截止日期
            milestone_id: 所属里程碑
        
        Returns:
            任务信息
        """
        project = self._projects_cache.get(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        
        task_data = {
            "id": task_id,
            "name": name,
            "description": description,
            "assignee_id": assignee_id,
            "priority": priority,
            "due_date": due_date,
            "milestone_id": milestone_id,
            "status": "pending",  # pending/in_progress/review/completed/failed
            "progress": 0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "started_at": None,
            "completed_at": None,
            "logs": [],
            "result": None,
        }
        
        # 保存任务
        task_file = os.path.join(
            self._get_project_path(project_id),
            "tasks",
            f"{task_id}.json"
        )
        with open(task_file, 'w', encoding='utf-8') as f:
            json.dump(task_data, f, ensure_ascii=False, indent=2)
        
        # 更新项目任务列表
        project.setdefault("tasks", []).append(task_id)
        self._save_project(project_id, project)
        
        # 如果有关联的里程碑，更新里程碑
        if milestone_id:
            self._add_task_to_milestone(project_id, milestone_id, task_id)
        
        return task_data
    
    def get_task(self, project_id: str, task_id: str) -> Optional[Dict]:
        """获取任务信息"""
        task_file = os.path.join(
            self._get_project_path(project_id),
            "tasks",
            f"{task_id}.json"
        )
        
        if not os.path.exists(task_file):
            return None
        
        with open(task_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def update_task(self, project_id: str, task_id: str, **kwargs) -> bool:
        """更新任务信息"""
        task = self.get_task(project_id, task_id)
        if not task:
            return False
        
        allowed_fields = ["name", "description", "assignee_id", "priority",
                         "due_date", "milestone_id", "status", "progress",
                         "started_at", "completed_at", "logs", "result"]
        
        for key, value in kwargs.items():
            if key in allowed_fields:
                task[key] = value
        
        task["updated_at"] = datetime.now().isoformat()
        
        # 自动记录状态变更时间
        if kwargs.get("status") == "in_progress" and not task.get("started_at"):
            task["started_at"] = datetime.now().isoformat()
        if kwargs.get("status") == "completed" and not task.get("completed_at"):
            task["completed_at"] = datetime.now().isoformat()
        
        task_file = os.path.join(
            self._get_project_path(project_id),
            "tasks",
            f"{task_id}.json"
        )
        
        with open(task_file, 'w', encoding='utf-8') as f:
            json.dump(task, f, ensure_ascii=False, indent=2)
        
        # 更新项目进度
        self._update_project_progress(project_id)
        
        return True
    
    def list_tasks(self, project_id: str, status: str = None, 
                   assignee_id: str = None) -> List[Dict]:
        """列出项目的所有任务"""
        project = self._projects_cache.get(project_id)
        if not project:
            return []
        
        tasks = []
        project_path = self._get_project_path(project_id)
        tasks_dir = os.path.join(project_path, "tasks")
        
        if not os.path.exists(tasks_dir):
            return []
        
        for task_file in os.listdir(tasks_dir):
            if task_file.endswith(".json"):
                with open(os.path.join(tasks_dir, task_file), 'r', encoding='utf-8') as f:
                    task = json.load(f)
                    # 过滤条件
                    if status and task.get("status") != status:
                        continue
                    if assignee_id and task.get("assignee_id") != assignee_id:
                        continue
                    tasks.append(task)
        
        # 按优先级和创建时间排序
        priority_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
        tasks.sort(key=lambda t: (priority_order.get(t.get("priority"), 3), t.get("created_at", "")))
        
        return tasks
    
    def _add_task_to_milestone(self, project_id: str, milestone_id: str, task_id: str):
        """将任务添加到里程碑"""
        project_path = self._get_project_path(project_id)
        milestones_file = os.path.join(project_path, "milestones.json")
        
        if not os.path.exists(milestones_file):
            return
        
        with open(milestones_file, 'r', encoding='utf-8') as f:
            milestones = json.load(f)
        
        for ms in milestones:
            if ms.get("id") == milestone_id:
                ms.setdefault("tasks", []).append(task_id)
                break
        
        with open(milestones_file, 'w', encoding='utf-8') as f:
            json.dump(milestones, f, ensure_ascii=False, indent=2)
    
    def _update_project_progress(self, project_id: str):
        """更新项目进度"""
        tasks = self.list_tasks(project_id)
        
        if not tasks:
            return
        
        completed = len([t for t in tasks if t.get("status") == "completed"])
        total = len(tasks)
        
        progress = int((completed / total) * 100) if total > 0 else 0
        
        self.update_project(project_id, progress=progress)
    
    def get_milestones(self, project_id: str) -> List[Dict]:
        """获取项目里程碑"""
        project_path = self._get_project_path(project_id)
        milestones_file = os.path.join(project_path, "milestones.json")
        
        if not os.path.exists(milestones_file):
            return []
        
        with open(milestones_file, 'r', encoding='utf-8') as f:
            milestones = json.load(f)
        
        # 填充里程碑的任务详情
        for ms in milestones:
            ms_tasks = []
            for task_id in ms.get("tasks", []):
                task = self.get_task(project_id, task_id)
                if task:
                    ms_tasks.append(task)
            ms["task_details"] = ms_tasks
            
            # 计算里程碑进度
            if ms_tasks:
                completed = len([t for t in ms_tasks if t.get("status") == "completed"])
                ms["progress"] = int((completed / len(ms_tasks)) * 100)
            else:
                ms["progress"] = 0
        
        return milestones
    
    # ============== 复盘总结 ==============
    
    def create_retrospective(self, project_id: str, title: str,
                             host: str, participants: List[str] = None,
                             what_went_well: List[str] = None,
                             what_could_improve: List[str] = None,
                             lessons_learned: List[str] = None) -> Dict:
        """
        创建项目复盘会议
        
        Args:
            project_id: 项目ID
            title: 复盘会议标题
            host: 主持人
            participants: 参会人
            what_went_well: 做得好的一面
            what_could_improve: 需要改进的
            lessons_learned: 经验教训
        
        Returns:
            复盘会议信息
        """
        meeting = self.create_meeting(
            project_id=project_id,
            meeting_type=MeetingType.RETROSPECTIVE.value,
            title=title,
            host=host,
            participants=participants or []
        )
        
        retrospective_data = {
            "what_went_well": what_went_well or [],
            "what_could_improve": what_could_improve or [],
            "lessons_learned": lessons_learned or [],
            "action_items": [],
        }
        
        self.update_meeting(
            project_id,
            meeting["id"],
            summary=retrospective_data,
            status="completed"
        )
        
        # 保存经验教训到知识库
        self._save_lessons_to_knowledge(project_id, lessons_learned or [])
        
        return retrospective_data
    
    def _save_lessons_to_knowledge(self, project_id: str, lessons: List[str]):
        """保存经验教训到知识库"""
        project = self._projects_cache.get(project_id)
        if not project:
            return
        
        lesson_entry = {
            "id": f"lesson_{uuid.uuid4().hex[:6]}",
            "project_id": project_id,
            "project_name": project.get("name"),
            "lessons": lessons,
            "created_at": datetime.now().isoformat(),
        }
        
        # 保存到项目目录
        project_path = self._get_project_path(project_id)
        lessons_dir = os.path.join(project_path, "lessons")
        os.makedirs(lessons_dir, exist_ok=True)
        
        lesson_file = os.path.join(lessons_dir, f"{lesson_entry['id']}.json")
        with open(lesson_file, 'w', encoding='utf-8') as f:
            json.dump(lesson_entry, f, ensure_ascii=False, indent=2)
        
        # 保存到全局知识库
        knowledge_lesson_file = os.path.join(
            KNOWLEDGE_PATH, 
            "lessons", 
            f"{lesson_entry['id']}.json"
        )
        with open(knowledge_lesson_file, 'w', encoding='utf-8') as f:
            json.dump(lesson_entry, f, ensure_ascii=False, indent=2)
        
        # 更新项目的经验教训列表
        project.setdefault("lessons", []).append(lesson_entry["id"])
        self._save_project(project_id, project)
    
    def complete_project(self, project_id: str, conclusion: str) -> Dict:
        """
        完成项目
        
        Args:
            project_id: 项目ID
            conclusion: 项目结论/总结
        
        Returns:
            完成状态
        """
        project = self._projects_cache.get(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        # 计算最终统计
        tasks = self.list_tasks(project_id)
        completed_tasks = len([t for t in tasks if t.get("status") == "completed"])
        total_tasks = len(tasks)
        
        meetings = self.list_meetings(project_id)
        
        # 生成项目总结
        summary = {
            "project_id": project_id,
            "project_name": project.get("name"),
            "conclusion": conclusion,
            "start_date": project.get("start_date"),
            "end_date": datetime.now().strftime("%Y-%m-%d"),
            "tasks_total": total_tasks,
            "tasks_completed": completed_tasks,
            "completion_rate": int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0,
            "meetings_count": len(meetings),
            "budget_used": project.get("budget", 0),
            "final_progress": 100,
            "created_at": datetime.now().isoformat(),
        }
        
        # 保存项目总结
        project_path = self._get_project_path(project_id)
        summary_file = os.path.join(project_path, "summary.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        # 保存到知识库
        knowledge_summary_file = os.path.join(
            KNOWLEDGE_PATH,
            "summaries",
            f"{project_id}_summary.json"
        )
        with open(knowledge_summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        # 更新项目状态
        self.update_project(
            project_id,
            status=ProjectStatus.COMPLETED.value,
            conclusion=conclusion,
            progress=100
        )
        
        return summary
    
    # ============== 知识库 ==============
    
    def get_knowledge_lessons(self, limit: int = 50) -> List[Dict]:
        """获取知识库中的所有经验教训"""
        lessons = []
        lessons_dir = os.path.join(KNOWLEDGE_PATH, "lessons")
        
        if not os.path.exists(lessons_dir):
            return []
        
        for lesson_file in os.listdir(lessons_dir):
            if lesson_file.endswith(".json"):
                with open(os.path.join(lessons_dir, lesson_file), 'r', encoding='utf-8') as f:
                    lessons.append(json.load(f))
        
        lessons.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return lessons[:limit]
    
    def get_knowledge_summaries(self, limit: int = 50) -> List[Dict]:
        """获取知识库中的所有项目总结"""
        summaries = []
        summaries_dir = os.path.join(KNOWLEDGE_PATH, "summaries")
        
        if not os.path.exists(summaries_dir):
            return []
        
        for summary_file in os.listdir(summaries_dir):
            if summary_file.endswith(".json"):
                with open(os.path.join(summaries_dir, summary_file), 'r', encoding='utf-8') as f:
                    summaries.append(json.load(f))
        
        summaries.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return summaries[:limit]
    
    def get_project_statistics(self) -> Dict:
        """获取项目统计信息"""
        all_projects = list(self._projects_cache.values())
        
        stats = {
            "total": len(all_projects),
            "planning": len([p for p in all_projects if p.get("status") == ProjectStatus.PLANNING.value]),
            "kickoff": len([p for p in all_projects if p.get("status") == ProjectStatus.KICKOFF.value]),
            "active": len([p for p in all_projects if p.get("status") == ProjectStatus.ACTIVE.value]),
            "review": len([p for p in all_projects if p.get("status") == ProjectStatus.REVIEW.value]),
            "completed": len([p for p in all_projects if p.get("status") == ProjectStatus.COMPLETED.value]),
            "archived": len([p for p in all_projects if p.get("status") == ProjectStatus.ARCHIVED.value]),
        }
        
        return stats


# 全局服务实例
_lifecycle_service = None


def get_lifecycle_service() -> ProjectLifecycleService:
    """获取项目生命周期服务实例"""
    global _lifecycle_service
    if _lifecycle_service is None:
        _lifecycle_service = ProjectLifecycleService()
    return _lifecycle_service
