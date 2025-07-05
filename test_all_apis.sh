#!/bin/bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

BASE_URL="http://localhost:8000"

echo "================================"
echo "教育AI助手 - 完整API测试"
echo "================================"

# 检查服务是否运行
echo -e "\n${YELLOW}检查服务状态...${NC}"
if curl -s -o /dev/null -w "%{http_code}" $BASE_URL | grep -q "200"; then
    echo -e "${GREEN}✓ 服务运行正常${NC}"
else
    echo -e "${RED}✗ 服务未启动，请先启动服务${NC}"
    exit 1
fi

# 1. 测试公共API
echo -e "\n${BLUE}=== 1. 公共API测试 ===${NC}"

echo -e "\n测试根路径:"
curl -s $BASE_URL | python3 -m json.tool

echo -e "\n测试健康检查:"
curl -s $BASE_URL/health | python3 -m json.tool

# 2. 测试认证功能
echo -e "\n${BLUE}=== 2. 认证功能测试 ===${NC}"

# 注册新用户
RANDOM_NUM=$RANDOM
echo -e "\n${YELLOW}注册新用户 (test_$RANDOM_NUM)${NC}"
REGISTER_RESPONSE=$(curl -s -X POST $BASE_URL/api/auth/student/register \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"test_$RANDOM_NUM\",
    \"email\": \"test_$RANDOM_NUM@example.com\",
    \"password\": \"Test123456!\",
    \"full_name\": \"测试用户$RANDOM_NUM\"
  }")
echo $REGISTER_RESPONSE | python3 -m json.tool

# 测试登录
echo -e "\n${YELLOW}测试学生登录${NC}"
STUDENT_LOGIN=$(curl -s -X POST $BASE_URL/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "student1",
    "password": "student123"
  }')
echo $STUDENT_LOGIN | python3 -m json.tool

# 提取token
STUDENT_TOKEN=$(echo $STUDENT_LOGIN | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
echo -e "${GREEN}学生Token获取成功${NC}"

# 教师登录
echo -e "\n${YELLOW}测试教师登录${NC}"
TEACHER_LOGIN=$(curl -s -X POST $BASE_URL/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "teacher1",
    "password": "teacher123"
  }')
TEACHER_TOKEN=$(echo $TEACHER_LOGIN | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
echo -e "${GREEN}教师Token获取成功${NC}"

# 管理员登录
echo -e "\n${YELLOW}测试管理员登录${NC}"
ADMIN_LOGIN=$(curl -s -X POST $BASE_URL/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }')
ADMIN_TOKEN=$(echo $ADMIN_LOGIN | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
echo -e "${GREEN}管理员Token获取成功${NC}"

# 3. 测试学生功能
echo -e "\n${BLUE}=== 3. 学生功能测试 ===${NC}"

echo -e "\n${YELLOW}获取已注册课程${NC}"
curl -s -H "Authorization: Bearer $STUDENT_TOKEN" \
  $BASE_URL/api/student/courses/enrolled | python3 -m json.tool | head -20

echo -e "\n${YELLOW}获取可选课程${NC}"
curl -s -H "Authorization: Bearer $STUDENT_TOKEN" \
  $BASE_URL/api/student/courses/available | python3 -m json.tool | head -20

echo -e "\n${YELLOW}获取学习进度${NC}"
curl -s -H "Authorization: Bearer $STUDENT_TOKEN" \
  $BASE_URL/api/student/learning/progress | python3 -m json.tool

echo -e "\n${YELLOW}测试智能问答${NC}"
curl -s -X POST $BASE_URL/api/student/learning/ask \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $STUDENT_TOKEN" \
  -d '{
    "question": "什么是Python？",
    "course_id": null
  }' | python3 -m json.tool

# 4. 测试教师功能
echo -e "\n${BLUE}=== 4. 教师功能测试 ===${NC}"

echo -e "\n${YELLOW}获取教师课程列表${NC}"
curl -s -H "Authorization: Bearer $TEACHER_TOKEN" \
  $BASE_URL/api/teacher/course/list | python3 -m json.tool | head -20

echo -e "\n${YELLOW}生成课程大纲${NC}"
curl -s -X POST $BASE_URL/api/teacher/course/generate-outline \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TEACHER_TOKEN" \
  -d '{
    "course_name": "Python进阶编程",
    "duration_minutes": 60,
    "grade_level": "大学三年级",
    "knowledge_points": ["装饰器", "生成器", "异步编程"],
    "teaching_objectives": ["掌握Python高级特性", "理解异步编程原理"]
  }' | python3 -m json.tool | head -30

echo -e "\n${YELLOW}生成测试题目${NC}"
curl -s -X POST $BASE_URL/api/teacher/course/generate-questions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TEACHER_TOKEN" \
  -d '{
    "knowledge_content": "Python装饰器是一种设计模式，用于在不修改原函数的情况下扩展函数功能。",
    "question_types": ["single_choice", "short_answer"],
    "num_questions": 2,
    "difficulty": 4
  }' | python3 -m json.tool

# 5. 测试管理员功能
echo -e "\n${BLUE}=== 5. 管理员功能测试 ===${NC}"

echo -e "\n${YELLOW}获取用户列表${NC}"
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  $BASE_URL/api/admin/users?page=1&page_size=5 | python3 -m json.tool | head -30

echo -e "\n${YELLOW}获取系统健康状态${NC}"
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  $BASE_URL/api/admin/system/health | python3 -m json.tool

echo -e "\n${YELLOW}获取系统统计信息${NC}"
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  $BASE_URL/api/admin/system/stats | python3 -m json.tool

# 6. 测试错误处理
echo -e "\n${BLUE}=== 6. 错误处理测试 ===${NC}"

echo -e "\n${YELLOW}测试重复注册错误${NC}"
curl -s -X POST $BASE_URL/api/auth/student/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "student1",
    "email": "new@test.com",
    "password": "Test123456!",
    "full_name": "重复用户"
  }' | python3 -m json.tool

echo -e "\n${YELLOW}测试无效登录${NC}"
curl -s -X POST $BASE_URL/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "nonexistent",
    "password": "wrongpassword"
  }' | python3 -m json.tool

echo -e "\n${YELLOW}测试未授权访问${NC}"
curl -s $BASE_URL/api/admin/users | python3 -m json.tool

# 7. 测试分页功能
echo -e "\n${BLUE}=== 7. 分页功能测试 ===${NC}"

echo -e "\n${YELLOW}测试课程分页${NC}"
curl -s -H "Authorization: Bearer $STUDENT_TOKEN" \
  "$BASE_URL/api/student/courses/available?page=1&page_size=2" | python3 -m json.tool

# 总结
echo -e "\n${BLUE}================================${NC}"
echo -e "${BLUE}测试完成！${NC}"
echo -e "${BLUE}================================${NC}"

echo -e "\n${YELLOW}测试账号信息：${NC}"
echo "管理员: admin / admin123"
echo "教师: teacher1 / teacher123"
echo "学生: student1 / student123"

echo -e "\n${YELLOW}API文档地址：${NC}"
echo "Swagger UI: http://localhost:8000/docs"
echo "ReDoc: http://localhost:8000/redoc"

echo -e "\n${GREEN}提示：如需测试更多功能，请查看 API_GUIDELINES.md 文档${NC}"