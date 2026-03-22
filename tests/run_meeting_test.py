# -*- coding: utf-8 -*-
"""会议讨论系统测试脚本"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import sys
sys.path.insert(0, '.')
from core.meeting import (
    MeetingDiscussion,
    start_meeting,
    next_speaker,
    end_meeting,
    get_current_meeting,
    run_full_discussion,
    ROLE_SPEECH_STYLES
)

print('=' * 60)
print('角色发言风格定义')
print('=' * 60)

for role, style in ROLE_SPEECH_STYLES.items():
    print(f"\n【{role}】{style['title']}")
    print(f"   关注领域: {style['focus']}")
    keywords = ', '.join(style['keywords'])
    print(f"   关键词: {keywords}")

print('\n' + '=' * 60)
print('测试: 完整会议流程')
print('=' * 60)

# 启动会议
result = start_meeting('AI智能助手产品开发')
print(f"\n会议ID: {result['meeting_id']}")
print(f"议题: {result['topic']}")
print(f"参与者: {result['participants']}")

# 依次发言
context = {'budget': 500000, 'deadline': 'T+180d', 'priority': 'high'}

while True:
    turn = next_speaker(context)
    if not turn.get('success'):
        print(f"\n发言结束\n")
        break
    
    speaker = turn['speaker']
    speech = turn['speech']
    print(f"\n--- {speaker['title']} ({speaker['role']}) 发言 ---")
    print(f"关注领域: {speaker['focus']}")
    content = speech['speech_content']
    # 替换emoji为文字
    content = content.replace('📊', '[状态]').replace('⚠️', '[问题]').replace('💡', '[建议]').replace('🔔', '[风险]').replace('📈', '[评分]')
    print(content)

# 结束会议
final_result = end_meeting()
summary = final_result['summary']

print('=' * 60)
print('会议纪要')
print('=' * 60)
print(f"议题: {summary['topic']}")
participants_str = ', '.join(summary['participants'])
print(f"参与者: {participants_str}")
print(f"平均可行性: {summary['average_feasibility']:.0%}")

print('\n问题汇总:')
for i, problem in enumerate(summary['problems_summary'], 1):
    print(f"   {i}. {problem}")

print('\n建议汇总:')
for i, imp in enumerate(summary['improvements_summary'], 1):
    print(f"   {i}. {imp}")

print('\n风险汇总:')
for risk in summary['risk_summary']:
    level = risk['level']
    level_str = f"[{level}级]"
    print(f"   {level_str} {risk['risk']}")

print('\n会议结论:')
print(f"   {summary['conclusion']}")

print('\n' + '=' * 60)
print('测试完成!')
print('=' * 60)
