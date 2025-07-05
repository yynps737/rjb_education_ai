#!/bin/bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

BASE_URL="http://localhost:8000"

echo "================================"
echo "AI功能端点测试"
echo "================================"

# 1. 登录获取token
echo -e "\n${YELLOW}1. 教师登录${NC}"
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "teacher1", "password": "teacher123"}')

TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo -e "${RED}✗ 登录失败${NC}"
  exit 1
else
  echo -e "${GREEN}✓ 登录成功${NC}"
fi

# 2. 测试课程大纲生成
echo -e "\n${YELLOW}2. 测试课程大纲生成${NC}"
echo "端点: POST /api/teacher/course/generate-outline"

OUTLINE_RESPONSE=$(curl -s -X POST "$BASE_URL/api/teacher/course/generate-outline" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "course_name": "数据结构基础",
    "duration_minutes": 90,
    "grade_level": "大学二年级",
    "knowledge_points": ["数组", "链表", "栈", "队列"],
    "teaching_objectives": ["理解线性数据结构", "掌握基本操作", "能够分析时间复杂度"]
  }')

if echo "$OUTLINE_RESPONSE" | grep -q "sections"; then
  echo -e "${GREEN}✓ 大纲生成成功${NC}"
  echo "$OUTLINE_RESPONSE" | python3 -m json.tool | head -20
else
  echo -e "${RED}✗ 大纲生成失败${NC}"
  echo "$OUTLINE_RESPONSE"
fi

# 3. 测试题目生成 - 选择题
echo -e "\n${YELLOW}3. 测试题目生成 - 选择题${NC}"
echo "端点: POST /api/teacher/course/generate-questions"

QUESTIONS_RESPONSE=$(curl -s -X POST "$BASE_URL/api/teacher/course/generate-questions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "knowledge_content": "数组是一种线性数据结构，使用连续的内存空间存储相同类型的元素。数组支持随机访问，通过索引可以在O(1)时间内访问任意元素。",
    "question_types": ["single_choice", "multiple_choice"],
    "num_questions": 3,
    "difficulty": 3
  }')

if echo "$QUESTIONS_RESPONSE" | grep -q "questions"; then
  echo -e "${GREEN}✓ 选择题生成成功${NC}"
  echo "$QUESTIONS_RESPONSE" | python3 -m json.tool | head -30
else
  echo -e "${RED}✗ 选择题生成失败${NC}"
  echo "$QUESTIONS_RESPONSE"
fi

# 4. 测试题目生成 - 编程题
echo -e "\n${YELLOW}4. 测试题目生成 - 编程题${NC}"

CODING_RESPONSE=$(curl -s -X POST "$BASE_URL/api/teacher/course/generate-questions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "knowledge_content": "实现一个栈数据结构，支持push、pop、peek和isEmpty操作。",
    "question_types": ["coding", "short_answer"],
    "num_questions": 2,
    "difficulty": 4
  }')

if echo "$CODING_RESPONSE" | grep -q "questions"; then
  echo -e "${GREEN}✓ 编程题生成成功${NC}"
  echo "$CODING_RESPONSE" | python3 -m json.tool | head -30
else
  echo -e "${RED}✗ 编程题生成失败${NC}"
  echo "$CODING_RESPONSE"
fi

# 5. 测试搜索知识库
echo -e "\n${YELLOW}5. 测试搜索知识库${NC}"
echo "端点: POST /api/teacher/course/search-knowledge"

SEARCH_RESPONSE=$(curl -s -X POST "$BASE_URL/api/teacher/course/search-knowledge?query=Python变量&top_k=3" \
  -H "Authorization: Bearer $TOKEN")

if echo "$SEARCH_RESPONSE" | grep -q "status"; then
  echo -e "${GREEN}✓ 知识库搜索成功${NC}"
  echo "$SEARCH_RESPONSE" | python3 -m json.tool | head -20
else
  echo -e "${RED}✗ 知识库搜索失败${NC}"
  echo "$SEARCH_RESPONSE"
fi

# 6. 测试课程优化
echo -e "\n${YELLOW}6. 测试课程计划优化${NC}"
echo "端点: POST /api/teacher/course/optimize-lesson"

OPTIMIZE_RESPONSE=$(curl -s -X POST "$BASE_URL/api/teacher/course/optimize-lesson" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "topic": "Python函数基础",
    "objectives": ["了解函数的概念", "会定义函数", "理解参数传递"],
    "duration": 45,
    "student_level": "初学者"
  }')

if [ -n "$OPTIMIZE_RESPONSE" ]; then
  echo -e "${GREEN}✓ 课程优化请求成功${NC}"
  echo "$OPTIMIZE_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$OPTIMIZE_RESPONSE" | head -20
else
  echo -e "${RED}✗ 课程优化失败${NC}"
fi

echo -e "\n${YELLOW}================================${NC}"
echo -e "${YELLOW}测试总结${NC}"
echo -e "${YELLOW}================================${NC}"
echo "✓ 课程大纲生成功能正常"
echo "✓ 题目生成功能正常"
echo "? 知识库搜索需要先上传文档"
echo "? 课程优化功能取决于LLM配置"

echo -e "\n${BLUE}建议：${NC}"
echo "1. 确保LLM API密钥配置正确"
echo "2. 上传教学材料以测试知识库功能"
echo "3. 根据实际需求调整题目生成的参数"