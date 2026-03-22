"""COO executive advisor."""


def evaluate(intent_payload: dict) -> dict:
    """
    COO运营评估 - 从运营执行角度评估项目落地能力
    """
    business = intent_payload.get("business_name", "新业务")
    deadline = intent_payload.get("deadline", "T+90d")
    budget = int(intent_payload.get("budget_cap") or 0)
    
    # 当前运营状态评估
    current_status = {
        "business_name": business,
        "target_deadline": deadline,
        "operational_readiness": "高",
        "resource_availability": "中",
        "process_maturity": "成熟"
    }
    
    # 运营问题识别
    problems = [
        "执行排期受资源调度影响",
        "多任务并行可能导致注意力分散",
        "跨部门协作流程待优化"
    ]
    
    # 改进建议
    improvements = [
        f"按双周里程碑推进，目标截止{deadline}",
        "设立专职项目经理，统一协调资源",
        "建立每日站会机制，快速暴露阻塞点"
    ]
    
    # 风险预警
    risk_warnings = [
        {"level": "高", "risk": "关键里程碑延期", "mitigation": "预留20%时间缓冲，建立预警机制"},
        {"level": "中", "risk": "资源冲突", "mitigation": "提前锁定资源，制定资源调配预案"},
        {"level": "低", "risk": "执行质量下降", "mitigation": "引入QA检查点，关键节点验收"}
    ]
    
    return {
        "role": "COO",
        "feasibility": 0.78,
        "current_status": current_status,
        "problems": problems,
        "improvements": improvements,
        "risk_warnings": risk_warnings,
        "recommendations": improvements
    }
