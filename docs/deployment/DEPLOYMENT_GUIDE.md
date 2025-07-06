# AI Education Assistant Platform - Deployment Guide

**作者**: Kisir  
**邮箱**: kikiboy1120@gmail.com  
**更新日期**: 2025-01-06

## 1. 部署概述

### 1.1 部署架构
本平台支持多种部署方式，推荐使用Docker容器化部署以确保环境一致性和可扩展性。

### 1.2 系统要求
- **操作系统**: Ubuntu 20.04+ / CentOS 8+ / Debian 10+
- **CPU**: 最低4核，推荐8核
- **内存**: 最低8GB，推荐16GB
- **存储**: 最低50GB SSD，推荐100GB+ SSD
- **网络**: 公网IP，开放端口80/443

### 1.3 软件依赖
- Docker 20.10+
- Docker Compose 2.0+
- Python 3.8+
- PostgreSQL 15+
- Redis 7+
- Nginx 1.20+
- Node.js 16+ (前端构建)

## 2. 环境准备

### 2.1 安装Docker
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2.2 系统优化
```bash
# 优化内核参数
sudo tee -a /etc/sysctl.conf << EOF
# 网络优化
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 1200
net.ipv4.tcp_max_tw_buckets = 5000
net.ipv4.tcp_tw_reuse = 1

# 文件描述符
fs.file-max = 1000000
EOF

sudo sysctl -p

# 设置文件描述符限制
sudo tee -a /etc/security/limits.conf << EOF
* soft nofile 1000000
* hard nofile 1000000
EOF
```

## 3. 快速部署

### 3.1 克隆项目
```bash
git clone https://github.com/kisir/ai-education-assistant.git
cd ai-education-assistant
```

### 3.2 配置环境变量
```bash
# 复制环境变量模板
cp .env.example .env.production

# 编辑生产环境配置
vim .env.production
```

关键配置项：
```env
# 应用配置
ENVIRONMENT=production
SECRET_KEY=<生成一个强密码>
DEBUG=false

# 数据库配置
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=education_ai
POSTGRES_USER=edu_user
POSTGRES_PASSWORD=<强密码>

# Redis配置
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=<强密码>

# AI服务配置 (阿里云千问)
DASHSCOPE_API_KEY=<你的DashScope API密钥>

# 安全配置
ALLOWED_HOSTS=["yourdomain.com", "www.yourdomain.com"]
CORS_ORIGINS=["https://yourdomain.com"]
```

### 3.3 启动服务
```bash
# 构建并启动所有服务
docker-compose -f docker-compose.production.yml up -d

# 查看服务状态
docker-compose -f docker-compose.production.yml ps

# 查看日志
docker-compose -f docker-compose.production.yml logs -f
```

## 4. 生产环境配置

### 4.1 Nginx配置
```nginx
upstream app_backend {
    server app:8000;
}

server {
    listen 80;
    server_name yourdomain.com;
    
    # 强制HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    # SSL证书配置
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # 静态文件
    location /static/ {
        alias /usr/share/nginx/html/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # API代理
    location /api/ {
        proxy_pass http://app_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # SSE流式输出支持
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_buffering off;
        proxy_cache off;
        chunked_transfer_encoding on;
        proxy_set_header X-Accel-Buffering no;
        
        # 超时设置
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
```

### 4.2 数据库优化
```sql
-- PostgreSQL优化配置
ALTER SYSTEM SET shared_buffers = '4GB';
ALTER SYSTEM SET effective_cache_size = '12GB';
ALTER SYSTEM SET maintenance_work_mem = '1GB';
ALTER SYSTEM SET work_mem = '16MB';
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;

-- 创建索引
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_courses_teacher_id ON courses(teacher_id);
CREATE INDEX idx_submissions_assignment_student ON submissions(assignment_id, student_id);
```

### 4.3 Redis配置
```conf
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
requirepass your_redis_password
```

## 5. 高可用部署

### 5.1 负载均衡架构
```
                    ┌─────────────┐
                    │   用户请求   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  负载均衡器  │
                    │   (Nginx)    │
                    └──────┬──────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
    ┌─────▼─────┐    ┌─────▼─────┐   ┌─────▼─────┐
    │  App节点1  │    │  App节点2  │   │  App节点3  │
    └─────┬─────┘    └─────┬─────┘   └─────┬─────┘
          │                │                │
          └────────────────┼────────────────┘
                           │
                ┌──────────┼──────────┐
                │          │          │
          ┌─────▼─────┐ ┌──▼──┐ ┌────▼────┐
          │PostgreSQL │ │Redis│ │ChromaDB │
          │  (主从)    │ │集群 │ │ 集群    │
          └───────────┘ └─────┘ └─────────┘
```

### 5.2 数据库主从配置
```bash
# 主库配置
echo "host replication replica 0.0.0.0/0 md5" >> $PGDATA/pg_hba.conf
echo "wal_level = replica" >> $PGDATA/postgresql.conf
echo "max_wal_senders = 3" >> $PGDATA/postgresql.conf

# 从库配置
pg_basebackup -h master_host -D $PGDATA -U replica -v -P -W
echo "standby_mode = 'on'" >> $PGDATA/recovery.conf
echo "primary_conninfo = 'host=master_host port=5432 user=replica'" >> $PGDATA/recovery.conf
```

## 6. 监控与日志

### 6.1 Prometheus配置
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'education-ai-app'
    static_configs:
      - targets: ['app:8000']
    metrics_path: '/metrics'
  
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
  
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

### 6.2 日志管理
```yaml
# Filebeat配置
filebeat.inputs:
- type: docker
  containers:
    ids:
      - "*"
  processors:
    - add_docker_metadata: ~

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  index: "education-ai-%{+yyyy.MM.dd}"
```

## 7. 备份与恢复

### 7.1 自动备份脚本
```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/education-ai"

# 备份数据库
docker exec edu_postgres pg_dump -U $POSTGRES_USER $POSTGRES_DB | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# 备份上传文件
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz /app/uploads

# 备份Redis
docker exec edu_redis redis-cli --rdb /data/dump.rdb
cp /var/lib/docker/volumes/edu_redis/_data/dump.rdb $BACKUP_DIR/redis_$DATE.rdb

# 保留最近7天的备份
find $BACKUP_DIR -type f -mtime +7 -delete
```

### 7.2 恢复流程
```bash
# 恢复数据库
gunzip -c db_20240705_120000.sql.gz | docker exec -i edu_postgres psql -U $POSTGRES_USER $POSTGRES_DB

# 恢复文件
tar -xzf uploads_20240705_120000.tar.gz -C /

# 恢复Redis
docker cp redis_20240705_120000.rdb edu_redis:/data/dump.rdb
docker restart edu_redis
```

## 8. 性能调优

### 8.1 应用层优化
```python
# gunicorn配置
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
keepalive = 5
max_requests = 1000
max_requests_jitter = 50
timeout = 30
```

### 8.2 缓存策略
- **静态资源CDN加速**: 图片、CSS、JS文件
- **Redis缓存**: 用户会话、热点数据、AI响应缓存
- **ChromaDB向量缓存**: 知识库嵌入向量
- **数据库查询缓存**: 频繁查询结果

## 9. 安全加固

### 9.1 防火墙配置
```bash
# UFW防火墙规则
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 9.2 安全检查清单
- [ ] 修改默认密码
- [ ] 启用SSL证书
- [ ] 配置防火墙规则
- [ ] 限制数据库访问
- [ ] 启用日志审计
- [ ] 定期安全扫描
- [ ] 配置备份策略
- [ ] 应急响应计划

## 10. 故障排查

### 10.1 常见问题
| 问题 | 可能原因 | 解决方案 |
|-----|---------|---------|
| 服务无法启动 | 端口占用 | 检查端口使用情况 |
| 数据库连接失败 | 配置错误 | 检查连接参数 |
| API响应慢 | 资源不足 | 增加服务器资源 |
| 文件上传失败 | 权限问题 | 检查目录权限 |

### 10.2 诊断命令
```bash
# 检查服务状态
docker-compose ps

# 查看服务日志
docker logs -f edu_app

# 进入容器调试
docker exec -it edu_app bash

# 检查网络连接
docker network inspect edu_network

# 性能监控
docker stats
```

## 11. 升级指南

### 11.1 升级流程
1. 备份当前数据
2. 拉取最新代码
3. 查看升级说明
4. 执行数据库迁移
5. 重启服务
6. 验证功能

### 11.2 版本回滚
```bash
# 回滚到指定版本
git checkout v1.0.0
docker-compose down
docker-compose up -d
```

## 12. 特殊配置说明

### 12.1 流式输出配置
为了支持AI流式输出，需要特别注意：

1. **Nginx配置**: 必须禁用缓冲 (`proxy_buffering off`)
2. **中间件配置**: 确保不会缓冲SSE响应
3. **超时设置**: 适当增加超时时间以支持长连接

### 12.2 知识库向量存储
```bash
# 创建持久化存储目录
mkdir -p /data/chroma
chmod 777 /data/chroma

# Docker挂载配置
volumes:
  - /data/chroma:/app/chroma_data
```

### 12.3 文件上传大小限制
```nginx
# Nginx配置
client_max_body_size 50M;

# FastAPI配置
MAX_UPLOAD_SIZE=52428800  # 50MB
```

---

**文档维护**: 本文档由 Kisir (kikiboy1120@gmail.com) 维护  
**部署支持**: 如遇问题，请在 [GitHub Issues](https://github.com/kisir/ai-education-assistant/issues) 提交