"""会议讨论系统 - 让AI员工根据角色发表观点并生成会议纪要"""

import uuid
from datetime import datetime
from typing import List, Dict, Optional

from executives.ceo import evaluate as ceo_evaluate
from executives.cfo import evaluate as cfo_evaluate
from executives.cto import evaluate as cto_evaluate
from executives.coo import evaluate as coo_evaluate
from executives.chro import evaluate as chro_evaluate


# 角色到评估函数的映射
ROLE_EVALUATORS = {
    "CEO": ceo_evaluate,
    "CFO": cfo_evaluate,
    "CTO": cto_evaluate,
    "COO": coo_evaluate,
    "CHRO": chro_evaluate,
}

# 角色发言风格定义
ROLE_SPEECH_STYLES = {
    "CEO": {
        "title": "战略官",
        "focus": "全局战略、长期规划、商业价值",
        "keywords": ["战略匹配", "竞争优势", "商业模式", "长期价值", "董事会"],
    },
    "CFO": {
        "title": "财务顾问",
        "focus": "成本收益、预算控制、ROI、现金流",
        "keywords": ["预算", "ROI", "成本", "收益", "现金流", "投资回报"],
    },
    "CTO": {
        "title": "技术专家",
        "focus": "技术可行性、系统架构、实现难度",
        "keywords": ["技术选型", "架构", "POC", "技术风险", "开发周期"],
    },
    "COO": {
        "title": "运营官",
        "focus": "执行计划、timeline、资源调度、运营效率",
        "keywords": ["里程碑", "排期", "资源", "运营", "执行", "流程"],
    },
    "CHRO": {
        "title": "人力资源官",
        "focus": "人才配置、团队能力、组织文化",
        "keywords": ["招聘", "团队", "人才", "培训", "组织", "文化"],
    },
}


class MeetingDiscussion:
    """会议讨论系统"""
    
    def __init__(self):
        self.meeting_id = None
        self.topic = None
        self.participants = []
        self.speeches = []
        self.current_speaker_index = 0
        self.start_time = None
        self.status = "initialized"  # initialized, in_progress, concluded
    
    def start_discussion(self, topic: str, participants: List[str] = None) -> Dict:
        """
        开始讨论
        
        Args:
            topic: 讨论议题
            participants: 参与者角色列表，默认全部参与者
        
        Returns:
            会议开始信息
        """
        self.meeting_id = str(uuid.uuid4())[:8]
        self.topic = topic
        self.start_time = datetime.now().isoformat()
        self.status = "in_progress"
        
        # 默认全部参与者
        if participants is None:
            participants = list(ROLE_EVALUATORS.keys())
        self.participants = participants
        self.current_speaker_index = 0
        
        return {
            "meeting_id": self.meeting_id,
            "topic": self.topic,
            "status": self.status,
            "start_time": self.start_time,
            "participants": self.participants,
            "message": f"会议 '{self.topic}' 开始！参与者: {', '.join(self.participants)}"
        }
    
    def get_next_speaker(self) -> Optional[Dict]:
        """
        确定下一个发言人
        
        Returns:
            下一个发言人的信息，如果没有则返回None
        """
        if self.current_speaker_index >= len(self.participants):
            return None
        
        role = self.participants[self.current_speaker_index]
        speech_style = ROLE_SPEECH_STYLES.get(role, {})
        
        return {
            "role": role,
            "title": speech_style.get("title", role),
            "focus": speech_style.get("focus", ""),
            "keywords": speech_style.get("keywords", []),
            "order": self.current_speaker_index + 1,
        }
    
    def generate_speech(self, speaker_role: str, topic: str, context: Dict = None) -> Dict:
        """
        根据发言人的角色生成观点
        
        Args:
            speaker_role: 发言人角色
            topic: 讨论议题
            context: 额外上下文信息
        
        Returns:
            发言内容
        """
        # 构建评估所需的payload
        intent_payload = {
            "business_name": topic,
            "budget_cap": context.get("budget", 200000) if context else 200000,
            "deadline": context.get("deadline", "T+90d") if context else "T+90d",
            "priority": context.get("priority", "medium") if context else "medium",
        }
        
        # 获取角色评估
        evaluator = ROLE_EVALUATORS.get(speaker_role)
        if not evaluator:
            return {
                "success": False,
                "error": f"Unknown role: {speaker_role}"
            }
        
        evaluation = evaluator(intent_payload)
        
        # 构建发言内容
        speech_style = ROLE_SPEECH_STYLES.get(speaker_role, {})
        
        speech = {
            "speaker_role": speaker_role,
            "speaker_title": speech_style.get("title", speaker_role),
            "topic": topic,
            "timestamp": datetime.now().isoformat(),
            "evaluation": evaluation,
            "speech_content": self._format_speech(speaker_role, evaluation, speech_style),
        }
        
        # 记录发言
        self.speeches.append(speech)
        
        return speech
    
    def _format_speech(self, role: str, evaluation: Dict, speech_style: Dict) -> str:
        """格式化发言内容"""
        lines = []
        lines.append(f"【{speech_style.get('title', role)}发言】")
        lines.append("")
        
        # 当前状态
        current_status = evaluation.get("current_status", {})
        if current_status:
            lines.append("📊 当前状态评估：")
            for key, value in current_status.items():
                lines.append(f"   • {key}: {value}")
            lines.append("")
        
        # 关键问题
        problems = evaluation.get("problems", [])
        if problems:
            lines.append("⚠️ 关键问题：")
            for problem in problems:
                lines.append(f"   • {problem}")
            lines.append("")
        
        # 改进建议
        improvements = evaluation.get("improvements", [])
        if improvements:
            lines.append("💡 改进建议：")
            for improvement in improvements:
                lines.append(f"   • {improvement}")
            lines.append("")
        
        # 风险预警
        risk_warnings = evaluation.get("risk_warnings", [])
        if risk_warnings:
            lines.append("🔔 风险预警：")
            for risk in risk_warnings:
                level_emoji = {"高": "🔴", "中": "🟡", "低": "🟢"}.get(risk.get("level", ""), "⚪")
                lines.append(f"   {level_emoji} {risk.get('level', '')}级风险: {risk.get('risk', '')}")
                lines.append(f"      应对: {risk.get('mitigation', '')}")
            lines.append("")
        
        # 可行性评分
        feasibility = evaluation.get("feasibility", 0)
        lines.append(f"📈 可行性评分: {feasibility:.0%}")
        
        return "\n".join(lines)
    
    def next_turn(self, context: Dict = None) -> Dict:
        """
        进行下一轮发言
        
        Args:
            context: 讨论上下文
        
        Returns:
            发言结果
        """
        speaker = self.get_next_speaker()
        if not speaker:
            return {
                "success": False,
                "message": "所有参与者已发言完毕",
                "status": self.status
            }
        
        role = speaker["role"]
        speech = self.generate_speech(role, self.topic, context)
        
        # 推进到下一个发言人
        self.current_speaker_index += 1
        
        return {
            "success": True,
            "speaker": speaker,
            "speech": speech,
            "remaining": len(self.participants) - self.current_speaker_index
        }
    
    def conclude_discussion(self) -> Dict:
        """
        结束讨论
        
        Returns:
            会议总结
        """
        self.status = "concluded"
        end_time = datetime.now().isoformat()
        
        # 生成会议纪要
        summary = self.generate_minutes()
        
        return {
            "meeting_id": self.meeting_id,
            "topic": self.topic,
            "status": self.status,
            "start_time": self.start_time,
            "end_time": end_time,
            "total_speeches": len(self.speeches),
            "summary": summary
        }
    
    def generate_minutes(self) -> Dict:
        """
        生成会议纪要
        
        Returns:
            会议纪要
        """
        if not self.speeches:
            return {"error": "No speeches recorded"}
        
        # 汇总可行性评分
        feasibility_scores = [s["evaluation"].get("feasibility", 0) for s in self.speeches]
        avg_feasibility = sum(feasibility_scores) / len(feasibility_scores) if feasibility_scores else 0
        
        # 汇总所有问题和建议
        all_problems = []
        all_improvements = []
        all_risks = []
        
        for speech in self.speeches:
            eval_data = speech["evaluation"]
            all_problems.extend(eval_data.get("problems", []))
            all_improvements.extend(eval_data.get("improvements", []))
            all_risks.extend(eval_data.get("risk_warnings", []))
        
        # 去重
        all_problems = list(set(all_problems))
        all_improvements = list(set(all_improvements))
        
        # 生成结论
        conclusion = self._generate_conclusion(avg_feasibility, all_risks)
        
        minutes = {
            "title": f"会议纪要: {self.topic}",
            "meeting_id": self.meeting_id,
            "generated_at": datetime.now().isoformat(),
            "topic": self.topic,
            "participants": [s["speaker_title"] for s in self.speeches],
            "speech_count": len(self.speeches),
            "average_feasibility": round(avg_feasibility, 2),
            "problems_summary": all_problems[:5],  # 最多5个
            "improvements_summary": all_improvements[:5],
            "risk_summary": all_risks[:3],
            "conclusion": conclusion,
            "detailed_speeches": [
                {
                    "role": s["speaker_role"],
                    "title": s["speaker_title"],
                    "content": s["speech_content"]
                }
                for s in self.speeches
            ]
        }
        
        return minutes
    
    def _generate_conclusion(self, avg_feasibility: float, risks: List[Dict]) -> str:
        """生成会议结论"""
        # 评估整体可行性
        if avg_feasibility >= 0.8:
            feasibility_text = "较高"
        elif avg_feasibility >= 0.7:
            feasibility_text = "中等"
        else:
            feasibility_text = "较低"
        
        # 评估风险等级
        high_risks = [r for r in risks if r.get("level") == "高"]
        risk_text = "存在较高风险" if high_risks else "整体风险可控"
        
        conclusion = f"经讨论，该项目可行性评估为{feasibility_text}（平均{avg_feasibility:.0%}），{risk_text}。"
        
        if avg_feasibility >= 0.75 and not high_risks:
            conclusion += "建议推进执行。"
        elif avg_feasibility >= 0.65:
            conclusion += "建议在风险可控的前提下推进，需重点关注高风险项。"
        else:
            conclusion += "建议暂缓，待条件成熟后再评估。"
        
        return conclusion
    
    def get_full_record(self) -> Dict:
        """获取完整会议记录"""
        return {
            "meeting_id": self.meeting_id,
            "topic": self.topic,
            "status": self.status,
            "start_time": self.start_time,
            "participants": self.participants,
            "speeches": self.speeches,
            "current_turn": self.current_speaker_index,
        }


# 全局会议实例
_current_meeting = None


def start_meeting(topic: str, participants: List[str] = None) -> Dict:
    """启动一个新会议"""
    global _current_meeting
    meeting = MeetingDiscussion()
    result = meeting.start_discussion(topic, participants)
    _current_meeting = meeting
    return result


def next_speaker(context: Dict = None) -> Dict:
    """获取下一位发言人及其发言"""
    global _current_meeting
    if not _current_meeting:
        return {"success": False, "error": "No active meeting. Call start_meeting first."}
    return _current_meeting.next_turn(context)


def get_current_meeting() -> Dict:
    """获取当前会议状态"""
    global _current_meeting
    if not _current_meeting:
        return {"success": False, "error": "No active meeting"}
    return _current_meeting.get_full_record()


def end_meeting() -> Dict:
    """结束当前会议并生成纪要"""
    global _current_meeting
    if not _current_meeting:
        return {"success": False, "error": "No active meeting"}
    result = _current_meeting.conclude_discussion()
    _current_meeting = None
    return result


def run_full_discussion(topic: str, context: Dict = None) -> Dict:
    """
    运行完整讨论流程
    
    Args:
        topic: 讨论议题
        context: 额外上下文
    
    Returns:
        完整的会议纪要
    """
    # 启动会议
    start_result = start_meeting(topic)
    
    # 依次让每个参与者发言
    while True:
        turn_result = next_speaker(context)
        if not turn_result.get("success"):
            break
    
    # 结束会议并生成纪要
    return end_meeting()
