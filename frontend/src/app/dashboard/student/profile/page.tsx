"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import {
  User,
  Mail,
  Lock,
  Save,
  Camera,
  TrendingUp,
  BookOpen,
  Clock,
  Award,
  Calendar,
  AlertCircle,
} from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import DashboardLayout from "@/components/layout/dashboard-layout"
import { useAuthStore } from "@/stores/auth-store"
import api from "@/lib/api"
import { extractData } from "@/lib/api-utils"
import toast from "react-hot-toast"
import { cn } from "@/lib/utils"

interface ProfileData {
  id: number
  username: string
  email: string
  full_name: string
  avatar_url?: string
  created_at: string
}

interface LearningStats {
  total_courses: number
  completed_courses: number
  total_assignments: number
  completed_assignments: number
  average_score: number
  study_days: number
  total_study_time: number
}

export default function ProfilePage() {
  const { user, updateUser } = useAuthStore()
  const [profile, setProfile] = useState<ProfileData | null>(null)
  const [stats, setStats] = useState<LearningStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [isEditing, setIsEditing] = useState(false)
  const [formData, setFormData] = useState({
    full_name: "",
    email: "",
  })
  const [passwordData, setPasswordData] = useState({
    current_password: "",
    new_password: "",
    confirm_password: "",
  })

  useEffect(() => {
    fetchProfile()
    fetchStats()
  }, [])

  const fetchProfile = async () => {
    try {
      const response = await api.get("/api/student/profile/me")
      // 使用 extractData 统一处理响应格式
      const profileData = extractData<ProfileData>(response)
      setProfile(profileData)
      setFormData({
        full_name: profileData.full_name,
        email: profileData.email,
      })
      // 如果头像URL有变化，更新 auth store
      if (user && profileData.avatar_url !== user.avatar_url) {
        updateUser({ ...user, avatar_url: profileData.avatar_url })
      }
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.log("获取个人资料失败:", error)
      }
      toast.error("获取个人资料失败")
    }
  }

  const fetchStats = async () => {
    try {
      const response = await api.get("/api/student/profile/me/stats")
      // 使用 extractData 统一处理响应格式
      const statsData = extractData<LearningStats>(response)
      setStats(statsData)
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.log("获取学习统计失败:", error)
      }
    } finally {
      setLoading(false)
    }
  }

  const handleUpdateProfile = async () => {
    try {
      const response = await api.put("/api/student/profile/me", formData)
      setProfile(response.data)
      updateUser(response.data)
      toast.success("个人资料更新成功")
      setIsEditing(false)
    } catch (error) {
      toast.error("更新失败，请重试")
    }
  }

  const handleChangePassword = async () => {
    if (passwordData.new_password !== passwordData.confirm_password) {
      toast.error("两次输入的密码不一致")
      return
    }

    try {
      await api.post("/api/student/profile/me/password", {
        current_password: passwordData.current_password,
        new_password: passwordData.new_password,
      })
      toast.success("密码修改成功")
      setPasswordData({
        current_password: "",
        new_password: "",
        confirm_password: "",
      })
    } catch (error) {
      toast.error("密码修改失败，请检查当前密码是否正确")
    }
  }

  const handleAvatarUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const formData = new FormData()
    formData.append("file", file)

    try {
      const response = await api.post("/api/student/profile/me/avatar", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      })
      // 更新头像URL
      const avatarUrl = response.data?.data?.avatar_url || response.data?.avatar_url
      if (avatarUrl && profile) {
        setProfile({ ...profile, avatar_url: avatarUrl })
        // 更新 auth store 中的用户信息
        if (user) {
          updateUser({ ...user, avatar_url: avatarUrl })
        }
      }
      toast.success("头像上传成功")
    } catch (error) {
      toast.error("头像上传失败")
    }
  }

  if (loading || !profile) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-96">
          <div className="animate-pulse text-muted-foreground">加载中...</div>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold">个人中心</h1>
          <p className="text-muted-foreground mt-1">管理你的个人信息和学习数据</p>
        </div>

        <Tabs defaultValue="profile" className="space-y-4">
          <TabsList>
            <TabsTrigger value="profile">个人资料</TabsTrigger>
            <TabsTrigger value="stats">学习统计</TabsTrigger>
            <TabsTrigger value="security">安全设置</TabsTrigger>
          </TabsList>

          {/* Profile Tab */}
          <TabsContent value="profile" className="space-y-6">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>基本信息</CardTitle>
                  {!isEditing ? (
                    <Button onClick={() => setIsEditing(true)}>编辑资料</Button>
                  ) : (
                    <div className="space-x-2">
                      <Button variant="outline" onClick={() => setIsEditing(false)}>
                        取消
                      </Button>
                      <Button onClick={handleUpdateProfile}>
                        <Save className="w-4 h-4 mr-2" />
                        保存
                      </Button>
                    </div>
                  )}
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Avatar */}
                <div className="flex items-center gap-6">
                  <div className="relative">
                    <Avatar className="w-24 h-24">
                      <AvatarImage src={profile.avatar_url} />
                      <AvatarFallback>{profile.full_name?.[0] || profile.username?.[0] || 'U'}</AvatarFallback>
                    </Avatar>
                    <label
                      htmlFor="avatar-upload"
                      className="absolute bottom-0 right-0 p-1 bg-primary text-primary-foreground rounded-full cursor-pointer hover:bg-primary/90"
                    >
                      <Camera className="w-4 h-4" />
                      <input
                        id="avatar-upload"
                        type="file"
                        className="hidden"
                        accept="image/*"
                        onChange={handleAvatarUpload}
                      />
                    </label>
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold">{profile.full_name}</h3>
                    <p className="text-muted-foreground">@{profile.username}</p>
                  </div>
                </div>

                {/* Form */}
                <div className="grid gap-4">
                  <div className="grid gap-2">
                    <Label htmlFor="full_name">姓名</Label>
                    <Input
                      id="full_name"
                      value={formData.full_name}
                      onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                      disabled={!isEditing}
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="email">邮箱</Label>
                    <Input
                      id="email"
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      disabled={!isEditing}
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="username">用户名</Label>
                    <Input id="username" value={profile.username} disabled />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="created_at">注册时间</Label>
                    <Input
                      id="created_at"
                      value={new Date(profile.created_at).toLocaleDateString()}
                      disabled
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Stats Tab */}
          <TabsContent value="stats" className="space-y-6">
            {stats && (
              <>
                {/* Overview Cards */}
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-medium">学习课程</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">{stats.total_courses}</div>
                      <Progress
                        value={(stats.completed_courses / stats.total_courses) * 100}
                        className="h-1 mt-2"
                      />
                      <p className="text-xs text-muted-foreground mt-1">
                        已完成 {stats.completed_courses} 门
                      </p>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-medium">作业完成</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">{stats.completed_assignments}</div>
                      <Progress
                        value={(stats.completed_assignments / stats.total_assignments) * 100}
                        className="h-1 mt-2"
                      />
                      <p className="text-xs text-muted-foreground mt-1">
                        总计 {stats.total_assignments} 个
                      </p>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-medium">平均成绩</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">{stats.average_score}%</div>
                      <div className="flex items-center gap-1 mt-2">
                        <Award className="w-4 h-4 text-yellow-600" />
                        <span className="text-xs text-muted-foreground">
                          {stats.average_score >= 90 ? "优秀" : stats.average_score >= 80 ? "良好" : "合格"}
                        </span>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-medium">学习天数</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">{stats.study_days}</div>
                      <div className="flex items-center gap-1 mt-2">
                        <Calendar className="w-4 h-4 text-blue-600" />
                        <span className="text-xs text-muted-foreground">
                          累计 {Math.floor(stats.total_study_time / 60)} 小时
                        </span>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Achievements */}
                <Card>
                  <CardHeader>
                    <CardTitle>学习成就</CardTitle>
                    <CardDescription>你在学习过程中获得的成就</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid gap-4 md:grid-cols-3">
                      {[
                        { name: "初学者", desc: "完成第一门课程", icon: BookOpen, earned: true },
                        { name: "勤奋学习", desc: "连续学习7天", icon: Clock, earned: true },
                        { name: "优等生", desc: "平均成绩90分以上", icon: Award, earned: stats.average_score >= 90 },
                      ].map((achievement, index) => (
                        <div
                          key={index}
                          className={cn(
                            "p-4 rounded-lg border-2 transition-all",
                            achievement.earned
                              ? "border-primary bg-primary/5"
                              : "border-muted bg-muted/20 opacity-60"
                          )}
                        >
                          <div className="flex items-center gap-3">
                            <div
                              className={cn(
                                "p-2 rounded-lg",
                                achievement.earned ? "bg-primary/10" : "bg-muted"
                              )}
                            >
                              <achievement.icon
                                className={cn(
                                  "w-6 h-6",
                                  achievement.earned ? "text-primary" : "text-muted-foreground"
                                )}
                              />
                            </div>
                            <div>
                              <p className="font-medium">{achievement.name}</p>
                              <p className="text-xs text-muted-foreground">{achievement.desc}</p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </>
            )}
          </TabsContent>

          {/* Security Tab */}
          <TabsContent value="security" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>修改密码</CardTitle>
                <CardDescription>定期更新密码以保护账户安全</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-2">
                  <Label htmlFor="current_password">当前密码</Label>
                  <Input
                    id="current_password"
                    type="password"
                    value={passwordData.current_password}
                    onChange={(e) =>
                      setPasswordData({ ...passwordData, current_password: e.target.value })
                    }
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="new_password">新密码</Label>
                  <Input
                    id="new_password"
                    type="password"
                    value={passwordData.new_password}
                    onChange={(e) =>
                      setPasswordData({ ...passwordData, new_password: e.target.value })
                    }
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="confirm_password">确认新密码</Label>
                  <Input
                    id="confirm_password"
                    type="password"
                    value={passwordData.confirm_password}
                    onChange={(e) =>
                      setPasswordData({ ...passwordData, confirm_password: e.target.value })
                    }
                  />
                </div>
                <Button onClick={handleChangePassword}>
                  <Lock className="w-4 h-4 mr-2" />
                  修改密码
                </Button>
              </CardContent>
            </Card>

            <Card className="border-destructive">
              <CardHeader>
                <CardTitle className="text-destructive">危险操作</CardTitle>
                <CardDescription>以下操作不可恢复，请谨慎操作</CardDescription>
              </CardHeader>
              <CardContent>
                <Dialog>
                  <DialogTrigger asChild>
                    <Button variant="destructive">
                      <AlertCircle className="w-4 h-4 mr-2" />
                      删除账户
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>确认删除账户？</DialogTitle>
                      <DialogDescription>
                        此操作将永久删除你的账户和所有相关数据，且无法恢复。
                      </DialogDescription>
                    </DialogHeader>
                    <div className="flex justify-end gap-2 mt-4">
                      <Button variant="outline">取消</Button>
                      <Button variant="destructive">确认删除</Button>
                    </div>
                  </DialogContent>
                </Dialog>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  )
}