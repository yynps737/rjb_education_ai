# 测试文档 (Testing Guide)

## 1. 测试策略概述

### 1.1 测试目标
- **功能正确性**：确保所有功能按预期工作
- **性能要求**：满足并发和响应时间要求
- **安全性**：防范常见安全威胁
- **可靠性**：系统稳定运行
- **兼容性**：跨平台和浏览器兼容

### 1.2 测试级别
```
┌─────────────────────────────────────┐
│           端到端测试 (E2E)           │
├─────────────────────────────────────┤
│           集成测试                   │
├─────────────────────────────────────┤
│           单元测试                   │
└─────────────────────────────────────┘
```

### 1.3 测试覆盖率目标
- 单元测试覆盖率：≥ 80%
- 集成测试覆盖率：≥ 70%
- 关键路径覆盖率：100%

## 2. 测试环境

### 2.1 环境配置
| 环境 | 用途 | 配置 |
|-----|------|------|
| 开发环境 | 开发自测 | 本地Docker |
| 测试环境 | 功能测试 | 独立服务器 |
| 预发布环境 | 验收测试 | 生产镜像 |
| 生产环境 | 线上运行 | 高可用集群 |

### 2.2 测试数据准备
```python
# 测试数据工厂
class TestDataFactory:
    @staticmethod
    def create_test_user(role="student"):
        return {
            "username": f"test_{role}_{uuid.uuid4().hex[:6]}",
            "password": "Test123456!",
            "email": f"test_{uuid.uuid4().hex[:6]}@test.com",
            "role": role
        }
    
    @staticmethod
    def create_test_course():
        return {
            "title": f"测试课程_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "description": "自动化测试创建的课程",
            "subject": "计算机科学"
        }
```

## 3. 单元测试

### 3.1 测试框架
- **框架选择**：pytest
- **Mock工具**：pytest-mock
- **覆盖率工具**：pytest-cov

### 3.2 单元测试示例

#### 3.2.1 服务层测试
```python
# test_user_service.py
import pytest
from unittest.mock import Mock, patch
from services.user_service import UserService
from models.user import User

class TestUserService:
    @pytest.fixture
    def user_service(self, db_session):
        return UserService(db_session)
    
    @pytest.fixture
    def mock_user(self):
        user = Mock(spec=User)
        user.id = 1
        user.username = "test_user"
        user.email = "test@example.com"
        user.role = "student"
        return user
    
    def test_create_user_success(self, user_service, db_session):
        # 准备测试数据
        user_data = {
            "username": "new_user",
            "email": "new@example.com",
            "password": "Test123456!"
        }
        
        # 执行测试
        user = user_service.create_user(user_data)
        
        # 验证结果
        assert user.username == "new_user"
        assert user.email == "new@example.com"
        assert user.check_password("Test123456!")
        
        # 验证数据库操作
        db_user = db_session.query(User).filter_by(username="new_user").first()
        assert db_user is not None
    
    def test_create_duplicate_user(self, user_service, mock_user, db_session):
        # 模拟已存在的用户
        db_session.query(User).filter_by().first.return_value = mock_user
        
        # 测试创建重复用户
        with pytest.raises(ValueError, match="用户名已存在"):
            user_service.create_user({
                "username": "test_user",
                "email": "another@example.com",
                "password": "Test123456!"
            })
```

#### 3.2.2 工具函数测试
```python
# test_validators.py
import pytest
from utils.validators import validate_email, validate_password

class TestValidators:
    @pytest.mark.parametrize("email,expected", [
        ("user@example.com", True),
        ("user.name@example.com", True),
        ("user@sub.example.com", True),
        ("invalid.email", False),
        ("@example.com", False),
        ("user@", False),
        ("", False),
        (None, False),
    ])
    def test_validate_email(self, email, expected):
        assert validate_email(email) == expected
    
    @pytest.mark.parametrize("password,expected", [
        ("Test123456!", True),      # 符合所有要求
        ("test123456!", False),     # 缺少大写字母
        ("TEST123456!", False),     # 缺少小写字母
        ("TestPassword!", False),   # 缺少数字
        ("Test123456", False),      # 缺少特殊字符
        ("Test1!", False),          # 长度不足
        ("", False),
        (None, False),
    ])
    def test_validate_password(self, password, expected):
        assert validate_password(password) == expected
```

### 3.3 AI服务测试
```python
# test_ai_service.py
import pytest
from unittest.mock import Mock, patch, AsyncMock
from services.ai_service import AIService

class TestAIService:
    @pytest.fixture
    def ai_service(self):
        return AIService()
    
    @pytest.fixture
    def mock_llm_response(self):
        return {
            "choices": [{
                "message": {
                    "content": "递归函数是调用自身的函数..."
                }
            }]
        }
    
    @pytest.mark.asyncio
    async def test_generate_answer(self, ai_service, mock_llm_response):
        with patch.object(ai_service.client, 'generate', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = mock_llm_response
            
            answer = await ai_service.generate_answer("什么是递归函数？")
            
            assert "递归函数" in answer
            mock_generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_questions(self, ai_service):
        with patch.object(ai_service.client, 'generate', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = {
                "choices": [{
                    "message": {
                        "content": '''[
                            {
                                "type": "single_choice",
                                "content": "Python中哪个是合法的变量名？",
                                "options": ["1var", "var_1", "var-1", "var 1"],
                                "answer": 1,
                                "explanation": "变量名可以包含字母、数字和下划线"
                            }
                        ]'''
                    }
                }]
            }
            
            questions = await ai_service.generate_questions(
                knowledge="Python变量命名规则",
                question_types=["single_choice"],
                count=1
            )
            
            assert len(questions) == 1
            assert questions[0]["type"] == "single_choice"
            assert len(questions[0]["options"]) == 4
```

## 4. 集成测试

### 4.1 API集成测试
```python
# test_auth_api.py
import pytest
from fastapi.testclient import TestClient
from main import app

class TestAuthAPI:
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def test_user_data(self):
        return {
            "username": "integration_test_user",
            "password": "Test123456!",
            "email": "integration@test.com"
        }
    
    def test_user_registration_flow(self, client, test_user_data):
        # 1. 注册新用户
        response = client.post("/api/auth/register", json=test_user_data)
        assert response.status_code == 201
        assert response.json()["success"] is True
        
        # 2. 尝试重复注册
        response = client.post("/api/auth/register", json=test_user_data)
        assert response.status_code == 400
        assert "已存在" in response.json()["message"]
        
        # 3. 登录测试
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "access_token" in data
        assert "refresh_token" in data
        
        # 4. 使用token访问受保护资源
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        response = client.get("/api/users/me", headers=headers)
        assert response.status_code == 200
        assert response.json()["data"]["username"] == test_user_data["username"]
```

### 4.2 数据库集成测试
```python
# test_database_integration.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.base import Base
from models.user import User
from models.course import Course

class TestDatabaseIntegration:
    @pytest.fixture
    def db_session(self):
        # 使用测试数据库
        engine = create_engine("postgresql://test_user:test_pass@localhost:5433/test_db")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        yield session
        
        session.close()
        Base.metadata.drop_all(engine)
    
    def test_user_course_relationship(self, db_session):
        # 创建教师
        teacher = User(
            username="teacher_test",
            email="teacher@test.com",
            role="teacher"
        )
        teacher.set_password("Test123456!")
        db_session.add(teacher)
        db_session.commit()
        
        # 创建课程
        course = Course(
            title="测试课程",
            description="集成测试课程",
            teacher_id=teacher.id
        )
        db_session.add(course)
        db_session.commit()
        
        # 创建学生并注册课程
        student = User(
            username="student_test",
            email="student@test.com",
            role="student"
        )
        student.set_password("Test123456!")
        course.students.append(student)
        db_session.add(student)
        db_session.commit()
        
        # 验证关系
        assert course.teacher.username == "teacher_test"
        assert len(course.students) == 1
        assert course.students[0].username == "student_test"
        assert len(student.enrolled_courses) == 1
```

## 5. 端到端测试

### 5.1 Playwright自动化测试
```python
# test_e2e_student_workflow.py
import pytest
from playwright.sync_api import Page, expect

class TestStudentWorkflow:
    @pytest.fixture
    def authenticated_page(self, page: Page):
        # 登录流程
        page.goto("http://localhost:8000")
        page.fill("input[name='username']", "test_student")
        page.fill("input[name='password']", "Test123456!")
        page.click("button[type='submit']")
        expect(page).to_have_url("http://localhost:8000/dashboard")
        return page
    
    def test_complete_assignment(self, authenticated_page: Page):
        page = authenticated_page
        
        # 1. 导航到作业列表
        page.click("text=我的作业")
        expect(page).to_have_url("http://localhost:8000/assignments")
        
        # 2. 选择一个待完成的作业
        page.click("text=Python基础练习")
        
        # 3. 回答问题
        # 选择题
        page.click("label:has-text('B. def')")
        
        # 填空题
        page.fill("input[name='question_2']", "print")
        
        # 编程题
        code_editor = page.locator(".code-editor")
        code_editor.fill("""
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
        """)
        
        # 4. 提交作业
        page.click("button:has-text('提交作业')")
        
        # 5. 确认提交
        page.click("button:has-text('确认提交')")
        
        # 6. 验证提交成功
        expect(page.locator(".toast-success")).to_have_text("作业提交成功")
```

### 5.2 性能测试
```python
# test_performance.py
import asyncio
import aiohttp
import time
from statistics import mean, stdev

class TestPerformance:
    async def make_request(self, session, url, headers):
        start_time = time.time()
        async with session.get(url, headers=headers) as response:
            await response.json()
            return time.time() - start_time
    
    async def test_api_performance(self):
        url = "http://localhost:8000/api/courses"
        headers = {"Authorization": "Bearer test_token"}
        
        async with aiohttp.ClientSession() as session:
            # 预热
            await self.make_request(session, url, headers)
            
            # 并发测试
            tasks = []
            for _ in range(100):
                task = self.make_request(session, url, headers)
                tasks.append(task)
            
            response_times = await asyncio.gather(*tasks)
            
        # 分析结果
        avg_time = mean(response_times) * 1000  # 转换为毫秒
        std_dev = stdev(response_times) * 1000
        max_time = max(response_times) * 1000
        min_time = min(response_times) * 1000
        
        print(f"平均响应时间: {avg_time:.2f}ms")
        print(f"标准差: {std_dev:.2f}ms")
        print(f"最大响应时间: {max_time:.2f}ms")
        print(f"最小响应时间: {min_time:.2f}ms")
        
        # 断言性能要求
        assert avg_time < 200  # 平均响应时间小于200ms
        assert max_time < 1000  # 最大响应时间小于1秒
```

## 6. 安全测试

### 6.1 SQL注入测试
```python
# test_security_sql_injection.py
import pytest
from fastapi.testclient import TestClient

class TestSQLInjection:
    @pytest.mark.parametrize("malicious_input", [
        "' OR '1'='1",
        "'; DROP TABLE users; --",
        "' UNION SELECT * FROM users --",
        "admin'--",
        "' OR 1=1#",
    ])
    def test_sql_injection_prevention(self, client: TestClient, malicious_input):
        # 测试登录接口
        response = client.post("/api/auth/login", json={
            "username": malicious_input,
            "password": "any_password"
        })
        
        # 应该返回认证失败，而不是SQL错误
        assert response.status_code == 401
        assert "用户名或密码错误" in response.json()["message"]
        
        # 测试搜索接口
        response = client.get(f"/api/courses/search?q={malicious_input}")
        assert response.status_code in [200, 404]  # 正常响应，没有SQL错误
```

### 6.2 XSS测试
```python
# test_security_xss.py
class TestXSSPrevention:
    @pytest.mark.parametrize("xss_payload", [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "javascript:alert('XSS')",
        "<iframe src='javascript:alert(1)'></iframe>",
    ])
    def test_xss_prevention(self, client: TestClient, xss_payload, auth_headers):
        # 测试课程创建
        response = client.post("/api/teacher/courses", 
            json={
                "title": xss_payload,
                "description": f"Description with {xss_payload}"
            },
            headers=auth_headers
        )
        
        if response.status_code == 201:
            course_id = response.json()["data"]["id"]
            
            # 获取课程详情，验证内容被转义
            response = client.get(f"/api/courses/{course_id}")
            data = response.json()["data"]
            
            # 验证XSS载荷被转义或清理
            assert "<script>" not in data["title"]
            assert "javascript:" not in data["description"]
```

## 7. 自动化测试流程

### 7.1 CI/CD集成
```yaml
# .github/workflows/test.yml
name: Automated Testing

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: test_password
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Run unit tests
      run: |
        pytest tests/unit -v --cov=app --cov-report=xml
    
    - name: Run integration tests
      run: |
        pytest tests/integration -v
    
    - name: Run security tests
      run: |
        pytest tests/security -v
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### 7.2 测试报告生成
```python
# pytest.ini
[pytest]
addopts = 
    --html=reports/test_report.html
    --self-contained-html
    --cov=app
    --cov-report=html:reports/coverage
    --cov-report=term-missing
    --junit-xml=reports/junit.xml
    -v

testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

## 8. 测试数据管理

### 8.1 测试数据生成脚本
```python
# scripts/generate_test_data.py
import random
from faker import Faker
from datetime import datetime, timedelta

fake = Faker('zh_CN')

class TestDataGenerator:
    @staticmethod
    def generate_users(count=100):
        users = []
        for i in range(count):
            role = random.choice(['student', 'teacher'])
            users.append({
                'username': f"{role}_{fake.user_name()}_{i}",
                'email': fake.email(),
                'full_name': fake.name(),
                'role': role,
                'password': 'Test123456!'
            })
        return users
    
    @staticmethod
    def generate_courses(teacher_ids, count=20):
        subjects = ['数学', '物理', '化学', '生物', '计算机', '英语']
        courses = []
        for i in range(count):
            courses.append({
                'title': f"{random.choice(subjects)}{fake.sentence(nb_words=3)}",
                'description': fake.text(max_nb_chars=200),
                'teacher_id': random.choice(teacher_ids),
                'subject': random.choice(subjects)
            })
        return courses
```

## 9. 测试最佳实践

### 9.1 测试原则
1. **独立性**：每个测试应该独立运行
2. **可重复性**：测试结果应该一致
3. **快速性**：单元测试应该快速执行
4. **完整性**：覆盖正常和异常场景

### 9.2 测试命名规范
```python
# 测试命名示例
def test_should_create_user_when_valid_data_provided():
    pass

def test_should_raise_error_when_duplicate_username():
    pass

def test_should_return_404_when_course_not_found():
    pass
```

### 9.3 测试组织结构
```
tests/
├── unit/                    # 单元测试
│   ├── services/
│   ├── utils/
│   └── models/
├── integration/             # 集成测试
│   ├── api/
│   └── database/
├── e2e/                     # 端到端测试
├── performance/             # 性能测试
├── security/                # 安全测试
├── fixtures/                # 测试夹具
├── factories/               # 测试数据工厂
└── conftest.py             # pytest配置
```

## 10. 测试检查清单

### 10.1 发布前测试清单
- [ ] 所有单元测试通过
- [ ] 集成测试通过
- [ ] 代码覆盖率达标
- [ ] 性能测试通过
- [ ] 安全测试通过
- [ ] 兼容性测试完成
- [ ] 回归测试执行
- [ ] 用户验收测试

### 10.2 测试报告模板
```markdown
# 测试报告

## 测试概要
- 测试版本：v1.0.0
- 测试日期：2024-07-05
- 测试环境：预发布环境
- 测试人员：测试团队

## 测试结果
- 总用例数：500
- 通过数：495
- 失败数：5
- 通过率：99%

## 问题汇总
1. [BUG-001] 批量导入用户时的内存溢出
2. [BUG-002] 并发提交作业时的死锁问题

## 性能测试结果
- 平均响应时间：150ms
- QPS：1000
- 并发用户数：500

## 建议
- 优化批量导入逻辑
- 增加数据库连接池大小
```

---

*测试文档版本：v1.0.0 | 更新日期：2024年7月*