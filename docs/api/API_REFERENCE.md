# AI Education Assistant Platform - API Reference

**作者**: Kisir  
**邮箱**: kikiboy1120@gmail.com  
**更新日期**: 2025-01-06

## 1. 概述

### 1.1 基础信息
- **基础URL**: `http://localhost:8000` (开发环境)
- **协议**: HTTP/HTTPS
- **数据格式**: JSON
- **字符编码**: UTF-8
- **API版本**: v1.0.0

### 1.2 认证方式
API使用Bearer Token认证方式：
```http
Authorization: Bearer <access_token>
```

### 1.3 通用响应格式
```json
{
  "success": true,
  "code": 200,
  "message": "Success",
  "data": {},
  "timestamp": "2024-07-05T12:00:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 1.4 错误码定义
| 错误码 | 描述 | 处理建议 |
|-------|------|---------|
| 200 | 成功 | - |
| 400 | 请求参数错误 | 检查请求参数 |
| 401 | 未授权 | 检查认证信息 |
| 403 | 禁止访问 | 检查权限 |
| 404 | 资源不存在 | 检查资源ID |
| 422 | 参数验证失败 | 查看错误详情 |
| 429 | 请求过于频繁 | 降低请求频率 |
| 500 | 服务器错误 | 联系技术支持 |

## 2. 认证接口

### 2.1 用户登录
**POST** `/api/auth/login`

#### 请求参数
```json
{
  "username": "string",
  "password": "string"
}
```

#### 响应示例
```json
{
  "success": true,
  "code": 200,
  "message": "登录成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 1800,
    "user": {
      "id": 1,
      "username": "teacher001",
      "email": "teacher@example.com",
      "full_name": "张老师",
      "role": "teacher"
    }
  }
}
```

### 2.2 刷新令牌
**POST** `/api/auth/refresh`

#### 请求参数
```json
{
  "refresh_token": "string"
}
```

### 2.3 用户注销
**POST** `/api/auth/logout`

## 3. 学生端接口

### 3.1 课程管理

#### 3.1.1 获取已注册课程列表
**GET** `/api/student/courses/enrolled`

##### 请求参数
| 参数名 | 类型 | 必填 | 描述 |
|-------|------|-----|------|
| page | integer | 否 | 页码，默认1 |
| page_size | integer | 否 | 每页数量，默认20 |
| status | string | 否 | 课程状态：active/completed |

##### 响应示例
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "title": "Python编程基础",
      "description": "从零开始学习Python",
      "teacher": {
        "id": 10,
        "name": "李老师"
      },
      "progress": 65.5,
      "next_lesson": {
        "id": 15,
        "title": "函数与模块"
      },
      "enrolled_at": "2024-06-01T08:00:00Z"
    }
  ],
  "meta": {
    "pagination": {
      "total": 5,
      "page": 1,
      "page_size": 20,
      "total_pages": 1
    }
  }
}
```

#### 3.1.2 获取课程详情
**GET** `/api/student/courses/{course_id}`

### 3.2 作业管理

#### 3.2.1 获取作业列表
**GET** `/api/student/assignments`

##### 请求参数
| 参数名 | 类型 | 必填 | 描述 |
|-------|------|-----|------|
| course_id | integer | 否 | 课程ID |
| status | string | 否 | pending/submitted/graded |

#### 3.2.2 提交作业
**POST** `/api/student/assignments/{assignment_id}/submit`

##### 请求体
```json
{
  "answers": [
    {
      "question_id": 1,
      "content": "答案内容"
    }
  ]
}
```

### 3.3 学习功能

#### 3.3.1 获取学习进度
**GET** `/api/student/learning/progress`

#### 3.3.2 智能问答
**POST** `/api/student/learning/ask`

##### 请求体
```json
{
  "question": "什么是递归函数？",
  "course_id": 1  // 可选
}
```

##### 响应示例
```json
{
  "success": true,
  "data": {
    "answer": "递归函数是指在函数定义中调用自身的函数...",
    "sources": [
      {
        "content": "Python函数进阶...",
        "metadata": {
          "title": "Python函数进阶",
          "document_id": 123
        },
        "relevance_score": 0.95
      }
    ],
    "confidence": 0.95
  }
}
```

#### 3.3.3 流式AI问答
**POST** `/api/student/learning/ask-stream`

##### 请求体
```json
{
  "question": "解释一下Python中的装饰器",
  "course_id": null
}
```

##### 响应格式 (Server-Sent Events)
```
data: {"type": "metadata", "sources": [{"content": "...", "metadata": {...}}]}

data: {"type": "content", "content": "装饰器是Python中"}

data: {"type": "content", "content": "一个强大的特性..."}

data: {"type": "done"}
```

## 4. 教师端接口

### 4.1 课程管理

#### 4.1.1 创建课程
**POST** `/api/teacher/courses`

##### 请求体
```json
{
  "title": "数据结构与算法",
  "description": "计算机科学基础课程",
  "subject": "计算机科学",
  "grade_level": "大学二年级",
  "tags": ["算法", "数据结构", "编程"]
}
```

#### 4.1.2 创建课程章节
**POST** `/api/teacher/courses/{course_id}/chapters`

### 4.2 作业管理

#### 4.2.1 创建作业
**POST** `/api/teacher/assignments`

##### 请求体
```json
{
  "course_id": 1,
  "title": "第三章课后作业",
  "description": "巩固函数知识",
  "due_date": "2024-07-15T23:59:59Z",
  "total_points": 100,
  "questions": [
    {
      "type": "single_choice",
      "content": "以下哪个是Python的关键字？",
      "options": ["function", "def", "define", "func"],
      "answer": 1,
      "points": 10
    }
  ]
}
```

#### 4.2.2 批改作业
**POST** `/api/teacher/assignments/{assignment_id}/grade`

### 4.3 智能辅助

#### 4.3.1 生成题目
**POST** `/api/teacher/ai/generate-questions`

##### 请求体
```json
{
  "knowledge_content": "Python函数的定义和使用",
  "question_types": ["single_choice", "short_answer", "coding"],
  "num_questions": 5,
  "difficulty": 3
}
```

##### 响应示例
```json
{
  "success": true,
  "data": {
    "questions": [
      {
        "type": "single_choice",
        "content": "Python中定义函数使用哪个关键字？",
        "options": ["function", "def", "define", "func"],
        "answer": 1,
        "explanation": "在Python中，使用def关键字来定义函数",
        "difficulty": 2,
        "points": 5,
        "knowledge_points": ["函数定义", "Python语法"]
      }
    ],
    "total": 5
  }
}
```

#### 4.3.2 生成课程大纲
**POST** `/api/teacher/ai/generate-outline`

## 5. 管理员接口

### 5.1 用户管理

#### 5.1.1 获取用户列表
**GET** `/api/admin/users`

#### 5.1.2 创建用户
**POST** `/api/admin/users`

### 5.2 系统管理

#### 5.2.1 系统健康检查
**GET** `/api/admin/system/health`

##### 响应示例
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "services": {
      "database": {
        "status": "healthy",
        "latency_ms": 5
      },
      "redis": {
        "status": "healthy",
        "latency_ms": 2
      },
      "ai_service": {
        "status": "healthy",
        "latency_ms": 150
      }
    },
    "system": {
      "cpu_usage": 35.2,
      "memory_usage": 62.8,
      "disk_usage": 45.1
    }
  }
}
```

### 5.3 数据分析

#### 5.3.1 平台概览
**GET** `/api/admin/analytics/overview`

## 6. 知识库接口

### 6.1 上传知识文档
**POST** `/api/knowledge/upload`

#### 请求格式
- Content-Type: `multipart/form-data`
- 最大文件大小: 10MB
- 支持格式: PDF, DOCX, PPTX, TXT, MD, JSON

#### 请求参数
```
file: 文件对象
course_id: 课程ID (可选)
description: 文档描述 (可选)
```

### 6.2 批量删除知识文档
**POST** `/api/knowledge/batch-delete`

#### 请求体
```json
{
  "ids": [1, 2, 3, 4, 5]
}
```

#### 响应示例
```json
{
  "success": true,
  "data": {
    "deleted": 5,
    "failed": 0,
    "details": []
  }
}
```

### 6.3 知识库问答
**POST** `/api/knowledge/ask`

#### 请求体
```json
{
  "query": "什么是机器学习？",
  "course_id": 1  // 可选
}
```

#### 响应示例
```json
{
  "success": true,
  "data": {
    "file_id": "file_20240705_123456",
    "filename": "课程资料.pdf",
    "size": 2048576,
    "mime_type": "application/pdf",
    "url": "/files/file_20240705_123456.pdf"
  }
}
```

## 7. 流式接口 (Server-Sent Events)

### 7.1 流式AI对话
**SSE** `/api/student/learning/ask-stream`

#### 消息类型
| 类型 | 描述 | 数据格式 |
|------|------|--------|
| metadata | 元数据信息 | `{"sources": [...]}` |
| content | 内容片段 | `{"content": "..."}` |
| done | 完成标识 | `{}` |
| error | 错误信息 | `{"error": "..."}` |

## 8. 速率限制

### 8.1 限制规则
| 端点类型 | 限制 | 时间窗口 |
|---------|------|---------|
| 认证接口 | 5次 | 1分钟 |
| 查询接口 | 100次 | 1分钟 |
| AI接口 | 10次 | 1分钟 |
| 上传接口 | 20次 | 1小时 |

### 8.2 限制响应头
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1625212800
```

## 9. SDK示例

### 9.1 Python SDK
```python
from education_ai import Client

client = Client(
    api_key="your_api_key",
    base_url="https://api.education-ai.com/v1"
)

# 登录
response = client.auth.login(
    username="teacher001",
    password="password123"
)

# 获取课程列表
courses = client.courses.list(page=1, page_size=20)

# AI生成题目
questions = client.ai.generate_questions(
    knowledge="Python函数",
    types=["single_choice", "coding"],
    count=5
)
```

### 9.2 JavaScript SDK
```javascript
import { EducationAI } from '@education-ai/sdk';

const client = new EducationAI({
  apiKey: 'your_api_key',
  baseURL: 'https://api.education-ai.com/v1'
});

// 异步调用示例
async function getCourses() {
  try {
    const courses = await client.courses.list({
      page: 1,
      pageSize: 20
    });
    console.log(courses);
  } catch (error) {
    console.error('Error:', error);
  }
}
```

## 10. 最新功能更新

### v1.1.0 (2025-01-06)
- **流式AI对话**: 实现类ChatGPT的实时流式输出
- **批量操作**: 支持知识库文档批量删除
- **权限优化**: 精确控制用户对资源的操作权限
- **智能引用**: AI回答只显示实际使用的参考源

### v1.0.0 (2024-12-01)
- 初始版本发布
- 基础认证功能
- 学生、教师、管理员核心功能
- AI集成功能 (阿里云千问)
- 知识库RAG系统

## 11. 错误处理最佳实践

### 11.1 流式调用失败处理
```javascript
// 前端代码示例
try {
  // 尝试流式调用
  for await (const data of streamAskQuestion(question)) {
    // 处理流式数据
  }
} catch (streamError) {
  // 降级到普通API
  const response = await api.post('/api/student/learning/ask', {
    question: question
  })
}
```

### 11.2 权限错误处理
- 401: Token过期或无效，需要重新登录
- 403: 没有权限访问该资源
- 404: 资源不存在或已被删除

---

**文档维护**: 本文档由 Kisir (kikiboy1120@gmail.com) 维护  
**在线API文档**: http://localhost:8000/docs (FastAPI自动生成)