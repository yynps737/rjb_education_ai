"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import {
  Settings,
  Bell,
  Shield,
  Database,
  Mail,
  Globe,
  Key,
  Users,
  FileText,
  Save,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Server,
  Zap,
  Activity,
  HardDrive,
} from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Switch } from "@/components/ui/switch"
import { Separator } from "@/components/ui/separator"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Alert,
  AlertDescription,
  AlertTitle,
} from "@/components/ui/alert"
import DashboardLayout from "@/components/layout/dashboard-layout"
import api from "@/lib/api"
import { extractData } from "@/lib/api-utils"
import toast from "react-hot-toast"
import { cn } from "@/lib/utils"

interface SystemSettings {
  site_name: string
  site_description: string
  admin_email: string
  support_email: string
  max_file_size: number
  allowed_file_types: string[]
  session_timeout: number
  enable_registration: boolean
  enable_email_verification: boolean
  enable_two_factor: boolean
  maintenance_mode: boolean
  maintenance_message: string
  backup_enabled: boolean
  backup_frequency: string
  backup_retention_days: number
  log_level: string
  log_retention_days: number
  smtp_host: string
  smtp_port: number
  smtp_username: string
  smtp_use_tls: boolean
}

interface SystemInfo {
  version: string
  python_version: string
  database_size: number
  storage_used: number
  storage_total: number
  cpu_usage: number
  memory_usage: number
  memory_total: number
  uptime_hours: number
  active_users: number
  total_courses: number
  total_assignments: number
}

export default function AdminSettingsPage() {
  const [settings, setSettings] = useState<SystemSettings>({
    site_name: "智能教学平台",
    site_description: "基于AI的现代化教学管理系统",
    admin_email: "admin@example.com",
    support_email: "support@example.com",
    max_file_size: 10,
    allowed_file_types: ["pdf", "doc", "docx", "ppt", "pptx", "xls", "xlsx", "jpg", "png"],
    session_timeout: 30,
    enable_registration: true,
    enable_email_verification: false,
    enable_two_factor: false,
    maintenance_mode: false,
    maintenance_message: "系统正在维护中，请稍后再试。",
    backup_enabled: true,
    backup_frequency: "daily",
    backup_retention_days: 30,
    log_level: "INFO",
    log_retention_days: 90,
    smtp_host: "smtp.gmail.com",
    smtp_port: 587,
    smtp_username: "",
    smtp_use_tls: true,
  })

  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [testingEmail, setTestingEmail] = useState(false)
  const [backingUp, setBackingUp] = useState(false)

  useEffect(() => {
    fetchSettings()
    fetchSystemInfo()
    const interval = setInterval(fetchSystemInfo, 30000) // Update every 30 seconds
    return () => clearInterval(interval)
  }, [])

  const fetchSettings = async () => {
    try {
      const response = await api.get("/api/admin/system/settings")
      const data = extractData(response)
      if (data) {
        setSettings(data)
      }
    } catch (error) {
      toast.error("获取系统设置失败")
    } finally {
      setLoading(false)
    }
  }

  const fetchSystemInfo = async () => {
    try {
      const response = await api.get("/api/admin/system/system-info")
      const data = extractData(response)
      if (data) {
        setSystemInfo(data)
      }
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.log("获取系统信息失败", error)
      }
    }
  }

  const handleSaveSettings = async () => {
    setSaving(true)
    try {
      await api.put("/api/admin/system/settings", settings)
      toast.success("设置保存成功")
    } catch (error) {
      toast.error("保存失败，请重试")
    } finally {
      setSaving(false)
    }
  }

  const handleTestEmail = async () => {
    setTestingEmail(true)
    try {
      await api.post("/api/admin/system/test-email", {
        to: settings.admin_email,
        smtp_settings: {
          host: settings.smtp_host,
          port: settings.smtp_port,
          username: settings.smtp_username,
          use_tls: settings.smtp_use_tls,
        },
      })
      toast.success("测试邮件已发送")
    } catch (error) {
      toast.error("邮件发送失败，请检查SMTP设置")
    } finally {
      setTestingEmail(false)
    }
  }

  const handleBackupNow = async () => {
    if (!confirm("确定要立即执行备份吗？这可能需要一些时间。")) return
    
    setBackingUp(true)
    try {
      await api.post("/api/admin/system/backup-now")
      toast.success("备份任务已启动")
    } catch (error) {
      toast.error("备份失败，请重试")
    } finally {
      setBackingUp(false)
    }
  }

  const handleClearCache = async () => {
    if (!confirm("确定要清除系统缓存吗？")) return
    
    try {
      await api.post("/api/admin/system/clear-cache")
      toast.success("缓存已清除")
    } catch (error) {
      toast.error("清除缓存失败")
    }
  }

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return "0 Bytes"
    const k = 1024
    const sizes = ["Bytes", "KB", "MB", "GB", "TB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">系统设置</h1>
            <p className="text-muted-foreground mt-1">配置和管理系统设置</p>
          </div>
          <Button onClick={handleSaveSettings} disabled={saving}>
            <Save className="w-4 h-4 mr-2" />
            {saving ? "保存中..." : "保存设置"}
          </Button>
        </div>

        {/* System Status */}
        {systemInfo && (
          <div className="grid gap-4 md:grid-cols-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  <Server className="w-4 h-4" />
                  系统状态
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                  <span className="text-sm">运行正常</span>
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  运行时间：{Math.round(systemInfo.uptime_hours)}小时
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  <Activity className="w-4 h-4" />
                  资源使用
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span>CPU</span>
                    <span>{systemInfo.cpu_usage}%</span>
                  </div>
                  <Progress value={systemInfo.cpu_usage} className="h-1" />
                  <div className="flex items-center justify-between text-xs">
                    <span>内存</span>
                    <span>{Math.round((systemInfo.memory_usage / systemInfo.memory_total) * 100)}%</span>
                  </div>
                  <Progress value={(systemInfo.memory_usage / systemInfo.memory_total) * 100} className="h-1" />
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  <HardDrive className="w-4 h-4" />
                  存储空间
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-sm">
                  <p>{formatBytes(systemInfo.storage_used)} / {formatBytes(systemInfo.storage_total)}</p>
                  <Progress 
                    value={(systemInfo.storage_used / systemInfo.storage_total) * 100} 
                    className="h-1 mt-2" 
                  />
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  <Database className="w-4 h-4" />
                  数据库
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm">{formatBytes(systemInfo.database_size)}</p>
                <p className="text-xs text-muted-foreground mt-1">
                  PostgreSQL v{systemInfo.version}
                </p>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Settings Tabs */}
        <Tabs defaultValue="general" className="space-y-4">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="general">常规设置</TabsTrigger>
            <TabsTrigger value="security">安全设置</TabsTrigger>
            <TabsTrigger value="email">邮件设置</TabsTrigger>
            <TabsTrigger value="backup">备份设置</TabsTrigger>
            <TabsTrigger value="advanced">高级设置</TabsTrigger>
          </TabsList>

          <TabsContent value="general" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>基本信息</CardTitle>
                <CardDescription>配置网站的基本信息</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-2">
                  <Label htmlFor="site-name">网站名称</Label>
                  <Input
                    id="site-name"
                    value={settings.site_name}
                    onChange={(e) => setSettings({ ...settings, site_name: e.target.value })}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="site-description">网站描述</Label>
                  <Textarea
                    id="site-description"
                    value={settings.site_description}
                    onChange={(e) => setSettings({ ...settings, site_description: e.target.value })}
                    rows={3}
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="grid gap-2">
                    <Label htmlFor="admin-email">管理员邮箱</Label>
                    <Input
                      id="admin-email"
                      type="email"
                      value={settings.admin_email}
                      onChange={(e) => setSettings({ ...settings, admin_email: e.target.value })}
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="support-email">支持邮箱</Label>
                    <Input
                      id="support-email"
                      type="email"
                      value={settings.support_email}
                      onChange={(e) => setSettings({ ...settings, support_email: e.target.value })}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>文件上传设置</CardTitle>
                <CardDescription>配置文件上传的限制</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-2">
                  <Label htmlFor="max-file-size">最大文件大小（MB）</Label>
                  <Input
                    id="max-file-size"
                    type="number"
                    value={settings.max_file_size}
                    onChange={(e) => setSettings({ ...settings, max_file_size: parseInt(e.target.value) })}
                  />
                </div>
                <div className="grid gap-2">
                  <Label>允许的文件类型</Label>
                  <div className="flex flex-wrap gap-2">
                    {settings.allowed_file_types.map((type) => (
                      <Badge key={type} variant="secondary">
                        .{type}
                      </Badge>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="security" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>安全选项</CardTitle>
                <CardDescription>配置系统的安全设置</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>允许用户注册</Label>
                    <p className="text-sm text-muted-foreground">允许新用户自行注册账号</p>
                  </div>
                  <Switch
                    checked={settings.enable_registration}
                    onCheckedChange={(checked) => 
                      setSettings({ ...settings, enable_registration: checked })
                    }
                  />
                </div>
                <Separator />
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>邮箱验证</Label>
                    <p className="text-sm text-muted-foreground">要求新用户验证邮箱地址</p>
                  </div>
                  <Switch
                    checked={settings.enable_email_verification}
                    onCheckedChange={(checked) => 
                      setSettings({ ...settings, enable_email_verification: checked })
                    }
                  />
                </div>
                <Separator />
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>双因素认证</Label>
                    <p className="text-sm text-muted-foreground">启用双因素认证功能</p>
                  </div>
                  <Switch
                    checked={settings.enable_two_factor}
                    onCheckedChange={(checked) => 
                      setSettings({ ...settings, enable_two_factor: checked })
                    }
                  />
                </div>
                <Separator />
                <div className="grid gap-2">
                  <Label htmlFor="session-timeout">会话超时（分钟）</Label>
                  <Input
                    id="session-timeout"
                    type="number"
                    value={settings.session_timeout}
                    onChange={(e) => setSettings({ ...settings, session_timeout: parseInt(e.target.value) })}
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>维护模式</CardTitle>
                <CardDescription>临时关闭网站进行维护</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>启用维护模式</Label>
                    <p className="text-sm text-muted-foreground">用户将看到维护提示</p>
                  </div>
                  <Switch
                    checked={settings.maintenance_mode}
                    onCheckedChange={(checked) => 
                      setSettings({ ...settings, maintenance_mode: checked })
                    }
                  />
                </div>
                {settings.maintenance_mode && (
                  <Alert>
                    <AlertCircle className="h-4 w-4" />
                    <AlertTitle>警告</AlertTitle>
                    <AlertDescription>
                      维护模式已启用，普通用户无法访问系统
                    </AlertDescription>
                  </Alert>
                )}
                <div className="grid gap-2">
                  <Label htmlFor="maintenance-message">维护提示信息</Label>
                  <Textarea
                    id="maintenance-message"
                    value={settings.maintenance_message}
                    onChange={(e) => setSettings({ ...settings, maintenance_message: e.target.value })}
                    rows={3}
                  />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="email" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>SMTP设置</CardTitle>
                <CardDescription>配置邮件发送服务器</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="grid gap-2">
                    <Label htmlFor="smtp-host">SMTP服务器</Label>
                    <Input
                      id="smtp-host"
                      value={settings.smtp_host}
                      onChange={(e) => setSettings({ ...settings, smtp_host: e.target.value })}
                      placeholder="smtp.gmail.com"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="smtp-port">端口</Label>
                    <Input
                      id="smtp-port"
                      type="number"
                      value={settings.smtp_port}
                      onChange={(e) => setSettings({ ...settings, smtp_port: parseInt(e.target.value) })}
                    />
                  </div>
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="smtp-username">用户名</Label>
                  <Input
                    id="smtp-username"
                    value={settings.smtp_username}
                    onChange={(e) => setSettings({ ...settings, smtp_username: e.target.value })}
                    placeholder="your-email@gmail.com"
                  />
                </div>
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>使用TLS加密</Label>
                    <p className="text-sm text-muted-foreground">建议开启以确保邮件安全</p>
                  </div>
                  <Switch
                    checked={settings.smtp_use_tls}
                    onCheckedChange={(checked) => 
                      setSettings({ ...settings, smtp_use_tls: checked })
                    }
                  />
                </div>
                <div className="flex justify-end">
                  <Button variant="outline" onClick={handleTestEmail} disabled={testingEmail}>
                    <Mail className="w-4 h-4 mr-2" />
                    {testingEmail ? "发送中..." : "发送测试邮件"}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="backup" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>自动备份</CardTitle>
                <CardDescription>配置系统自动备份策略</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>启用自动备份</Label>
                    <p className="text-sm text-muted-foreground">定期备份数据库和文件</p>
                  </div>
                  <Switch
                    checked={settings.backup_enabled}
                    onCheckedChange={(checked) => 
                      setSettings({ ...settings, backup_enabled: checked })
                    }
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="backup-frequency">备份频率</Label>
                  <Select
                    value={settings.backup_frequency}
                    onValueChange={(value) => setSettings({ ...settings, backup_frequency: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="hourly">每小时</SelectItem>
                      <SelectItem value="daily">每天</SelectItem>
                      <SelectItem value="weekly">每周</SelectItem>
                      <SelectItem value="monthly">每月</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="backup-retention">备份保留天数</Label>
                  <Input
                    id="backup-retention"
                    type="number"
                    value={settings.backup_retention_days}
                    onChange={(e) => setSettings({ ...settings, backup_retention_days: parseInt(e.target.value) })}
                  />
                </div>
                <div className="flex justify-end">
                  <Button variant="outline" onClick={handleBackupNow} disabled={backingUp}>
                    <Database className="w-4 h-4 mr-2" />
                    {backingUp ? "备份中..." : "立即备份"}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="advanced" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>日志设置</CardTitle>
                <CardDescription>配置系统日志记录</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-2">
                  <Label htmlFor="log-level">日志级别</Label>
                  <Select
                    value={settings.log_level}
                    onValueChange={(value) => setSettings({ ...settings, log_level: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="DEBUG">DEBUG</SelectItem>
                      <SelectItem value="INFO">INFO</SelectItem>
                      <SelectItem value="WARNING">WARNING</SelectItem>
                      <SelectItem value="ERROR">ERROR</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="log-retention">日志保留天数</Label>
                  <Input
                    id="log-retention"
                    type="number"
                    value={settings.log_retention_days}
                    onChange={(e) => setSettings({ ...settings, log_retention_days: parseInt(e.target.value) })}
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>系统维护</CardTitle>
                <CardDescription>执行系统维护操作</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">清除缓存</p>
                    <p className="text-sm text-muted-foreground">清除系统缓存以释放空间</p>
                  </div>
                  <Button variant="outline" onClick={handleClearCache}>
                    <RefreshCw className="w-4 h-4 mr-2" />
                    清除缓存
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  )
}