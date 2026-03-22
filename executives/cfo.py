"""CFO executive advisor."""


def evaluate(intent_payload: dict) -> dict:
    """
    CFO财务评估 - 从财务角度评估业务可行性
    """
    business = intent_payload.get("business_name", "新业务")
    budget = int(intent_payload.get("budget_cap") or 0)
    deadline = intent_payload.get("deadline", "T+90d")
    
    # 当前财务状态评估
    current_status = {
        "business_name": business,
        "requested_budget": budget,
        "proposed_timeline": deadline,
        "roi_expectation": "正向" if budget < 300000 else "待验证",
        "cash_flow_impact": "可控" if budget < 500000 else "需关注"
    }
    
    # 财务问题识别
    problems = [
        "前期投入回收周期不确定",
        "现金流压力需持续监控",
        "预算超支风险存在"
    ]
    
    # 改进建议
    improvements = [
        f"建议分阶段拨付预算，首期拨付不超过{min(200000, budget)}元",
        "建立成本管控KPI，按月审计支出",
        "预留10%应急储备金"
    ]
    
    # 风险预警
    risk_warnings = [
        {"level": "高", "risk": "预算超支", "mitigation": "设置硬性预算上限，超支需重新审批"},
        {"level": "中", "risk": "ROI不达预期", "mitigation": "首期验证后立即评估，决定是否追加投资"},
        {"level": "低", "risk": "现金流断裂", "mitigation": "保持3个月运营现金储备"}
    ]
    
    return {
        "role": "CFO",
        "feasibility": 0.72,
        "current_status": current_status,
        "problems": problems,
        "improvements": improvements,
        "risk_warnings": risk_warnings,
        "recommendations": improvements
    }
