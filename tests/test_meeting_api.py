# -*- coding: utf-8 -*-
"""测试会议API接口"""
import sys
sys.path.insert(0, '.')
import json

# 模拟API请求
def mock_request(path, method='GET', body=None):
    """模拟handle_request调用"""
    # 这里直接调用会议模块函数，不走完整的handle_request
    from core.meeting import (
        start_meeting,
        next_speaker,
        end_meeting,
        get_current_meeting,
        run_full_discussion,
        ROLE_SPEECH_STYLES
    )
    
    # 测试各个接口
    results = {}
    
    # GET /api/meeting/roles
    results['roles'] = {"success": True, "roles": ROLE_SPEECH_STYLES}
    
    # POST /api/meeting/start
    results['start'] = start_meeting(
        topic="新产品线规划",
        participants=["CEO", "CFO", "CTO"]
    )
    
    # POST /api/meeting/next
    context = {"budget": 300000, "deadline": "T+90d"}
    turn1 = next_speaker(context)
    results['turn1'] = turn1
    
    turn2 = next_speaker(context)
    results['turn2'] = turn2
    
    turn3 = next_speaker(context)
    results['turn3'] = turn3
    
    # POST /api/meeting/end
    results['end'] = end_meeting()
    
    return results


if __name__ == "__main__":
    print("=" * 60)
    print("会议API接口测试")
    print("=" * 60)
    
    results = mock_request("/api/meeting", "POST")
    
    print("\n1. 角色列表:")
    for role, style in results['roles']['roles'].items():
        print(f"   {role}: {style['title']}")
    
    print(f"\n2. 会议启动:")
    print(f"   会议ID: {results['start']['meeting_id']}")
    print(f"   议题: {results['start']['topic']}")
    print(f"   参与者: {results['start']['participants']}")
    
    print(f"\n3. 发言轮次:")
    print(f"   第1位: {results['turn1']['speaker']['title']}")
    print(f"   第2位: {results['turn2']['speaker']['title']}")
    print(f"   第3位: {results['turn3']['speaker']['title']}")
    
    summary = results['end']['summary']
    print(f"\n4. 会议总结:")
    print(f"   平均可行性: {summary['average_feasibility']:.0%}")
    print(f"   结论: {summary['conclusion']}")
    
    print("\n" + "=" * 60)
    print("API测试完成!")
    print("=" * 60)
