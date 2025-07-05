# 维护指南 (Maintenance Guide)

## 1. 维护概述

### 1.1 维护目标
- **系统稳定性**：确保7×24小时稳定运行
- **性能优化**：持续优化系统性能
- **安全更新**：及时修复安全漏洞
- **功能迭代**：根据需求更新功能
- **数据完整**：保证数据安全完整

### 1.2 维护职责分配
| 角色 | 职责 | 工作内容 |
|-----|------|---------|
| 系统管理员 | 基础设施维护 | 服务器、网络、存储管理 |
| 数据库管理员 | 数据库维护 | 性能优化、备份恢复、监控 |
| 应用管理员 | 应用维护 | 部署更新、配置管理、日志分析 |
| 安全管理员 | 安全维护 | 漏洞扫描、补丁管理、审计 |

### 1.3 维护级别
- **日常维护**：每日执行的常规检查
- **定期维护**：按计划执行的维护任务
- **紧急维护**：处理突发问题
- **预防性维护**：防止问题发生

## 2. 日常维护

### 2.1 每日检查清单

#### 2.1.1 系统健康检查
```bash
#!/bin/bash
# daily_check.sh - 每日系统检查脚本

echo "=== 智能教育平台每日检查 $(date) ==="

# 1. 检查服务状态
echo "1. 检查服务状态..."
services=("nginx" "postgresql" "redis" "education-api")
for service in "${services[@]}"; do
    if systemctl is-active --quiet $service; then
        echo "  ✓ $service 运行正常"
    else
        echo "  ✗ $service 服务异常"
        # 发送告警
        send_alert "服务异常" "$service 服务未运行"
    fi
done

# 2. 检查磁盘空间
echo "2. 检查磁盘空间..."
df -h | awk '{
    if (NR>1 && substr($5, 1, length($5)-1) > 80) {
        print "  ⚠ 磁盘空间告警: " $6 " 使用率 " $5
    }
}'

# 3. 检查内存使用
echo "3. 检查内存使用..."
free -m | awk 'NR==2{
    usage=($3/$2)*100
    if (usage > 80) {
        printf "  ⚠ 内存使用率: %.1f%%\n", usage
    } else {
        printf "  ✓ 内存使用率: %.1f%%\n", usage
    }
}'

# 4. 检查CPU负载
echo "4. 检查CPU负载..."
load_avg=$(uptime | awk -F'load average:' '{print $2}')
echo "  当前负载: $load_avg"

# 5. 检查错误日志
echo "5. 检查错误日志..."
error_count=$(grep -c "ERROR" /var/log/education/app.log 2>/dev/null || echo 0)
if [ $error_count -gt 0 ]; then
    echo "  ⚠ 发现 $error_count 个错误"
    tail -5 /var/log/education/app.log | grep "ERROR"
else
    echo "  ✓ 无错误日志"
fi

# 6. 检查数据库连接
echo "6. 检查数据库连接..."
if psql -h localhost -p 5433 -U education_user -d education_ai_db -c "SELECT 1" > /dev/null 2>&1; then
    echo "  ✓ 数据库连接正常"
else
    echo "  ✗ 数据库连接失败"
fi

# 7. 检查API响应
echo "7. 检查API健康状态..."
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
if [ $response -eq 200 ]; then
    echo "  ✓ API响应正常"
else
    echo "  ✗ API响应异常: HTTP $response"
fi

echo "=== 检查完成 ==="
```

### 2.2 性能监控

#### 2.2.1 实时监控指标
```python
# monitoring/metrics_collector.py
import psutil
import asyncio
from datetime import datetime
from prometheus_client import Gauge, Counter, Histogram
import aioredis

# Prometheus指标定义
cpu_usage = Gauge('system_cpu_usage_percent', 'CPU使用率')
memory_usage = Gauge('system_memory_usage_percent', '内存使用率')
disk_usage = Gauge('system_disk_usage_percent', '磁盘使用率', ['mount_point'])
api_requests = Counter('api_requests_total', 'API请求总数', ['method', 'endpoint', 'status'])
api_latency = Histogram('api_request_duration_seconds', 'API请求延迟', ['method', 'endpoint'])

class MetricsCollector:
    def __init__(self):
        self.redis = None
        
    async def start(self):
        """启动监控采集"""
        self.redis = await aioredis.create_redis_pool('redis://localhost:6380')
        
        # 启动采集任务
        await asyncio.gather(
            self.collect_system_metrics(),
            self.collect_application_metrics()
        )
    
    async def collect_system_metrics(self):
        """采集系统指标"""
        while True:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_usage.set(cpu_percent)
            
            # 内存使用率
            memory = psutil.virtual_memory()
            memory_usage.set(memory.percent)
            
            # 磁盘使用率
            for partition in psutil.disk_partitions():
                usage = psutil.disk_usage(partition.mountpoint)
                disk_usage.labels(mount_point=partition.mountpoint).set(usage.percent)
            
            # 存储到Redis（用于实时展示）
            await self.redis.hset('system_metrics', mapping={
                'cpu_usage': cpu_percent,
                'memory_usage': memory.percent,
                'timestamp': datetime.now().isoformat()
            })
            
            await asyncio.sleep(10)  # 每10秒采集一次
    
    async def collect_application_metrics(self):
        """采集应用指标"""
        while True:
            # 从Redis获取应用指标
            metrics = await self.redis.hgetall('app_metrics')
            
            if metrics:
                # 活跃用户数
                active_users = int(metrics.get(b'active_users', 0))
                
                # 数据库连接池状态
                db_pool_size = int(metrics.get(b'db_pool_size', 0))
                db_pool_used = int(metrics.get(b'db_pool_used', 0))
                
                # 缓存命中率
                cache_hits = int(metrics.get(b'cache_hits', 0))
                cache_misses = int(metrics.get(b'cache_misses', 0))
                
                if cache_hits + cache_misses > 0:
                    cache_hit_rate = cache_hits / (cache_hits + cache_misses) * 100
                else:
                    cache_hit_rate = 0
                
                # 记录指标
                logger.info(f"应用指标 - 活跃用户: {active_users}, "
                          f"DB连接池: {db_pool_used}/{db_pool_size}, "
                          f"缓存命中率: {cache_hit_rate:.2f}%")
            
            await asyncio.sleep(60)  # 每分钟采集一次
```

### 2.3 日志管理

#### 2.3.1 日志轮转配置
```bash
# /etc/logrotate.d/education-ai
/var/log/education/*.log {
    daily                    # 每日轮转
    missingok               # 忽略不存在的文件
    rotate 30               # 保留30天
    compress                # 压缩旧日志
    delaycompress          # 延迟压缩
    notifempty             # 空文件不轮转
    create 0644 app app    # 创建新文件权限
    sharedscripts          # 共享脚本
    postrotate
        # 通知应用重新打开日志文件
        systemctl reload education-api
    endscript
}
```

#### 2.3.2 日志分析脚本
```python
# scripts/log_analyzer.py
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta

class LogAnalyzer:
    def __init__(self, log_file):
        self.log_file = log_file
        self.error_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*ERROR.*')
        self.api_pattern = re.compile(r'"(GET|POST|PUT|DELETE) ([^"]+)" (\d{3})')
        
    def analyze_errors(self, hours=24):
        """分析错误日志"""
        errors = defaultdict(int)
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with open(self.log_file, 'r') as f:
            for line in f:
                match = self.error_pattern.match(line)
                if match:
                    timestamp_str = match.group(1)
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                    
                    if timestamp > cutoff_time:
                        # 提取错误类型
                        error_type = self._extract_error_type(line)
                        errors[error_type] += 1
        
        return dict(errors)
    
    def analyze_api_performance(self):
        """分析API性能"""
        api_stats = defaultdict(lambda: {'count': 0, 'errors': 0})
        
        with open(self.log_file, 'r') as f:
            for line in f:
                match = self.api_pattern.search(line)
                if match:
                    method = match.group(1)
                    endpoint = match.group(2)
                    status_code = int(match.group(3))
                    
                    key = f"{method} {endpoint}"
                    api_stats[key]['count'] += 1
                    
                    if status_code >= 400:
                        api_stats[key]['errors'] += 1
        
        # 计算错误率
        for key, stats in api_stats.items():
            stats['error_rate'] = stats['errors'] / stats['count'] * 100
        
        return dict(api_stats)
    
    def generate_report(self):
        """生成分析报告"""
        report = []
        report.append(f"=== 日志分析报告 {datetime.now().strftime('%Y-%m-%d %H:%M')} ===\n")
        
        # 错误分析
        errors = self.analyze_errors()
        report.append("## 错误统计（最近24小时）")
        for error_type, count in sorted(errors.items(), key=lambda x: x[1], reverse=True)[:10]:
            report.append(f"  - {error_type}: {count}次")
        
        # API性能分析
        api_stats = self.analyze_api_performance()
        report.append("\n## API性能统计")
        report.append("| 接口 | 调用次数 | 错误次数 | 错误率 |")
        report.append("|------|---------|---------|--------|")
        
        for endpoint, stats in sorted(api_stats.items(), key=lambda x: x[1]['count'], reverse=True)[:20]:
            report.append(f"| {endpoint} | {stats['count']} | {stats['errors']} | {stats['error_rate']:.1f}% |")
        
        return '\n'.join(report)
```

## 3. 定期维护

### 3.1 周维护任务

#### 3.1.1 数据库维护
```sql
-- weekly_db_maintenance.sql
-- 每周数据库维护脚本

-- 1. 更新统计信息
ANALYZE;

-- 2. 重建索引（如果碎片化严重）
REINDEX DATABASE education_ai_db;

-- 3. 清理过期数据
-- 删除30天前的日志
DELETE FROM audit_logs WHERE created_at < NOW() - INTERVAL '30 days';

-- 删除过期的会话
DELETE FROM user_sessions WHERE expires_at < NOW();

-- 4. 检查表大小
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;

-- 5. 检查慢查询
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    max_time
FROM pg_stat_statements
WHERE mean_time > 100  -- 平均执行时间超过100ms
ORDER BY mean_time DESC
LIMIT 10;
```

#### 3.1.2 安全扫描
```bash
#!/bin/bash
# weekly_security_scan.sh

echo "=== 周安全扫描 $(date) ==="

# 1. 检查系统更新
echo "1. 检查系统更新..."
apt update > /tmp/updates.log 2>&1
updates_available=$(apt list --upgradable 2>/dev/null | grep -c "upgradable")
if [ $updates_available -gt 0 ]; then
    echo "  ⚠ 有 $updates_available 个更新可用"
    apt list --upgradable 2>/dev/null | head -10
else
    echo "  ✓ 系统已是最新"
fi

# 2. 检查开放端口
echo "2. 检查开放端口..."
netstat -tlnp | grep LISTEN | awk '{print $4}' | sort -u

# 3. 检查异常用户
echo "3. 检查系统用户..."
# 检查最近创建的用户
echo "  最近创建的用户:"
grep -E "useradd|adduser" /var/log/auth.log | tail -5

# 4. 检查文件完整性
echo "4. 检查关键文件修改..."
# 使用tripwire或aide检查文件完整性
find /etc /usr/bin /usr/sbin -type f -mtime -7 -ls | head -20

# 5. 扫描恶意软件
echo "5. 扫描恶意软件..."
clamscan -r -i /var/www /home --exclude-dir="^/sys|^/proc" 2>/dev/null

echo "=== 扫描完成 ==="
```

### 3.2 月度维护

#### 3.2.1 性能优化
```python
# scripts/monthly_optimization.py
import os
import subprocess
from datetime import datetime

class MonthlyOptimization:
    def __init__(self):
        self.report = []
        
    def optimize_database(self):
        """数据库优化"""
        self.report.append("## 数据库优化")
        
        # 1. VACUUM FULL（注意：会锁表）
        cmd = "psql -U education_user -d education_ai_db -c 'VACUUM FULL ANALYZE;'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            self.report.append("  ✓ VACUUM FULL 执行成功")
        else:
            self.report.append(f"  ✗ VACUUM FULL 失败: {result.stderr}")
        
        # 2. 更新序列
        sequences_sql = """
        SELECT 'ALTER SEQUENCE ' || sequence_name || ' RESTART WITH ' || 
               (SELECT MAX(id) + 1 FROM ' || table_name || ');'
        FROM information_schema.sequences;
        """
        # 执行序列更新...
        
    def clean_old_data(self):
        """清理旧数据"""
        self.report.append("\n## 数据清理")
        
        # 清理规则
        cleanup_rules = [
            ("删除3个月前的临时文件", "/tmp/education_*", 90),
            ("删除6个月前的日志备份", "/backup/logs/*", 180),
            ("删除1年前的数据备份", "/backup/old/*", 365),
        ]
        
        for description, pattern, days in cleanup_rules:
            cmd = f"find {pattern} -type f -mtime +{days} -delete 2>/dev/null | wc -l"
            deleted_count = subprocess.getoutput(cmd)
            self.report.append(f"  - {description}: 删除 {deleted_count} 个文件")
    
    def update_dependencies(self):
        """更新依赖包"""
        self.report.append("\n## 依赖更新")
        
        # Python依赖更新
        cmd = "pip list --outdated --format=json"
        outdated = subprocess.getoutput(cmd)
        
        # 分析并更新安全相关的包
        security_packages = ['django', 'fastapi', 'sqlalchemy', 'cryptography']
        # ... 更新逻辑
    
    def generate_report(self):
        """生成月度报告"""
        report_content = f"# 月度维护报告\n"
        report_content += f"日期: {datetime.now().strftime('%Y-%m-%d')}\n\n"
        report_content += '\n'.join(self.report)
        
        # 保存报告
        report_file = f"/var/log/education/monthly_report_{datetime.now().strftime('%Y%m')}.md"
        with open(report_file, 'w') as f:
            f.write(report_content)
        
        return report_content
```

### 3.3 季度维护

#### 3.3.1 容量规划
```python
# scripts/capacity_planning.py
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

class CapacityPlanner:
    def __init__(self):
        self.metrics_data = self.load_metrics_data()
    
    def analyze_growth_trend(self):
        """分析增长趋势"""
        # 分析用户增长
        user_growth = self.calculate_growth_rate('user_count')
        
        # 分析存储增长
        storage_growth = self.calculate_growth_rate('storage_used')
        
        # 分析请求量增长
        request_growth = self.calculate_growth_rate('daily_requests')
        
        return {
            'user_growth_rate': user_growth,
            'storage_growth_rate': storage_growth,
            'request_growth_rate': request_growth
        }
    
    def predict_capacity_needs(self, months=6):
        """预测未来容量需求"""
        predictions = {}
        
        # 当前资源使用情况
        current_stats = self.get_current_stats()
        growth_rates = self.analyze_growth_trend()
        
        # 预测计算
        for resource, current_value in current_stats.items():
            growth_rate = growth_rates.get(f"{resource}_growth_rate", 0.1)  # 默认10%增长
            predicted_value = current_value * ((1 + growth_rate) ** months)
            predictions[resource] = {
                'current': current_value,
                'predicted': predicted_value,
                'increase_percent': (predicted_value - current_value) / current_value * 100
            }
        
        return predictions
    
    def generate_capacity_report(self):
        """生成容量规划报告"""
        report = []
        report.append("# 季度容量规划报告\n")
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d')}\n")
        
        # 当前使用情况
        report.append("## 当前资源使用情况")
        current_stats = self.get_current_stats()
        for resource, value in current_stats.items():
            report.append(f"- {resource}: {value}")
        
        # 增长趋势
        report.append("\n## 增长趋势分析")
        growth_trends = self.analyze_growth_trend()
        for metric, rate in growth_trends.items():
            report.append(f"- {metric}: {rate*100:.1f}% 月增长率")
        
        # 容量预测
        report.append("\n## 6个月容量预测")
        predictions = self.predict_capacity_needs(6)
        
        report.append("| 资源 | 当前值 | 预测值 | 增长率 |")
        report.append("|-----|--------|--------|--------|")
        for resource, pred in predictions.items():
            report.append(f"| {resource} | {pred['current']} | "
                         f"{pred['predicted']:.0f} | {pred['increase_percent']:.1f}% |")
        
        # 建议
        report.append("\n## 扩容建议")
        for resource, pred in predictions.items():
            if pred['increase_percent'] > 70:
                report.append(f"⚠ {resource} 需要扩容规划")
        
        return '\n'.join(report)
```

## 4. 故障处理

### 4.1 故障分级与响应

#### 4.1.1 故障级别定义
| 级别 | 描述 | 影响范围 | 响应时间 | 处理优先级 |
|-----|------|---------|---------|-----------|
| P0 | 严重故障 | 全站不可用 | 5分钟 | 最高 |
| P1 | 重大故障 | 核心功能不可用 | 15分钟 | 高 |
| P2 | 一般故障 | 部分功能受影响 | 30分钟 | 中 |
| P3 | 轻微故障 | 用户体验问题 | 2小时 | 低 |

#### 4.1.2 故障处理流程
```python
# incident_handler.py
class IncidentHandler:
    def __init__(self):
        self.incidents = []
        self.notification_channels = ['email', 'sms', 'webhook']
    
    async def handle_incident(self, incident_type, severity, description):
        """处理故障事件"""
        incident = {
            'id': self.generate_incident_id(),
            'type': incident_type,
            'severity': severity,
            'description': description,
            'status': 'open',
            'created_at': datetime.now(),
            'timeline': []
        }
        
        # 1. 记录事件
        self.log_incident(incident)
        
        # 2. 通知相关人员
        await self.notify_team(incident)
        
        # 3. 执行自动恢复
        if incident_type in self.auto_recovery_actions:
            await self.attempt_auto_recovery(incident)
        
        # 4. 创建故障单
        ticket_id = await self.create_ticket(incident)
        incident['ticket_id'] = ticket_id
        
        return incident
    
    async def attempt_auto_recovery(self, incident):
        """尝试自动恢复"""
        recovery_actions = {
            'service_down': self.restart_service,
            'database_connection_lost': self.reconnect_database,
            'high_memory_usage': self.clear_cache,
            'disk_full': self.clean_disk_space
        }
        
        action = recovery_actions.get(incident['type'])
        if action:
            try:
                result = await action()
                incident['timeline'].append({
                    'time': datetime.now(),
                    'action': 'auto_recovery_attempted',
                    'result': result
                })
                
                if result['success']:
                    incident['status'] = 'auto_resolved'
                    await self.notify_team(incident, "故障已自动恢复")
            except Exception as e:
                incident['timeline'].append({
                    'time': datetime.now(),
                    'action': 'auto_recovery_failed',
                    'error': str(e)
                })
```

### 4.2 常见故障处理

#### 4.2.1 数据库故障处理
```bash
#!/bin/bash
# db_recovery.sh - 数据库故障恢复脚本

handle_db_connection_issue() {
    echo "处理数据库连接问题..."
    
    # 1. 检查PostgreSQL服务状态
    if ! systemctl is-active --quiet postgresql; then
        echo "PostgreSQL服务未运行，尝试启动..."
        systemctl start postgresql
        sleep 5
    fi
    
    # 2. 检查连接数
    current_connections=$(psql -U postgres -t -c "SELECT count(*) FROM pg_stat_activity;")
    max_connections=$(psql -U postgres -t -c "SHOW max_connections;")
    
    if [ $current_connections -gt $((max_connections * 90 / 100)) ]; then
        echo "连接数过多，清理空闲连接..."
        psql -U postgres -c "SELECT pg_terminate_backend(pid) 
                              FROM pg_stat_activity 
                              WHERE state = 'idle' 
                              AND state_change < NOW() - INTERVAL '10 minutes';"
    fi
    
    # 3. 检查锁等待
    psql -U postgres -c "SELECT pid, usename, query, waiting 
                          FROM pg_stat_activity 
                          WHERE waiting = true;"
}

handle_db_performance_issue() {
    echo "处理数据库性能问题..."
    
    # 1. 取消长时间运行的查询
    psql -U postgres -c "SELECT pg_cancel_backend(pid) 
                          FROM pg_stat_activity 
                          WHERE (NOW() - pg_stat_activity.query_start) > interval '5 minutes' 
                          AND state = 'active';"
    
    # 2. 更新统计信息
    psql -U education_user -d education_ai_db -c "ANALYZE;"
    
    # 3. 重置查询计划缓存
    psql -U postgres -c "DISCARD PLANS;"
}
```

#### 4.2.2 应用故障处理
```python
# app_troubleshooter.py
import asyncio
import aiohttp
import psutil

class AppTroubleshooter:
    async def diagnose_high_cpu(self):
        """诊断CPU占用过高"""
        diagnosis = []
        
        # 1. 获取进程CPU使用情况
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
            if proc.info['cpu_percent'] > 50:
                processes.append(proc.info)
        
        diagnosis.append(f"高CPU进程: {processes}")
        
        # 2. 检查是否有死循环
        # 分析应用日志中的重复模式
        
        # 3. 检查数据库慢查询
        slow_queries = await self.check_slow_queries()
        if slow_queries:
            diagnosis.append(f"发现慢查询: {len(slow_queries)}个")
        
        return diagnosis
    
    async def diagnose_memory_leak(self):
        """诊断内存泄漏"""
        diagnosis = []
        
        # 1. 检查内存增长趋势
        memory_trend = await self.analyze_memory_trend()
        if memory_trend['growing']:
            diagnosis.append(f"内存持续增长: {memory_trend['rate']}MB/小时")
        
        # 2. 分析对象数量
        object_counts = await self.get_object_counts()
        diagnosis.append(f"对象统计: {object_counts}")
        
        # 3. 检查缓存大小
        cache_size = await self.check_cache_size()
        if cache_size > 1024 * 1024 * 1024:  # 1GB
            diagnosis.append(f"缓存过大: {cache_size / 1024 / 1024 / 1024:.2f}GB")
        
        return diagnosis
    
    async def fix_common_issues(self):
        """修复常见问题"""
        fixes_applied = []
        
        # 1. 清理过期会话
        cleaned = await self.clean_expired_sessions()
        if cleaned > 0:
            fixes_applied.append(f"清理了 {cleaned} 个过期会话")
        
        # 2. 重启工作进程
        if await self.should_restart_workers():
            await self.restart_workers()
            fixes_applied.append("重启了工作进程")
        
        # 3. 清理临时文件
        cleaned_size = await self.clean_temp_files()
        if cleaned_size > 0:
            fixes_applied.append(f"清理了 {cleaned_size}MB 临时文件")
        
        return fixes_applied
```

## 5. 备份与恢复

### 5.1 备份策略

#### 5.1.1 自动备份脚本
```bash
#!/bin/bash
# automated_backup.sh - 自动备份脚本

# 配置
BACKUP_ROOT="/backup"
DB_NAME="education_ai_db"
DB_USER="education_user"
RETENTION_DAYS=30
S3_BUCKET="s3://education-ai-backups"

# 创建备份目录
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$BACKUP_ROOT/$DATE"
mkdir -p $BACKUP_DIR

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $BACKUP_DIR/backup.log
}

# 1. 数据库备份
backup_database() {
    log "开始数据库备份..."
    
    # 全量备份
    pg_dump -U $DB_USER -h localhost -p 5433 $DB_NAME -Fc -f $BACKUP_DIR/database.dump
    
    if [ $? -eq 0 ]; then
        log "数据库备份成功"
        
        # 压缩备份
        gzip -9 $BACKUP_DIR/database.dump
        
        # 生成校验和
        sha256sum $BACKUP_DIR/database.dump.gz > $BACKUP_DIR/database.dump.gz.sha256
    else
        log "数据库备份失败！"
        return 1
    fi
}

# 2. 文件备份
backup_files() {
    log "开始文件备份..."
    
    # 备份上传的文件
    tar -czf $BACKUP_DIR/uploads.tar.gz /app/uploads 2>/dev/null
    
    # 备份配置文件
    tar -czf $BACKUP_DIR/configs.tar.gz \
        /etc/nginx/sites-available/education-ai \
        /app/.env \
        /etc/systemd/system/education-api.service \
        2>/dev/null
    
    log "文件备份完成"
}

# 3. Redis备份
backup_redis() {
    log "开始Redis备份..."
    
    redis-cli -p 6380 --rdb $BACKUP_DIR/redis.rdb
    gzip -9 $BACKUP_DIR/redis.rdb
    
    log "Redis备份完成"
}

# 4. 上传到云存储
upload_to_cloud() {
    log "上传备份到云存储..."
    
    # 上传到S3
    aws s3 sync $BACKUP_DIR $S3_BUCKET/$DATE/ --storage-class GLACIER
    
    if [ $? -eq 0 ]; then
        log "云存储上传成功"
        
        # 记录备份元数据
        echo "{
            \"date\": \"$DATE\",
            \"size\": \"$(du -sh $BACKUP_DIR | cut -f1)\",
            \"location\": \"$S3_BUCKET/$DATE/\",
            \"type\": \"full\",
            \"status\": \"success\"
        }" > $BACKUP_DIR/metadata.json
    else
        log "云存储上传失败！"
        return 1
    fi
}

# 5. 清理旧备份
cleanup_old_backups() {
    log "清理旧备份..."
    
    # 本地清理
    find $BACKUP_ROOT -type d -mtime +$RETENTION_DAYS -exec rm -rf {} \; 2>/dev/null
    
    # 云端清理（保留更长时间）
    aws s3 ls $S3_BUCKET/ | while read -r line; do
        backup_date=$(echo $line | awk '{print $2}' | tr -d '/')
        if [[ ! -z "$backup_date" ]]; then
            backup_timestamp=$(date -d "${backup_date:0:8}" +%s 2>/dev/null)
            current_timestamp=$(date +%s)
            age_days=$(( ($current_timestamp - $backup_timestamp) / 86400 ))
            
            if [ $age_days -gt 90 ]; then
                log "删除90天前的云备份: $backup_date"
                aws s3 rm $S3_BUCKET/$backup_date/ --recursive
            fi
        fi
    done
}

# 主流程
main() {
    log "=== 开始自动备份 ==="
    
    # 执行备份
    backup_database && \
    backup_files && \
    backup_redis && \
    upload_to_cloud && \
    cleanup_old_backups
    
    if [ $? -eq 0 ]; then
        log "=== 备份完成 ==="
        
        # 发送成功通知
        send_notification "备份成功" "备份完成，大小: $(du -sh $BACKUP_DIR | cut -f1)"
    else
        log "=== 备份失败！ ==="
        
        # 发送失败告警
        send_alert "备份失败" "请立即检查备份系统"
    fi
}

# 执行主流程
main
```

### 5.2 恢复流程

#### 5.2.1 恢复脚本
```bash
#!/bin/bash
# restore_system.sh - 系统恢复脚本

# 恢复前检查
pre_restore_check() {
    echo "执行恢复前检查..."
    
    # 1. 确认恢复文件存在
    if [ ! -f "$BACKUP_FILE" ]; then
        echo "错误: 备份文件不存在"
        exit 1
    fi
    
    # 2. 验证备份完整性
    if [ -f "${BACKUP_FILE}.sha256" ]; then
        echo "验证备份完整性..."
        sha256sum -c "${BACKUP_FILE}.sha256"
        if [ $? -ne 0 ]; then
            echo "错误: 备份文件损坏"
            exit 1
        fi
    fi
    
    # 3. 备份当前数据
    echo "备份当前数据..."
    pg_dump -U $DB_USER $DB_NAME > /tmp/current_backup_$(date +%Y%m%d_%H%M%S).sql
}

# 数据库恢复
restore_database() {
    echo "开始数据库恢复..."
    
    # 1. 停止应用服务
    systemctl stop education-api
    
    # 2. 清空当前数据库
    psql -U postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"
    psql -U postgres -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"
    
    # 3. 恢复数据
    gunzip -c $BACKUP_FILE | pg_restore -U $DB_USER -d $DB_NAME -v
    
    # 4. 验证恢复
    table_count=$(psql -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
    echo "恢复完成，共恢复 $table_count 个表"
    
    # 5. 重启服务
    systemctl start education-api
}

# 文件恢复
restore_files() {
    echo "开始文件恢复..."
    
    # 解压文件
    tar -xzf $UPLOADS_BACKUP -C /
    tar -xzf $CONFIGS_BACKUP -C /
    
    # 设置权限
    chown -R app:app /app/uploads
    chmod -R 755 /app/uploads
}

# 验证恢复
verify_restore() {
    echo "验证恢复结果..."
    
    # 1. 检查数据库连接
    if psql -U $DB_USER -d $DB_NAME -c "SELECT 1" > /dev/null 2>&1; then
        echo "✓ 数据库连接正常"
    else
        echo "✗ 数据库连接失败"
        return 1
    fi
    
    # 2. 检查API响应
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
    if [ $response -eq 200 ]; then
        echo "✓ API响应正常"
    else
        echo "✗ API响应异常"
        return 1
    fi
    
    # 3. 检查数据完整性
    user_count=$(psql -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM users;")
    echo "用户数: $user_count"
    
    return 0
}
```

## 6. 监控告警

### 6.1 告警规则配置

#### 6.1.1 Prometheus告警规则
```yaml
# prometheus/alerts.yml
groups:
  - name: education_ai_alerts
    interval: 30s
    rules:
      # 服务可用性
      - alert: ServiceDown
        expr: up{job="education-api"} == 0
        for: 2m
        labels:
          severity: critical
          team: backend
        annotations:
          summary: "服务 {{ $labels.instance }} 已停止"
          description: "教育AI服务已经停止超过2分钟"
      
      # CPU使用率
      - alert: HighCPUUsage
        expr: cpu_usage_percent > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "CPU使用率过高"
          description: "CPU使用率超过80%已持续5分钟，当前值: {{ $value }}%"
      
      # 内存使用率
      - alert: HighMemoryUsage
        expr: memory_usage_percent > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "内存使用率过高"
          description: "内存使用率超过85%已持续5分钟，当前值: {{ $value }}%"
      
      # 磁盘空间
      - alert: DiskSpaceLow
        expr: disk_usage_percent > 90
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "磁盘空间不足"
          description: "磁盘 {{ $labels.mount_point }} 使用率超过90%，当前值: {{ $value }}%"
      
      # API错误率
      - alert: HighAPIErrorRate
        expr: |
          sum(rate(api_requests_total{status=~"5.."}[5m])) / 
          sum(rate(api_requests_total[5m])) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "API错误率过高"
          description: "API错误率超过5%，当前值: {{ $value | humanizePercentage }}"
      
      # 数据库连接池
      - alert: DatabaseConnectionPoolExhausted
        expr: db_pool_used / db_pool_size > 0.9
        for: 3m
        labels:
          severity: warning
        annotations:
          summary: "数据库连接池即将耗尽"
          description: "数据库连接池使用率超过90%"
```

### 6.2 告警通知

#### 6.2.1 多渠道通知
```python
# alert_notifier.py
import aiohttp
import smtplib
from email.mime.text import MIMEText
from typing import Dict, List

class AlertNotifier:
    def __init__(self, config):
        self.config = config
        self.channels = {
            'email': self.send_email,
            'webhook': self.send_webhook,
            'sms': self.send_sms,
            'dingtalk': self.send_dingtalk
        }
    
    async def notify(self, alert: Dict, channels: List[str]):
        """发送告警通知"""
        for channel in channels:
            if channel in self.channels:
                try:
                    await self.channels[channel](alert)
                except Exception as e:
                    logger.error(f"发送{channel}通知失败: {e}")
    
    async def send_email(self, alert: Dict):
        """发送邮件通知"""
        msg = MIMEText(self.format_alert_message(alert))
        msg['Subject'] = f"[{alert['severity']}] {alert['summary']}"
        msg['From'] = self.config['email']['from']
        msg['To'] = ', '.join(self.config['email']['to'])
        
        with smtplib.SMTP(self.config['email']['smtp_host']) as server:
            server.send_message(msg)
    
    async def send_webhook(self, alert: Dict):
        """发送Webhook通知"""
        async with aiohttp.ClientSession() as session:
            await session.post(
                self.config['webhook']['url'],
                json={
                    'text': self.format_alert_message(alert),
                    'alert': alert
                }
            )
    
    async def send_dingtalk(self, alert: Dict):
        """发送钉钉通知"""
        webhook_url = self.config['dingtalk']['webhook']
        
        # 根据严重程度设置@人员
        at_mobiles = []
        if alert['severity'] == 'critical':
            at_mobiles = self.config['dingtalk']['critical_contacts']
        
        message = {
            "msgtype": "markdown",
            "markdown": {
                "title": f"【{alert['severity']}】监控告警",
                "text": f"## {alert['summary']}\n\n"
                       f"> **详情**: {alert['description']}\n\n"
                       f"> **时间**: {alert['timestamp']}\n\n"
                       f"> **级别**: {alert['severity']}\n"
            },
            "at": {
                "atMobiles": at_mobiles,
                "isAtAll": alert['severity'] == 'critical'
            }
        }
        
        async with aiohttp.ClientSession() as session:
            await session.post(webhook_url, json=message)
    
    def format_alert_message(self, alert: Dict) -> str:
        """格式化告警消息"""
        return f"""
告警通知
========
摘要: {alert['summary']}
详情: {alert['description']}
级别: {alert['severity']}
时间: {alert['timestamp']}
标签: {alert.get('labels', {})}
        """
```

## 7. 维护工具箱

### 7.1 常用维护命令

#### 7.1.1 快速诊断命令集
```bash
# maintenance_toolkit.sh

# 系统状态总览
system_overview() {
    echo "=== 系统状态总览 ==="
    echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}')%"
    echo "内存: $(free -m | awk 'NR==2{printf "%.1f%%", $3*100/$2}')"
    echo "磁盘: $(df -h / | awk 'NR==2{print $5}')"
    echo "负载: $(uptime | awk -F'load average:' '{print $2}')"
    echo "连接数: $(ss -s | grep estab | awk '{print $4}')"
}

# 查找大文件
find_large_files() {
    echo "=== 查找大于100MB的文件 ==="
    find / -type f -size +100M -exec ls -lh {} \; 2>/dev/null | \
        awk '{print $5, $9}' | sort -rh | head -20
}

# 清理系统
system_cleanup() {
    echo "=== 系统清理 ==="
    
    # 清理包缓存
    apt-get clean
    
    # 清理日志
    find /var/log -type f -name "*.log" -mtime +30 -delete
    
    # 清理临时文件
    find /tmp -type f -atime +7 -delete
    
    # 清理Docker
    docker system prune -af --volumes
}

# 性能分析
performance_analysis() {
    echo "=== 性能分析 ==="
    
    # IO统计
    iostat -x 1 5
    
    # 网络统计
    netstat -i
    
    # 进程统计
    ps aux --sort=-%cpu | head -10
}
```

### 7.2 维护检查清单

#### 7.2.1 日常检查清单
- [ ] 服务运行状态
- [ ] 系统资源使用率
- [ ] 错误日志检查
- [ ] 备份完成情况
- [ ] 安全事件检查

#### 7.2.2 周检查清单
- [ ] 数据库性能分析
- [ ] 慢查询优化
- [ ] 安全更新检查
- [ ] 存储空间清理
- [ ] 用户访问分析

#### 7.2.3 月检查清单
- [ ] 系统性能趋势分析
- [ ] 容量规划评估
- [ ] 依赖包更新
- [ ] 安全审计
- [ ] 灾难恢复演练

## 8. 维护文档

### 8.1 维护记录模板
```markdown
# 维护记录

## 基本信息
- 日期: 2024-07-05
- 维护人员: 系统管理员
- 维护类型: 定期维护/紧急维护
- 持续时间: 2小时

## 维护内容
1. 数据库优化
   - 执行VACUUM FULL
   - 重建索引
   - 更新统计信息

2. 系统更新
   - 更新操作系统补丁
   - 更新应用依赖包

## 发现的问题
- 问题1: 数据库连接池配置过小
  - 解决方案: 调整连接池大小从20到50

## 后续建议
- 增加内存到32GB
- 考虑数据库读写分离

## 验证结果
- [ ] 所有服务正常启动
- [ ] API响应时间正常
- [ ] 无错误日志
```

### 8.2 知识库维护

维护团队应该建立并维护知识库，包括：
- 常见问题解决方案
- 系统架构文档
- 操作手册
- 故障案例分析
- 最佳实践指南

---

*维护指南版本：v1.0.0 | 更新日期：2024年7月*