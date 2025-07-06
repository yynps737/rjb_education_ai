"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import {
  BookOpen,
  Clock,
  Users,
  TrendingUp,
  Calendar,
  ChevronRight,
  Search,
  Filter,
  Plus,
} from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import DashboardLayout from "@/components/layout/dashboard-layout"
import api from "@/lib/api"
import { extractData, extractPaginatedData } from "@/lib/api-utils"
import toast from "react-hot-toast"
import { useRouter } from "next/navigation"

interface Course {
  id: number
  title: string
  description: string
  subject: string
  grade_level: string
  teacher_name: string
  enrolled_students: number
  progress: number
}

interface AvailableCourse {
  id: number
  title: string
  description: string
  teacher_name: string
  student_count: number
  subject: string
  grade_level: number
}

export default function MyCoursesPage() {
  const router = useRouter()
  const [enrolledCourses, setEnrolledCourses] = useState<Course[]>([])
  const [availableCourses, setAvailableCourses] = useState<AvailableCourse[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState("")
  const [isEnrollDialogOpen, setIsEnrollDialogOpen] = useState(false)

  useEffect(() => {
    fetchCourses()
  }, [])

  const fetchCourses = async () => {
    try {
      const [enrolledRes, availableRes] = await Promise.all([
        api.get("/api/student/courses/enrolled"),
        api.get("/api/student/courses/available"),
      ])
      
      // 使用 extractData 处理不同的响应格式
      const enrolledData = extractData<Course[]>(enrolledRes) || []
      setEnrolledCourses(enrolledData)
      
      // /available 返回分页数据
      const availableData = extractPaginatedData<AvailableCourse>(availableRes)
      setAvailableCourses(availableData.items)
    } catch (error: any) {
      // 开发环境下输出错误信息
      if (process.env.NODE_ENV === 'development') {
        console.log("获取课程失败:", error)
        console.log("错误详情:", error.response?.data)
      }
      toast.error(error.response?.data?.message || "获取课程失败")
    } finally {
      setLoading(false)
    }
  }

  const handleEnrollCourse = async (courseId: number) => {
    try {
      await api.post(`/api/student/courses/${courseId}/enroll`)
      toast.success("注册成功！")
      setIsEnrollDialogOpen(false)
      fetchCourses()
    } catch (error) {
      toast.error("注册失败，请重试")
    }
  }

  const handleUnenrollCourse = async (courseId: number) => {
    if (!confirm("确定要退出这门课程吗？")) return
    
    try {
      await api.delete(`/api/student/courses/${courseId}/unenroll`)
      toast.success("已退出课程")
      fetchCourses()
    } catch (error) {
      toast.error("操作失败，请重试")
    }
  }

  const filteredEnrolled = enrolledCourses.filter(course =>
    course.title.toLowerCase().includes(searchQuery.toLowerCase())
  )
  
  // 根据进度判断课程状态
  const activeCourses = filteredEnrolled.filter(course => course.progress < 100)
  const completedCourses = filteredEnrolled.filter(course => course.progress >= 100)

  const filteredAvailable = availableCourses.filter(course =>
    course.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    course.description.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">我的课程</h1>
            <p className="text-muted-foreground mt-1">管理你的学习进度</p>
          </div>
          <Dialog open={isEnrollDialogOpen} onOpenChange={setIsEnrollDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="gradient">
                <Plus className="w-4 h-4" />
                注册新课程
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>可选课程</DialogTitle>
                <DialogDescription>
                  选择你感兴趣的课程进行注册
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 mt-4">
                {filteredAvailable.map((course) => (
                  <Card key={course.id} className="hover:shadow-md transition-shadow">
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div>
                          <CardTitle className="text-lg">{course.title}</CardTitle>
                          <CardDescription className="mt-1">
                            {course.description}
                          </CardDescription>
                        </div>
                        <Button
                          size="sm"
                          onClick={() => handleEnrollCourse(course.id)}
                        >
                          注册
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <Users className="w-4 h-4" />
                          {course.teacher_name}
                        </span>
                        <span className="flex items-center gap-1">
                          <BookOpen className="w-4 h-4" />
                          {course.subject}
                        </span>
                        <Badge variant="secondary">
                          {course.grade_level}年级
                        </Badge>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </DialogContent>
          </Dialog>
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

        {/* Tabs */}
        <Tabs defaultValue="active" className="space-y-4">
          <TabsList>
            <TabsTrigger value="active">进行中</TabsTrigger>
            <TabsTrigger value="completed">已完成</TabsTrigger>
          </TabsList>

          <TabsContent value="active" className="space-y-4">
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {activeCourses.map((course) => (
                  <motion.div
                    key={course.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    whileHover={{ y: -5 }}
                    transition={{ duration: 0.2 }}
                  >
                    <Card className="h-full hover:shadow-lg transition-all cursor-pointer"
                          onClick={() => router.push(`/dashboard/courses/${course.id}`)}>
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <CardTitle className="text-lg line-clamp-2">
                            {course.title}
                          </CardTitle>
                          <Badge variant="secondary">进行中</Badge>
                        </div>
                        <CardDescription className="line-clamp-2">
                          {course.description}
                        </CardDescription>
                        <div className="flex gap-2 mt-2">
                          <Badge variant="outline" className="text-xs">
                            {course.subject}
                          </Badge>
                          <Badge variant="outline" className="text-xs">
                            {course.grade_level}
                          </Badge>
                        </div>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="space-y-2">
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-muted-foreground">学习进度</span>
                            <span className="font-medium">{course.progress}%</span>
                          </div>
                          <Progress value={course.progress} className="h-2" />
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div className="flex items-center gap-2">
                            <Users className="w-4 h-4 text-muted-foreground" />
                            <span>{course.teacher_name}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <Clock className="w-4 h-4 text-muted-foreground" />
                            <span>{course.enrolled_students} 学生</span>
                          </div>
                        </div>

                        <div className="flex items-center justify-between pt-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation()
                              handleUnenrollCourse(course.id)
                            }}
                          >
                            退出课程
                          </Button>
                          <Button size="sm" variant="ghost">
                            继续学习
                            <ChevronRight className="w-4 h-4 ml-1" />
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                ))}
              
              {activeCourses.length === 0 && (
                <div className="col-span-full text-center py-12">
                  <BookOpen className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                  <h3 className="text-lg font-medium mb-2">暂无进行中的课程</h3>
                  <p className="text-muted-foreground mb-4">
                    快去探索新课程，开始你的学习之旅吧！
                  </p>
                  <Button onClick={() => setIsEnrollDialogOpen(true)}>
                    <Plus className="w-4 h-4 mr-2" />
                    探索新课程
                  </Button>
                </div>
              )}
            </div>
          </TabsContent>

          <TabsContent value="completed" className="space-y-4">
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {completedCourses.map((course) => (
                  <motion.div
                    key={course.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                  >
                    <Card className="h-full">
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <CardTitle className="text-lg line-clamp-2">
                            {course.title}
                          </CardTitle>
                          <Badge variant="default">已完成</Badge>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2 text-sm text-muted-foreground">
                          <div className="flex items-center gap-2">
                            <Users className="w-4 h-4" />
                            <span>教师：{course.teacher_name}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <TrendingUp className="w-4 h-4" />
                            <span>最终进度 100%</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <BookOpen className="w-4 h-4" />
                            <span>{course.subject} · {course.grade_level}</span>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                ))}
              
              {completedCourses.length === 0 && (
                <div className="col-span-full text-center py-12">
                  <TrendingUp className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                  <h3 className="text-lg font-medium mb-2">暂无已完成的课程</h3>
                  <p className="text-muted-foreground">
                    继续努力学习，完成更多课程！
                  </p>
                </div>
              )}
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  )
}