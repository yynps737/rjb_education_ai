"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import {
  Users,
  BookOpen,
  FileText,
  TrendingUp,
  Award,
  Activity,
  Brain,
  Calendar,
} from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import DashboardLayout from "@/components/layout/dashboard-layout"
import api from "@/lib/api"
import { extractData } from "@/lib/api-utils"
import { format } from "date-fns"
import { zhCN } from "date-fns/locale"

interface OverviewStats {
  totalStudents: number
  totalTeachers: number
  totalCourses: number
  totalAssignments: number
  averageScore: number
  activeUsers: number
  todaySubmissions: number
  pendingGrading: number
}

export default function AdminDashboardPage() {
  const [stats, setStats] = useState<OverviewStats>({
    totalStudents: 0,
    totalTeachers: 0,
    totalCourses: 0,
    totalAssignments: 0,
    averageScore: 0,
    activeUsers: 0,
    todaySubmissions: 0,
    pendingGrading: 0,
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchOverviewStats()
  }, [])

  const fetchOverviewStats = async () => {
    try {
      // 获取分析概览
      const analyticsRes = await api.get("/api/admin/analytics/overview")
      const analyticsData = extractData(analyticsRes)
      
      // 组合所有数据
      setStats({
        totalStudents: analyticsData?.users?.by_role?.student || 0,
        totalTeachers: analyticsData?.users?.by_role?.teacher || 0,
        totalCourses: analyticsData?.courses?.total || 0,
        totalAssignments: analyticsData?.assignments?.total || 0,
        averageScore: analyticsData?.assignments?.average_score || 0,
        activeUsers: analyticsData?.users?.active_last_7_days || 0,
        todaySubmissions: analyticsData?.assignments?.submissions || 0,
        pendingGrading: analyticsData?.assignments?.submissions - analyticsData?.assignments?.graded || 0,
      })
    } catch (error) {
      console.error("获取统计数据失败:", error)
    } finally {
      setLoading(false)
    }
  }

  const statsCards = [
    {
      title: "学生总数",
      value: stats.totalStudents,
      icon: Users,
      color: "text-blue-600",
      bgColor: "bg-blue-50",
    },
    {
      title: "教师总数",
      value: stats.totalTeachers,
      icon: Users,
      color: "text-green-600",
      bgColor: "bg-green-50",
    },
    {
      title: "课程总数",
      value: stats.totalCourses,
      icon: BookOpen,
      color: "text-purple-600",
      bgColor: "bg-purple-50",
    },
    {
      title: "作业总数",
      value: stats.totalAssignments,
      icon: FileText,
      color: "text-orange-600",
      bgColor: "bg-orange-50",
    },
    {
      title: "平均分数",
      value: stats.averageScore.toFixed(1),
      icon: Award,
      color: "text-red-600",
      bgColor: "bg-red-50",
    },
    {
      title: "活跃用户",
      value: stats.activeUsers,
      icon: Activity,
      color: "text-indigo-600",
      bgColor: "bg-indigo-50",
    },
    {
      title: "今日提交",
      value: stats.todaySubmissions,
      icon: Calendar,
      color: "text-teal-600",
      bgColor: "bg-teal-50",
    },
    {
      title: "待批改",
      value: stats.pendingGrading,
      icon: Brain,
      color: "text-pink-600",
      bgColor: "bg-pink-50",
    },
  ]

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* 头部 */}
        <div>
          <h1 className="text-3xl font-bold">管理员概览</h1>
          <p className="text-muted-foreground mt-1">
            欢迎回来！今天是 {format(new Date(), "yyyy年MM月dd日", { locale: zhCN })}
          </p>
        </div>

        {/* 统计卡片 */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {statsCards.map((stat, index) => (
            <motion.div
              key={stat.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">
                    {stat.title}
                  </CardTitle>
                  <div className={`p-2 rounded-lg ${stat.bgColor}`}>
                    <stat.icon className={`w-4 h-4 ${stat.color}`} />
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
        </div>

        {/* 快速操作 */}
        <Card>
          <CardHeader>
            <CardTitle>快速操作</CardTitle>
            <CardDescription>常用管理功能快捷入口</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-4">
              <a
                href="/dashboard/admin/users"
                className="flex flex-col items-center gap-2 p-4 rounded-lg border hover:bg-accent transition-colors"
              >
                <Users className="w-8 h-8 text-muted-foreground" />
                <span className="text-sm font-medium">用户管理</span>
              </a>
              <a
                href="/dashboard/admin/courses"
                className="flex flex-col items-center gap-2 p-4 rounded-lg border hover:bg-accent transition-colors"
              >
                <BookOpen className="w-8 h-8 text-muted-foreground" />
                <span className="text-sm font-medium">课程管理</span>
              </a>
              <a
                href="/dashboard/admin/analytics"
                className="flex flex-col items-center gap-2 p-4 rounded-lg border hover:bg-accent transition-colors"
              >
                <TrendingUp className="w-8 h-8 text-muted-foreground" />
                <span className="text-sm font-medium">数据分析</span>
              </a>
              <a
                href="/dashboard/admin/system"
                className="flex flex-col items-center gap-2 p-4 rounded-lg border hover:bg-accent transition-colors"
              >
                <Activity className="w-8 h-8 text-muted-foreground" />
                <span className="text-sm font-medium">系统设置</span>
              </a>
            </div>
          </CardContent>
        </Card>

        {/* 最近活动 */}
        <Card>
          <CardHeader>
            <CardTitle>最近活动</CardTitle>
            <CardDescription>系统最新动态</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[
                { user: "张三", action: "提交了作业", course: "机器学习基础", time: "5分钟前" },
                { user: "李老师", action: "发布了新作业", course: "深度学习", time: "1小时前" },
                { user: "王五", action: "完成了课程", course: "Python编程", time: "2小时前" },
                { user: "赵老师", action: "批改了作业", course: "数据结构", time: "3小时前" },
              ].map((activity, index) => (
                <div key={index} className="flex items-center gap-4">
                  <div className="w-2 h-2 bg-blue-600 rounded-full" />
                  <div className="flex-1">
                    <p className="text-sm">
                      <span className="font-medium">{activity.user}</span>{" "}
                      {activity.action}{" "}
                      <span className="text-muted-foreground">
                        {activity.course}
                      </span>
                    </p>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    {activity.time}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  )
}