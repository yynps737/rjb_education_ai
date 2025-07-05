# 安全文档 (Security Guide)

## 1. 安全概述

### 1.1 安全原则
- **纵深防御**：多层安全防护机制
- **最小权限**：用户仅获得必要的权限
- **安全默认**：默认配置即为安全配置
- **持续监控**：实时监控安全威胁
- **快速响应**：安全事件快速响应机制

### 1.2 安全架构
```
┌────────────────────────────────────────┐
│          WAF防火墙                     │
├────────────────────────────────────────┤
│          HTTPS/TLS加密                 │
├────────────────────────────────────────┤
│          API网关认证                   │
├────────────────────────────────────────┤
│          应用层安全                    │
├────────────────────────────────────────┤
│          数据层加密                    │
└────────────────────────────────────────┘
```

### 1.3 合规性要求
- **数据保护法规**：符合GDPR、个人信息保护法
- **教育行业标准**：遵守教育部相关规定
- **安全认证**：ISO 27001、等保三级

## 2. 认证与授权

### 2.1 JWT认证机制

#### 2.1.1 Token结构
```python
# JWT Payload示例
{
    "sub": "user_id",          # 用户ID
    "username": "teacher001",   # 用户名
    "role": "teacher",          # 角色
    "permissions": [...],       # 权限列表
    "exp": 1625232000,         # 过期时间
    "iat": 1625228400,         # 签发时间
    "jti": "unique_token_id"   # Token ID
}
```

#### 2.1.2 Token安全配置
```python
# settings.py
class SecuritySettings:
    # JWT配置
    SECRET_KEY = os.getenv("SECRET_KEY")  # 至少32位随机字符串
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    
    # Token黑名单
    TOKEN_BLACKLIST_ENABLED = True
    TOKEN_BLACKLIST_TTL = 86400  # 24小时
```

#### 2.1.3 Token刷新机制
```python
# auth_service.py
class AuthService:
    async def refresh_access_token(self, refresh_token: str) -> dict:
        """刷新访问令牌"""
        try:
            # 验证refresh token
            payload = jwt.decode(
                refresh_token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            
            # 检查是否在黑名单
            if await self.is_token_blacklisted(payload["jti"]):
                raise HTTPException(status_code=401, detail="Token已失效")
            
            # 生成新的access token
            user_id = payload["sub"]
            user = await self.get_user(user_id)
            
            new_access_token = self.create_access_token(user)
            
            return {
                "access_token": new_access_token,
                "token_type": "bearer"
            }
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Refresh token已过期")
        except jwt.JWTError:
            raise HTTPException(status_code=401, detail="无效的token")
```

### 2.2 RBAC权限控制

#### 2.2.1 角色权限矩阵
| 功能模块 | 管理员 | 教师 | 学生 |
|---------|--------|------|------|
| 用户管理 | ✓ | ✗ | ✗ |
| 课程创建 | ✓ | ✓ | ✗ |
| 课程学习 | ✓ | ✓ | ✓ |
| 作业发布 | ✓ | ✓ | ✗ |
| 作业提交 | ✗ | ✗ | ✓ |
| 成绩查看 | ✓ | ✓ | ✓* |
| 系统配置 | ✓ | ✗ | ✗ |

*注：学生仅能查看自己的成绩

#### 2.2.2 权限装饰器实现
```python
# decorators.py
from functools import wraps
from typing import List

def require_permissions(*required_permissions: str):
    """权限验证装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取当前用户
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(status_code=401, detail="未认证")
            
            # 验证权限
            user_permissions = get_user_permissions(current_user)
            
            for permission in required_permissions:
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
async def create_course(
    course_data: CourseCreate,
    current_user: User = Depends(get_current_user)
):
    return await course_service.create_course(course_data, current_user)
```

## 3. 数据安全

### 3.1 数据加密

#### 3.1.1 敏感数据加密
```python
# encryption.py
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

class DataEncryption:
    def __init__(self, master_key: str):
        # 生成加密密钥
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'stable_salt',  # 生产环境应使用随机salt
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
        self.cipher = Fernet(key)
    
    def encrypt(self, data: str) -> str:
        """加密数据"""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """解密数据"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()

# 使用示例
encryption = DataEncryption(settings.MASTER_KEY)

# 加密敏感信息
encrypted_answer = encryption.encrypt(student_answer)

# 存储到数据库
submission.encrypted_answer = encrypted_answer
```

#### 3.1.2 数据库字段加密
```python
# models/encrypted_fields.py
from sqlalchemy import TypeDecorator, String

class EncryptedType(TypeDecorator):
    impl = String
    
    def __init__(self, encryption_key, *args, **kwargs):
        self.encryption = DataEncryption(encryption_key)
        super().__init__(*args, **kwargs)
    
    def process_bind_param(self, value, dialect):
        if value is not None:
            return self.encryption.encrypt(value)
        return value
    
    def process_result_value(self, value, dialect):
        if value is not None:
            return self.encryption.decrypt(value)
        return value

# 模型使用
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True)
    # 加密存储手机号
    phone = Column(EncryptedType(settings.ENCRYPTION_KEY))
    # 加密存储身份证号
    id_card = Column(EncryptedType(settings.ENCRYPTION_KEY))
```

### 3.2 密码安全

#### 3.2.1 密码策略
```python
# password_policy.py
import re
from typing import List, Tuple

class PasswordPolicy:
    MIN_LENGTH = 8
    MAX_LENGTH = 128
    
    @classmethod
    def validate(cls, password: str) -> Tuple[bool, List[str]]:
        """验证密码强度"""
        errors = []
        
        # 长度检查
        if len(password) < cls.MIN_LENGTH:
            errors.append(f"密码长度至少{cls.MIN_LENGTH}位")
        if len(password) > cls.MAX_LENGTH:
            errors.append(f"密码长度不能超过{cls.MAX_LENGTH}位")
        
        # 复杂度检查
        if not re.search(r"[A-Z]", password):
            errors.append("密码必须包含大写字母")
        if not re.search(r"[a-z]", password):
            errors.append("密码必须包含小写字母")
        if not re.search(r"\d", password):
            errors.append("密码必须包含数字")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            errors.append("密码必须包含特殊字符")
        
        # 常见密码检查
        common_passwords = ["password", "123456", "admin", "qwerty"]
        if password.lower() in common_passwords:
            errors.append("密码过于简单")
        
        return len(errors) == 0, errors
```

#### 3.2.2 密码哈希存储
```python
# password_hasher.py
from passlib.context import CryptContext

# 配置密码哈希
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # 增加计算复杂度
)

class PasswordHasher:
    @staticmethod
    def hash(password: str) -> str:
        """哈希密码"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify(plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def needs_rehash(hashed_password: str) -> bool:
        """检查是否需要重新哈希"""
        return pwd_context.needs_update(hashed_password)
```

## 4. 输入验证与防护

### 4.1 SQL注入防护

#### 4.1.1 参数化查询
```python
# 正确的做法 - 使用ORM
user = db.query(User).filter(User.username == username).first()

# 正确的做法 - 使用参数化SQL
query = text("SELECT * FROM users WHERE username = :username")
result = db.execute(query, {"username": username})

# 错误的做法 - 容易SQL注入
# query = f"SELECT * FROM users WHERE username = '{username}'"  # 危险！
```

#### 4.1.2 输入验证示例
```python
# validators.py
from pydantic import BaseModel, validator, constr
import re

class UserInput(BaseModel):
    username: constr(regex="^[a-zA-Z0-9_]{3,20}$")
    email: EmailStr
    full_name: constr(min_length=2, max_length=50)
    
    @validator('username')
    def validate_username(cls, v):
        # 防止SQL注入关键字
        sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'UNION']
        if any(keyword in v.upper() for keyword in sql_keywords):
            raise ValueError('用户名包含非法字符')
        return v
    
    @validator('full_name')
    def validate_full_name(cls, v):
        # 只允许中文、英文、空格
        if not re.match(r'^[\u4e00-\u9fa5a-zA-Z\s]+$', v):
            raise ValueError('姓名只能包含中英文字符')
        return v
```

### 4.2 XSS防护

#### 4.2.1 HTML转义
```python
# sanitizer.py
import html
import bleach

class HTMLSanitizer:
    # 允许的HTML标签
    ALLOWED_TAGS = [
        'p', 'br', 'span', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'strong', 'em', 'u', 'strike', 'a', 'img', 'blockquote',
        'ul', 'ol', 'li', 'code', 'pre'
    ]
    
    # 允许的属性
    ALLOWED_ATTRIBUTES = {
        'a': ['href', 'title'],
        'img': ['src', 'alt', 'width', 'height'],
        'div': ['class'],
        'span': ['class'],
        'code': ['class']
    }
    
    @classmethod
    def clean(cls, content: str) -> str:
        """清理HTML内容"""
        # 使用bleach清理HTML
        cleaned = bleach.clean(
            content,
            tags=cls.ALLOWED_TAGS,
            attributes=cls.ALLOWED_ATTRIBUTES,
            strip=True
        )
        return cleaned
    
    @classmethod
    def escape(cls, content: str) -> str:
        """转义HTML特殊字符"""
        return html.escape(content)
```

#### 4.2.2 响应头设置
```python
# middleware.py
from fastapi import Request
from fastapi.responses import Response

@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    
    # 安全响应头
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' data:; "
        "connect-src 'self' wss: https:;"
    )
    
    return response
```

### 4.3 文件上传安全

#### 4.3.1 文件类型验证
```python
# file_validator.py
import magic
import hashlib
from pathlib import Path

class FileValidator:
    # 允许的文件类型
    ALLOWED_EXTENSIONS = {
        'pdf', 'doc', 'docx', 'xls', 'xlsx', 
        'ppt', 'pptx', 'txt', 'md', 'jpg', 
        'jpeg', 'png', 'gif', 'mp4', 'mp3'
    }
    
    # MIME类型映射
    ALLOWED_MIMES = {
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'image/jpeg',
        'image/png',
        'text/plain',
        # ... 更多MIME类型
    }
    
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    @classmethod
    def validate_file(cls, file_content: bytes, filename: str) -> tuple:
        """验证文件安全性"""
        # 检查文件大小
        if len(file_content) > cls.MAX_FILE_SIZE:
            return False, "文件大小超过限制"
        
        # 检查文件扩展名
        ext = Path(filename).suffix[1:].lower()
        if ext not in cls.ALLOWED_EXTENSIONS:
            return False, "不支持的文件类型"
        
        # 检查MIME类型（魔术字节）
        mime = magic.from_buffer(file_content, mime=True)
        if mime not in cls.ALLOWED_MIMES:
            return False, "文件内容与扩展名不匹配"
        
        # 检查文件内容是否包含恶意代码
        if cls._contains_malicious_content(file_content):
            return False, "文件包含可疑内容"
        
        return True, "验证通过"
    
    @staticmethod
    def _contains_malicious_content(content: bytes) -> bool:
        """检查恶意内容"""
        # 检查常见的恶意模式
        malicious_patterns = [
            b'<script',
            b'javascript:',
            b'onerror=',
            b'onclick=',
            b'<?php',
            b'<%',
            b'<jsp:',
        ]
        
        content_lower = content.lower()
        return any(pattern in content_lower for pattern in malicious_patterns)
    
    @staticmethod
    def generate_safe_filename(original_filename: str) -> str:
        """生成安全的文件名"""
        # 获取文件扩展名
        ext = Path(original_filename).suffix
        
        # 生成唯一文件名
        timestamp = int(time.time())
        random_str = secrets.token_hex(8)
        safe_name = f"{timestamp}_{random_str}{ext}"
        
        return safe_name
```

## 5. API安全

### 5.1 速率限制

#### 5.1.1 Redis速率限制器
```python
# rate_limiter.py
from datetime import datetime, timedelta
import redis
from fastapi import HTTPException

class RateLimiter:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    async def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> bool:
        """检查速率限制"""
        pipe = self.redis.pipeline()
        now = datetime.now()
        window_start = now - timedelta(seconds=window_seconds)
        
        # 使用滑动窗口算法
        pipe.zremrangebyscore(key, 0, window_start.timestamp())
        pipe.zadd(key, {str(now.timestamp()): now.timestamp()})
        pipe.zcount(key, window_start.timestamp(), now.timestamp())
        pipe.expire(key, window_seconds)
        
        results = pipe.execute()
        request_count = results[2]
        
        if request_count > max_requests:
            raise HTTPException(
                status_code=429,
                detail=f"请求过于频繁，请{window_seconds}秒后重试"
            )
        
        return True

# 使用装饰器
def rate_limit(max_requests: int = 100, window: int = 60):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get('request')
            user = kwargs.get('current_user')
            
            # 生成限流key
            if user:
                key = f"rate_limit:user:{user.id}:{func.__name__}"
            else:
                key = f"rate_limit:ip:{request.client.host}:{func.__name__}"
            
            # 检查限流
            await rate_limiter.check_rate_limit(key, max_requests, window)
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

### 5.2 API密钥管理

#### 5.2.1 API密钥生成与验证
```python
# api_key_manager.py
import secrets
import hashlib
from datetime import datetime, timedelta

class APIKeyManager:
    @staticmethod
    def generate_api_key() -> tuple:
        """生成API密钥对"""
        # 生成密钥
        key = secrets.token_urlsafe(32)
        key_id = secrets.token_hex(8)
        
        # 计算密钥哈希（存储用）
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        return key_id, key, key_hash
    
    @staticmethod
    async def validate_api_key(key_id: str, key: str, db) -> bool:
        """验证API密钥"""
        # 查询密钥记录
        api_key_record = db.query(APIKey).filter(
            APIKey.key_id == key_id,
            APIKey.is_active == True
        ).first()
        
        if not api_key_record:
            return False
        
        # 验证密钥哈希
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        if key_hash != api_key_record.key_hash:
            return False
        
        # 检查过期时间
        if api_key_record.expires_at < datetime.utcnow():
            return False
        
        # 更新最后使用时间
        api_key_record.last_used_at = datetime.utcnow()
        db.commit()
        
        return True
```

## 6. 安全监控与审计

### 6.1 安全日志

#### 6.1.1 审计日志记录
```python
# audit_logger.py
import json
from datetime import datetime
from typing import Any, Dict

class AuditLogger:
    def __init__(self, logger):
        self.logger = logger
    
    def log_security_event(
        self,
        event_type: str,
        user_id: int,
        ip_address: str,
        details: Dict[str, Any],
        severity: str = "INFO"
    ):
        """记录安全事件"""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "ip_address": ip_address,
            "severity": severity,
            "details": details
        }
        
        # 记录到日志
        self.logger.info(f"SECURITY_EVENT: {json.dumps(event)}")
        
        # 存储到数据库（可选）
        self._store_to_database(event)
    
    def _store_to_database(self, event: dict):
        """存储审计日志到数据库"""
        # 实现数据库存储逻辑
        pass

# 使用示例
audit_logger = AuditLogger(logger)

# 记录登录事件
audit_logger.log_security_event(
    event_type="LOGIN_SUCCESS",
    user_id=user.id,
    ip_address=request.client.host,
    details={
        "username": user.username,
        "login_method": "password"
    }
)

# 记录异常访问
audit_logger.log_security_event(
    event_type="UNAUTHORIZED_ACCESS",
    user_id=user.id if user else None,
    ip_address=request.client.host,
    details={
        "endpoint": request.url.path,
        "method": request.method
    },
    severity="WARNING"
)
```

### 6.2 异常检测

#### 6.2.1 行为分析
```python
# anomaly_detector.py
from collections import defaultdict
from datetime import datetime, timedelta

class AnomalyDetector:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.thresholds = {
            "failed_login": 5,      # 5次失败登录
            "rapid_requests": 100,  # 100次/分钟
            "data_download": 50,    # 50MB/小时
        }
    
    async def check_failed_login_attempts(self, username: str, ip: str) -> bool:
        """检查登录失败次数"""
        key = f"failed_login:{username}:{ip}"
        count = await self.redis.incr(key)
        await self.redis.expire(key, 3600)  # 1小时过期
        
        if count > self.thresholds["failed_login"]:
            await self.trigger_alert(
                "MULTIPLE_FAILED_LOGINS",
                {
                    "username": username,
                    "ip": ip,
                    "count": count
                }
            )
            return True
        return False
    
    async def check_unusual_access_pattern(self, user_id: int, endpoint: str):
        """检查异常访问模式"""
        # 记录访问时间
        key = f"access_pattern:{user_id}"
        now = datetime.now().timestamp()
        
        # 添加到有序集合
        await self.redis.zadd(key, {endpoint: now})
        
        # 获取最近1分钟的访问记录
        minute_ago = now - 60
        recent_count = await self.redis.zcount(key, minute_ago, now)
        
        if recent_count > self.thresholds["rapid_requests"]:
            await self.trigger_alert(
                "UNUSUAL_ACCESS_PATTERN",
                {
                    "user_id": user_id,
                    "request_count": recent_count,
                    "time_window": "1 minute"
                }
            )
    
    async def trigger_alert(self, alert_type: str, details: dict):
        """触发安全警报"""
        alert = {
            "type": alert_type,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details
        }
        
        # 发送到监控系统
        await self.send_to_monitoring(alert)
        
        # 记录到日志
        logger.warning(f"SECURITY_ALERT: {alert}")
```

## 7. 应急响应

### 7.1 安全事件处理流程

#### 7.1.1 事件分级
| 级别 | 描述 | 响应时间 | 示例 |
|-----|------|---------|------|
| P0 | 紧急 | 15分钟 | 数据泄露、系统入侵 |
| P1 | 高 | 1小时 | 多次失败登录、异常数据访问 |
| P2 | 中 | 4小时 | 单次SQL注入尝试、XSS尝试 |
| P3 | 低 | 24小时 | 端口扫描、异常请求 |

#### 7.1.2 响应脚本
```python
# incident_response.py
class IncidentResponse:
    def __init__(self):
        self.response_actions = {
            "MULTIPLE_FAILED_LOGINS": self.handle_brute_force,
            "SQL_INJECTION_ATTEMPT": self.handle_sql_injection,
            "DATA_BREACH": self.handle_data_breach,
        }
    
    async def handle_incident(self, incident_type: str, details: dict):
        """处理安全事件"""
        handler = self.response_actions.get(incident_type)
        if handler:
            await handler(details)
        else:
            await self.default_handler(incident_type, details)
    
    async def handle_brute_force(self, details: dict):
        """处理暴力破解"""
        username = details.get("username")
        ip = details.get("ip")
        
        # 1. 锁定账户
        await self.lock_user_account(username)
        
        # 2. 封禁IP
        await self.block_ip_address(ip, duration=3600)
        
        # 3. 通知用户
        await self.notify_user(username, "账户因异常登录被临时锁定")
        
        # 4. 记录事件
        await self.log_incident("BRUTE_FORCE_ATTACK", details)
    
    async def handle_data_breach(self, details: dict):
        """处理数据泄露"""
        # 1. 立即停止相关服务
        await self.stop_affected_services(details.get("services"))
        
        # 2. 保存现场
        await self.preserve_evidence(details)
        
        # 3. 通知管理员
        await self.alert_administrators("CRITICAL: 检测到数据泄露", details)
        
        # 4. 启动应急预案
        await self.activate_emergency_plan("DATA_BREACH")
```

### 7.2 灾难恢复

#### 7.2.1 备份策略
```bash
#!/bin/bash
# backup.sh - 安全备份脚本

# 配置
BACKUP_DIR="/secure/backups"
ENCRYPTION_KEY=$BACKUP_ENCRYPTION_KEY
DATE=$(date +%Y%m%d_%H%M%S)

# 数据库备份
echo "开始数据库备份..."
pg_dump -U $DB_USER -h $DB_HOST $DB_NAME | \
    gzip | \
    openssl enc -aes-256-cbc -salt -k $ENCRYPTION_KEY \
    > $BACKUP_DIR/db_backup_$DATE.sql.gz.enc

# 文件备份
echo "开始文件备份..."
tar -czf - /app/uploads | \
    openssl enc -aes-256-cbc -salt -k $ENCRYPTION_KEY \
    > $BACKUP_DIR/files_backup_$DATE.tar.gz.enc

# 验证备份
echo "验证备份完整性..."
for file in $BACKUP_DIR/*_$DATE.*; do
    if [ -f "$file" ]; then
        echo "验证: $file"
        openssl enc -d -aes-256-cbc -k $ENCRYPTION_KEY -in "$file" | \
            gzip -t && echo "✓ 备份验证通过" || echo "✗ 备份验证失败"
    fi
done

# 清理旧备份（保留30天）
find $BACKUP_DIR -type f -mtime +30 -delete
```

## 8. 安全检查清单

### 8.1 部署前安全检查
- [ ] 更改所有默认密码
- [ ] 启用HTTPS/TLS
- [ ] 配置防火墙规则
- [ ] 禁用不必要的服务和端口
- [ ] 更新所有依赖到最新安全版本
- [ ] 配置安全响应头
- [ ] 启用日志记录和监控
- [ ] 实施访问控制策略
- [ ] 配置自动备份
- [ ] 制定应急响应计划

### 8.2 定期安全审计
- [ ] 每月：审查用户权限
- [ ] 每月：检查异常登录记录
- [ ] 每季度：更新依赖包
- [ ] 每季度：渗透测试
- [ ] 每半年：安全培训
- [ ] 每年：完整安全审计

## 9. 安全最佳实践

### 9.1 开发安全准则
1. **永不信任用户输入**
2. **使用参数化查询**
3. **实施最小权限原则**
4. **加密敏感数据**
5. **定期更新依赖**
6. **记录安全事件**
7. **实施防御编程**

### 9.2 运维安全准则
1. **及时打补丁**
2. **监控异常行为**
3. **定期备份数据**
4. **限制网络访问**
5. **使用强密码策略**
6. **启用多因素认证**
7. **定期安全演练**

## 10. 安全联系方式

### 10.1 安全团队
- **安全负责人**：security@education-ai.com
- **24/7应急响应**：+86-xxx-xxxx-xxxx
- **漏洞报告**：https://security.education-ai.com/report

### 10.2 漏洞披露政策
我们欢迎安全研究人员报告漏洞：
1. 请勿公开披露未修复的漏洞
2. 提供详细的复现步骤
3. 我们承诺在48小时内响应
4. 修复后会公开致谢（如果您愿意）

---

*安全文档版本：v1.0.0 | 更新日期：2024年7月 | 密级：内部*