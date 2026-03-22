"""Intent parser for chairman natural-language commands - 增强版
包含意图解析、AI专家匹配、智能招募功能
"""

import re
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Tuple


DEFAULT_BUDGET = 200000


# ============== AI专家模板库 ==============

class AIExpertRegistry:
    """AI专家注册表 - 预定义的专家类型和技能映射"""
    
    # 专家模板定义
    EXPERTS = {
        # 核心管理层
        "市场专家": {
            "skills": ["市场分析", "用户调研", "竞品分析"],
            "role": "market",
            "keywords": ["市场", "营销", "推广", "获客", "客户", "品牌"]
        },
        "财务顾问": {
            "skills": ["财务分析", "风险评估", "投资规划"],
            "role": "finance",
            "keywords": ["赚钱", "盈利", "财务", "投资", "股票", "理财", "收益"]
        },
        "技术专家": {
            "skills": ["编程", "架构设计", "技术方案"],
            "role": "tech",
            "keywords": ["写代码", "编程", "开发", "技术", "系统", "软件", "网站", "APP"]
        },
        "运营官": {
            "skills": ["项目管理", "数据分析", "流程优化"],
            "role": "operations",
            "keywords": ["运营", "管理", "效率", "优化", "流程"]
        },
        "战略官": {
            "skills": ["战略规划", "商业分析", "行业洞察"],
            "role": "strategy",
            "keywords": ["战略", "规划", "商业模式", "商业", "方向", "决策"]
        },
        "内容专家": {
            "skills": ["内容创作", "文案写作", "创意策划"],
            "role": "content",
            "keywords": ["内容", "文案", "写作", "创作", "文章", "文案"]
        },
        
        # 垂直领域专家
        "小红书运营": {
            "skills": ["小红书运营", "种草文案", "社交媒体营销"],
            "role": "xiaohongshu",
            "keywords": ["小红书", "种草", "博主", "自媒体"]
        },
        "抖音运营": {
            "skills": ["短视频运营", "抖音拍摄", "直播带货"],
            "role": "douyin",
            "keywords": ["抖音", "短视频", "直播", "带货", "视频"]
        },
        "短视频运营": {
            "skills": ["短视频策划", "编导", "视频剪辑", "内容创作"],
            "role": "short_video",
            "keywords": ["短视频", "做视频", "拍视频", "剪辑"]
        },
        "金融分析师": {
            "skills": ["股票分析", "行业研究", "财务报表分析"],
            "role": "financial_analyst",
            "keywords": ["股票", "分析股票", "股市", "金融", "K线", "行情"]
        },
        "数据专家": {
            "skills": ["数据分析", "数据挖掘", "可视化"],
            "role": "data",
            "keywords": ["数据分析", "数据", "统计", "报表"]
        },
        "程序员": {
            "skills": ["Python", "JavaScript", "Web开发", "API开发"],
            "role": "programmer",
            "keywords": ["程序员", "码农", "写程序", "代码"]
        },
        "电商运营": {
            "skills": ["电商运营", "店铺管理", "商品推广"],
            "role": "ecommerce",
            "keywords": ["电商", "淘宝", "京东", "拼多多", "开店", "店铺"]
        },
        "产品经理": {
            "skills": ["产品设计", "需求分析", "产品规划"],
            "role": "product",
            "keywords": ["产品", "产品设计", "需求", "功能"]
        },
        "设计师": {
            "skills": ["UI设计", "平面设计", "品牌设计"],
            "role": "design",
            "keywords": ["设计", "logo", "海报", "UI", "美工"]
        },
        "客服专家": {
            "skills": ["客户服务", "沟通技巧", "问题解决"],
            "role": "customer_service",
            "keywords": ["客服", "售后", "服务", "解答"]
        },
        "HR专家": {
            "skills": ["招聘", "员工关系", "培训"],
            "role": "hr",
            "keywords": ["招聘", "人力", "员工", "HR"]
        },
        "法务专家": {
            "skills": ["合同审核", "法律咨询", "合规审查"],
            "role": "legal",
            "keywords": ["法律", "合同", "合规", "法务"]
        }
    }
    
    @classmethod
    def get_all_experts(cls) -> Dict:
        """获取所有专家模板"""
        return cls.EXPERTS
    
    @classmethod
    def get_expert_by_name(cls, name: str) -> Optional[Dict]:
        """根据名称获取专家模板"""
        return cls.EXPERTS.get(name)
    
    @classmethod
    def find_matching_experts(cls, text: str) -> List[Tuple[str, float]]:
        """
        根据文本查找匹配的专家
        
        Args:
            text: 用户需求文本
        
        Returns:
            List of (expert_name, confidence_score) sorted by score descending
        """
        text = text.lower()
        matches = []
        
        for expert_name, config in cls.EXPERTS.items():
            score = 0
            keywords = config.get("keywords", [])
            
            # 精确匹配关键词
            for kw in keywords:
                if kw in text:
                    score += 1.0
                    # 完整匹配比部分匹配得分更高
                    if kw == text or text.startswith(kw) or text.endswith(kw):
                        score += 0.5
            
            if score > 0:
                matches.append((expert_name, score))
        
        # 按分数降序排序
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches
    
    @classmethod
    def recommend_experts(cls, text: str, top_k: int = 3) -> List[Dict]:
        """
        推荐最合适的专家
        
        Args:
            text: 用户需求文本
            top_k: 返回前K个最匹配的专家
        
        Returns:
            推荐的专家列表（包含专家信息和匹配分数）
        """
        matches = cls.find_matching_experts(text)
        
        results = []
        for expert_name, score in matches[:top_k]:
            expert_config = cls.EXPERTS[expert_name]
            results.append({
                "name": expert_name,
                "skills": expert_config["skills"],
                "role": expert_config["role"],
                "confidence": min(score / 3.0, 1.0),  # 归一化到0-1
                "matched_keywords": [kw for kw in expert_config.get("keywords", []) if kw in text.lower()]
            })
        
        return results


# ============== 智能招募器 ==============

class SmartRecruiter:
    """智能招募器 - 根据需求自动招募AI员工"""
    
    def __init__(self, company=None):
        self.company = company
        self.expert_registry = AIExpertRegistry()
    
    def parse_and_recruit(self, user_request: str, company=None) -> Dict:
        """
        解析用户需求并自动招募合适的AI员工
        
        Args:
            user_request: 用户需求描述
            company: 公司实例（可选）
        
        Returns:
            招募结果字典
        """
        # 解析意图
        intent_result = parse_chairman_command(user_request)
        
        # 推荐专家
        recommended_experts = self.expert_registry.recommend_experts(user_request, top_k=3)
        
        # 如果传入了公司实例，则自动招募
        recruited = []
        if company:
            for expert in recommended_experts:
                emp = self._recruit_expert(company, expert)
                if emp:
                    recruited.append({
                        "name": emp.name,
                        "role": emp.role,
                        "skills": emp.skills,
                        "status": "success"
                    })
        
        return {
            "user_request": user_request,
            "parsed_intent": intent_result,
            "recommended_experts": recommended_experts,
            "recruited_employees": recruited,
            "recruitment_needed": len(recommended_experts) > 0,
            "action_summary": f"已识别需求，建议招募 {len(recommended_experts)} 位专家" if recommended_experts else "未识别到特定专家需求"
        }
    
    def _recruit_expert(self, company, expert_info: Dict):
        """招募单个专家"""
        try:
            # 生成员工名称
            name = f"AI{expert_info['name']}"
            
            # 查找或创建部门
            department_id = self._get_or_create_department(company, expert_info['role'])
            
            # 雇佣员工
            emp = company.hire_employee(
                name=name,
                role=expert_info['role'],
                department_id=department_id,
                skills=expert_info['skills'],
                salary=0,  # AI员工无薪资
                create_openclaw_agent=True
            )
            return emp
        except Exception as e:
            print(f"Recruitment failed: {e}")
            return None
    
    def _get_or_create_department(self, company, role: str) -> str:
        """获取或创建部门"""
        # 简单映射角色到部门
        role_dept_map = {
            "market": "市场部",
            "finance": "财务部", 
            "tech": "研发部",
            "operations": "运营部",
            "strategy": "总经办",
            "content": "市场部",
            "xiaohongshu": "市场部",
            "douyin": "市场部",
            "short_video": "市场部",
            "financial_analyst": "财务部",
            "data": "研发部",
            "programmer": "研发部",
            "ecommerce": "运营部",
            "product": "研发部",
            "design": "研发部",
            "customer_service": "运营部",
            "hr": "总经办",
            "legal": "总经办"
        }
        
        dept_name = role_dept_map.get(role, "运营部")
        
        # 查找部门
        for dept in company.departments:
            if dept.name == dept_name:
                return dept.id
        
        # 创建部门
        dept = company.add_department(dept_name, f"{dept_name}部门")
        return dept.id


# ============== 原有解析功能 =============

def _extract_budget(text: str) -> int:
    """Extract budget cap from Chinese command text, supports 万/亿/元."""
    patterns = [
        (r"预算(?:上限|不超过|控制在)?\s*(\d+(?:\.\d+)?)\s*亿", 100000000),
        (r"预算(?:上限|不超过|控制在)?\s*(\d+(?:\.\d+)?)\s*万", 10000),
        (r"预算(?:上限|不超过|控制在)?\s*(\d+(?:\.\d+)?)\s*元", 1),
        (r"(\d+(?:\.\d+)?)\s*亿\s*预算", 100000000),
        (r"(\d+(?:\.\d+)?)\s*万\s*预算", 10000),
        (r"(\d+(?:\.\d+)?)\s*元\s*预算", 1),
    ]

    for pattern, unit in patterns:
        m = re.search(pattern, text)
        if m:
            value = float(m.group(1))
            return int(value * unit)

    # 兜底：只有"预算 500000"这类纯数字
    m_plain = re.search(r"预算(?:上限|不超过|控制在)?\s*(\d+)", text)
    if m_plain:
        return int(m_plain.group(1))

    return DEFAULT_BUDGET


def _extract_deadline(text: str) -> str:
    now = datetime.now()

    # Q格式
    m_q = re.search(r"(20\d{2})\s*[Qq]\s*([1-4])", text)
    if m_q:
        return f"{m_q.group(1)}-Q{m_q.group(2)}"

    # 中文季度表达
    if "本季度" in text or "季度内" in text:
        return f"{now.year}-Q{((now.month - 1) // 3) + 1}"
    if "下季度" in text:
        q = ((now.month - 1) // 3) + 1
        if q == 4:
            return f"{now.year + 1}-Q1"
        return f"{now.year}-Q{q + 1}"

    # 月
    if "本月" in text:
        return now.strftime("%Y-%m")
    if "下月" in text:
        year = now.year + 1 if now.month == 12 else now.year
        month = 1 if now.month == 12 else now.month + 1
        return f"{year}-{month:02d}"

    # 天数
    m_days = re.search(r"(\d+)\s*天内", text)
    if m_days:
        return f"T+{int(m_days.group(1))}d"

    return "T+90d"


def _extract_priority(text: str) -> str:
    if any(k in text for k in ["紧急", "立即", "马上", "最高优先级"]):
        return "high"
    if any(k in text for k in ["普通", "常规"]):
        return "medium"
    return "medium"


def parse_chairman_command(text: str) -> dict:
    """Parse chairman command to structured intent."""
    text = (text or "").strip()

    if not text:
        return {
            "intent": "unknown",
            "raw_text": text,
            "errors": ["empty_command"],
        }

    intent = "launch_new_business"
    if any(k in text for k in ["周报", "汇报", "复盘"]):
        intent = "weekly_review"
    
    # 新增：识别招聘意图
    if any(k in text for k in ["招聘", "招募", "雇人", "招人", "添加员工"]):
        intent = "recruit_employee"
    
    # 新增：识别专家需求
    if any(k in text for k in ["需要", "想要", "找个", "请个", "招募"]):
        # 检查是否有具体的专家类型关键词
        registry = AIExpertRegistry()
        matches = registry.find_matching_experts(text)
        if matches:
            intent = "need_expert"

    business_name = "新业务"
    business_patterns = [
        r"做([\u4e00-\u9fa5A-Za-z0-9\-]+)",
        r"落地([\u4e00-\u9fa5A-Za-z0-9\-]+)",
        r"启动([\u4e00-\u9fa5A-Za-z0-9\-]+)",
    ]
    for p in business_patterns:
        m = re.search(p, text)
        if m:
            business_name = m.group(1)
            break
    
    # 识别需要的专家类型
    recommended_experts = []
    if intent in ["need_expert", "launch_new_business"]:
        registry = AIExpertRegistry()
        recommended_experts = registry.recommend_experts(text, top_k=3)

    return {
        "intent": intent,
        "raw_text": text,
        "business_name": business_name,
        "budget_cap": _extract_budget(text),
        "deadline": _extract_deadline(text),
        "priority": _extract_priority(text),
        "constraints": [],
        "requires_approval": True,
        "recommended_experts": recommended_experts,
    }


# ============== 测试函数 ==============

def test_intent_parser():
    """测试意图解析功能"""
    print("=" * 60)
    print("意图解析模块测试")
    print("=" * 60)
    
    test_cases = [
        "我想赚钱",
        "做小红书创业",
        "写代码",
        "分析股票",
        "做短视频",
        "帮我做个电商网站",
        "需要招聘一个财务顾问",
        "帮我分析一下市场情况",
        "做一个抖音账号运营",
    ]
    
    registry = AIExpertRegistry()
    
    for text in test_cases:
        print(f"\n==> Input: {text}")
        print("-" * 40)
        
        # 解析意图
        result = parse_chairman_command(text)
        print(f"  Intent: {result['intent']}")
        print(f"  Business: {result['business_name']}")
        
        # 推荐专家
        experts = registry.recommend_experts(text)
        print(f"  Recommended Experts:")
        for exp in experts:
            print(f"    - {exp['name']}: {exp['skills']} (confidence: {exp['confidence']:.1%})")
            if exp.get('matched_keywords'):
                print(f"      Keywords: {exp['matched_keywords']}")


def test_smart_recruiter():
    """测试智能招募功能"""
    print("\n" + "=" * 60)
    print("Smart Recruitment Test")
    print("=" * 60)
    
    # 只测试解析功能，不实际创建员工
    registry = AIExpertRegistry()
    
    test_requests = [
        "我想做小红书创业",
        "需要写代码开发网站", 
        "想分析股票赚钱"
    ]
    
    for req in test_requests:
        print(f"\n==> Request: {req}")
        print("-" * 40)
        
        # 使用解析功能
        result = parse_chairman_command(req)
        
        print(f"  Intent: {result['intent']}")
        print(f"  Business: {result['business_name']}")
        print(f"  Recommended Experts:")
        for exp in result.get('recommended_experts', []):
            print(f"    - {exp['name']}: {exp['skills']} (confidence: {exp['confidence']:.1%})")
        
        # 模拟招募（不实际创建）
        print(f"  Would recruit: {len(result.get('recommended_experts', []))} experts")


if __name__ == "__main__":
    # 运行测试
    test_intent_parser()
    test_smart_recruiter()
