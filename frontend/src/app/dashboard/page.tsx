"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { motion } from "framer-motion"
import {
  BookOpen,
  Users,
  FileText,
  TrendingUp,
  Brain,
  MessageSquare,
  Award,
  Clock,
} from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { useAuthStore } from "@/stores/auth-store"
import DashboardLayout from "@/components/layout/dashboard-layout"
import api from "@/lib/api"
import { cn } from "@/lib/utils"

interface DashboardStats {
  totalCourses: number
  totalStudents: number
  totalAssignments: number
  avgScore: number
  todayQuestions: number
  weeklyProgress: number
}

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
}

const itemVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: {
      type: "spring",
      stiffness: 100,
    },
  },
}

export default function DashboardPage() {
  const { user } = useAuthStore()
  const router = useRouter()
  const [stats, setStats] = useState<DashboardStats>({
    totalCourses: 0,
    totalStudents: 0,
    totalAssignments: 0,
    avgScore: 0,
    todayQuestions: 0,
    weeklyProgress: 0,
  })
  const [loading, setLoading] = useState(true)
  
  // 调试信息
  useEffect(() => {
    console.log('Dashboard - Current user:', user);
    console.log('Dashboard - User role:', user?.role);
  }, [user])

  useEffect(() => {
    if (user) {
      fetchDashboardStats()
    }
  }, [user])

  const fetchDashboardStats = async () => {
    try {
      // 根据用户角色获取不同的统计数据
      if (user?.role === 'admin') {
        // 管理员获取全局统计
        const response = await api.get('/api/admin/analytics/overview')
        const data = response.data?.data
        if (data) {
          setStats({
            totalCourses: data.courses?.total || 0,
            totalStudents: data.users?.by_role?.student || 0,
            totalAssignments: data.assignments?.total || 0,
            avgScore: Math.round(data.assignments?.average_score || 0),
            todayQuestions: data.assignments?.submissions || 0,
            weeklyProgress: 75, // 暂时保留模拟数据
          })
        }
      } else if (user?.role === 'teacher') {
        // 教师获取自己的统计
        const response = await api.get('/api/teacher/stats')
        const data = response.data?.data
        setStats({
          totalCourses: data?.total_courses || 0,
          totalStudents: data?.total_students || 0,
          totalAssignments: data?.total_assignments || 0,
          avgScore: Math.round(data?.average_score || 0),
          todayQuestions: data?.today_questions || 0,
          weeklyProgress: data?.weekly_progress || 75,
        })
      } else if (user?.role === 'student') {
        // 学生获取个人统计 - 使用正确的API路径
        const response = await api.get('/api/student/profile/me/stats')
        const data = response.data?.data
        setStats({
          totalCourses: data?.courses?.total || 0,
          totalStudents: data?.assignments?.completed || 0, // 这里显示完成的作业数
          totalAssignments: data?.assignments?.total || 0,
          avgScore: Math.round(data?.average_score || 0),
          todayQuestions: data?.recent_activities?.length || 0,
          weeklyProgress: Math.round((data?.assignments?.completed / data?.assignments?.total) * 100) || 0,
        })
      }
    } catch (error: any) {
      // 在开发环境中使用console.warn避免Next.js的错误拦截
      if (process.env.NODE_ENV === 'development') {
        console.warn('获取统计数据失败:', error?.response?.data || error?.message || error)
      }
      
      // 如果API失败，使用默认值
      setStats({
        totalCourses: 0,
        totalStudents: 0,
        totalAssignments: 0,
        avgScore: 0,
        todayQuestions: 0,
        weeklyProgress: 0,
      })
    } finally {
      setLoading(false)
    }
  }

  const getGreeting = () => {
    const hour = new Date().getHours()
    if (hour < 12) return "早上好"
    if (hour < 18) return "下午好"
    return "晚上好"
  }

  const statsCards = [
    {
      title: user?.role === "student" ? "我的课程" : "课程总数",
      value: stats.totalCourses,
      icon: BookOpen,
      color: "text-blue-600",
      bgColor: "bg-blue-50",
    },
    {
      title: user?.role === "student" ? "完成作业" : "学生总数",
      value: stats.totalStudents,
      icon: Users,
      color: "text-green-600",
      bgColor: "bg-green-50",
    },
    {
      title: "作业总数",
      value: stats.totalAssignments,
      icon: FileText,
      color: "text-purple-600",
      bgColor: "bg-purple-50",
    },
    {
      title: "平均分数",
      value: `${stats.avgScore}%`,
      icon: Award,
      color: "text-orange-600",
      bgColor: "bg-orange-50",
    },
  ]

  return (
    <DashboardLayout>
      <div className="space-y-8">
        {/* Welcome Section */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-primary to-blue-600 p-8 text-white"
        >
          <div className="absolute right-0 top-0 -mt-4 -mr-4 h-40 w-40 rounded-full bg-white/10 blur-3xl" />
          <div className="absolute left-20 bottom-0 -mb-8 h-32 w-32 rounded-full bg-white/10 blur-2xl" />
          
          <div className="relative z-10">
            <h1 className="text-3xl font-bold mb-2">
              {getGreeting()}，{user?.full_name}！
            </h1>
            <p className="text-white/90">
              {user?.role === "student" && "继续你的学习之旅，今天又是充满机遇的一天"}
              {user?.role === "teacher" && "准备好激发学生的潜能了吗？"}
              {user?.role === "admin" && "系统运行状态良好，一切尽在掌控"}
            </p>
          </div>
        </motion.div>

        {/* Stats Grid */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
        >
          {statsCards.map((stat, index) => (
            <motion.div key={index} variants={itemVariants}>
              <Card className="hover:shadow-lg transition-all duration-300 hover:scale-[1.02]">
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">
                    {stat.title}
                  </CardTitle>
                  <div className={cn("p-2 rounded-lg", stat.bgColor)}>
                    <stat.icon className={cn("w-5 h-5", stat.color)} />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {loading ? (
                      <div className="h-8 w-20 bg-muted animate-pulse rounded" />
                    ) : (
                      stat.value
                    )}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </motion.div>

        {/* Quick Actions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <h2 className="text-xl font-semibold mb-4">快速操作</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {user?.role === "student" && (
              <>
                <Card 
                  className="cursor-pointer hover:shadow-md transition-all duration-300 group"
                  onClick={() => router.push('/dashboard/student/learning/chat')}
                >
                  <CardHeader>
                    <div className="flex items-center gap-3">
                      <div className="p-3 rounded-lg bg-blue-50 group-hover:bg-blue-100 transition-colors">
                        <MessageSquare className="w-6 h-6 text-blue-600" />
                      </div>
                      <div>
                        <CardTitle className="text-base">智能问答</CardTitle>
                        <CardDescription>AI助手随时为你答疑</CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                </Card>
                <Card 
                  className="cursor-pointer hover:shadow-md transition-all duration-300 group"
                  onClick={() => router.push('/dashboard/student/assignments')}
                >
                  <CardHeader>
                    <div className="flex items-center gap-3">
                      <div className="p-3 rounded-lg bg-green-50 group-hover:bg-green-100 transition-colors">
                        <FileText className="w-6 h-6 text-green-600" />
                      </div>
                      <div>
                        <CardTitle className="text-base">查看作业</CardTitle>
                        <CardDescription>3个待完成的作业</CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                </Card>
              </>
            )}
            {user?.role === "teacher" && (
              <>
                <Card 
                  className="cursor-pointer hover:shadow-md transition-all duration-300 group"
                  onClick={() => router.push('/dashboard/teacher/assignments')}
                >
                  <CardHeader>
                    <div className="flex items-center gap-3">
                      <div className="p-3 rounded-lg bg-purple-50 group-hover:bg-purple-100 transition-colors">
                        <Brain className="w-6 h-6 text-purple-600" />
                      </div>
                      <div>
                        <CardTitle className="text-base">生成题目</CardTitle>
                        <CardDescription>AI智能出题</CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                </Card>
                <Card 
                  className="cursor-pointer hover:shadow-md transition-all duration-300 group"
                  onClick={() => router.push('/dashboard/teacher/students')}
                >
                  <CardHeader>
                    <div className="flex items-center gap-3">
                      <div className="p-3 rounded-lg bg-orange-50 group-hover:bg-orange-100 transition-colors">
                        <Users className="w-6 h-6 text-orange-600" />
                      </div>
                      <div>
                        <CardTitle className="text-base">学生管理</CardTitle>
                        <CardDescription>查看学生进度</CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                </Card>
              </>
            )}
            {user?.role === "admin" && (
              <>
                <Card 
                  className="cursor-pointer hover:shadow-md transition-all duration-300 group"
                  onClick={() => router.push('/dashboard/admin/users')}
                >
                  <CardHeader>
                    <div className="flex items-center gap-3">
                      <div className="p-3 rounded-lg bg-red-50 group-hover:bg-red-100 transition-colors">
                        <Users className="w-6 h-6 text-red-600" />
                      </div>
                      <div>
                        <CardTitle className="text-base">用户管理</CardTitle>
                        <CardDescription>管理所有用户</CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                </Card>
                <Card 
                  className="cursor-pointer hover:shadow-md transition-all duration-300 group"
                  onClick={() => router.push('/dashboard/admin/courses')}
                >
                  <CardHeader>
                    <div className="flex items-center gap-3">
                      <div className="p-3 rounded-lg bg-emerald-50 group-hover:bg-emerald-100 transition-colors">
                        <BookOpen className="w-6 h-6 text-emerald-600" />
                      </div>
                      <div>
                        <CardTitle className="text-base">课程管理</CardTitle>
                        <CardDescription>管理所有课程</CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                </Card>
              </>
            )}
            <Card 
              className="cursor-pointer hover:shadow-md transition-all duration-300 group"
              onClick={() => {
                if (user?.role === 'student') {
                  router.push('/dashboard/student/learning')
                } else if (user?.role === 'teacher') {
                  router.push('/dashboard/teacher/courses')
                } else if (user?.role === 'admin') {
                  router.push('/dashboard/admin/analytics')
                }
              }}
            >
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="p-3 rounded-lg bg-indigo-50 group-hover:bg-indigo-100 transition-colors">
                    <Clock className="w-6 h-6 text-indigo-600" />
                  </div>
                  <div>
                    <CardTitle className="text-base">最近活动</CardTitle>
                    <CardDescription>查看学习记录</CardDescription>
                  </div>
                </div>
              </CardHeader>
            </Card>
          </div>
        </motion.div>
      </div>
    </DashboardLayout>
  )
}