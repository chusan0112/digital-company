"""CTO executive advisor."""


def evaluate(intent_payload: dict) -> dict:
    """
    CTO技术评估 - 从技术角度评估业务实现可行性
    """
    business = intent_payload.get("business_name", "新业务")
    budget = int(intent_payload.get("budget_cap") or 0)
    
    # 当前技术状态评估
    current_status = {
        "business_name": business,
        "tech_stack_requirement": "标准Web服务",
        "infrastructure_ready": True,
        "technical_complexity": "中" if budget < 300000 else "高",
        "team_capacity": "充足"
    }
    
    # 技术问题识别
    problems = [
        "关键技术能力尚需补齐",
        "系统架构扩展性待验证",
        "技术债务需关注"
    ]
    
    # 改进建议
    improvements = [
        f"先组建{business}技术小组，完成基础架构验证",
        "采用敏捷开发，2周一个迭代",
        "优先使用成熟开源方案，降低自研风险"
    ]
    
    # 风险预警
    risk_warnings = [
        {"level": "高", "risk": "技术选型失误", "mitigation": "POC验证后再大规模投入"},
        {"level": "中", "risk": "开发进度延期", "mitigation": "设置缓冲期，关键路径预留余量"},
        {"level": "低", "risk": "技术人才流失", "mitigation": "建立知识文档，代码集体所有权"}
    ]
    
    return {
        "role": "CTO",
        "feasibility": 0.76,
        "current_status": current_status,
        "problems": problems,
        "improvements": improvements,
        "risk_warnings": risk_warnings,
        "recommendations": improvements
    }
