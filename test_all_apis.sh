#!/bin/bash

# 登录获取令牌
echo "=== 获取访问令牌 ==="
STUDENT_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/auth/login" -H "Content-Type: application/json" -d '{"username":"student","password":"student123"}')
STUDENT_TOKEN=$(echo $STUDENT_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
echo "学生令牌: ${STUDENT_TOKEN:0:50}..."

TEACHER_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/auth/login" -H "Content-Type: application/json" -d '{"username":"teacher","password":"teacher123"}')
TEACHER_TOKEN=$(echo $TEACHER_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
echo "教师令牌: ${TEACHER_TOKEN:0:50}..."

ADMIN_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/auth/login" -H "Content-Type: application/json" -d '{"username":"admin","password":"admin123"}')
ADMIN_TOKEN=$(echo $ADMIN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
echo "管理员令牌: ${ADMIN_TOKEN:0:50}..."

echo -e "\n=== 测试公共端点 ==="
echo "1. 健康检查: $(curl -s http://localhost:8000/health)"
echo "2. 根路径: $(curl -s http://localhost:8000/ | grep -o '"message":"[^"]*' | cut -d'"' -f4)"

echo -e "\n=== 测试学生API ==="
echo "1. 获取已注册课程:"
curl -s -X GET "http://localhost:8000/api/student/courses/enrolled" -H "Authorization: Bearer $STUDENT_TOKEN"

echo -e "\n\n2. 获取学习进度:"
curl -s -X GET "http://localhost:8000/api/student/learning/progress" -H "Authorization: Bearer $STUDENT_TOKEN"

echo -e "\n=== 测试教师API ==="
echo "1. 获取学生列表:"
curl -s -X GET "http://localhost:8000/api/teacher/students/" -H "Authorization: Bearer $TEACHER_TOKEN"

echo -e "\n\n2. 获取课程列表:"
curl -s -X GET "http://localhost:8000/api/teacher/course/list" -H "Authorization: Bearer $TEACHER_TOKEN"

echo -e "\n=== 测试管理员API ==="
echo "1. 系统健康状态:"
curl -s -X GET "http://localhost:8000/api/admin/system/health" -H "Authorization: Bearer $ADMIN_TOKEN"

echo -e "\n\n2. 用户统计:"
curl -s -X GET "http://localhost:8000/api/admin/users/stats/summary" -H "Authorization: Bearer $ADMIN_TOKEN"

echo -e "\n\n3. 分析概览:"
curl -s -X GET "http://localhost:8000/api/admin/analytics/overview" -H "Authorization: Bearer $ADMIN_TOKEN"

echo -e "\n=== 测试知识库API ==="
echo "1. 提问测试:"
curl -s -X POST "http://localhost:8000/api/knowledge/ask" \
  -H "Authorization: Bearer $STUDENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"什么是Python？","context_type":"general"}'

echo -e "\n\n=== 测试完成 ==="