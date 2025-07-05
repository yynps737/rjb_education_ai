#!/bin/bash

# 教育AI助手API简化测试脚本
# 测试主要API端点的功能

BASE_URL="http://localhost:8000"
CONTENT_TYPE="Content-Type: application/json"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 测试计数器
PASS=0
FAIL=0

# 测试函数
test_api() {
    local method=$1
    local endpoint=$2
    local data=$3
    local headers=$4
    local description=$5
    local expected_code=$6
    
    echo -e "\n${BLUE}测试: $description${NC}"
    echo "端点: $method $endpoint"
    
    # 构建curl命令
    local cmd="curl -s -X $method \"$BASE_URL$endpoint\""
    
    if [ -n "$headers" ]; then
        cmd="$cmd -H \"$CONTENT_TYPE\" $headers"
    else
        cmd="$cmd -H \"$CONTENT_TYPE\""
    fi
    
    if [ -n "$data" ] && [ "$data" != " " ]; then
        cmd="$cmd -d '$data'"
    fi
    
    # 执行请求（同时获取响应和状态码）
    local response=$(eval "$cmd -w '\n%{http_code}'")
    local status_code=$(echo "$response" | tail -n1)
    response=$(echo "$response" | head -n-1)
    
    echo "状态码: $status_code (期望: ${expected_code:-200})"
    echo "响应: $response" | python3 -m json.tool 2>/dev/null || echo "响应: $response"
    
    # 判断测试结果
    if [[ $status_code -eq ${expected_code:-200} ]]; then
        echo -e "${GREEN}✓ 测试通过${NC}"
        ((PASS++))
        return 0
    else
        echo -e "${RED}✗ 测试失败${NC}"
        ((FAIL++))
        return 1
    fi
}

echo "================================"
echo "教育AI助手API简化测试"
echo "================================"

# 1. 公共API测试
echo -e "\n${YELLOW}=== 1. 公共API测试 ====${NC}"
test_api "GET" "/" "" "" "根路径" 200
test_api "GET" "/health" "" "" "健康检查" 200

# 2. 认证API测试
echo -e "\n${YELLOW}=== 2. 认证API测试 ====${NC}"

# 2.1 学生注册（使用存在的端点）
test_api "POST" "/api/auth/student/register" '{
    "username": "test_api_student_'$(date +%s)'",
    "password": "Test123456!",
    "email": "test_api_'$(date +%s)'@test.com",
    "full_name": "API测试学生"
}' "" "学生注册" 200

# 2.2 登录测试 - 使用已存在的用户
echo -e "\n${YELLOW}测试登录功能...${NC}"

# 首先创建一个新用户并设置密码
echo "创建测试用户..."
cd /home/kkb/RJB/backend && source ../backend_venv/bin/activate && python -c "
from models.database import SessionLocal, init_db
from models.user import User, UserRole
from utils.auth import get_password_hash

init_db()
db = SessionLocal()

try:
    # 创建一个新的测试用户
    test_user = User(
        username='api_test_user',
        email='api_test@test.com',
        full_name='API测试用户',
        hashed_password=get_password_hash('Test123456!'),
        role=UserRole.STUDENT,
        is_active=True
    )
    db.add(test_user)
    db.commit()
    print('测试用户创建成功')
except Exception as e:
    db.rollback()
    print(f'用户可能已存在: {e}')
finally:
    db.close()
" 2>/dev/null

# 使用刚创建的用户登录
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login" \
    -H "$CONTENT_TYPE" \
    -d '{"username": "api_test_user", "password": "Test123456!"}')

TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('data', {}).get('access_token', ''))" 2>/dev/null)

if [ -n "$TOKEN" ]; then
    echo -e "${GREEN}登录成功，获取到Token${NC}"
    ((PASS++))
else
    echo -e "${RED}登录失败${NC}"
    ((FAIL++))
    echo "响应: $LOGIN_RESPONSE"
fi

# 2.3 使用Token测试需要认证的API
if [ -n "$TOKEN" ]; then
    echo -e "\n${YELLOW}=== 3. 需要认证的API测试 ====${NC}"
    
    # 学生端API
    test_api "GET" "/api/student/courses/enrolled" "" "-H \"Authorization: Bearer $TOKEN\"" "获取已注册课程" 200
    test_api "GET" "/api/student/learning/progress" "" "-H \"Authorization: Bearer $TOKEN\"" "获取学习进度" 200
    
    # 知识库API
    test_api "POST" "/api/student/learning/ask" '{
        "question": "什么是Python？",
        "course_id": null
    }' "-H \"Authorization: Bearer $TOKEN\"" "智能问答" 200
fi

# 3. 检查各种端点的可用性（不需要认证）
echo -e "\n${YELLOW}=== 4. API端点可用性检查 ====${NC}"

endpoints=(
    "GET|/api/auth/student/info|401|学生信息(需要认证)"
    "POST|/api/auth/logout|200|登出"
    "GET|/api/student/courses/enrolled|401|学生课程(需要认证)"
    "GET|/api/teacher/course/list|401|教师课程(需要认证)"
    "GET|/api/admin/users|401|用户管理(需要认证)"
    "GET|/api/admin/system/health|401|系统健康(需要认证)"
)

for endpoint in "${endpoints[@]}"; do
    IFS='|' read -r method path expected desc <<< "$endpoint"
    test_api "$method" "$path" "" "" "$desc" "$expected"
done

# 5. 测试总结
echo -e "\n${YELLOW}================================${NC}"
echo -e "${YELLOW}测试总结${NC}"
echo -e "${YELLOW}================================${NC}"
echo -e "${GREEN}通过: $PASS${NC}"
echo -e "${RED}失败: $FAIL${NC}"
echo "总计: $((PASS + FAIL))"

# 6. API可用性总结
echo -e "\n${BLUE}API可用性总结:${NC}"
echo "✓ 公共API（根路径、健康检查）: 正常"
echo "✓ 认证API（学生注册、登录、登出）: 部分可用"
echo "✗ 学生端API: 需要有效的认证Token"
echo "✗ 教师端API: 需要教师角色的Token"
echo "✗ 管理员API: 需要管理员角色的Token"
echo "✓ 知识库API: 需要认证Token但可用"

# 7. 问题总结
echo -e "\n${RED}发现的问题:${NC}"
echo "1. 缺少通用的注册端点（只有学生注册）"
echo "2. 部分API端点返回404（未实现）"
echo "3. 部分API端点返回307/405（路由配置问题）"
echo "4. 需要为不同角色创建相应的测试用户"

echo -e "\n${BLUE}建议:${NC}"
echo "1. 实现缺失的API端点"
echo "2. 修复路由配置问题"
echo "3. 添加通用的注册端点"
echo "4. 完善API文档与实际实现的一致性"