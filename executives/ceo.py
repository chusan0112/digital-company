"""CEO executive advisor."""


def evaluate(intent_payload: dict) -> dict:
    """
    CEO战略评估 - 从全局视角评估业务立项
    """
    business = intent_payload.get("business_name", "新业务")
    budget = int(intent_payload.get("budget_cap") or 0)
    priority = intent_payload.get("priority", "medium")
    
    # 评估业务与公司战略的匹配度
    current_status = {
        "business_name": business,
        "proposed_budget": budget,
        "priority": priority,
        "strategic_alignment": "高" if budget < 500000 else "中",
        "market_timing": "有利" if priority == "high" else "一般"
    }
    
    # 识别关键问题
    problems = [
        "跨部门协同复杂度上升",
        "资源分配需权衡现有业务",
        "战略优先级需与董事会对齐"
    ]
    
    # 改进建议
    improvements = [
        f"建议以90天试点方式启动{business}",
        "建立双周review机制，及时调整策略",
        "明确各阶段退出标准"
    ]
    
    # 风险预警
    risk_warnings = [
        {"level": "中", "risk": "市场竞争加剧", "mitigation": "快速验证MVP，控制沉没成本"},
        {"level": "低", "risk": "执行偏差", "mitigation": "设立里程碑检查点"}
    ]
    
    return {
        "role": "CEO",
        "feasibility": 0.8,
        "current_status": current_status,
        "problems": problems,
        "improvements": improvements,
        "risk_warnings": risk_warnings,
        "recommendations": improvements
    }
