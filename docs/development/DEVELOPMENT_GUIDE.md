# 开发指南 (Development Guide)

## 1. 开发环境搭建

### 1.1 系统要求
- Python 3.8-3.11
- Node.js 16+ (前端开发)
- Git 2.20+
- Docker & Docker Compose
- VS Code / PyCharm (推荐IDE)

### 1.2 快速开始
```bash
# 1. 克隆项目
git clone https://github.com/yynps737/rjb_education_ai.git
cd rjb_education_ai

# 2. 创建虚拟环境
python -m venv backend_venv
source backend_venv/bin/activate  # Linux/Mac
# backend_venv\Scripts\activate  # Windows

# 3. 安装依赖
cd backend
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 开发依赖

# 4. 启动本地服务
docker-compose up -d  # 启动数据库和Redis
python main.py  # 启动应用
```

### 1.3 IDE配置

#### VS Code推荐扩展
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.black-formatter",
    "charliermarsh.ruff",
    "tamasfe.even-better-toml",
    "redhat.vscode-yaml",
    "ms-azuretools.vscode-docker"
  ]
}
```

#### PyCharm配置
1. 设置Python解释器为虚拟环境
2. 启用Django支持（虽然使用FastAPI，但有助于模板支持）
3. 配置代码风格为PEP 8
4. 启用类型检查

## 2. 项目结构

### 2.1 目录结构说明
```
backend/
├── api/                # API端点定义
│   ├── admin/         # 管理员接口
│   ├── student/       # 学生接口
│   └── teacher/       # 教师接口
├── core/              # 核心功能模块
│   ├── ai/           # AI集成
│   ├── llm/          # 大语言模型客户端
│   └── rag/          # RAG系统实现
├── models/            # 数据模型
├── services/          # 业务逻辑
├── utils/            # 工具函数
├── tasks/            # 异步任务
└── tests/            # 测试代码
```

### 2.2 命名规范
- **文件名**: 小写下划线 `user_service.py`
- **类名**: 大驼峰 `UserService`
- **函数名**: 小写下划线 `get_user_by_id`
- **常量**: 大写下划线 `MAX_UPLOAD_SIZE`
- **私有成员**: 前缀下划线 `_private_method`

## 3. 编码规范

### 3.1 Python代码规范
遵循PEP 8和Google Python Style Guide

```python
"""模块文档字符串

详细描述模块功能
"""
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from models.user import User
from utils.auth import get_current_user


class UserService:
    """用户服务类
    
    处理用户相关的业务逻辑
    """
    
    def __init__(self, db: Session):
        """初始化用户服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """根据ID获取用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            User对象或None
            
        Raises:
            HTTPException: 当用户不存在时
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        return user
```

### 3.2 Git提交规范
采用Conventional Commits规范

```bash
# 格式
<type>(<scope>): <subject>

# 类型
feat: 新功能
fix: 修复bug
docs: 文档更新
style: 代码格式调整
refactor: 重构
perf: 性能优化
test: 测试相关
chore: 构建或辅助工具变动

# 示例
feat(auth): 添加JWT刷新令牌功能
fix(api): 修复用户注册时的验证错误
docs(readme): 更新部署说明
```

### 3.3 代码审查清单
- [ ] 代码符合项目规范
- [ ] 有适当的错误处理
- [ ] 有必要的日志记录
- [ ] 有单元测试覆盖
- [ ] 文档和注释完整
- [ ] 无安全漏洞
- [ ] 性能考虑充分

## 4. 数据库开发

### 4.1 模型定义规范
```python
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from models.base import BaseModel


class Course(BaseModel):
    """课程模型
    
    存储课程基本信息和关联关系
    """
    __tablename__ = "courses"
    
    # 基本字段
    title = Column(String(200), nullable=False, comment="课程标题")
    description = Column(Text, comment="课程描述")
    
    # 外键关系
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 关系定义
    teacher = relationship("User", back_populates="courses")
    chapters = relationship("Chapter", back_populates="course", cascade="all, delete-orphan")
    
    # 索引定义
    __table_args__ = (
        Index("idx_course_teacher", "teacher_id"),
        Index("idx_course_created", "created_at"),
    )
```

### 4.2 数据库迁移
```bash
# 创建迁移
alembic revision --autogenerate -m "添加课程评分字段"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

### 4.3 查询优化原则
1. 使用索引优化查询
2. 避免N+1查询问题
3. 使用适当的eager loading
4. 大数据量使用分页
5. 复杂查询考虑使用原生SQL

## 5. API开发

### 5.1 路由定义规范
```python
from fastapi import APIRouter, Depends, Query
from typing import List

router = APIRouter(prefix="/courses", tags=["课程管理"])


@router.get("", response_model=List[CourseResponse])
async def get_courses(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    subject: Optional[str] = Query(None, description="学科筛选"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取课程列表
    
    支持分页和学科筛选
    """
    service = CourseService(db)
    return await service.get_courses(
        page=page,
        page_size=page_size,
        subject=subject,
        user=current_user
    )
```

### 5.2 请求验证
```python
from pydantic import BaseModel, validator, EmailStr
from typing import Optional


class UserCreateRequest(BaseModel):
    """用户创建请求模型"""
    
    username: str = Field(..., min_length=3, max_length=20, regex="^[a-zA-Z0-9_]+$")
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=50)
    
    @validator('password')
    def validate_password(cls, v):
        """验证密码强度"""
        if not any(char.isdigit() for char in v):
            raise ValueError('密码必须包含数字')
        if not any(char.isupper() for char in v):
            raise ValueError('密码必须包含大写字母')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "username": "student001",
                "email": "student@example.com",
                "password": "MyPass123",
                "full_name": "张三"
            }
        }
```

### 5.3 错误处理
```python
from fastapi import HTTPException
from utils.response import StandardResponse


class BusinessException(Exception):
    """业务异常基类"""
    def __init__(self, message: str, code: str = "BUSINESS_ERROR"):
        self.message = message
        self.code = code


@app.exception_handler(BusinessException)
async def business_exception_handler(request: Request, exc: BusinessException):
    """业务异常处理器"""
    return StandardResponse.error(
        message=exc.message,
        code=exc.code,
        status_code=400
    )


# 使用示例
if not course.is_active:
    raise BusinessException("课程已下架", code="COURSE_INACTIVE")
```

## 6. AI功能开发

### 6.1 Prompt模板管理
```python
class PromptTemplates:
    """Prompt模板管理"""
    
    QUESTION_GENERATION = """
    基于以下知识内容生成{num_questions}道{question_type}题目：
    
    知识内容：
    {content}
    
    要求：
    1. 难度等级：{difficulty}
    2. 认知层次：{bloom_level}
    3. 每道题包含：题目、选项（如适用）、答案、解析
    4. 输出JSON格式
    
    输出格式：
    {{
        "questions": [
            {{
                "content": "题目内容",
                "options": ["选项A", "选项B", "选项C", "选项D"],
                "answer": 0,
                "explanation": "详细解析"
            }}
        ]
    }}
    """
    
    @classmethod
    def get_question_prompt(cls, **kwargs) -> str:
        """获取题目生成prompt"""
        return cls.QUESTION_GENERATION.format(**kwargs)
```

### 6.2 AI服务封装
```python
class AIService:
    """AI服务封装"""
    
    def __init__(self):
        self.client = QwenClient()
        self.cache = RedisCache()
    
    async def generate_with_cache(
        self,
        prompt: str,
        cache_key: str,
        ttl: int = 3600,
        **kwargs
    ) -> str:
        """带缓存的生成"""
        # 检查缓存
        cached = await self.cache.get(cache_key)
        if cached:
            return cached
            
        # 生成内容
        response = await self.client.generate(prompt, **kwargs)
        
        # 存入缓存
        await self.cache.set(cache_key, response, ttl=ttl)
        
        return response
```

## 7. 测试开发

### 7.1 单元测试
```python
import pytest
from unittest.mock import Mock, patch
from services.user_service import UserService


class TestUserService:
    """用户服务测试"""
    
    @pytest.fixture
    def service(self, db_session):
        """创建服务实例"""
        return UserService(db_session)
    
    @pytest.fixture
    def mock_user(self):
        """模拟用户数据"""
        return User(
            id=1,
            username="test_user",
            email="test@example.com"
        )
    
    async def test_get_user_by_id_success(self, service, mock_user, db_session):
        """测试成功获取用户"""
        # 准备数据
        db_session.add(mock_user)
        db_session.commit()
        
        # 执行测试
        user = await service.get_user_by_id(1)
        
        # 验证结果
        assert user is not None
        assert user.username == "test_user"
    
    async def test_get_user_by_id_not_found(self, service):
        """测试用户不存在的情况"""
        with pytest.raises(HTTPException) as exc_info:
            await service.get_user_by_id(999)
        
        assert exc_info.value.status_code == 404
```

### 7.2 集成测试
```python
from fastapi.testclient import TestClient
from main import app


class TestAuthAPI:
    """认证API测试"""
    
    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)
    
    def test_login_success(self, client, test_user):
        """测试登录成功"""
        response = client.post("/api/auth/login", json={
            "username": test_user.username,
            "password": "test_password"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data["data"]
        assert data["data"]["user"]["username"] == test_user.username
```

### 7.3 性能测试
```python
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor


async def performance_test():
    """API性能测试"""
    url = "http://localhost:8000/api/courses"
    headers = {"Authorization": "Bearer token"}
    
    async def make_request():
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                return await response.json()
    
    # 并发测试
    start_time = time.time()
    tasks = [make_request() for _ in range(100)]
    await asyncio.gather(*tasks)
    
    elapsed = time.time() - start_time
    print(f"100个请求耗时: {elapsed:.2f}秒")
    print(f"QPS: {100/elapsed:.2f}")
```

## 8. 性能优化

### 8.1 数据库优化
```python
# 使用连接池
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,
    pool_recycle=3600
)

# 批量操作
def bulk_create_users(users_data: List[dict]):
    """批量创建用户"""
    db.bulk_insert_mappings(User, users_data)
    db.commit()

# 使用原生SQL提升性能
def get_course_statistics(course_id: int):
    """获取课程统计信息"""
    sql = """
    SELECT 
        COUNT(DISTINCT uc.user_id) as student_count,
        AVG(s.score) as avg_score,
        COUNT(DISTINCT a.id) as assignment_count
    FROM courses c
    LEFT JOIN user_courses uc ON c.id = uc.course_id
    LEFT JOIN assignments a ON c.id = a.course_id
    LEFT JOIN submissions s ON a.id = s.assignment_id
    WHERE c.id = :course_id
    GROUP BY c.id
    """
    return db.execute(text(sql), {"course_id": course_id}).first()
```

### 8.2 缓存策略
```python
from functools import lru_cache
from utils.cache import redis_cache


class CacheService:
    """缓存服务"""
    
    @redis_cache(ttl=300)
    async def get_hot_courses(self, limit: int = 10):
        """获取热门课程（5分钟缓存）"""
        return await self._fetch_hot_courses(limit)
    
    @lru_cache(maxsize=128)
    def get_question_template(self, question_type: str):
        """获取题目模板（内存缓存）"""
        return self._load_template(question_type)
    
    async def invalidate_course_cache(self, course_id: int):
        """失效课程相关缓存"""
        keys = [
            f"course:{course_id}",
            f"course:{course_id}:students",
            f"course:{course_id}:assignments"
        ]
        await redis_client.delete(*keys)
```

### 8.3 异步优化
```python
import asyncio
from typing import List


async def process_assignments_parallel(assignments: List[Assignment]):
    """并行处理作业"""
    tasks = []
    for assignment in assignments:
        task = asyncio.create_task(process_single_assignment(assignment))
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 处理异常
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"处理作业 {assignments[i].id} 失败: {result}")
    
    return [r for r in results if not isinstance(r, Exception)]
```

## 9. 安全开发

### 9.1 输入验证
```python
from utils.validators import sanitize_html, validate_file_type


class SecurityMiddleware:
    """安全中间件"""
    
    async def validate_input(self, request: Request):
        """验证输入"""
        # SQL注入防护（使用ORM参数化查询）
        # XSS防护
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.json()
            for key, value in body.items():
                if isinstance(value, str):
                    body[key] = sanitize_html(value)
        
        # 文件上传验证
        if "file" in request.headers.get("content-type", ""):
            # 验证文件类型、大小等
            pass
```

### 9.2 权限控制
```python
from functools import wraps
from typing import List


def require_permissions(*permissions: str):
    """权限装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(status_code=401, detail="未认证")
            
            user_permissions = get_user_permissions(current_user)
            for permission in permissions:
                if permission not in user_permissions:
                    raise HTTPException(
                        status_code=403,
                        detail=f"缺少权限: {permission}"
                    )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# 使用示例
@router.post("/courses")
@require_permissions("course.create")
async def create_course(...):
    pass
```

## 10. 调试技巧

### 10.1 日志调试
```python
import logging
from core.logging import get_logger

logger = get_logger(__name__)


def debug_function():
    """调试示例"""
    logger.debug("进入函数", extra={"function": "debug_function"})
    
    try:
        # 记录关键变量
        logger.debug(f"处理数据", extra={"data_count": len(data)})
        result = process_data(data)
        logger.info("处理成功", extra={"result": result})
    except Exception as e:
        logger.error("处理失败", exc_info=True, extra={"error": str(e)})
        raise
```

### 10.2 性能分析
```python
import cProfile
import pstats
from line_profiler import LineProfiler


def profile_function():
    """性能分析"""
    # 使用cProfile
    profiler = cProfile.Profile()
    profiler.enable()
    
    # 执行代码
    result = expensive_function()
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)  # 打印前10个耗时函数
    
    return result


# 使用装饰器进行行级分析
@profile
def expensive_function():
    """需要分析的函数"""
    pass
```

### 10.3 调试工具
```python
# 使用ipdb进行断点调试
import ipdb

def debug_code():
    data = get_data()
    ipdb.set_trace()  # 设置断点
    result = process_data(data)
    return result

# 使用VS Code调试配置
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "FastAPI Debug",
            "type": "python",
            "request": "launch",
            "module": "uvicorn",
            "args": [
                "main:app",
                "--reload",
                "--port", "8000"
            ],
            "jinja": true,
            "justMyCode": false
        }
    ]
}
```

## 11. 最佳实践

### 11.1 代码组织
1. 保持函数小而专注
2. 使用依赖注入
3. 避免循环导入
4. 合理使用设计模式

### 11.2 文档编写
1. 每个模块都要有文档字符串
2. 复杂逻辑要有行内注释
3. API要有完整的OpenAPI文档
4. 维护CHANGELOG

### 11.3 代码复审
1. 使用Pull Request工作流
2. 至少一人复审
3. 运行自动化测试
4. 检查代码覆盖率

---

*开发中遇到问题？查看FAQ或在GitHub提Issue*