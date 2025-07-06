"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import {
  Plus,
  Search,
  Filter,
  MoreVertical,
  Edit,
  Trash,
  Users,
  BookOpen,
  Calendar,
  FileText,
  Upload,
  Sparkles,
} from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import DashboardLayout from "@/components/layout/dashboard-layout"
import api from "@/lib/api"
import toast from "react-hot-toast"
import { useRouter } from "next/navigation"

interface Course {
  id: number
  title: string
  description: string
  subject: string
  grade_level: number
  student_count: number
  created_at: string
  updated_at: string
  chapters?: Chapter[]
}

interface Chapter {
  id: number
  title: string
  order: number
  lessons: number
}

export default function TeacherCoursesPage() {
  const router = useRouter()
  const [courses, setCourses] = useState<Course[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState("")
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [isAIDialogOpen, setIsAIDialogOpen] = useState(false)
  const [selectedCourse, setSelectedCourse] = useState<Course | null>(null)
  
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    subject: "",
    grade_level: 1,
  })

  const [aiFormData, setAiFormData] = useState({
    course_name: "",
    duration_minutes: 45,
    grade_level: 1,
    knowledge_points: "",
    teaching_objectives: "",
  })

  useEffect(() => {
    fetchCourses()
  }, [])

  const fetchCourses = async () => {
    try {
      const response = await api.get("/api/teacher/course/list")
      setCourses(response.data)
    } catch (error) {
      toast.error("获取课程列表失败")
    } finally {
      setLoading(false)
    }
  }

  const handleCreateCourse = async () => {
    try {
      const response = await api.post("/api/teacher/course/create", formData)
      setCourses([...courses, response.data])
      toast.success("课程创建成功")
      setIsCreateDialogOpen(false)
      resetForm()
    } catch (error) {
      toast.error("创建失败，请重试")
    }
  }

  const handleGenerateOutline = async () => {
    try {
      const response = await api.post("/api/teacher/course/generate-outline", {
        ...aiFormData,
        knowledge_points: aiFormData.knowledge_points.split(",").map(k => k.trim()),
      })
      
      // 使用生成的大纲创建课程
      setFormData({
        title: aiFormData.course_name,
        description: response.data.description || "",
        subject: response.data.subject || "",
        grade_level: aiFormData.grade_level,
      })
      
      setIsAIDialogOpen(false)
      setIsCreateDialogOpen(true)
      toast.success("AI大纲生成成功！")
    } catch (error) {
      toast.error("生成失败，请重试")
    }
  }

  const handleDeleteCourse = async (courseId: number) => {
    if (!confirm("确定要删除这门课程吗？")) return

    try {
      await api.delete(`/api/teacher/course/${courseId}`)
      setCourses(courses.filter(c => c.id !== courseId))
      toast.success("课程已删除")
    } catch (error) {
      toast.error("删除失败，请重试")
    }
  }

  const resetForm = () => {
    setFormData({
      title: "",
      description: "",
      subject: "",
      grade_level: 1,
    })
  }

  const filteredCourses = courses.filter(course =>
    course.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    course.subject.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">课程管理</h1>
            <p className="text-muted-foreground mt-1">创建和管理你的教学课程</p>
          </div>
          <div className="flex items-center gap-2">
            <Dialog open={isAIDialogOpen} onOpenChange={setIsAIDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="outline">
                  <Sparkles className="w-4 h-4" />
                  AI生成大纲
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl">
                <DialogHeader>
                  <DialogTitle>AI课程大纲生成</DialogTitle>
                  <DialogDescription>
                    输入课程信息，AI将为你生成详细的教学大纲
                  </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="grid gap-2">
                    <Label htmlFor="ai-course-name">课程名称</Label>
                    <Input
                      id="ai-course-name"
                      value={aiFormData.course_name}
                      onChange={(e) => setAiFormData({ ...aiFormData, course_name: e.target.value })}
                      placeholder="例如：Python编程基础"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="grid gap-2">
                      <Label htmlFor="duration">课时时长（分钟）</Label>
                      <Input
                        id="duration"
                        type="number"
                        value={aiFormData.duration_minutes}
                        onChange={(e) => setAiFormData({ ...aiFormData, duration_minutes: parseInt(e.target.value) })}
                      />
                    </div>
                    <div className="grid gap-2">
                      <Label htmlFor="ai-grade-level">年级</Label>
                      <Select
                        value={String(aiFormData.grade_level)}
                        onValueChange={(value) => setAiFormData({ ...aiFormData, grade_level: parseInt(value) })}
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
                    <Label htmlFor="knowledge-points">知识点（逗号分隔）</Label>
                    <Input
                      id="knowledge-points"
                      value={aiFormData.knowledge_points}
                      onChange={(e) => setAiFormData({ ...aiFormData, knowledge_points: e.target.value })}
                      placeholder="例如：变量, 数据类型, 条件语句"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="objectives">教学目标</Label>
                    <Textarea
                      id="objectives"
                      value={aiFormData.teaching_objectives}
                      onChange={(e) => setAiFormData({ ...aiFormData, teaching_objectives: e.target.value })}
                      placeholder="描述本课程的教学目标..."
                      rows={3}
                    />
                  </div>
                </div>
                <div className="flex justify-end gap-2">
                  <Button variant="outline" onClick={() => setIsAIDialogOpen(false)}>
                    取消
                  </Button>
                  <Button onClick={handleGenerateOutline}>
                    <Sparkles className="w-4 h-4 mr-2" />
                    生成大纲
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
            
            <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="w-4 h-4" />
                  创建课程
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>创建新课程</DialogTitle>
                  <DialogDescription>
                    填写课程信息以创建新的教学课程
                  </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="grid gap-2">
                    <Label htmlFor="title">课程标题</Label>
                    <Input
                      id="title"
                      value={formData.title}
                      onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="description">课程描述</Label>
                    <Textarea
                      id="description"
                      value={formData.description}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      rows={3}
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

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="搜索课程..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>

        {/* Courses Grid */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {filteredCourses.map((course, index) => (
            <motion.div
              key={course.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <Card className="h-full hover:shadow-lg transition-all cursor-pointer"
                    onClick={() => router.push(`/dashboard/courses/${course.id}/manage`)}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <CardTitle className="text-lg line-clamp-1">
                        {course.title}
                      </CardTitle>
                      <CardDescription className="line-clamp-2">
                        {course.description}
                      </CardDescription>
                    </div>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                        <Button variant="ghost" size="icon">
                          <MoreVertical className="w-4 h-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={(e) => {
                          e.stopPropagation()
                          router.push(`/dashboard/courses/${course.id}/edit`)
                        }}>
                          <Edit className="w-4 h-4 mr-2" />
                          编辑
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={(e) => {
                          e.stopPropagation()
                          handleDeleteCourse(course.id)
                        }} className="text-destructive">
                          <Trash className="w-4 h-4 mr-2" />
                          删除
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <div className="flex items-center gap-1">
                        <BookOpen className="w-4 h-4" />
                        <span>{course.subject}</span>
                      </div>
                      <Badge variant="secondary">{course.grade_level}年级</Badge>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <p className="text-muted-foreground">学生数</p>
                        <p className="font-medium flex items-center gap-1 mt-1">
                          <Users className="w-4 h-4" />
                          {course.student_count}
                        </p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">章节数</p>
                        <p className="font-medium flex items-center gap-1 mt-1">
                          <FileText className="w-4 h-4" />
                          {course.chapters?.length || 0}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center justify-between pt-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation()
                          router.push(`/dashboard/courses/${course.id}/materials`)
                        }}
                      >
                        <Upload className="w-4 h-4 mr-1" />
                        上传材料
                      </Button>
                      <Button size="sm">
                        管理课程
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>

        {filteredCourses.length === 0 && (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <BookOpen className="w-12 h-12 text-muted-foreground mb-4" />
              <p className="text-muted-foreground">
                {searchQuery ? "没有找到匹配的课程" : "暂无课程，点击上方按钮创建"}
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardLayout>
  )
}