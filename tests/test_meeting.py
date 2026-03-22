"""会议讨论系统测试"""

from core.meeting import (
    MeetingDiscussion,
    start_meeting,
    next_speaker,
    end_meeting,
    get_current_meeting,
    run_full_discussion,
    ROLE_SPEECH_STYLES
)


def test_meeting_flow():
    """测试完整会议流程"""
    print("=" * 60)
    print("测试1: 完整会议流程")
    print("=" * 60)
    
    # 1. 启动会议
    print("\n📌 启动会议...")
    result = start_meeting("AI智能助手产品开发")
    print(f"会议ID: {result['meeting_id']}")
    print(f"议题: {result['topic']}")
    print(f"参与者: {result['participants']}")
    
    # 2. 依次发言
    print("\n📌 依次发言...")
    context = {"budget": 500000, "deadline": "T+180d", "priority": "high"}
    
    while True:
        turn = next_speaker(context)
        if not turn.get("success"):
            print(f"\n✅ 发言结束: {turn.get('message')}")
            break
        
        speaker = turn["speaker"]
        speech = turn["speech"]
        
        print(f"\n--- 第{turn['remaining'] + 1}位发言人: {speaker['title']} ({speaker['role']}) ---")
        print(f"关注领域: {speaker['focus']}")
        print(f"发言内容:\n{speech['speech_content']}")
    
    # 3. 结束会议
    print("\n📌 结束会议并生成纪要...")
    final_result = end_meeting()
    
    summary = final_result["summary"]
    print("\n" + "=" * 60)
    print("📋 会议纪要")
    print("=" * 60)
    print(f"会议ID: {summary['meeting_id']}")
    print(f"议题: {summary['topic']}")
    print(f"参与者: {', '.join(summary['participants'])}")
    print(f"平均可行性: {summary['average_feasibility']:.0%}")
    
    print("\n⚠️ 问题汇总:")
    for i, problem in enumerate(summary['problems_summary'], 1):
        print(f"   {i}. {problem}")
    
    print("\n💡 建议汇总:")
    for i, imp in enumerate(summary['improvements_summary'], 1):
        print(f"   {i}. {imp}")
    
    print("\n🔔 风险汇总:")
    for risk in summary['risk_summary']:
        print(f"   - [{risk['level']}级] {risk['risk']}")
    
    print("\n📌 会议结论:")
    print(f"   {summary['conclusion']}")
    
    return final_result


def test_individual_turns():
    """测试逐轮发言"""
    print("\n" + "=" * 60)
    print("测试2: 逐轮发言测试")
    print("=" * 60)
    
    # 指定参与者顺序
    meeting = MeetingDiscussion()
    meeting.start_discussion("跨境电商平台", participants=["CTO", "CFO", "COO"])
    
    print(f"\n会议ID: {meeting.meeting_id}")
    print(f"参与者: {meeting.participants}")
    
    # 只进行两轮
    for i in range(2):
        turn = meeting.next_turn({"budget": 300000})
        if turn.get("success"):
            print(f"\n--- 发言 {i+1}: {turn['speaker']['title']} ---")
            print(turn['speech']['speech_content'][:200] + "...")
    
    # 查看当前状态
    status = get_current_meeting()
    print(f"\n当前状态: 已发言{status['current_turn']}轮，还剩{len(status['participants']) - status['current_turn']}轮")


def test_run_full_discussion():
    """测试快捷完整讨论"""
    print("\n" + "=" * 60)
    print("测试3: 快捷完整讨论 (run_full_discussion)")
    print("=" * 60)
    
    result = run_full_discussion(
        "智能家居产品线扩展",
        {"budget": 800000, "deadline": "T+365d", "priority": "medium"}
    )
    
    summary = result["summary"]
    print(f"\n议题: {summary['topic']}")
    print(f"平均可行性: {summary['average_feasibility']:.0%}")
    print(f"结论: {summary['conclusion']}")


def show_role_styles():
    """展示角色发言风格"""
    print("\n" + "=" * 60)
    print("角色发言风格定义")
    print("=" * 60)
    
    for role, style in ROLE_SPEECH_STYLES.items():
        print(f"\n【{role}】{style['title']}")
        print(f"   关注领域: {style['focus']}")
        print(f"   关键词: {', '.join(style['keywords'])}")


if __name__ == "__main__":
    # 展示角色风格
    show_role_styles()
    
    # 运行测试
    test_meeting_flow()
    test_individual_turns()
    test_run_full_discussion()
    
    print("\n" + "=" * 60)
    print("✅ 所有测试完成!")
    print("=" * 60)
