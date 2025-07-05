# 智能教育平台 (Education AI Assistant)

基于千问API的智能教育平台，为教师和学生提供AI驱动的教学辅助功能。

## 🚀 功能特点

### 核心功能
- **智能题目生成**：支持10种题型，基于布鲁姆认知层次分类
- **自动评分系统**：客观题精确判断，主观题语义理解评分
- **知识库问答**：基于RAG技术的智能答疑系统
- **学习进度跟踪**：多维度学习数据分析
- **个性化推荐**：自适应学习内容推荐

### 用户角色
- **学生**：课程学习、作业提交、智能答疑
- **教师**：课程管理、作业发布、学生管理
- **管理员**：系统管理、数据分析、用户管理

## 🛠️ 技术栈

- **后端框架**：FastAPI + SQLAlchemy
- **数据库**：PostgreSQL + Redis
- **AI服务**：阿里云千问API (通义千问)
- **向量数据库**：ChromaDB
- **认证**：JWT
- **文档处理**：支持PDF、Word、PPT等多种格式

## 📋 系统要求

- Python 3.8+
- PostgreSQL 12+
- Redis 6+
- Docker & Docker Compose

## 🔧 快速开始

### 1. 克隆项目
```bash
git clone https://github.com/yynps737/rjb_education_ai.git
cd rjb_education_ai
```

### 2. 环境配置
创建 `.env` 文件：
```env
# 基础配置
ENVIRONMENT=development
SECRET_KEY=your-secret-key

# 数据库
DATABASE_URL=postgresql://user:password@localhost:5433/education_db

# Redis
REDIS_URL=redis://localhost:6380/0

# 阿里云API
DASHSCOPE_API_KEY=your-dashscope-api-key
```

### 3. 启动服务
```bash
# 启动数据库服务
docker-compose up -d

# 创建虚拟环境
python -m venv backend_venv
source backend_venv/bin/activate  # Linux/Mac
# backend_venv\Scripts\activate  # Windows

# 安装依赖
cd backend
pip install -r requirements.txt

# 启动应用
python main.py
```

### 4. 访问应用
- API文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

## 📚 API使用示例

### 登录
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"student","password":"student123"}'
```

### 智能问答
```bash
curl -X POST "http://localhost:8000/api/knowledge/ask" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"什么是机器学习？"}'
```

## 🏗️ 项目结构

```
backend/
├── api/            # API路由
│   ├── admin/      # 管理员接口
│   ├── student/    # 学生接口
│   └── teacher/    # 教师接口
├── core/           # 核心功能
│   ├── ai/         # AI集成
│   ├── llm/        # 大语言模型
│   └── rag/        # RAG系统
├── models/         # 数据模型
├── services/       # 业务服务
├── utils/          # 工具函数
└── main.py         # 入口文件
```

## 🔒 安全特性

- JWT认证机制
- 密码bcrypt加密
- 文件上传安全检查
- SQL注入防护
- 敏感信息日志过滤

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 👥 联系方式

- GitHub: [@yynps737](https://github.com/yynps737)
- 项目地址: https://github.com/yynps737/rjb_education_ai

---

⭐ 如果这个项目对你有帮助，请给我们一个Star！