#\!/bin/bash

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=== 教育AI助手启动脚本 ===${NC}"

# 检查Docker服务
echo -e "\n${YELLOW}1. 检查Docker服务...${NC}"
if docker ps >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Docker服务正常${NC}"
else
    echo -e "${RED}✗ Docker服务未启动${NC}"
    exit 1
fi

# 启动数据库和Redis
echo -e "\n${YELLOW}2. 启动数据库和Redis...${NC}"
docker-compose up -d
sleep 3

# 检查服务状态
if docker ps  < /dev/null |  grep -q "education_postgres"; then
    echo -e "${GREEN}✓ PostgreSQL已启动${NC}"
else
    echo -e "${RED}✗ PostgreSQL启动失败${NC}"
fi

if docker ps | grep -q "education_redis"; then
    echo -e "${GREEN}✓ Redis已启动${NC}"
else
    echo -e "${RED}✗ Redis启动失败${NC}"
fi

# 检查端口占用
echo -e "\n${YELLOW}3. 检查端口8000...${NC}"
if lsof -i :8000 >/dev/null 2>&1; then
    echo -e "${RED}端口8000已被占用${NC}"
    echo "是否要终止占用进程？(y/n)"
    read -r answer
    if [ "$answer" = "y" ]; then
        sudo kill -9 $(lsof -t -i:8000) 2>/dev/null
        echo -e "${GREEN}✓ 已清理端口${NC}"
    else
        echo "请手动处理或使用其他端口"
        exit 1
    fi
else
    echo -e "${GREEN}✓ 端口8000可用${NC}"
fi

# 启动后端服务
echo -e "\n${YELLOW}4. 启动后端服务...${NC}"
cd backend
source ../backend_venv/bin/activate

echo -e "${GREEN}服务启动中...${NC}"
echo -e "${YELLOW}API文档地址: http://localhost:8000/docs${NC}"
echo -e "${YELLOW}按 Ctrl+C 停止服务${NC}\n"

python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
