"""
市场竞争模拟模块 - 市场数据采集、竞争对手分析、市场份额模拟
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional, Dict
import uuid
import json
import os
import random

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "storage")


# ============== 市场数据 ==============

@dataclass
class MarketData:
    """市场数据"""
    id: str
    market_name: str
    industry: str
    total_market_size: float  # 总市场规模
    growth_rate: float  # 增长率
    current_period: str  # 当前周期
    data: dict = field(default_factory=dict)
    collected_at: str = ""
    
    def __post_init__(self):
        if not self.collected_at:
            self.collected_at = datetime.now().isoformat()
    
    def to_dict(self):
        return asdict(self)
    
    @staticmethod
    def from_dict(d):
        return MarketData(**d)


# ============== 竞争对手 ==============

@dataclass
class Competitor:
    """竞争对手"""
    id: str
    name: str
    industry: str
    market_share: float  # 市场份额 %
    revenue: float  # 收入
    strength_score: float = 50  # 实力评分 0-100
    weakness: List[str] = field(default_factory=list)
    threat_level: str = "medium"  # low, medium, high
    description: str = ""
    last_updated: str = ""
    
    def __post_init__(self):
        if not self.last_updated:
            self.last_updated = datetime.now().isoformat()
    
    def to_dict(self):
        return asdict(self)
    
    @staticmethod
    def from_dict(d):
        return Competitor(**d)


# ============== 市场份额 ==============

@dataclass
class MarketShare:
    """市场份额记录"""
    id: str
    market_name: str
    company_name: str
    period: str
    share: float  # 份额 %
    revenue: float
    rank: int = 0
    trend: str = "stable"  # growing, stable, declining
    recorded_at: str = ""
    
    def __post_init__(self):
        if not self.recorded_at:
            self.recorded_at = datetime.now().isoformat()
    
    def to_dict(self):
        return asdict(self)
    
    @staticmethod
    def from_dict(d):
        return MarketShare(**d)


# ============== 市场情报报告 ==============

@dataclass
class MarketReport:
    """市场情报报告"""
    id: str
    title: str
    market_name: str
    period: str
    summary: str = ""
    opportunities: List[str] = field(default_factory=list)
    threats: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    data: dict = field(default_factory=dict)
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self):
        return asdict(self)
    
    @staticmethod
    def from_dict(d):
        return MarketReport(**d)


# ============== 市场服务类 ==============

class MarketService:
    """市场服务"""
    
    def __init__(self):
        self.market_data: List[MarketData] = []
        self.competitors: List[Competitor] = []
        self.market_shares: List[MarketShare] = []
        self.reports: List[MarketReport] = []
        
        # 模拟的行业数据
        self.industries = {
            "tech": {"name": "科技", "base_growth": 0.15, "volatility": 0.1},
            "retail": {"name": "零售", "base_growth": 0.05, "volatility": 0.05},
            "finance": {"name": "金融", "base_growth": 0.08, "volatility": 0.08},
            "healthcare": {"name": "医疗", "base_growth": 0.12, "volatility": 0.06},
            "education": {"name": "教育", "base_growth": 0.10, "volatility": 0.07}
        }
        
        self.load()
    
    def _get_data_file(self, name: str) -> str:
        os.makedirs(DATA_DIR, exist_ok=True)
        return os.path.join(DATA_DIR, f"market_{name}.json")
    
    def save(self):
        """保存所有数据"""
        with open(self._get_data_file("data"), "w", encoding="utf-8") as f:
            json.dump([m.to_dict() for m in self.market_data], f, ensure_ascii=False, indent=2)
        with open(self._get_data_file("competitors"), "w", encoding="utf-8") as f:
            json.dump([c.to_dict() for c in self.competitors], f, ensure_ascii=False, indent=2)
        with open(self._get_data_file("shares"), "w", encoding="utf-8") as f:
            json.dump([s.to_dict() for s in self.market_shares], f, ensure_ascii=False, indent=2)
        with open(self._get_data_file("reports"), "w", encoding="utf-8") as f:
            json.dump([r.to_dict() for r in self.reports], f, ensure_ascii=False, indent=2)
    
    def load(self):
        """加载数据"""
        if os.path.exists(self._get_data_file("data")):
            with open(self._get_data_file("data"), "r", encoding="utf-8") as f:
                self.market_data = [MarketData.from_dict(m) for m in json.load(f)]
        if os.path.exists(self._get_data_file("competitors")):
            with open(self._get_data_file("competitors"), "r", encoding="utf-8") as f:
                self.competitors = [Competitor.from_dict(c) for c in json.load(f)]
        if os.path.exists(self._get_data_file("shares")):
            with open(self._get_data_file("shares"), "r", encoding="utf-8") as f:
                self.market_shares = [MarketShare.from_dict(s) for s in json.load(f)]
        if os.path.exists(self._get_data_file("reports")):
            with open(self._get_data_file("reports"), "r", encoding="utf-8") as f:
                self.reports = [MarketReport.from_dict(r) for r in json.load(f)]
    
    # ---------- 市场数据采集 ----------
    
    def collect_market_data(self, market_name: str, industry: str, 
                           total_market_size: float = 1000000) -> MarketData:
        """采集市场数据"""
        industry_info = self.industries.get(industry, self.industries["tech"])
        
        # 计算增长率（带随机波动）
        growth_rate = industry_info["base_growth"] + random.uniform(
            -industry_info["volatility"], 
            industry_info["volatility"]
        )
        
        data = MarketData(
            id=str(uuid.uuid4())[:8],
            market_name=market_name,
            industry=industry,
            total_market_size=total_market_size,
            growth_rate=growth_rate,
            current_period=datetime.now().strftime("%Y-%m"),
            data={
                "avg_deal_size": total_market_size * 0.001,
                "customer_count": int(total_market_size / 10000),
                "competition_intensity": random.uniform(0.3, 0.9),
                "market_trend": "growing" if growth_rate > 0 else "declining"
            }
        )
        self.market_data.append(data)
        self.save()
        return data
    
    def get_market_data(self, market_name: str = None) -> List[MarketData]:
        if market_name:
            return [m for m in self.market_data if m.market_name == market_name]
        return self.market_data
    
    def get_latest_market_data(self, market_name: str) -> Optional[MarketData]:
        """获取最新市场数据"""
        data = self.get_market_data(market_name)
        if data:
            return data[-1]
        return None
    
    # ---------- 竞争对手管理 ----------
    
    def add_competitor(self, name: str, industry: str, market_share: float,
                      revenue: float, strength_score: float = 50,
                      weakness: List[str] = None, threat_level: str = "medium",
                      description: str = "") -> Competitor:
        """添加竞争对手"""
        competitor = Competitor(
            id=str(uuid.uuid4())[:8],
            name=name,
            industry=industry,
            market_share=market_share,
            revenue=revenue,
            strength_score=strength_score,
            weakness=weakness or [],
            threat_level=threat_level,
            description=description
        )
        self.competitors.append(competitor)
        self.save()
        return competitor
    
    def get_competitor(self, competitor_id: str) -> Optional[Competitor]:
        for c in self.competitors:
            if c.id == competitor_id:
                return c
        return None
    
    def list_competitors(self, industry: str = None, 
                        min_threat: str = None) -> List[Competitor]:
        result = self.competitors
        if industry:
            result = [c for c in result if c.industry == industry]
        if min_threat:
            threat_levels = {"low": 0, "medium": 1, "high": 2}
            min_level = threat_levels.get(min_threat, 0)
            result = [c for c in result if threat_levels.get(c.threat_level, 0) >= min_level]
        return result
    
    def update_competitor(self, competitor_id: str, **kwargs) -> bool:
        """更新竞争对手信息"""
        for c in self.competitors:
            if c.id == competitor_id:
                for key, value in kwargs.items():
                    if hasattr(c, key):
                        setattr(c, key, value)
                c.last_updated = datetime.now().isoformat()
                self.save()
                return True
        return False
    
    def analyze_competitor_threats(self) -> dict:
        """分析竞争对手威胁"""
        threats = []
        for c in self.competitors:
            if c.threat_level == "high":
                threats.append({
                    "competitor": c.name,
                    "market_share": c.market_share,
                    "strength": c.strength_score,
                    "weakness": c.weakness[:2]
                })
        return {
            "high_threat_competitors": threats,
            "total_count": len(threats),
            "recommendation": "关注高威胁竞争对手动向" if threats else "暂无高威胁竞争对手"
        }
    
    # ---------- 市场份额模拟 ----------
    
    def update_market_share(self, market_name: str, company_name: str,
                           period: str, share: float, revenue: float) -> MarketShare:
        """更新市场份额"""
        # 获取历史排名
        existing = [s for s in self.market_shares if s.market_name == market_name and s.period == period]
        rank = len(existing) + 1
        
        # 计算趋势
        trend = "stable"
        prev_shares = [s for s in self.market_shares 
                      if s.market_name == market_name and s.company_name == company_name]
        if prev_shares:
            prev_share = prev_shares[-1].share
            if share > prev_share + 0.5:
                trend = "growing"
            elif share < prev_share - 0.5:
                trend = "declining"
        
        record = MarketShare(
            id=str(uuid.uuid4())[:8],
            market_name=market_name,
            company_name=company_name,
            period=period,
            share=share,
            revenue=revenue,
            rank=rank,
            trend=trend
        )
        self.market_shares.append(record)
        self.save()
        return record
    
    def get_market_shares(self, market_name: str = None, period: str = None) -> List[MarketShare]:
        result = self.market_shares
        if market_name:
            result = [s for s in result if s.market_name == market_name]
        if period:
            result = [s for s in result if s.period == period]
        return result
    
    def simulate_market_share_change(self, company_name: str, market_name: str,
                                     marketing_budget: float, product_quality: float) -> dict:
        """模拟市场份额变化"""
        # 获取当前市场份额
        current = [s for s in self.market_shares 
                  if s.market_name == market_name and s.company_name == company_name]
        current_share = current[-1].share if current else 10.0
        
        # 模拟逻辑
        # 营销预算正向影响（边际效益递减）
        marketing_effect = min(5, marketing_budget / 10000)
        
        # 产品质量正向影响
        quality_effect = (product_quality - 50) / 50 * 3  # ±3%
        
        # 竞争对手影响
        competitors = self.list_competitors(industry=market_name)
        competitor_threat = sum(c.market_share for c in competitors 
                               if c.threat_level in ["high", "medium"]) * 0.01
        
        # 计算变化
        change = marketing_effect + quality_effect - competitor_threat + random.uniform(-0.5, 0.5)
        new_share = max(1, min(50, current_share + change))
        
        # 模拟收入
        market_data = self.get_latest_market_data(market_name)
        market_size = market_data.total_market_size if market_data else 1000000
        simulated_revenue = market_size * new_share / 100
        
        return {
            "company": company_name,
            "market": market_name,
            "current_share": current_share,
            "predicted_share": round(new_share, 2),
            "change": round(change, 2),
            "predicted_revenue": round(simulated_revenue, 2),
            "confidence": 0.7,
            "factors": {
                "marketing_effect": round(marketing_effect, 2),
                "quality_effect": round(quality_effect, 2),
                "competitor_threat": round(competitor_threat, 2)
            }
        }
    
    # ---------- 市场报告 ----------
    
    def generate_market_report(self, market_name: str, period: str) -> MarketReport:
        """生成市场情报报告"""
        market_data = self.get_latest_market_data(market_name)
        competitors = self.list_competitors(industry=market_name)
        shares = self.get_market_shares(market_name=market_name, period=period)
        
        opportunities = []
        threats = []
        recommendations = []
        
        # 分析机会
        if market_data:
            if market_data.growth_rate > 0.1:
                opportunities.append("市场快速增长")
                recommendations.append("加大市场投入，抢占份额")
            if market_data.data.get("competition_intensity", 0) < 0.5:
                opportunities.append("竞争强度较低")
                recommendations.append("可考虑进入该市场")
        
        # 分析威胁
        high_threat = [c for c in competitors if c.threat_level == "high"]
        if high_threat:
            threats.append(f"主要竞争对手: {', '.join([c.name for c in high_threat])}")
            recommendations.append("关注竞争对手动态，制定应对策略")
        
        if not opportunities:
            opportunities.append("市场平稳")
        if not threats:
            threats.append("暂无明显威胁")
        
        report = MarketReport(
            id=str(uuid.uuid4())[:8],
            title=f"{market_name}市场情报报告 - {period}",
            market_name=market_name,
            period=period,
            summary=f"市场规模约{market_data.total_market_size if market_data else '未知'}，增长率{market_data.growth_rate if market_data else 0:.1%}" if market_data else "暂无数据",
            opportunities=opportunities,
            threats=threats,
            recommendations=recommendations,
            data={
                "competitor_count": len(competitors),
                "market_share_records": len(shares)
            }
        )
        self.reports.append(report)
        self.save()
        return report
    
    def get_reports(self, market_name: str = None) -> List[MarketReport]:
        if market_name:
            return [r for r in self.reports if r.market_name == market_name]
        return self.reports
    
    # ---------- 市场概览 ----------
    
    def get_market_overview(self, market_name: str) -> dict:
        """获取市场概览"""
        market_data = self.get_latest_market_data(market_name)
        competitors = self.list_competitors(industry=market_name)
        shares = self.get_market_shares(market_name=market_name)
        
        return {
            "market_name": market_name,
            "market_data": market_data.to_dict() if market_data else None,
            "competitors": {
                "total": len(competitors),
                "high_threat": len([c for c in competitors if c.threat_level == "high"]),
                "list": [c.to_dict() for c in competitors[:5]]
            },
            "market_shares": {
                "records": len(shares),
                "latest": shares[-1].to_dict() if shares else None
            }
        }


# 全局实例
_market_service: Optional[MarketService] = None


def get_market_service() -> MarketService:
    global _market_service
    if _market_service is None:
        _market_service = MarketService()
    return _market_service
