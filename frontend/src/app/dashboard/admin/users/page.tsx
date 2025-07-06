"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import {
  Search,
  Filter,
  UserPlus,
  Shield,
  Users,
  UserCheck,
  AlertCircle,
  Edit,
  Trash,
  Key,
  MoreVertical,
  Download,
  Upload,
} from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import DashboardLayout from "@/components/layout/dashboard-layout"
import api from "@/lib/api"
import toast from "react-hot-toast"
import { cn } from "@/lib/utils"
import { format } from "date-fns"
import { zhCN } from "date-fns/locale"

interface User {
  id: number
  username: string
  full_name: string
  email: string
  role: "student" | "teacher" | "admin"
  is_active: boolean
  created_at: string
  last_login?: string
  courses_count?: number
  assignments_count?: number
}

export default function AdminUsersPage() {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedRole, setSelectedRole] = useState<string>("all")
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [isResetPasswordDialogOpen, setIsResetPasswordDialogOpen] = useState(false)
  
  const [formData, setFormData] = useState({
    username: "",
    password: "",
    full_name: "",
    email: "",
    role: "student",
  })

  const [editFormData, setEditFormData] = useState({
    full_name: "",
    email: "",
    role: "",
    is_active: true,
  })

  const [newPassword, setNewPassword] = useState("")

  useEffect(() => {
    fetchUsers()
  }, [selectedRole])

  const fetchUsers = async () => {
    try {
      const params = selectedRole !== "all" ? { role: selectedRole } : {}
      const response = await api.get("/api/admin/users", { params })
      setUsers(response.data)
    } catch (error) {
      toast.error("获取用户列表失败")
    } finally {
      setLoading(false)
    }
  }

  const handleCreateUser = async () => {
    try {
      const response = await api.post("/api/admin/users", formData)
      setUsers([...users, response.data])
      toast.success("用户创建成功")
      setIsCreateDialogOpen(false)
      resetForm()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "创建失败，请重试")
    }
  }

  const handleUpdateUser = async () => {
    if (!selectedUser) return

    try {
      const response = await api.put(`/api/admin/users/${selectedUser.id}`, editFormData)
      setUsers(users.map(u => u.id === selectedUser.id ? response.data : u))
      toast.success("用户信息更新成功")
      setIsEditDialogOpen(false)
      setSelectedUser(null)
    } catch (error) {
      toast.error("更新失败，请重试")
    }
  }

  const handleDeleteUser = async (userId: number) => {
    if (!confirm("确定要删除这个用户吗？此操作不可恢复。")) return

    try {
      await api.delete(`/api/admin/users/${userId}`)
      setUsers(users.filter(u => u.id !== userId))
      toast.success("用户已删除")
    } catch (error) {
      toast.error("删除失败，请重试")
    }
  }

  const handleResetPassword = async () => {
    if (!selectedUser) return

    try {
      await api.post(`/api/admin/users/${selectedUser.id}/reset-password`, {
        new_password: newPassword
      })
      toast.success("密码重置成功")
      setIsResetPasswordDialogOpen(false)
      setNewPassword("")
      setSelectedUser(null)
    } catch (error) {
      toast.error("密码重置失败，请重试")
    }
  }

  const handleToggleUserStatus = async (user: User) => {
    try {
      await api.put(`/api/admin/users/${user.id}`, {
        ...user,
        is_active: !user.is_active
      })
      setUsers(users.map(u => 
        u.id === user.id ? { ...u, is_active: !u.is_active } : u
      ))
      toast.success(`用户已${user.is_active ? '禁用' : '启用'}`)
    } catch (error) {
      toast.error("操作失败，请重试")
    }
  }

  const resetForm = () => {
    setFormData({
      username: "",
      password: "",
      full_name: "",
      email: "",
      role: "student",
    })
  }

  const filteredUsers = users.filter(user =>
    user.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
    user.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    user.email.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const getUserStats = () => {
    const total = users.length
    const active = users.filter(u => u.is_active).length
    const students = users.filter(u => u.role === "student").length
    const teachers = users.filter(u => u.role === "teacher").length
    const admins = users.filter(u => u.role === "admin").length

    return { total, active, students, teachers, admins }
  }

  const stats = getUserStats()

  const getRoleBadgeVariant = (role: string) => {
    switch (role) {
      case "admin":
        return "destructive"
      case "teacher":
        return "default"
      case "student":
        return "secondary"
      default:
        return "outline"
    }
  }

  const getRoleIcon = (role: string) => {
    switch (role) {
      case "admin":
        return <Shield className="w-3 h-3" />
      case "teacher":
        return <UserCheck className="w-3 h-3" />
      case "student":
        return <Users className="w-3 h-3" />
      default:
        return null
    }
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">用户管理</h1>
            <p className="text-muted-foreground mt-1">管理系统中的所有用户账户</p>
          </div>
          <div className="flex items-center gap-2">
            <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
              <DialogTrigger asChild>
                <Button>
                  <UserPlus className="w-4 h-4" />
                  创建用户
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>创建新用户</DialogTitle>
                  <DialogDescription>
                    填写信息以创建新的用户账户
                  </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="grid gap-2">
                    <Label htmlFor="username">用户名</Label>
                    <Input
                      id="username"
                      value={formData.username}
                      onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                      placeholder="输入用户名"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="password">密码</Label>
                    <Input
                      id="password"
                      type="password"
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      placeholder="输入密码"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="full_name">姓名</Label>
                    <Input
                      id="full_name"
                      value={formData.full_name}
                      onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                      placeholder="输入真实姓名"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="email">邮箱</Label>
                    <Input
                      id="email"
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      placeholder="输入邮箱地址"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="role">角色</Label>
                    <Select
                      value={formData.role}
                      onValueChange={(value) => setFormData({ ...formData, role: value })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="student">学生</SelectItem>
                        <SelectItem value="teacher">教师</SelectItem>
                        <SelectItem value="admin">管理员</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="flex justify-end gap-2">
                  <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                    取消
                  </Button>
                  <Button onClick={handleCreateUser}>创建</Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        {/* Stats */}
        <div className="grid gap-4 md:grid-cols-5">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">总用户数</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total}</div>
              <p className="text-xs text-muted-foreground mt-1">
                活跃 {stats.active} 人
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">学生</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.students}</div>
              <Badge variant="secondary" className="mt-1">
                <Users className="w-3 h-3 mr-1" />
                学生
              </Badge>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">教师</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.teachers}</div>
              <Badge variant="default" className="mt-1">
                <UserCheck className="w-3 h-3 mr-1" />
                教师
              </Badge>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">管理员</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.admins}</div>
              <Badge variant="destructive" className="mt-1">
                <Shield className="w-3 h-3 mr-1" />
                管理员
              </Badge>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">活跃率</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {stats.total > 0 ? Math.round((stats.active / stats.total) * 100) : 0}%
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                最近7天
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="搜索用户名、姓名或邮箱..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          <Select value={selectedRole} onValueChange={setSelectedRole}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="筛选角色" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">所有角色</SelectItem>
              <SelectItem value="student">学生</SelectItem>
              <SelectItem value="teacher">教师</SelectItem>
              <SelectItem value="admin">管理员</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Users Table */}
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>用户</TableHead>
                  <TableHead>角色</TableHead>
                  <TableHead>邮箱</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>注册时间</TableHead>
                  <TableHead>最后登录</TableHead>
                  <TableHead>操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredUsers.map((user) => (
                  <TableRow key={user.id}>
                    <TableCell>
                      <div>
                        <p className="font-medium">{user.full_name}</p>
                        <p className="text-sm text-muted-foreground">@{user.username}</p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={getRoleBadgeVariant(user.role)} className="gap-1">
                        {getRoleIcon(user.role)}
                        {user.role === "student" ? "学生" : 
                         user.role === "teacher" ? "教师" : "管理员"}
                      </Badge>
                    </TableCell>
                    <TableCell>{user.email}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Switch
                          checked={user.is_active}
                          onCheckedChange={() => handleToggleUserStatus(user)}
                        />
                        <span className={cn(
                          "text-sm",
                          user.is_active ? "text-green-600" : "text-red-600"
                        )}>
                          {user.is_active ? "启用" : "禁用"}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      {format(new Date(user.created_at), "yyyy-MM-dd", { locale: zhCN })}
                    </TableCell>
                    <TableCell>
                      {user.last_login ? (
                        format(new Date(user.last_login), "MM-dd HH:mm", { locale: zhCN })
                      ) : (
                        <span className="text-muted-foreground">从未登录</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreVertical className="w-4 h-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => {
                            setSelectedUser(user)
                            setEditFormData({
                              full_name: user.full_name,
                              email: user.email,
                              role: user.role,
                              is_active: user.is_active,
                            })
                            setIsEditDialogOpen(true)
                          }}>
                            <Edit className="w-4 h-4 mr-2" />
                            编辑信息
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => {
                            setSelectedUser(user)
                            setIsResetPasswordDialogOpen(true)
                          }}>
                            <Key className="w-4 h-4 mr-2" />
                            重置密码
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem 
                            onClick={() => handleDeleteUser(user.id)}
                            className="text-destructive"
                          >
                            <Trash className="w-4 h-4 mr-2" />
                            删除用户
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* Edit User Dialog */}
        <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>编辑用户信息</DialogTitle>
              <DialogDescription>
                修改用户的基本信息
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="edit-full_name">姓名</Label>
                <Input
                  id="edit-full_name"
                  value={editFormData.full_name}
                  onChange={(e) => setEditFormData({ ...editFormData, full_name: e.target.value })}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="edit-email">邮箱</Label>
                <Input
                  id="edit-email"
                  type="email"
                  value={editFormData.email}
                  onChange={(e) => setEditFormData({ ...editFormData, email: e.target.value })}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="edit-role">角色</Label>
                <Select
                  value={editFormData.role}
                  onValueChange={(value) => setEditFormData({ ...editFormData, role: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="student">学生</SelectItem>
                    <SelectItem value="teacher">教师</SelectItem>
                    <SelectItem value="admin">管理员</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
                取消
              </Button>
              <Button onClick={handleUpdateUser}>保存</Button>
            </div>
          </DialogContent>
        </Dialog>

        {/* Reset Password Dialog */}
        <Dialog open={isResetPasswordDialogOpen} onOpenChange={setIsResetPasswordDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>重置密码</DialogTitle>
              <DialogDescription>
                为用户 {selectedUser?.full_name} 设置新密码
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="new-password">新密码</Label>
                <Input
                  id="new-password"
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="输入新密码"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => {
                setIsResetPasswordDialogOpen(false)
                setNewPassword("")
              }}>
                取消
              </Button>
              <Button onClick={handleResetPassword}>重置密码</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  )
}