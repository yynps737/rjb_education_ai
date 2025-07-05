# 项目文档目录

## 目录结构

### api-docs/ - API相关文档
- `API_GUIDELINES.md` - API开发指南，包含路由规范、错误处理、认证授权等
- `API_FIXES_SUMMARY.md` - API修复历史记录和改进总结

### reports/ - 测试报告
- `API_TEST_REPORT.md` - API测试报告
- `api_test_report_*.txt` - 历史测试记录

### test-scripts/ - 测试脚本（备份）
- `test_api_simple.sh` - 简单API测试脚本
- `test_ai_endpoints.sh` - AI功能专项测试脚本

## 主要测试脚本

项目根目录保留了最新的完整测试脚本：
- `/test_all_apis.sh` - 完整的API测试脚本（推荐使用）

## 快速开始

1. 启动服务：
```bash
cd /home/kkb/RJB/backend
source ../backend_venv/bin/activate
python -m uvicorn main:app --reload
```

2. 运行测试：
```bash
cd /home/kkb/RJB
./test_all_apis.sh
```

3. 查看API文档：
- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)