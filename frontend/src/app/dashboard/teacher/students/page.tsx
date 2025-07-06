"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import {
  Search,
  Filter,
  Users,
  UserCheck,
  TrendingUp,
  Award,
  Clock,
  BookOpen,
  FileText,
  Mail,
  MoreVertical,
  Eye,
} from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
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
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import DashboardLayout from "@/components/layout/dashboard-layout"
import api from "@/lib/api"
import toast from "react-hot-toast"
import { cn } from "@/lib/utils"

interface Student {
  id: number
  username: string
  full_name: string
  email: string
  avatar_url?: string
  enrolled_courses: number
  completed_assignments: number
  average_score: number
  last_active: string
  status: "active" | "inactive"
}

interface StudentDetail {
  id: number
  full_name: string
  email: string
  courses: CourseProgress[]
  assignments: AssignmentProgress[]
  overall_progress: number
  total_study_time: number
}

interface CourseProgress {
  course_id: number
  course_name: string
  progress: number
  last_accessed: string
}

interface AssignmentProgress {
  assignment_id: number
  assignment_title: string
  course_name: string
  status: "pending" | "submitted" | "graded"
  score?: number
  submitted_at?: string
}

export default function TeacherStudentsPage() {
  const [students, setStudents] = useState<Student[]>([])
  const [courses, setCourses] = useState<{ id: number; title: string }[]>([])
  const [selectedStudent, setSelectedStudent] = useState<StudentDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedCourse, setSelectedCourse] = useState<string>("all")
  const [viewMode, setViewMode] = useState<"grid" | "table">("grid")

  useEffect(() => {
    fetchStudents()
    fetchCourses()
  }, [selectedCourse])

  const fetchStudents = async () => {
    try {
      const params = selectedCourse !== "all" ? { course_id: selectedCourse } : {}
      const response = await api.get("/api/teacher/students", { params })
      setStudents(response.data)
    } catch (error) {
      toast.error("获取学生列表失败")
    } finally {
      setLoading(false)
    }
  }

  const fetchCourses = async () => {
    try {
      const response = await api.get("/api/teacher/course/list")
      setCourses(response.data)
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.log("获取课程列表失败", error)
      }
    }
  }

  const fetchStudentDetail = async (studentId: number) => {
    try {
      const [detailRes, progressRes, assignmentsRes] = await Promise.all([
        api.get(`/api/teacher/students/${studentId}`),
        api.get(`/api/teacher/students/${studentId}/progress`),
        api.get(`/api/teacher/students/${studentId}/assignments`),
      ])
      
      setSelectedStudent({
        ...detailRes.data,
        ...progressRes.data,
        assignments: assignmentsRes.data,
      })
    } catch (error) {
      toast.error("获取学生详情失败")
    }
  }

  const filteredStudents = students.filter(student =>
    student.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    student.email.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const getPerformanceLevel = (score: number) => {
    if (score >= 90) return { label: "优秀", color: "text-green-600", bg: "bg-green-50" }
    if (score >= 80) return { label: "良好", color: "text-blue-600", bg: "bg-blue-50" }
    if (score >= 70) return { label: "中等", color: "text-yellow-600", bg: "bg-yellow-50" }
    return { label: "需要帮助", color: "text-red-600", bg: "bg-red-50" }
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">学生管理</h1>
            <p className="text-muted-foreground mt-1">查看和管理学生学习情况</p>
          </div>
          <div className="flex items-center gap-2">
            <Select value={selectedCourse} onValueChange={setSelectedCourse}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="筛选课程" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">所有课程</SelectItem>
                {courses.map((course) => (
                  <SelectItem key={course.id} value={String(course.id)}>
                    {course.title}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <div className="flex items-center border rounded-lg">
              <Button
                variant={viewMode === "grid" ? "default" : "ghost"}
                size="sm"
                onClick={() => setViewMode("grid")}
                className="rounded-r-none"
              >
                网格
              </Button>
              <Button
                variant={viewMode === "table" ? "default" : "ghost"}
                size="sm"
                onClick={() => setViewMode("table")}
                className="rounded-l-none"
              >
                列表
              </Button>
            </div>
          </div>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="搜索学生姓名或邮箱..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>

        {/* Stats Overview */}
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">学生总数</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{students.length}</div>
              <p className="text-xs text-muted-foreground mt-1">
                活跃 {students.filter(s => s.status === "active").length} 人
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">平均成绩</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {students.length > 0
                  ? Math.round(
                      students.reduce((acc, s) => acc + s.average_score, 0) / students.length
                    )
                  : 0}%
              </div>
              <div className="flex items-center gap-1 mt-1">
                <TrendingUp className="w-3 h-3 text-green-600" />
                <span className="text-xs text-green-600">+2.5%</span>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">作业完成率</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">87%</div>
              <Progress value={87} className="h-1 mt-2" />
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">优秀学生</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {students.filter(s => s.average_score >= 90).length}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                占比 {Math.round((students.filter(s => s.average_score >= 90).length / students.length) * 100)}%
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Students List/Grid */}
        {viewMode === "grid" ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filteredStudents.map((student, index) => {
              const performance = getPerformanceLevel(student.average_score)
              return (
                <motion.div
                  key={student.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <Card className="hover:shadow-lg transition-shadow cursor-pointer"
                        onClick={() => fetchStudentDetail(student.id)}>
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-3">
                          <Avatar>
                            <AvatarImage src={student.avatar_url} />
                            <AvatarFallback>{student.full_name[0]}</AvatarFallback>
                          </Avatar>
                          <div>
                            <CardTitle className="text-base">{student.full_name}</CardTitle>
                            <CardDescription className="text-xs">
                              {student.email}
                            </CardDescription>
                          </div>
                        </div>
                        <Badge
                          variant="outline"
                          className={cn(
                            student.status === "active" ? "border-green-600 text-green-600" : "border-gray-400 text-gray-400"
                          )}
                        >
                          {student.status === "active" ? "活跃" : "不活跃"}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <p className="text-muted-foreground">课程数</p>
                            <p className="font-medium flex items-center gap-1 mt-1">
                              <BookOpen className="w-4 h-4" />
                              {student.enrolled_courses}
                            </p>
                          </div>
                          <div>
                            <p className="text-muted-foreground">作业完成</p>
                            <p className="font-medium flex items-center gap-1 mt-1">
                              <FileText className="w-4 h-4" />
                              {student.completed_assignments}
                            </p>
                          </div>
                        </div>
                        
                        <div>
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-sm text-muted-foreground">平均成绩</span>
                            <span className={cn("text-sm font-medium", performance.color)}>
                              {student.average_score}%
                            </span>
                          </div>
                          <Progress value={student.average_score} className="h-2" />
                        </div>
                        
                        <div className={cn("text-center py-2 rounded-lg", performance.bg)}>
                          <span className={cn("text-sm font-medium", performance.color)}>
                            {performance.label}
                          </span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              )
            })}
          </div>
        ) : (
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>学生</TableHead>
                    <TableHead>课程数</TableHead>
                    <TableHead>作业完成</TableHead>
                    <TableHead>平均成绩</TableHead>
                    <TableHead>状态</TableHead>
                    <TableHead>最后活跃</TableHead>
                    <TableHead>操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredStudents.map((student) => {
                    const performance = getPerformanceLevel(student.average_score)
                    return (
                      <TableRow key={student.id}>
                        <TableCell>
                          <div className="flex items-center gap-3">
                            <Avatar className="w-8 h-8">
                              <AvatarImage src={student.avatar_url} />
                              <AvatarFallback>{student.full_name[0]}</AvatarFallback>
                            </Avatar>
                            <div>
                              <p className="font-medium">{student.full_name}</p>
                              <p className="text-xs text-muted-foreground">{student.email}</p>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>{student.enrolled_courses}</TableCell>
                        <TableCell>{student.completed_assignments}</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <span className={cn("font-medium", performance.color)}>
                              {student.average_score}%
                            </span>
                            <Badge variant="outline" className={cn("text-xs", performance.color, "border-current")}>
                              {performance.label}
                            </Badge>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant="outline"
                            className={cn(
                              student.status === "active" ? "border-green-600 text-green-600" : "border-gray-400 text-gray-400"
                            )}
                          >
                            {student.status === "active" ? "活跃" : "不活跃"}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground">
                          {new Date(student.last_active).toLocaleDateString()}
                        </TableCell>
                        <TableCell>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="icon">
                                <MoreVertical className="w-4 h-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem onClick={() => fetchStudentDetail(student.id)}>
                                <Eye className="w-4 h-4 mr-2" />
                                查看详情
                              </DropdownMenuItem>
                              <DropdownMenuItem>
                                <Mail className="w-4 h-4 mr-2" />
                                发送邮件
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        )}

        {/* Student Detail Dialog */}
        <Dialog open={!!selectedStudent} onOpenChange={() => setSelectedStudent(null)}>
          <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>学生详情 - {selectedStudent?.full_name}</DialogTitle>
              <DialogDescription>
                查看学生的学习进度和成绩情况
              </DialogDescription>
            </DialogHeader>
            
            {selectedStudent && (
              <Tabs defaultValue="overview" className="mt-4">
                <TabsList>
                  <TabsTrigger value="overview">概览</TabsTrigger>
                  <TabsTrigger value="courses">课程进度</TabsTrigger>
                  <TabsTrigger value="assignments">作业情况</TabsTrigger>
                </TabsList>
                
                <TabsContent value="overview" className="space-y-4">
                  <div className="grid gap-4 md:grid-cols-3">
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm">总体进度</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">{selectedStudent.overall_progress}%</div>
                        <Progress value={selectedStudent.overall_progress} className="h-1 mt-2" />
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm">学习时长</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">
                          {Math.round(selectedStudent.total_study_time / 60)}小时
                        </div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm">邮箱</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <p className="text-sm">{selectedStudent.email}</p>
                      </CardContent>
                    </Card>
                  </div>
                </TabsContent>
                
                <TabsContent value="courses" className="space-y-4">
                  {selectedStudent.courses.map((course) => (
                    <Card key={course.course_id}>
                      <CardHeader>
                        <div className="flex items-center justify-between">
                          <CardTitle className="text-base">{course.course_name}</CardTitle>
                          <Badge variant="outline">{course.progress}%</Badge>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <Progress value={course.progress} className="h-2" />
                        <p className="text-sm text-muted-foreground mt-2">
                          最后学习：{new Date(course.last_accessed).toLocaleDateString()}
                        </p>
                      </CardContent>
                    </Card>
                  ))}
                </TabsContent>
                
                <TabsContent value="assignments" className="space-y-4">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>作业名称</TableHead>
                        <TableHead>课程</TableHead>
                        <TableHead>状态</TableHead>
                        <TableHead>分数</TableHead>
                        <TableHead>提交时间</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {selectedStudent.assignments.map((assignment) => (
                        <TableRow key={assignment.assignment_id}>
                          <TableCell>{assignment.assignment_title}</TableCell>
                          <TableCell>{assignment.course_name}</TableCell>
                          <TableCell>
                            <Badge variant={
                              assignment.status === "graded" ? "default" :
                              assignment.status === "submitted" ? "secondary" : "outline"
                            }>
                              {assignment.status === "graded" ? "已批改" :
                               assignment.status === "submitted" ? "已提交" : "待完成"}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            {assignment.score !== undefined ? (
                              <span className="font-medium">{assignment.score}分</span>
                            ) : (
                              <span className="text-muted-foreground">-</span>
                            )}
                          </TableCell>
                          <TableCell>
                            {assignment.submitted_at ? (
                              new Date(assignment.submitted_at).toLocaleDateString()
                            ) : (
                              <span className="text-muted-foreground">-</span>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TabsContent>
              </Tabs>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  )
}