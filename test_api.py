#!/usr/bin/env python
"""测试API功能"""
import requests
import json

BASE_URL = "http://localhost:8000"

print("=== 测试教育AI助手API ===\n")

# 1. 测试健康检查
print("1. 健康检查")
response = requests.get(f"{BASE_URL}/health")
print(f"状态码: {response.status_code}")
print(f"响应: {response.json()}\n")

# 2. 测试根路径
print("2. 根路径")
response = requests.get(f"{BASE_URL}/")
print(f"状态码: {response.status_code}")
print(f"响应: {response.json()}\n")

# 3. 测试注册（先尝试注册管理员）
print("3. 注册管理员")
register_data = {
    "username": "admin2",
    "password": "admin123456",
    "email": "admin2@test.com",
    "full_name": "管理员2",
    "role": "ADMIN"
}
response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
print(f"状态码: {response.status_code}")
print(f"响应: {response.text}\n")

# 4. 测试登录
print("4. 测试登录")
login_data = {
    "username": "student",
    "password": "student123"
}
response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
print(f"状态码: {response.status_code}")
print(f"响应: {response.text[:200] if len(response.text) > 200 else response.text}\n")

# 如果登录成功，提取token
if response.status_code == 200:
    try:
        data = response.json()
        token = data.get('data', {}).get('access_token')
        if token:
            print(f"获取到Token: {token[:50]}...")
            
            # 5. 使用token测试需要认证的端点
            headers = {"Authorization": f"Bearer {token}"}
            
            print("\n5. 测试需要认证的端点")
            response = requests.get(f"{BASE_URL}/api/student/courses/enrolled", headers=headers)
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.text[:200] if len(response.text) > 200 else response.text}")
    except:
        print("无法解析登录响应")