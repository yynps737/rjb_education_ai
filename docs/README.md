# AI Education Assistant Platform - 文档中心

**作者**: Kisir  
**邮箱**: kikiboy1120@gmail.com  
**更新日期**: 2025-01-06

## 📚 文档目录

### 核心文档
- `ARCHITECTURE.md` - 系统架构设计文档
- `USER_GUIDE.md` - 用户使用手册
- `PROJECT_OVERVIEW.md` - 项目概览
- `FAQ.md` - 常见问题解答

### 技术文档
- `api/API_REFERENCE.md` - API接口参考文档
- `deployment/DEPLOYMENT_GUIDE.md` - 部署指南
- `development/DEVELOPMENT_GUIDE.md` - 开发指南
- `security/SECURITY_GUIDE.md` - 安全指南
- `maintenance/MAINTENANCE_GUIDE.md` - 维护指南
- `quality/TESTING_GUIDE.md` - 测试指南

### API相关
- `api-docs/API_GUIDELINES.md` - API开发规范
- `api-docs/API_FIXES_SUMMARY.md` - API修复历史

### 测试报告
- `reports/API_TEST_REPORT.md` - API测试报告

## 🚀 快速开始

### 1. 启动后端服务
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### 2. 启动前端服务
```bash
cd frontend
npm install
npm run dev
```

### 3. 访问应用
- **前端应用**: http://localhost:3000
- **API文档**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔑 默认账户

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |
| 教师 | teacher1 | password123 |
| 学生 | student1 | password123 |

## 📋 最新功能

### v1.1.0 (2025-01-06)
- ✨ 流式AI对话功能
- 🗑️ 知识库批量删除
- 🔐 精确权限控制
- 📚 智能引用追踪

## 📞 技术支持

如有问题，请通过以下方式联系：
- 📧 邮箱: kikiboy1120@gmail.com
- 🐛 Issues: [GitHub Issues](https://github.com/kisir/ai-education-assistant/issues)

---

**文档维护**: 本文档中心由 Kisir 维护，持续更新中...