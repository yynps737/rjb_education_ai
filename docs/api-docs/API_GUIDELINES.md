# API开发指南

## 路由定义规范

### 1. URL末尾斜杠规则

FastAPI对URL末尾的斜杠非常敏感。为了避免307重定向问题，请遵循以下规则：

```python
# ✅ 正确 - 不带斜杠
@router.get("")  # 用于列表端点
@router.post("")  # 用于创建端点

# ❌ 错误 - 会导致307重定向
@router.get("/")
@router.post("/")
```

### 2. 路由示例

```python
# 资源列表
@router.get("")  # GET /api/users
async def get_users():
    pass

# 创建资源
@router.post("")  # POST /api/users
async def create_user():
    pass

# 获取单个资源
@router.get("/{user_id}")  # GET /api/users/123
async def get_user(user_id: int):
    pass

# 更新资源
@router.put("/{user_id}")  # PUT /api/users/123
async def update_user(user_id: int):
    pass

# 删除资源
@router.delete("/{user_id}")  # DELETE /api/users/123
async def delete_user(user_id: int):
    pass
```

## 错误处理规范

### 1. 使用统一的错误处理器

```python
from utils.error_handler import AppError, not_found, permission_denied

# 资源未找到
if not resource:
    raise not_found("课程")

# 权限不足
if user.role != required_role:
    raise AppError("PERMISSION_DENIED", status_code=403)

# 业务逻辑错误
if already_enrolled:
    raise AppError("ALREADY_ENROLLED")
```

### 2. 错误代码列表

| 错误代码 | 说明 | HTTP状态码 |
|---------|------|-----------|
| USER_NOT_FOUND | 用户不存在 | 404 |
| INVALID_CREDENTIALS | 用户名或密码错误 | 401 |
| USER_EXISTS | 用户名已被注册 | 400 |
| EMAIL_EXISTS | 邮箱已被注册 | 400 |
| PERMISSION_DENIED | 权限不足 | 403 |
| NOT_AUTHENTICATED | 未认证 | 401 |
| COURSE_NOT_FOUND | 课程不存在 | 404 |
| ALREADY_ENROLLED | 已经注册了此课程 | 400 |
| NOT_ENROLLED | 未注册此课程 | 400 |

### 3. 错误响应格式

```json
{
    "success": false,
    "error": {
        "code": "USER_EXISTS",
        "message": "用户名已被注册",
        "timestamp": "2025-01-01T00:00:00.000Z"
    }
}
```

## 认证与授权

### 1. 使用装饰器进行角色验证

```python
from utils.auth import require_role
from models.user import UserRole

# 单个角色
@router.get("/admin-only")
async def admin_endpoint(
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    pass

# 多个角色
@router.get("/teacher-or-admin")
async def teacher_admin_endpoint(
    current_user: User = Depends(require_role([UserRole.TEACHER, UserRole.ADMIN]))
):
    pass
```

### 2. Token管理

- Access Token有效期：30分钟
- Refresh Token有效期：7天
- 使用Bearer认证方式

```bash
# 请求示例
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/protected
```

## 分页规范

### 1. 请求参数

- `page`: 页码，从1开始
- `page_size`: 每页数量，默认20，最大100

### 2. 响应格式

```json
{
    "success": true,
    "data": {
        "items": [...],
        "pagination": {
            "total": 100,
            "page": 1,
            "page_size": 20,
            "total_pages": 5
        }
    }
}
```

## 文件上传

### 1. 使用文件验证器

```python
from utils.file_security import file_validator

# 上传文档
allowed_categories = ["document", "presentation", "spreadsheet"]
relative_path, file_info = await file_validator.save_upload_file(
    file,
    allowed_categories=allowed_categories,
    subfolder=f"teacher_{current_user.id}"
)
```

### 2. 支持的文件类型

- 文档：pdf, doc, docx, txt, md
- 演示文稿：ppt, pptx
- 表格：xls, xlsx, csv
- 图片：jpg, jpeg, png, gif, webp

## AI功能接口

### 1. 课程大纲生成

```python
POST /api/teacher/course/generate-outline
{
    "course_name": "Python基础",
    "duration_minutes": 45,
    "grade_level": "大学一年级",
    "knowledge_points": ["变量", "数据类型"],
    "teaching_objectives": ["理解基本概念"]
}
```

### 2. 题目生成

```python
POST /api/teacher/course/generate-questions
{
    "knowledge_content": "知识点内容",
    "question_types": ["single_choice", "short_answer"],
    "num_questions": 5,
    "difficulty": 3  # 1-5
}
```

## 测试建议

1. 使用提供的测试脚本进行API测试
2. 确保所有错误情况都有适当的错误消息
3. 测试不同角色的权限控制
4. 验证分页功能的边界情况