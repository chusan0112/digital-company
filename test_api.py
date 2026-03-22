# -*- coding: utf-8 -*-
import requests
import json

url = "http://127.0.0.1:8080/api/realtime/meeting/speak"
data = {"agent_id": "jxshi", "topic": "新产品发布策略"}

try:
    response = requests.post(url, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
