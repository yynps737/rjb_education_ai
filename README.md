# AI Education Assistant Platform

<div align="center">
  <h3>基于大语言模型的智能教育辅助平台</h3>
  <p>An AI-powered education platform built with Next.js, FastAPI, and LLM integration</p>
  
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
  [![Node.js](https://img.shields.io/badge/Node.js-16+-green.svg)](https://nodejs.org/)
</div>

## 📋 目录

- [简介](#简介)
- [核心特性](#核心特性)
- [技术架构](#技术架构)
- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [API文档](#api文档)
- [部署指南](#部署指南)
- [开发指南](#开发指南)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

## 🎯 简介

AI Education Assistant Platform 是一个集成了大语言模型的智能教育平台，旨在通过人工智能技术提升教学质量和学习效率。平台支持多角色（学生、教师、管理员）访问，提供个性化学习体验、智能问答、自动评分等功能。

### 主要目标

- 🤖 **智能化教学** - 利用AI技术辅助教师进行课程设计和作业批改
- 📚 **个性化学习** - 基于学生数据提供定制化学习路径和内容推荐
- 📊 **数据驱动** - 通过学习数据分析帮助教师和学生优化教学策略
- 🔄 **实时互动** - 提供流式AI对话，增强学习体验

## ✨ 核心特性

### 🎓 教学管理
- **智能课程设计** - AI辅助生成课程大纲和教学计划
- **多样化作业系统** - 支持单选、多选、判断、填空、简答、论述、编程等题型
- **自动评分引擎** - 基于AI的作业自动批改和反馈
- **学习进度追踪** - 实时监控学生学习状态和进度

### 🤖 AI功能
- **智能问答系统** - 基于知识库的RAG（检索增强生成）问答
- **流式对话体验** - 实时流式输出，提供类ChatGPT的交互体验
- **知识库管理** - 支持文档上传、向量化存储、智能检索
- **个性化推荐** - 根据学习数据推荐相关内容

### 👥 多角色支持
- **学生端** - 课程学习、作业提交、AI助手、进度查看
- **教师端** - 课程管理、作业设计、学生管理、数据分析
- **管理员端** - 用户管理、系统配置、全局统计、日志监控

### 🛡️ 安全与性能
- **JWT认证机制** - 安全的用户认证和授权
- **角色权限控制** - 细粒度的访问控制
- **数据加密存储** - 敏感信息加密保护
- **响应式设计** - 支持PC、平板、手机多端访问

## 🏗️ 技术架构

### 后端技术栈
- **Web框架**: FastAPI (高性能异步框架)
- **数据库**: PostgreSQL + SQLAlchemy ORM
- **缓存**: Redis (会话管理和数据缓存)
- **向量数据库**: ChromaDB (知识库向量存储)
- **AI模型**: 阿里云千问 (通过DashScope API)
- **认证**: JWT + Passlib
- **文档处理**: PyPDF2, python-docx, python-pptx

### 前端技术栈
- **框架**: Next.js 15 + React 19
- **语言**: TypeScript
- **样式**: Tailwind CSS + Radix UI
- **状态管理**: Zustand
- **数据请求**: Axios + React Query
- **表单处理**: React Hook Form + Zod
- **动画**: Framer Motion
- **图表**: Recharts

### 基础设施
- **容器化**: Docker + Docker Compose
- **Web服务器**: Uvicorn
- **进程管理**: Gunicorn
- **反向代理**: Nginx (可选)

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Node.js 16+
- PostgreSQL 12+
- Redis 6+
- Git

### 1. 克隆仓库

```bash
git clone https://github.com/kisir/ai-education-assistant.git
cd ai-education-assistant
```

### 2. 后端配置

创建环境配置文件 `backend/.env`:

```env
# 数据库配置
DATABASE_URL=postgresql://education_user:your_password@localhost:5432/education_db

# Redis配置
REDIS_URL=redis://localhost:6379/0

# AI服务配置 (阿里云千问)
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx

# 安全配置
SECRET_KEY=your-secret-key-here-at-least-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 环境配置
ENVIRONMENT=development
```

安装依赖并启动：

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### 3. 前端配置

创建环境配置文件 `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

安装依赖并启动：

```bash
cd frontend
npm install
npm run dev
```

### 4. 访问应用

- 前端应用: http://localhost:3000
- 后端API文档: http://localhost:8000/docs
- 数据库管理: 使用 pgAdmin 或其他 PostgreSQL 客户端

### 默认账户

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |
| 教师 | teacher1 | password123 |
| 学生 | student1 | password123 |

## 📁 项目结构

```
ai-education-assistant/
├── backend/                # 后端服务
│   ├── api/               # API路由
│   │   ├── admin/         # 管理员接口
│   │   ├── student/       # 学生接口
│   │   ├── teacher/       # 教师接口
│   │   ├── auth.py        # 认证接口
│   │   └── knowledge.py   # 知识库接口
│   ├── core/              # 核心功能
│   │   ├── ai/           # AI相关功能
│   │   ├── llm/          # LLM客户端
│   │   └── vector_db/    # 向量数据库
│   ├── models/            # 数据模型
│   ├── services/          # 业务逻辑
│   ├── utils/             # 工具函数
│   └── main.py           # 应用入口
├── frontend/              # 前端应用
│   ├── src/
│   │   ├── app/          # Next.js应用路由
│   │   ├── components/   # React组件
│   │   ├── hooks/        # 自定义Hooks
│   │   ├── lib/          # 工具库
│   │   └── stores/       # 状态管理
│   └── public/           # 静态资源
├── docs/                  # 项目文档
└── docker-compose.yml     # Docker编排配置
```

## 📚 API文档

后端启动后，可以通过以下地址访问完整的API文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

主要API模块：

- `/api/auth` - 认证相关
- `/api/knowledge` - 知识库管理
- `/api/admin/*` - 管理员功能
- `/api/student/*` - 学生功能
- `/api/teacher/*` - 教师功能

详细API文档请参考 [API Reference](docs/api/API_REFERENCE.md)

## 🚢 部署指南

### Docker Compose 部署

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 生产环境配置

1. 修改 `.env` 文件中的配置
2. 设置强密码和密钥
3. 配置 SSL 证书
4. 设置反向代理 (Nginx)
5. 配置日志和监控

详细部署指南请参考 [Deployment Guide](docs/deployment/DEPLOYMENT_GUIDE.md)

## 💻 开发指南

### 开发环境设置

1. 安装开发依赖
2. 配置 IDE (推荐 VS Code)
3. 设置代码格式化工具
4. 配置 Git hooks

### 代码规范

- Python: 遵循 PEP 8
- TypeScript: 使用 ESLint + Prettier
- Git: 使用 Conventional Commits

详细开发指南请参考 [Development Guide](docs/development/DEVELOPMENT_GUIDE.md)

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出新功能建议！

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 👨‍💻 作者

**Kisir**

- Email: kikiboy1120@gmail.com
- GitHub: [@kisir](https://github.com/kisir)

## 🙏 致谢

感谢以下开源项目的支持：

- [FastAPI](https://fastapi.tiangolo.com/)
- [Next.js](https://nextjs.org/)
- [Radix UI](https://www.radix-ui.com/)
- [ChromaDB](https://www.trychroma.com/)
- [DashScope](https://dashscope.aliyun.com/)

---

<div align="center">
  <p>如果这个项目对你有帮助，请给一个 ⭐️ Star！</p>
</div>