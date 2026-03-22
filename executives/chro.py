"""CHRO executive advisor."""


def evaluate(intent_payload: dict) -> dict:
    """
    CHRO人力资源评估 - 从人才与组织角度评估项目团队能力
    """
    business = intent_payload.get("business_name", "新业务")
    budget = int(intent_payload.get("budget_cap") or 0)
    
    # 当前人才状态评估
    current_status = {
        "business_name": business,
        "team_readiness": "中",
        "key_roles_availability": "部分到位",
        "training_needs": "需要",
        "culture_fit": "良好"
    }
    
    # 人才问题识别
    problems = [
        "关键岗位招聘周期不确定",
        "现有团队可能面临工作负荷增加",
        "新人培训与融入需要时间"
    ]
    
    # 改进建议
    improvements = [
        f"先确定{business}岗位编制，再分批招聘",
        "核心岗位优先内部调配，减少外招风险",
        "建立导师制度，加速新人成长"
    ]
    
    # 风险预警
    risk_warnings = [
        {"level": "高", "risk": "核心人员招聘困难", "mitigation": "提前启动招聘，建立人才储备池"},
        {"level": "中", "risk": "团队过度疲劳", "mitigation": "合理分配任务，避免一人多项目"},
        {"level": "低", "risk": "人员流动", "mitigation": "完善激励机制，定期沟通了解诉求"}
    ]
    
    return {
        "role": "CHRO",
        "feasibility": 0.74,
        "current_status": current_status,
        "problems": problems,
        "improvements": improvements,
        "risk_warnings": risk_warnings,
        "recommendations": improvements
    }
