# -*- coding: utf-8 -*-
"""测试生命周期API"""
import requests
import json

BASE_URL = "http://127.0.0.1:8080"

# 1. 创建项目
print("=" * 50)
print("[1] 创建小红书运营项目")
print("=" * 50)

project_data = {
    "name": "小红书运营项目",
    "description": "目标：日入1000元",
    "budget": 1000,
    "owner": "金多多",
    "tags": ["运营", "小红书", "自动化"]
}

resp = requests.post(f"{BASE_URL}/api/lifecycle/project", json=project_data)
print(f"Status: {resp.status_code}")
result = resp.json()
print(f"Result: {json.dumps(result, ensure_ascii=False, indent=2)}")

if result.get("success"):
    project = result.get("project", {})
    project_id = project.get("id")
    print(f"\n✅ 项目创建成功! ID: {project_id}")
    
    # 2. 发起立项会议
    print("\n" + "=" * 50)
    print("[2] 发起立项会议")
    print("=" * 50)
    
    kickoff_data = {
        "budget": 1000,
        "deadline": "T+30d",
        "priority": "high",
        "target": "日入1000元"
    }
    
    resp2 = requests.post(f"{BASE_URL}/api/lifecycle/kickoff/{project_id}", json=kickoff_data)
    print(f"Status: {resp2.status_code}")
    result2 = resp2.json()
    print(f"Result: {json.dumps(result2, ensure_ascii=False, indent=2)}")
    
    if result2.get("success"):
        print("\n✅ 立项会议发起成功!")
        
        # 3. 检查当前会议
        print("\n" + "=" * 50)
        print("[3] 检查当前进行中的会议")
        print("=" * 50)
        
        resp3 = requests.get(f"{BASE_URL}/api/lifecycle/active-meeting")
        result3 = resp3.json()
        print(f"Result: {json.dumps(result3, ensure_ascii=False, indent=2)}")
    else:
        print(f"\n❌ 立项会议发起失败: {result2.get('error')}")
else:
    print(f"\n❌ 项目创建失败: {result.get('error')}")
