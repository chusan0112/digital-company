"""
员工满意度模块 - 满意度调查问卷、满意度分析引擎
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional, Dict
import uuid
import json
import os
import random

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "storage")


# ============== 满意度调查问卷 ==============

@dataclass
class Survey:
    """满意度调查问卷"""
    id: str
    title: str
    department_id: str
    status: str = "draft"  # draft, active, closed
    questions: List[dict] = field(default_factory=list)
    start_date: str = ""
    end_date: str = ""
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self):
        return asdict(self)
    
    @staticmethod
    def from_dict(d):
        return Survey(**d)


@dataclass
class SurveyResponse:
    """问卷响应"""
    id: str
    survey_id: str
    employee_id: str
    responses: dict = field(default_factory=dict)  # question_id -> score
    overall_score: float = 0
    comments: str = ""
    submitted_at: str = ""
    
    def __post_init__(self):
        if not self.submitted_at:
            self.submitted_at = datetime.now().isoformat()
        # 计算总分
        if self.responses:
            self.overall_score = sum(self.responses.values()) / len(self.responses)
    
    def to_dict(self):
        return asdict(self)
    
    @staticmethod
    def from_dict(d):
        return SurveyResponse(**d)


# ============== 满意度指标 ==============

@dataclass
class SatisfactionMetrics:
    """满意度指标"""
    id: str
    department_id: str
    survey_id: str = ""
    period: str = ""  # monthly, quarterly
    
    # 核心指标 (0-100)
    overall_score: float = 0
    work_environment: float = 0  # 工作环境
    compensation: float = 0  # 薪酬福利
    growth_opportunity: float = 0  # 成长机会
    management: float = 0  # 管理水平
    team_collaboration: float = 0  # 团队协作
    work_life_balance: float = 0  # 工作生活平衡
    
    # 附加指标
    response_rate: float = 0  # 响应率
    nps_score: float = 0  # NPS净推荐值
    
    calculated_at: str = ""
    
    def __post_init__(self):
        if not self.calculated_at:
            self.calculated_at = datetime.now().isoformat()
        # 计算综合得分
        scores = [self.work_environment, self.compensation, self.growth_opportunity,
                 self.management, self.team_collaboration, self.work_life_balance]
        valid_scores = [s for s in scores if s > 0]
        if valid_scores:
            self.overall_score = sum(valid_scores) / len(valid_scores)
    
    def to_dict(self):
        return asdict(self)
    
    @staticmethod
    def from_dict(d):
        return SatisfactionMetrics(**d)


# ============== 满意度建议 ==============

@dataclass
class SatisfactionInsight:
    """满意度洞察"""
    id: str
    department_id: str
    period: str
    
    strengths: List[str] = field(default_factory=list)  # 优势
    weaknesses: List[str] = field(default_factory=list)  # 待改进
    action_items: List[dict] = field(default_factory=list)  # 行动项
    
    trend: str = "stable"  # improving, stable, declining
    compared_to_last: float = 0  # 与上期相比变化
    
    generated_at: str = ""
    
    def __post_init__(self):
        if not self.generated_at:
            self.generated_at = datetime.now().isoformat()
    
    def to_dict(self):
        return asdict(self)
    
    @staticmethod
    def from_dict(d):
        return SatisfactionInsight(**d)


# ============== 预设问卷题目 ==============

DEFAULT_QUESTIONS = [
    {
        "id": "q1",
        "text": "我对目前的工作环境感到满意",
        "category": "work_environment",
        "weight": 1.0
    },
    {
        "id": "q2",
        "text": "我的薪酬待遇具有竞争力",
        "category": "compensation",
        "weight": 1.2
    },
    {
        "id": "q3",
        "text": "公司提供足够的成长和发展机会",
        "category": "growth_opportunity",
        "weight": 1.1
    },
    {
        "id": "q4",
        "text": "我的直属上司管理方式得当",
        "category": "management",
        "weight": 1.0
    },
    {
        "id": "q5",
        "text": "团队成员之间协作顺畅",
        "category": "team_collaboration",
        "weight": 1.0
    },
    {
        "id": "q6",
        "text": "我能够很好地平衡工作和生活",
        "category": "work_life_balance",
        "weight": 1.0
    },
    {
        "id": "q7",
        "text": "我愿意向朋友推荐来这家公司工作",
        "category": "nps",
        "weight": 1.3
    },
    {
        "id": "q8",
        "text": "我对公司的未来发展充满信心",
        "category": "overall",
        "weight": 1.1
    }
]


# ============== 满意度服务类 ==============

class SatisfactionService:
    """员工满意度服务"""
    
    def __init__(self):
        self.surveys: List[Survey] = []
        self.responses: List[SurveyResponse] = []
        self.metrics: List[SatisfactionMetrics] = []
        self.insights: List[SatisfactionInsight] = []
        
        self.load()
    
    def _get_data_file(self, name: str) -> str:
        os.makedirs(DATA_DIR, exist_ok=True)
        return os.path.join(DATA_DIR, f"satisfaction_{name}.json")
    
    def save(self):
        """保存所有数据"""
        with open(self._get_data_file("surveys"), "w", encoding="utf-8") as f:
            json.dump([s.to_dict() for s in self.surveys], f, ensure_ascii=False, indent=2)
        with open(self._get_data_file("responses"), "w", encoding="utf-8") as f:
            json.dump([r.to_dict() for r in self.responses], f, ensure_ascii=False, indent=2)
        with open(self._get_data_file("metrics"), "w", encoding="utf-8") as f:
            json.dump([m.to_dict() for m in self.metrics], f, ensure_ascii=False, indent=2)
        with open(self._get_data_file("insights"), "w", encoding="utf-8") as f:
            json.dump([i.to_dict() for i in self.insights], f, ensure_ascii=False, indent=2)
    
    def load(self):
        """加载数据"""
        if os.path.exists(self._get_data_file("surveys")):
            with open(self._get_data_file("surveys"), "r", encoding="utf-8") as f:
                self.surveys = [Survey.from_dict(s) for s in json.load(f)]
        if os.path.exists(self._get_data_file("responses")):
            with open(self._get_data_file("responses"), "r", encoding="utf-8") as f:
                self.responses = [SurveyResponse.from_dict(r) for r in json.load(f)]
        if os.path.exists(self._get_data_file("metrics")):
            with open(self._get_data_file("metrics"), "r", encoding="utf-8") as f:
                self.metrics = [SatisfactionMetrics.from_dict(m) for m in json.load(f)]
        if os.path.exists(self._get_data_file("insights")):
            with open(self._get_data_file("insights"), "r", encoding="utf-8") as f:
                self.insights = [SatisfactionInsight.from_dict(i) for i in json.load(f)]
    
    # ---------- 问卷管理 ----------
    
    def create_survey(self, title: str, department_id: str,
                      questions: List[dict] = None,
                      start_date: str = "", end_date: str = "") -> Survey:
        """创建满意度调查问卷"""
        survey = Survey(
            id=str(uuid.uuid4())[:8],
            title=title,
            department_id=department_id,
            questions=questions or DEFAULT_QUESTIONS,
            status="draft",
            start_date=start_date,
            end_date=end_date or datetime.now().strftime("%Y-%m-%d")
        )
        self.surveys.append(survey)
        self.save()
        return survey
    
    def activate_survey(self, survey_id: str) -> bool:
        """激活问卷"""
        for s in self.surveys:
            if s.id == survey_id:
                s.status = "active"
                s.start_date = datetime.now().strftime("%Y-%m-%d")
                self.save()
                return True
        return False
    
    def close_survey(self, survey_id: str) -> bool:
        """关闭问卷"""
        for s in self.surveys:
            if s.id == survey_id:
                s.status = "closed"
                s.end_date = datetime.now().strftime("%Y-%m-%d")
                self.save()
                return True
        return False
    
    def get_survey(self, survey_id: str) -> Optional[Survey]:
        for s in self.surveys:
            if s.id == survey_id:
                return s
        return None
    
    def list_surveys(self, department_id: str = None, status: str = None) -> List[Survey]:
        result = self.surveys
        if department_id:
            result = [s for s in result if s.department_id == department_id]
        if status:
            result = [s for s in result if s.status == status]
        return result
    
    # ---------- 问卷响应 ----------
    
    def submit_response(self, survey_id: str, employee_id: str,
                       responses: dict, comments: str = "") -> SurveyResponse:
        """提交问卷响应"""
        # 验证问卷状态
        survey = self.get_survey(survey_id)
        if not survey or survey.status != "active":
            raise ValueError("问卷未激活或不存在")
        
        # 验证题目
        valid_question_ids = {q["id"] for q in survey.questions}
        filtered_responses = {k: v for k, v in responses.items() if k in valid_question_ids}
        
        response = SurveyResponse(
            id=str(uuid.uuid4())[:8],
            survey_id=survey_id,
            employee_id=employee_id,
            responses=filtered_responses,
            comments=comments
        )
        self.responses.append(response)
        self.save()
        return response
    
    def get_responses(self, survey_id: str = None, 
                     employee_id: str = None) -> List[SurveyResponse]:
        result = self.responses
        if survey_id:
            result = [r for r in result if r.survey_id == survey_id]
        if employee_id:
            result = [r for r in result if r.employee_id == employee_id]
        return result
    
    # ---------- 满意度分析引擎 ----------
    
    def calculate_metrics(self, survey_id: str, department_id: str) -> SatisfactionMetrics:
        """计算满意度指标"""
        responses = self.get_responses(survey_id=survey_id)
        survey = self.get_survey(survey_id)
        
        if not responses:
            raise ValueError("暂无问卷响应")
        
        # 按类别汇总得分
        category_scores = {}
        question_weights = {}
        
        for q in survey.questions:
            cat = q.get("category", "overall")
            weight = q.get("weight", 1.0)
            question_weights[q["id"]] = weight
            if cat not in category_scores:
                category_scores[cat] = {"total": 0, "count": 0}
        
        # 计算各类别得分
        for response in responses:
            for q_id, score in response.responses.items():
                for q in survey.questions:
                    if q["id"] == q_id:
                        cat = q.get("category", "overall")
                        weight = q.get("weight", 1.0)
                        category_scores[cat]["total"] += score * weight
                        category_scores[cat]["count"] += weight
        
        # 计算加权平均
        metrics = SatisfactionMetrics(
            id=str(uuid.uuid4())[:8],
            department_id=department_id,
            survey_id=survey_id,
            period="monthly",
            work_environment=category_scores.get("work_environment", {}).get("total", 0) / 
                             max(1, category_scores.get("work_environment", {}).get("count", 1)),
            compensation=category_scores.get("compensation", {}).get("total", 0) /
                       max(1, category_scores.get("compensation", {}).get("count", 1)),
            growth_opportunity=category_scores.get("growth_opportunity", {}).get("total", 0) /
                               max(1, category_scores.get("growth_opportunity", {}).get("count", 1)),
            management=category_scores.get("management", {}).get("total", 0) /
                       max(1, category_scores.get("management", {}).get("count", 1)),
            team_collaboration=category_scores.get("team_collaboration", {}).get("total", 0) /
                              max(1, category_scores.get("team_collaboration", {}).get("count", 1)),
            work_life_balance=category_scores.get("work_life_balance", {}).get("total", 0) /
                            max(1, category_scores.get("work_life_balance", {}).get("count", 1)),
            response_rate=len(responses) / 10  # 假设10人部门
        )
        
        # 计算NPS
        nps_responses = [r.responses.get("q7", 0) for r in responses]
        if nps_responses:
            promoters = sum(1 for s in nps_responses if s >= 9)
            detractors = sum(1 for s in nps_responses if s <= 6)
            metrics.nps_score = (promoters - detractors) / len(nps_responses) * 100
        
        self.metrics.append(metrics)
        self.save()
        return metrics
    
    def generate_insights(self, department_id: str) -> SatisfactionInsight:
        """生成满意度洞察"""
        # 获取最新指标
        dept_metrics = [m for m in self.metrics if m.department_id == department_id]
        if not dept_metrics:
            raise ValueError("暂无满意度数据")
        
        current = dept_metrics[-1]
        previous = dept_metrics[-2] if len(dept_metrics) > 1 else None
        
        strengths = []
        weaknesses = []
        action_items = []
        
        # 分析各维度
        dimensions = [
            ("work_environment", "工作环境"),
            ("compensation", "薪酬福利"),
            ("growth_opportunity", "成长机会"),
            ("management", "管理水平"),
            ("team_collaboration", "团队协作"),
            ("work_life_balance", "工作生活平衡")
        ]
        
        for dim_id, dim_name in dimensions:
            score = getattr(current, dim_id, 0)
            if score >= 80:
                strengths.append(f"{dim_name}优秀 (得分: {score:.1f})")
            elif score < 60:
                weaknesses.append(f"{dim_name}需改进 (得分: {score:.1f})")
                action_items.append({
                    "dimension": dim_name,
                    "priority": "high" if score < 50 else "medium",
                    "suggestion": f"重点关注{dim_name}的改善"
                })
        
        # 计算趋势
        trend = "stable"
        compared_to_last = 0
        if previous:
            compared_to_last = current.overall_score - previous.overall_score
            if compared_to_last > 3:
                trend = "improving"
            elif compared_to_last < -3:
                trend = "declining"
        
        insight = SatisfactionInsight(
            id=str(uuid.uuid4())[:8],
            department_id=department_id,
            period=datetime.now().strftime("%Y-%m"),
            strengths=strengths,
            weaknesses=weaknesses,
            action_items=action_items,
            trend=trend,
            compared_to_last=round(compared_to_last, 2)
        )
        self.insights.append(insight)
        self.save()
        return insight
    
    def get_metrics_history(self, department_id: str = None) -> List[SatisfactionMetrics]:
        if department_id:
            return [m for m in self.metrics if m.department_id == department_id]
        return self.metrics
    
    def get_latest_metrics(self, department_id: str) -> Optional[SatisfactionMetrics]:
        dept_metrics = [m for m in self.metrics if m.department_id == department_id]
        return dept_metrics[-1] if dept_metrics else None
    
    # ---------- 模拟满意度数据 ----------
    
    def simulate_satisfaction_data(self, department_id: str, employee_count: int = 10) -> dict:
        """模拟满意度数据（用于测试）"""
        # 创建问卷
        survey = self.create_survey(
            title=f"{department_id}满意度调查",
            department_id=department_id
        )
        self.activate_survey(survey.id)
        
        # 模拟员工响应
        response_count = 0
        for i in range(employee_count):
            responses = {}
            for q in survey.questions:
                # 模拟评分 60-95 分
                responses[q["id"]] = random.randint(60, 95)
            
            self.submit_response(
                survey_id=survey.id,
                employee_id=f"emp_{i+1}",
                responses=responses,
                comments=f"员工{i+1}的反馈"
            )
            response_count += 1
        
        # 计算指标
        metrics = self.calculate_metrics(survey.id, department_id)
        
        # 生成洞察
        insight = self.generate_insights(department_id)
        
        self.close_survey(survey.id)
        
        return {
            "survey_id": survey.id,
            "response_count": response_count,
            "metrics": metrics.to_dict(),
            "insight": insight.to_dict()
        }
    
    # ---------- 满意度概览 ----------
    
    def get_satisfaction_overview(self, department_id: str = None) -> dict:
        """获取满意度概览"""
        if department_id:
            surveys = self.list_surveys(department_id=department_id)
            metrics = self.get_metrics_history(department_id=department_id)
            insights = [i for i in self.insights if i.department_id == department_id]
        else:
            surveys = self.list_surveys()
            metrics = self.metrics
            insights = self.insights
        
        latest_metrics = metrics[-1] if metrics else None
        
        return {
            "surveys": {
                "total": len(surveys),
                "active": len([s for s in surveys if s.status == "active"]),
                "closed": len([s for s in surveys if s.status == "closed"])
            },
            "latest_metrics": latest_metrics.to_dict() if latest_metrics else None,
            "latest_insight": insights[-1].to_dict() if insights else None,
            "response_rate": (latest_metrics.response_rate if latest_metrics else 0) * 100
        }


# 全局实例
_satisfaction_service: Optional[SatisfactionService] = None


def get_satisfaction_service() -> SatisfactionService:
    global _satisfaction_service
    if _satisfaction_service is None:
        _satisfaction_service = SatisfactionService()
    return _satisfaction_service
