"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import {
  Search,
  Filter,
  BookOpen,
  Plus,
  Users,
  FileText,
  Calendar,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Edit,
  Trash,
  Eye,
  MoreVertical,
  Download,
  Upload,
  BarChart,
} from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
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
import { extractData } from "@/lib/api-utils"
import toast from "react-hot-toast"
import { cn } from "@/lib/utils"
import { format } from "date-fns"
import { zhCN } from "date-fns/locale"
import {
  LineChart,
  Line,
  BarChart as RechartsBarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts"

interface Course {
  id: number
  title: string
  description: string
  subject: string
  grade_level: number
  teacher_id: number
  teacher_name: string
  student_count: number
  chapter_count: number
  assignment_count: number
  is_published: boolean
  created_at: string
  updated_at: string
  completion_rate: number
  average_score: number
}

interface CourseStats {
  total_courses: number
  published_courses: number
  total_students: number
  total_assignments: number
  subject_distribution: { subject: string; count: number }[]
  grade_distribution: { grade: number; count: number }[]
  monthly_courses: { month: string; count: number }[]
}

interface Teacher {
  id: number
  full_name: string
}

const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#8884D8"]

export default function AdminCoursesPage() {
  const [courses, setCourses] = useState<Course[]>([])
  const [teachers, setTeachers] = useState<Teacher[]>([])
  const [stats, setStats] = useState<CourseStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedSubject, setSelectedSubject] = useState<string>("all")
  const [selectedGrade, setSelectedGrade] = useState<string>("all")
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [selectedCourse, setSelectedCourse] = useState<Course | null>(null)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [isStatsDialogOpen, setIsStatsDialogOpen] = useState(false)
  
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    subject: "",
    grade_level: 1,
    teacher_id: "",
  })

  const [editFormData, setEditFormData] = useState({
    title: "",
    description: "",
    subject: "",
    grade_level: 1,
    teacher_id: "",
    is_published: false,
  })

  useEffect(() => {
    fetchCourses()
    fetchTeachers()
    fetchStats()
  }, [selectedSubject, selectedGrade])

  const fetchCourses = async () => {
    try {
      const params: any = {}
      if (selectedSubject !== "all") params.subject = selectedSubject
      if (selectedGrade !== "all") params.grade_level = selectedGrade
      
      const response = await api.get("/api/admin/courses", { params })
      const data = extractData(response)
      setCourses(data?.courses || [])
    } catch (error) {
      toast.error("获取课程列表失败")
    } finally {
      setLoading(false)
    }
  }

  const fetchTeachers = async () => {
    try {
      const response = await api.get("/api/admin/users", { params: { role: "teacher" } })
      setTeachers(response.data)
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.log("获取教师列表失败", error)
      }
    }
  }

  const fetchStats = async () => {
    try {
      const response = await api.get("/api/admin/courses/stats/summary")
      const data = extractData(response)
      setStats(data)
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.log("获取统计数据失败", error)
      }
    }
  }

  const handleCreateCourse = async () => {
    try {
      const response = await api.post("/api/admin/courses", {
        ...formData,
        teacher_id: parseInt(formData.teacher_id),
        grade_level: parseInt(formData.grade_level),
      })
      const newCourse = extractData(response)
      if (newCourse) {
        setCourses([...courses, newCourse])
      }
      toast.success("课程创建成功")
      setIsCreateDialogOpen(false)
      resetForm()
      fetchStats()
    } catch (error) {
      toast.error("创建失败，请重试")
    }
  }

  const handleUpdateCourse = async () => {
    if (!selectedCourse) return

    try {
      const response = await api.put(`/api/admin/courses/${selectedCourse.id}`, {
        ...editFormData,
        teacher_id: parseInt(editFormData.teacher_id),
        grade_level: parseInt(editFormData.grade_level),
      })
      const updatedCourse = extractData(response)
      if (updatedCourse) {
        setCourses(courses.map(c => c.id === selectedCourse.id ? updatedCourse : c))
      }
      toast.success("课程更新成功")
      setIsEditDialogOpen(false)
      setSelectedCourse(null)
      fetchStats()
    } catch (error) {
      toast.error("更新失败，请重试")
    }
  }

  const handleDeleteCourse = async (courseId: number) => {
    if (!confirm("确定要删除这门课程吗？此操作将删除所有相关的章节、作业和学生数据。")) return

    try {
      await api.delete(`/api/admin/courses/${courseId}`)
      setCourses(courses.filter(c => c.id !== courseId))
      toast.success("课程已删除")
      fetchStats()
    } catch (error) {
      toast.error("删除失败，请重试")
    }
  }

  const handleToggleCourseStatus = async (course: Course) => {
    try {
      await api.put(`/api/admin/courses/${course.id}`, {
        ...course,
        is_published: !course.is_published
      })
      setCourses(courses.map(c => 
        c.id === course.id ? { ...c, is_published: !c.is_published } : c
      ))
      toast.success(`课程已${course.is_published ? '下架' : '发布'}`)
    } catch (error) {
      toast.error("操作失败，请重试")
    }
  }

  const resetForm = () => {
    setFormData({
      title: "",
      description: "",
      subject: "",
      grade_level: 1,
      teacher_id: "",
    })
  }

  const filteredCourses = courses.filter(course =>
    course.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    course.teacher_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    course.subject.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const uniqueSubjects = Array.from(new Set(courses.map(c => c.subject)))

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">课程管理</h1>
            <p className="text-muted-foreground mt-1">管理系统中的所有课程</p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={() => setIsStatsDialogOpen(true)}>
              <BarChart className="w-4 h-4" />
              查看统计
            </Button>
            <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="w-4 h-4" />
                  创建课程
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl">
                <DialogHeader>
                  <DialogTitle>创建新课程</DialogTitle>
                  <DialogDescription>
                    填写信息以创建新的课程
                  </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="grid gap-2">
                    <Label htmlFor="title">课程标题</Label>
                    <Input
                      id="title"
                      value={formData.title}
                      onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                      placeholder="输入课程标题"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="description">课程描述</Label>
                    <Textarea
                      id="description"
                      value={formData.description}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      rows={3}
                      placeholder="输入课程描述"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="grid gap-2">
                      <Label htmlFor="subject">学科</Label>
                      <Input
                        id="subject"
                        value={formData.subject}
                        onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                        placeholder="例如：计算机科学"
                      />
                    </div>
                    <div className="grid gap-2">
                      <Label htmlFor="grade_level">年级</Label>
                      <Select
                        value={String(formData.grade_level)}
                        onValueChange={(value) => setFormData({ ...formData, grade_level: parseInt(value) })}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {[1, 2, 3, 4].map((level) => (
                            <SelectItem key={level} value={String(level)}>
                              {level}年级
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="teacher">授课教师</Label>
                    <Select
                      value={formData.teacher_id}
                      onValueChange={(value) => setFormData({ ...formData, teacher_id: value })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="选择教师" />
                      </SelectTrigger>
                      <SelectContent>
                        {teachers.map((teacher) => (
                          <SelectItem key={teacher.id} value={String(teacher.id)}>
                            {teacher.full_name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="flex justify-end gap-2">
                  <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                    取消
                  </Button>
                  <Button onClick={handleCreateCourse}>创建</Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        {/* Stats Overview */}
        {stats && (
          <div className="grid gap-4 md:grid-cols-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">总课程数</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.total_courses}</div>
                <p className="text-xs text-muted-foreground mt-1">
                  已发布 {stats.published_courses} 门
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">总学生数</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.total_students}</div>
                <div className="flex items-center gap-1 mt-1">
                  <TrendingUp className="w-3 h-3 text-green-600" />
                  <span className="text-xs text-green-600">+12%</span>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">总作业数</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.total_assignments}</div>
                <p className="text-xs text-muted-foreground mt-1">
                  平均每门 {Math.round(stats.total_assignments / stats.total_courses)} 个
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">平均完成率</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {courses.length > 0 
                    ? Math.round(courses.reduce((acc, c) => acc + c.completion_rate, 0) / courses.length)
                    : 0}%
                </div>
                <Progress 
                  value={courses.length > 0 
                    ? courses.reduce((acc, c) => acc + c.completion_rate, 0) / courses.length
                    : 0} 
                  className="h-1 mt-2" 
                />
              </CardContent>
            </Card>
          </div>
        )}

        {/* Filters */}
        <div className="flex items-center gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="搜索课程名称、教师或学科..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          <Select value={selectedSubject} onValueChange={setSelectedSubject}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="筛选学科" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">所有学科</SelectItem>
              {uniqueSubjects.map((subject) => (
                <SelectItem key={subject} value={subject}>
                  {subject}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={selectedGrade} onValueChange={setSelectedGrade}>
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="筛选年级" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">所有年级</SelectItem>
              {[1, 2, 3, 4].map((grade) => (
                <SelectItem key={grade} value={String(grade)}>
                  {grade}年级
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Courses Table */}
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>课程信息</TableHead>
                  <TableHead>教师</TableHead>
                  <TableHead>年级/学科</TableHead>
                  <TableHead>学生数</TableHead>
                  <TableHead>作业数</TableHead>
                  <TableHead>完成率</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>创建时间</TableHead>
                  <TableHead>操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredCourses.map((course) => (
                  <TableRow key={course.id}>
                    <TableCell>
                      <div>
                        <p className="font-medium">{course.title}</p>
                        <p className="text-sm text-muted-foreground line-clamp-1">
                          {course.description}
                        </p>
                      </div>
                    </TableCell>
                    <TableCell>{course.teacher_name}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">{course.grade_level}年级</Badge>
                        <span className="text-sm">{course.subject}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <Users className="w-4 h-4 text-muted-foreground" />
                        {course.student_count}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <FileText className="w-4 h-4 text-muted-foreground" />
                        {course.assignment_count}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium">{course.completion_rate}%</span>
                        </div>
                        <Progress value={course.completion_rate} className="h-1" />
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Switch
                          checked={course.is_published}
                          onCheckedChange={() => handleToggleCourseStatus(course)}
                        />
                        <Badge
                          variant={course.is_published ? "default" : "secondary"}
                        >
                          {course.is_published ? "已发布" : "未发布"}
                        </Badge>
                      </div>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {format(new Date(course.created_at), "yyyy-MM-dd", { locale: zhCN })}
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
                            setSelectedCourse(course)
                            setEditFormData({
                              title: course.title,
                              description: course.description,
                              subject: course.subject,
                              grade_level: course.grade_level,
                              teacher_id: String(course.teacher_id),
                              is_published: course.is_published,
                            })
                            setIsEditDialogOpen(true)
                          }}>
                            <Edit className="w-4 h-4 mr-2" />
                            编辑课程
                          </DropdownMenuItem>
                          <DropdownMenuItem>
                            <Eye className="w-4 h-4 mr-2" />
                            查看详情
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem 
                            onClick={() => handleDeleteCourse(course.id)}
                            className="text-destructive"
                          >
                            <Trash className="w-4 h-4 mr-2" />
                            删除课程
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

        {/* Edit Course Dialog */}
        <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>编辑课程</DialogTitle>
              <DialogDescription>
                修改课程信息
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="edit-title">课程标题</Label>
                <Input
                  id="edit-title"
                  value={editFormData.title}
                  onChange={(e) => setEditFormData({ ...editFormData, title: e.target.value })}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="edit-description">课程描述</Label>
                <Textarea
                  id="edit-description"
                  value={editFormData.description}
                  onChange={(e) => setEditFormData({ ...editFormData, description: e.target.value })}
                  rows={3}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="edit-subject">学科</Label>
                  <Input
                    id="edit-subject"
                    value={editFormData.subject}
                    onChange={(e) => setEditFormData({ ...editFormData, subject: e.target.value })}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="edit-grade_level">年级</Label>
                  <Select
                    value={String(editFormData.grade_level)}
                    onValueChange={(value) => setEditFormData({ ...editFormData, grade_level: parseInt(value) })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {[1, 2, 3, 4].map((level) => (
                        <SelectItem key={level} value={String(level)}>
                          {level}年级
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid gap-2">
                <Label htmlFor="edit-teacher">授课教师</Label>
                <Select
                  value={editFormData.teacher_id}
                  onValueChange={(value) => setEditFormData({ ...editFormData, teacher_id: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {teachers.map((teacher) => (
                      <SelectItem key={teacher.id} value={String(teacher.id)}>
                        {teacher.full_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
                取消
              </Button>
              <Button onClick={handleUpdateCourse}>保存</Button>
            </div>
          </DialogContent>
        </Dialog>

        {/* Stats Dialog */}
        <Dialog open={isStatsDialogOpen} onOpenChange={setIsStatsDialogOpen}>
          <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>课程统计数据</DialogTitle>
              <DialogDescription>
                查看系统中课程的详细统计信息
              </DialogDescription>
            </DialogHeader>
            {stats && (
              <div className="space-y-6 mt-4">
                <div className="grid gap-4 md:grid-cols-2">
                  {/* Subject Distribution */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">学科分布</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={200}>
                        <PieChart>
                          <Pie
                            data={stats.subject_distribution}
                            cx="50%"
                            cy="50%"
                            labelLine={false}
                            label={(entry) => `${entry.subject}: ${entry.count}`}
                            outerRadius={80}
                            fill="#8884d8"
                            dataKey="count"
                          >
                            {stats.subject_distribution.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                          </Pie>
                          <Tooltip />
                        </PieChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>

                  {/* Grade Distribution */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">年级分布</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={200}>
                        <RechartsBarChart data={stats.grade_distribution}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="grade" tickFormatter={(value) => `${value}年级`} />
                          <YAxis />
                          <Tooltip formatter={(value) => [`${value}门`, "课程数"]} />
                          <Bar dataKey="count" fill="#8884d8" />
                        </RechartsBarChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>
                </div>

                {/* Monthly Trend */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">月度新增课程趋势</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={200}>
                      <LineChart data={stats.monthly_courses}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="month" />
                        <YAxis />
                        <Tooltip />
                        <Line type="monotone" dataKey="count" stroke="#8884d8" />
                      </LineChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  )
}