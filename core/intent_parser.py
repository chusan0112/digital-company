"""Intent parser for chairman natural-language commands."""

import re
from datetime import datetime


DEFAULT_BUDGET = 200000


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

    # 兜底：只有“预算 500000”这类纯数字
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

    return {
        "intent": intent,
        "raw_text": text,
        "business_name": business_name,
        "budget_cap": _extract_budget(text),
        "deadline": _extract_deadline(text),
        "priority": _extract_priority(text),
        "constraints": [],
        "requires_approval": True,
    }
