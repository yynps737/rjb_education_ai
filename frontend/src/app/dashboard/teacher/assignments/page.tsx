"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import {
  Plus,
  Search,
  Filter,
  FileText,
  Users,
  Calendar,
  Clock,
  CheckCircle,
  AlertCircle,
  Edit,
  Trash,
  Eye,
  Download,
} from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import DashboardLayout from "@/components/layout/dashboard-layout"
import api from "@/lib/api"
import { extractData } from "@/lib/api-utils"
import toast from "react-hot-toast"
import { useRouter } from "next/navigation"
import { format } from "date-fns"
import { zhCN } from "date-fns/locale"

interface Assignment {
  id: number
  title: string
  description: string
  course_id: number
  course_name: string
  due_date: string
  total_points: number
  created_at: string
  submission_count: number
  graded_count: number
  avg_score: number
}

interface Submission {
  id: number
  student_id: number
  student_name: string
  submitted_at: string
  score?: number
  graded_at?: string
  status: "submitted" | "graded"
}

export default function TeacherAssignmentsPage() {
  const router = useRouter()
  const [assignments, setAssignments] = useState<Assignment[]>([])
  const [courses, setCourses] = useState<{ id: number; title: string }[]>([])
  const [selectedAssignment, setSelectedAssignment] = useState<Assignment | null>(null)
  const [submissions, setSubmissions] = useState<Submission[]>([])
  const [loading, setLoading] = useState(true)
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [selectedCourse, setSelectedCourse] = useState<string>("all")
  
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    instructions: "",
    course_id: "",
    due_date: "",
    total_points: 100,
  })

  useEffect(() => {
    fetchAssignments()
    fetchCourses()
  }, [selectedCourse])

  const fetchAssignments = async () => {
    try {
      const params = selectedCourse !== "all" ? { course_id: selectedCourse } : {}
      const response = await api.get("/api/teacher/assignments", { params })
      const data = extractData<Assignment[]>(response) || []
      setAssignments(data)
    } catch (error) {
      toast.error("获取作业列表失败")
    } finally {
      setLoading(false)
    }
  }

  const fetchCourses = async () => {
    try {
      const response = await api.get("/api/teacher/course/list")
      const data = extractData<{ id: number; title: string }[]>(response) || []
      setCourses(data)
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.log("获取课程列表失败", error)
      }
      // 设置默认值避免 map 错误
      setCourses([])
    }
  }

  const fetchSubmissions = async (assignmentId: number) => {
    try {
      const response = await api.get(`/api/teacher/assignments/${assignmentId}/submissions`)
      const data = extractData<Submission[]>(response) || []
      setSubmissions(data)
    } catch (error) {
      toast.error("获取提交列表失败")
    }
  }

  const handleCreateAssignment = async () => {
    try {
      const response = await api.post("/api/teacher/assignments", {
        ...formData,
        course_id: parseInt(formData.course_id),
      })
      const newAssignment = extractData<Assignment>(response)
      if (newAssignment) {
        setAssignments([...assignments, newAssignment])
      }
      toast.success("作业创建成功")
      setIsCreateDialogOpen(false)
      resetForm()
    } catch (error) {
      toast.error("创建失败，请重试")
    }
  }

  const handleDeleteAssignment = async (assignmentId: number) => {
    if (!confirm("确定要删除这个作业吗？")) return

    try {
      await api.delete(`/api/teacher/assignments/${assignmentId}`)
      setAssignments(assignments.filter(a => a.id !== assignmentId))
      toast.success("作业已删除")
    } catch (error) {
      toast.error("删除失败，请重试")
    }
  }

  const resetForm = () => {
    setFormData({
      title: "",
      description: "",
      instructions: "",
      course_id: "",
      due_date: "",
      total_points: 100,
    })
  }

  const getSubmissionStats = (assignment: Assignment) => {
    const submissionRate = assignment.submission_count > 0 
      ? (assignment.submission_count / 30) * 100 // 假设班级有30人
      : 0
    const gradedRate = assignment.submission_count > 0
      ? (assignment.graded_count / assignment.submission_count) * 100
      : 0

    return { submissionRate, gradedRate }
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">作业管理</h1>
            <p className="text-muted-foreground mt-1">创建和管理课程作业</p>
          </div>
          <div className="flex items-center gap-2">
            <Select value={selectedCourse} onValueChange={setSelectedCourse}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="筛选课程" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">所有课程</SelectItem>
                {courses && courses.length > 0 ? (
                  courses.map((course) => (
                    <SelectItem key={course.id} value={String(course.id)}>
                      {course.title}
                    </SelectItem>
                  ))
                ) : (
                  <SelectItem value="no-courses" disabled>
                    暂无课程
                  </SelectItem>
                )}
              </SelectContent>
            </Select>
            
            <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="w-4 h-4" />
                  创建作业
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl">
                <DialogHeader>
                  <DialogTitle>创建新作业</DialogTitle>
                  <DialogDescription>
                    为学生布置新的课程作业
                  </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="grid gap-2">
                    <Label htmlFor="title">作业标题</Label>
                    <Input
                      id="title"
                      value={formData.title}
                      onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                      placeholder="例如：第一章课后练习"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="course">所属课程</Label>
                    <Select
                      value={formData.course_id}
                      onValueChange={(value) => setFormData({ ...formData, course_id: value })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="选择课程" />
                      </SelectTrigger>
                      <SelectContent>
                        {courses && courses.length > 0 ? (
                          courses.map((course) => (
                            <SelectItem key={course.id} value={String(course.id)}>
                              {course.title}
                            </SelectItem>
                          ))
                        ) : (
                          <SelectItem value="no-courses" disabled>
                            请先创建课程
                          </SelectItem>
                        )}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="description">作业描述</Label>
                    <Textarea
                      id="description"
                      value={formData.description}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      rows={3}
                      placeholder="简要描述作业内容..."
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="instructions">作业要求</Label>
                    <Textarea
                      id="instructions"
                      value={formData.instructions}
                      onChange={(e) => setFormData({ ...formData, instructions: e.target.value })}
                      rows={4}
                      placeholder="详细说明作业要求和注意事项..."
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="grid gap-2">
                      <Label htmlFor="due_date">截止时间</Label>
                      <Input
                        id="due_date"
                        type="datetime-local"
                        value={formData.due_date}
                        onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                      />
                    </div>
                    <div className="grid gap-2">
                      <Label htmlFor="total_points">总分</Label>
                      <Input
                        id="total_points"
                        type="number"
                        value={formData.total_points}
                        onChange={(e) => setFormData({ ...formData, total_points: parseInt(e.target.value) })}
                      />
                    </div>
                  </div>
                </div>
                <div className="flex justify-end gap-2">
                  <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                    取消
                  </Button>
                  <Button onClick={handleCreateAssignment}>创建</Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        {/* Stats Overview */}
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">总作业数</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{assignments.length}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">待批改</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-orange-600">
                {assignments.reduce((acc, a) => acc + (a.submission_count - a.graded_count), 0)}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">平均分数</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {assignments.length > 0
                  ? Math.round(
                      assignments.reduce((acc, a) => acc + a.avg_score, 0) / assignments.length
                    )
                  : 0}%
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">完成率</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {assignments.length > 0
                  ? Math.round(
                      (assignments.reduce((acc, a) => acc + a.submission_count, 0) /
                        (assignments.length * 30)) * 100
                    )
                  : 0}%
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Assignments List */}
        <Card>
          <CardHeader>
            <CardTitle>作业列表</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {assignments.length === 0 && courses.length === 0 ? (
                <div className="text-center py-12">
                  <FileText className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                  <h3 className="text-lg font-medium mb-2">暂无课程</h3>
                  <p className="text-muted-foreground mb-4">
                    请先联系管理员为您分配课程，然后才能创建作业
                  </p>
                  <Button variant="outline" onClick={() => router.push('/dashboard/teacher/courses')}>
                    查看课程
                  </Button>
                </div>
              ) : assignments.length === 0 ? (
                <div className="text-center py-12">
                  <FileText className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                  <h3 className="text-lg font-medium mb-2">暂无作业</h3>
                  <p className="text-muted-foreground mb-4">
                    点击右上角的"创建作业"按钮开始
                  </p>
                </div>
              ) : (
                assignments.map((assignment) => {
                const { submissionRate, gradedRate } = getSubmissionStats(assignment)
                return (
                  <motion.div
                    key={assignment.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="p-4 border rounded-lg hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-start justify-between">
                      <div className="space-y-2 flex-1">
                        <div className="flex items-start gap-3">
                          <FileText className="w-5 h-5 text-muted-foreground mt-0.5" />
                          <div className="flex-1">
                            <h3 className="font-medium">{assignment.title}</h3>
                            <p className="text-sm text-muted-foreground">
                              {assignment.course_name} • {assignment.total_points}分
                            </p>
                            <p className="text-sm text-muted-foreground mt-1">
                              {assignment.description}
                            </p>
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                          <div>
                            <p className="text-xs text-muted-foreground">截止时间</p>
                            <p className="text-sm font-medium flex items-center gap-1">
                              <Calendar className="w-3 h-3" />
                              {format(new Date(assignment.due_date), "MM月dd日", { locale: zhCN })}
                            </p>
                          </div>
                          <div>
                            <p className="text-xs text-muted-foreground">提交情况</p>
                            <div className="space-y-1">
                              <p className="text-sm font-medium">
                                {assignment.submission_count}/30
                              </p>
                              <Progress value={submissionRate} className="h-1" />
                            </div>
                          </div>
                          <div>
                            <p className="text-xs text-muted-foreground">批改进度</p>
                            <div className="space-y-1">
                              <p className="text-sm font-medium">
                                {assignment.graded_count}/{assignment.submission_count}
                              </p>
                              <Progress value={gradedRate} className="h-1" />
                            </div>
                          </div>
                          <div>
                            <p className="text-xs text-muted-foreground">平均分</p>
                            <p className="text-sm font-medium">
                              {assignment.avg_score}%
                            </p>
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-2 ml-4">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setSelectedAssignment(assignment)
                            fetchSubmissions(assignment.id)
                          }}
                        >
                          <Eye className="w-4 h-4" />
                          查看提交
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => router.push(`/dashboard/assignments/${assignment.id}/edit`)}
                        >
                          <Edit className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDeleteAssignment(assignment.id)}
                        >
                          <Trash className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </motion.div>
                )
              })
              )}
            </div>
          </CardContent>
        </Card>

        {/* Submissions Dialog */}
        <Dialog open={!!selectedAssignment} onOpenChange={() => setSelectedAssignment(null)}>
          <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>{selectedAssignment?.title} - 学生提交</DialogTitle>
              <DialogDescription>
                查看和批改学生提交的作业
              </DialogDescription>
            </DialogHeader>
            <div className="mt-4">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>学生姓名</TableHead>
                    <TableHead>提交时间</TableHead>
                    <TableHead>状态</TableHead>
                    <TableHead>分数</TableHead>
                    <TableHead>操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {submissions.map((submission) => (
                    <TableRow key={submission.id}>
                      <TableCell>{submission.student_name}</TableCell>
                      <TableCell>
                        {format(new Date(submission.submitted_at), "MM-dd HH:mm", { locale: zhCN })}
                      </TableCell>
                      <TableCell>
                        <Badge variant={submission.status === "graded" ? "default" : "secondary"}>
                          {submission.status === "graded" ? "已批改" : "待批改"}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {submission.score !== undefined ? (
                          <span className="font-medium">{submission.score}分</span>
                        ) : (
                          <span className="text-muted-foreground">-</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <Button
                          size="sm"
                          onClick={() => 
                            router.push(`/dashboard/assignments/${selectedAssignment?.id}/submissions/${submission.id}`)
                          }
                        >
                          {submission.status === "graded" ? "查看" : "批改"}
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  )
}