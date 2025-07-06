"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import {
  FileText,
  Clock,
  CheckCircle,
  AlertCircle,
  Calendar,
  ArrowRight,
  Filter,
  Download,
} from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import DashboardLayout from "@/components/layout/dashboard-layout"
import api from "@/lib/api"
import { extractData } from "@/lib/api-utils"
import toast from "react-hot-toast"
import { useRouter } from "next/navigation"
import { format } from "date-fns"
import { zhCN } from "date-fns/locale"
import { cn } from "@/lib/utils"

interface Assignment {
  id: number
  title: string
  description: string
  course_name: string
  due_date: string
  total_points: number
  status: "pending" | "submitted" | "graded"
  score?: number
  submitted_at?: string
  graded_at?: string
}

const statusConfig = {
  pending: {
    label: "待完成",
    color: "bg-yellow-500",
    icon: Clock,
  },
  submitted: {
    label: "已提交",
    color: "bg-blue-500",
    icon: CheckCircle,
  },
  graded: {
    label: "已批改",
    color: "bg-green-500",
    icon: CheckCircle,
  },
}

export default function MyAssignmentsPage() {
  const router = useRouter()
  const [assignments, setAssignments] = useState<Assignment[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedCourse, setSelectedCourse] = useState<string>("all")
  const [courses, setCourses] = useState<{ id: string; name: string }[]>([])

  useEffect(() => {
    fetchAssignments()
  }, [selectedCourse])

  const fetchAssignments = async () => {
    try {
      const params = selectedCourse !== "all" ? { course_id: selectedCourse } : {}
      const response = await api.get("/api/student/assignments", { params })
      // 使用 extractData 统一处理响应格式
      const assignmentsData = extractData<Assignment[]>(response) || []
      setAssignments(assignmentsData)
      
      // Extract unique courses
      const uniqueCourses = Array.from(
        new Set(assignmentsData.map((a: Assignment) => a.course_name))
      ).map((name, index) => ({ id: String(index), name: name as string }))
      setCourses(uniqueCourses)
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.log("获取作业列表失败:", error)
      }
      toast.error("获取作业列表失败")
    } finally {
      setLoading(false)
    }
  }

  const getDaysUntilDue = (dueDate: string) => {
    const today = new Date()
    const due = new Date(dueDate)
    const diffTime = due.getTime() - today.getTime()
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    return diffDays
  }

  const getUpcomingAssignments = () => {
    return assignments
      .filter((a) => a.status === "pending")
      .sort((a, b) => new Date(a.due_date).getTime() - new Date(b.due_date).getTime())
      .slice(0, 5)
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">我的作业</h1>
            <p className="text-muted-foreground mt-1">查看和提交你的课程作业</p>
          </div>
          <Select value={selectedCourse} onValueChange={setSelectedCourse}>
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="筛选课程" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">所有课程</SelectItem>
              {courses.map((course) => (
                <SelectItem key={course.id} value={course.id}>
                  {course.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Upcoming Assignments Alert */}
        {getUpcomingAssignments().length > 0 && (
          <Card className="border-orange-200 bg-orange-50 dark:bg-orange-950/20">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-orange-600" />
                即将到期的作业
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {getUpcomingAssignments().map((assignment) => {
                  const daysLeft = getDaysUntilDue(assignment.due_date)
                  return (
                    <div
                      key={assignment.id}
                      className="flex items-center justify-between p-2 rounded-lg hover:bg-orange-100 dark:hover:bg-orange-950/40"
                    >
                      <div>
                        <p className="font-medium">{assignment.title}</p>
                        <p className="text-sm text-muted-foreground">
                          {assignment.course_name}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant={daysLeft <= 1 ? "destructive" : "secondary"}>
                          {daysLeft === 0
                            ? "今天到期"
                            : daysLeft === 1
                            ? "明天到期"
                            : `${daysLeft} 天后到期`}
                        </Badge>
                        <Button
                          size="sm"
                          onClick={() => router.push(`/dashboard/assignments/${assignment.id}`)}
                        >
                          去完成
                          <ArrowRight className="w-4 h-4 ml-1" />
                        </Button>
                      </div>
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Assignments Tabs */}
        <Tabs defaultValue="pending" className="space-y-4">
          <TabsList>
            <TabsTrigger value="pending">
              待完成 ({assignments.filter((a) => a.status === "pending").length})
            </TabsTrigger>
            <TabsTrigger value="submitted">
              已提交 ({assignments.filter((a) => a.status === "submitted").length})
            </TabsTrigger>
            <TabsTrigger value="graded">
              已批改 ({assignments.filter((a) => a.status === "graded").length})
            </TabsTrigger>
          </TabsList>

          {["pending", "submitted", "graded"].map((status) => (
            <TabsContent key={status} value={status} className="space-y-4">
              <div className="grid gap-4">
                {assignments
                  .filter((a) => a.status === status)
                  .map((assignment, index) => (
                    <motion.div
                      key={assignment.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                    >
                      <Card className="hover:shadow-md transition-shadow">
                        <CardHeader>
                          <div className="flex items-start justify-between">
                            <div className="space-y-1">
                              <CardTitle className="text-lg">
                                {assignment.title}
                              </CardTitle>
                              <CardDescription>
                                {assignment.course_name} • {assignment.total_points} 分
                              </CardDescription>
                            </div>
                            <Badge
                              variant="outline"
                              className={cn(
                                "flex items-center gap-1",
                                statusConfig[assignment.status as keyof typeof statusConfig].color,
                                "text-white border-0"
                              )}
                            >
                              {React.createElement(
                                statusConfig[assignment.status as keyof typeof statusConfig].icon,
                                { className: "w-3 h-3" }
                              )}
                              {statusConfig[assignment.status as keyof typeof statusConfig].label}
                            </Badge>
                          </div>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-3">
                            <p className="text-sm text-muted-foreground">
                              {assignment.description}
                            </p>
                            
                            <div className="flex items-center gap-4 text-sm">
                              <div className="flex items-center gap-1">
                                <Calendar className="w-4 h-4 text-muted-foreground" />
                                <span>
                                  截止时间：
                                  {format(new Date(assignment.due_date), "MM月dd日 HH:mm", {
                                    locale: zhCN,
                                  })}
                                </span>
                              </div>
                              
                              {assignment.submitted_at && (
                                <div className="flex items-center gap-1">
                                  <CheckCircle className="w-4 h-4 text-green-600" />
                                  <span>
                                    提交于：
                                    {format(new Date(assignment.submitted_at), "MM月dd日 HH:mm", {
                                      locale: zhCN,
                                    })}
                                  </span>
                                </div>
                              )}
                              
                              {assignment.score !== undefined && (
                                <div className="flex items-center gap-1">
                                  <span className="font-medium">
                                    得分：{assignment.score}/{assignment.total_points}
                                  </span>
                                </div>
                              )}
                            </div>
                            
                            <div className="flex items-center gap-2 pt-2">
                              {assignment.status === "pending" && (
                                <Button
                                  onClick={() => router.push(`/dashboard/assignments/${assignment.id}`)}
                                >
                                  开始作业
                                  <ArrowRight className="w-4 h-4 ml-1" />
                                </Button>
                              )}
                              
                              {assignment.status === "submitted" && (
                                <Button
                                  variant="outline"
                                  onClick={() => router.push(`/dashboard/assignments/${assignment.id}/submission`)}
                                >
                                  查看提交
                                </Button>
                              )}
                              
                              {assignment.status === "graded" && (
                                <>
                                  <Button
                                    onClick={() => router.push(`/dashboard/assignments/${assignment.id}/submission`)}
                                  >
                                    查看批改结果
                                  </Button>
                                  <Button variant="outline" size="icon">
                                    <Download className="w-4 h-4" />
                                  </Button>
                                </>
                              )}
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    </motion.div>
                  ))}
                  
                {assignments.filter((a) => a.status === status).length === 0 && (
                  <Card>
                    <CardContent className="flex flex-col items-center justify-center py-12">
                      <FileText className="w-12 h-12 text-muted-foreground mb-4" />
                      <p className="text-muted-foreground">
                        暂无{statusConfig[status as keyof typeof statusConfig].label}的作业
                      </p>
                    </CardContent>
                  </Card>
                )}
              </div>
            </TabsContent>
          ))}
        </Tabs>
      </div>
    </DashboardLayout>
  )
}