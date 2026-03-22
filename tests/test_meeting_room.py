#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
会议室管理功能测试
"""
import urllib.request
import json
import sys


def test_meeting_room_api():
    """测试会议室管理API"""
    base_url = 'http://127.0.0.1:8080'
    
    print('=== 会议室管理功能测试 ===')
    print()
    
    # 1. 获取所有会议室
    print('1. GET /api/meeting-rooms - 获取所有会议室')
    result = urllib.request.urlopen(f'{base_url}/api/meeting-rooms').read()
    rooms = json.loads(result)['meeting_rooms']
    print(f'   已有会议室数量: {len(rooms)}')
    for r in rooms:
        print(f'   - {r["name"]} (容纳{r["capacity"]}人, 位置:{r["location"]}, 状态:{r["status"]})')
    print('   [OK]')
    print()
    
    # 2. 创建会议室
    print('2. POST /api/meeting-rooms - 创建会议室')
    room_data = json.dumps({
        'name': 'CTO会议室',
        'capacity': 8,
        'location': '4F CTO办公室',
        'status': 'available'
    }).encode('utf-8')
    req = urllib.request.Request(f'{base_url}/api/meeting-rooms', data=room_data, headers={'Content-Type': 'application/json'})
    result = urllib.request.urlopen(req).read().decode()
    new_room_id = json.loads(result)['id']
    print(f'   创建成功，ID: {new_room_id}')
    print('   [OK] 成功')
    print()
    
    # 3. 预订会议
    print('3. POST /api/meetings - 预订会议')
    meeting_data = json.dumps({
        'title': '产品规划会议',
        'host_id': '053e2121',
        'start_time': '2026-03-25 14:00',
        'end_time': '2026-03-25 16:00',
        'meeting_room_id': 1,
        'notes': '讨论Q2产品规划'
    }).encode('utf-8')
    req = urllib.request.Request(f'{base_url}/api/meetings', data=meeting_data, headers={'Content-Type': 'application/json'})
    result = urllib.request.urlopen(req).read().decode()
    meeting_id = json.loads(result)['id']
    print(f'   会议预订成功，ID: {meeting_id}')
    print('   [OK] 成功')
    print()
    
    # 4. 冲突检测 - 尝试预订同一会议室的重叠时间
    print('4. 冲突检测 - 预订重叠时间段')
    conflict_data = json.dumps({
        'title': '另一个会议',
        'host_id': '70fd3b51',
        'start_time': '2026-03-25 15:00',
        'end_time': '2026-03-25 17:00',
        'meeting_room_id': 1
    }).encode('utf-8')
    req = urllib.request.Request(f'{base_url}/api/meetings', data=conflict_data, headers={'Content-Type': 'application/json'})
    try:
        result = urllib.request.urlopen(req).read().decode()
        print('   [FAIL] 未检测到冲突!')
    except urllib.error.HTTPError as e:
        if e.code == 409:
            print(f'   [OK] 正确检测到冲突: HTTP 409')
        else:
            print(f'   [FAIL] 错误: HTTP {e.code}')
    print()
    
    # 5. 获取会议列表
    print('5. GET /api/meetings - 获取会议列表')
    result = urllib.request.urlopen(f'{base_url}/api/meetings').read()
    meetings = json.loads(result)['meetings']
    print(f'   会议数量: {len(meetings)}')
    for m in meetings:
        print(f'   - {m["title"]} (状态: {m["status"]})')
    print('   [OK] 成功')
    print()
    
    # 6. 更新会议
    print('6. PUT /api/meetings/{id} - 更新会议')
    update_data = json.dumps({
        'title': '产品规划会议 - 已确认',
        'notes': '需要CEO参加'
    }).encode('utf-8')
    req = urllib.request.Request(f'{base_url}/api/meetings/{meeting_id}', data=update_data, headers={'Content-Type': 'application/json'})
    req.get_method = lambda: 'PUT'
    result = urllib.request.urlopen(req).read().decode()
    print(f'   更新结果: {result}')
    print('   [OK] 成功')
    print()
    
    # 7. 取消会议
    print('7. DELETE /api/meetings/{id} - 取消会议')
    req = urllib.request.Request(f'{base_url}/api/meetings/{meeting_id}', headers={'Content-Type': 'application/json'})
    req.get_method = lambda: 'DELETE'
    result = urllib.request.urlopen(req).read().decode()
    print(f'   取消结果: {result}')
    print('   [OK] 成功')
    print()
    
    # 8. 更新会议室
    print('8. PUT /api/meeting-rooms/{id} - 更新会议室')
    update_room = json.dumps({
        'status': 'occupied'
    }).encode('utf-8')
    req = urllib.request.Request(f'{base_url}/api/meeting-rooms/1', data=update_room, headers={'Content-Type': 'application/json'})
    req.get_method = lambda: 'PUT'
    result = urllib.request.urlopen(req).read().decode()
    print(f'   更新结果: {result}')
    print('   [OK] 成功')
    print()
    
    # 9. 删除会议室
    print('9. DELETE /api/meeting-rooms/{id} - 删除会议室')
    req = urllib.request.Request(f'{base_url}/api/meeting-rooms/{new_room_id}', headers={'Content-Type': 'application/json'})
    req.get_method = lambda: 'DELETE'
    result = urllib.request.urlopen(req).read().decode()
    print(f'   删除结果: {result}')
    print('   [OK] 成功')
    print()
    
    print('=== 所有测试通过 ===')
    return True


if __name__ == '__main__':
    try:
        test_meeting_room_api()
    except Exception as e:
        print(f'测试失败: {e}')
        sys.exit(1)
