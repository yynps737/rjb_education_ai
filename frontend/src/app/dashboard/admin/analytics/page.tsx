"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import {
  TrendingUp,
  Users,
  BookOpen,
  Brain,
  Award,
  Activity,
  Calendar,
  Filter,
  Download,
  RefreshCw,
} from "lucide-react"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import DashboardLayout from "@/components/layout/dashboard-layout"
import {
  ResponsiveContainer,
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from "recharts"
import api from "@/lib/api"
import { extractData } from "@/lib/api-utils"
import { cn } from "@/lib/utils"

// 模拟数据
const learningTrendData = [
  { date: "1月", students: 120, avgScore: 78, completion: 85 },
  { date: "2月", students: 150, avgScore: 80, completion: 87 },
  { date: "3月", students: 180, avgScore: 82, completion: 89 },
  { date: "4月", students: 220, avgScore: 85, completion: 91 },
  { date: "5月", students: 280, avgScore: 87, completion: 93 },
  { date: "6月", students: 350, avgScore: 89, completion: 95 },
]

const courseDistribution = [
  { name: "机器学习", value: 35, color: "#3b82f6" },
  { name: "深度学习", value: 25, color: "#8b5cf6" },
  { name: "数据结构", value: 20, color: "#ec4899" },
  { name: "算法设计", value: 15, color: "#f59e0b" },
  { name: "其他", value: 5, color: "#10b981" },
]

const knowledgeRadarData = [
  { subject: "基础概念", score: 85 },
  { subject: "编程实践", score: 78 },
  { subject: "算法理解", score: 82 },
  { subject: "项目应用", score: 75 },
  { subject: "理论知识", score: 88 },
  { subject: "创新能力", score: 72 },
]

const topStudents = [
  { name: "张三", score: 95, progress: 98, trend: "up" },
  { name: "李四", score: 93, progress: 96, trend: "up" },
  { name: "王五", score: 91, progress: 94, trend: "stable" },
  { name: "赵六", score: 89, progress: 92, trend: "up" },
  { name: "陈七", score: 87, progress: 90, trend: "down" },
]

export default function AnalyticsPage() {
  const [timeRange, setTimeRange] = useState("month")
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState({
    totalStudents: 0,
    activeStudents: 0,
    totalCourses: 0,
    avgCompletionRate: 0,
    totalQuestions: 15420,
    aiInteractions: 8960,
  })
  const [learningTrend, setLearningTrend] = useState<any[]>(learningTrendData)
  const [courseDist, setCourseDist] = useState<any[]>(courseDistribution)
  const [knowledgeRadar, setKnowledgeRadar] = useState<any[]>(knowledgeRadarData)
  const [topStudentsList, setTopStudentsList] = useState<any[]>(topStudents)

  useEffect(() => {
    fetchAnalytics()
  }, [timeRange])

  const fetchAnalytics = async () => {
    setLoading(true)
    try {
      // Fetch overview data
      const overviewRes = await api.get("/api/admin/analytics/overview")
      const overviewData = extractData(overviewRes)
      
      if (overviewData?.users && overviewData?.courses) {
        setStats({
          totalStudents: overviewData.users.by_role?.student || 0,
          activeStudents: overviewData.users.active_last_7_days || 0,
          totalCourses: overviewData.courses.total || 0,
          avgCompletionRate: overviewData.courses.utilization_rate || 0,
          totalQuestions: 15420, // Still mock
          aiInteractions: 8960, // Still mock
        })
      }

      // Fetch top students
      const topStudentsRes = await api.get("/api/admin/analytics/top/students", {
        params: { limit: 5 }
      })
      const topStudentsData = extractData(topStudentsRes)
      if (topStudentsData?.top_students) {
        const formattedTopStudents = topStudentsData.top_students.map((student: any, index: number) => ({
          name: student.full_name || student.username,
          score: Math.round(student.average_score || 0),
          progress: 90 + index * 2, // Mock progress
          trend: index < 3 ? "up" : index === 4 ? "down" : "stable"
        }))
        setTopStudentsList(formattedTopStudents)
      }
      
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.log("获取分析数据失败", error)
      }
    } finally {
      setLoading(false)
    }
  }

  const handleRefresh = async () => {
    setIsRefreshing(true)
    await fetchAnalytics()
    setIsRefreshing(false)
  }

  const handleExport = () => {
    // 导出数据逻辑
    console.log("Exporting data...")
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold gradient-text">数据分析中心</h1>
            <p className="text-muted-foreground mt-1">
              全方位教学数据分析，驱动智能决策
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Select value={timeRange} onValueChange={setTimeRange}>
              <SelectTrigger className="w-[120px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="week">本周</SelectItem>
                <SelectItem value="month">本月</SelectItem>
                <SelectItem value="quarter">本季度</SelectItem>
                <SelectItem value="year">本年</SelectItem>
              </SelectContent>
            </Select>
            <Button
              variant="outline"
              size="icon"
              onClick={handleRefresh}
              disabled={isRefreshing}
            >
              <RefreshCw
                className={cn("w-4 h-4", isRefreshing && "animate-spin")}
              />
            </Button>
            <Button variant="outline" size="sm" onClick={handleExport}>
              <Download className="w-4 h-4" />
              导出报告
            </Button>
          </div>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <Card className="relative overflow-hidden">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  学生总数
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.totalStudents}</div>
                <div className="flex items-center gap-1 text-xs text-green-600 mt-1">
                  <TrendingUp className="w-3 h-3" />
                  <span>+12.5%</span>
                </div>
                <div className="absolute right-4 top-4 text-4xl text-muted-foreground/10">
                  <Users />
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <Card className="relative overflow-hidden">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  活跃学生
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.activeStudents}</div>
                <Progress
                  value={(stats.activeStudents / stats.totalStudents) * 100}
                  className="h-1 mt-2"
                />
                <div className="absolute right-4 top-4 text-4xl text-muted-foreground/10">
                  <Activity />
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <Card className="relative overflow-hidden">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  课程数量
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.totalCourses}</div>
                <Badge variant="secondary" className="mt-1">
                  新增 5 门
                </Badge>
                <div className="absolute right-4 top-4 text-4xl text-muted-foreground/10">
                  <BookOpen />
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            <Card className="relative overflow-hidden">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  平均完成率
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {stats.avgCompletionRate}%
                </div>
                <div className="flex items-center gap-1 text-xs text-green-600 mt-1">
                  <TrendingUp className="w-3 h-3" />
                  <span>+2.3%</span>
                </div>
                <div className="absolute right-4 top-4 text-4xl text-muted-foreground/10">
                  <Award />
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
          >
            <Card className="relative overflow-hidden">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  题目生成
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.totalQuestions}</div>
                <p className="text-xs text-muted-foreground mt-1">本月生成</p>
                <div className="absolute right-4 top-4 text-4xl text-muted-foreground/10">
                  <Brain />
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
          >
            <Card className="relative overflow-hidden">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  AI交互次数
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.aiInteractions}</div>
                <p className="text-xs text-muted-foreground mt-1">日均 299</p>
                <div className="absolute right-4 top-4 text-4xl text-muted-foreground/10">
                  <Brain />
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Charts Row 1 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Learning Trend */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.7 }}
          >
            <Card>
              <CardHeader>
                <CardTitle>学习趋势分析</CardTitle>
                <CardDescription>
                  学生数量、平均分数和完成率变化
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={learningTrend}>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                    <XAxis dataKey="date" className="text-xs" />
                    <YAxis className="text-xs" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(var(--background))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: "8px",
                      }}
                    />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="students"
                      stroke="#3b82f6"
                      strokeWidth={2}
                      dot={{ fill: "#3b82f6", r: 4 }}
                      activeDot={{ r: 6 }}
                      name="学生数"
                    />
                    <Line
                      type="monotone"
                      dataKey="avgScore"
                      stroke="#8b5cf6"
                      strokeWidth={2}
                      dot={{ fill: "#8b5cf6", r: 4 }}
                      activeDot={{ r: 6 }}
                      name="平均分"
                    />
                    <Line
                      type="monotone"
                      dataKey="completion"
                      stroke="#10b981"
                      strokeWidth={2}
                      dot={{ fill: "#10b981", r: 4 }}
                      activeDot={{ r: 6 }}
                      name="完成率"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </motion.div>

          {/* Course Distribution */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.8 }}
          >
            <Card>
              <CardHeader>
                <CardTitle>课程分布</CardTitle>
                <CardDescription>各类课程学生占比</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={courseDist}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) =>
                        `${name} ${(percent * 100).toFixed(0)}%`
                      }
                      outerRadius={100}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {courseDist.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Charts Row 2 */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Knowledge Radar */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.9 }}
          >
            <Card>
              <CardHeader>
                <CardTitle>知识掌握雷达图</CardTitle>
                <CardDescription>各维度平均掌握程度</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <RadarChart data={knowledgeRadar}>
                    <PolarGrid stroke="hsl(var(--border))" />
                    <PolarAngleAxis
                      dataKey="subject"
                      className="text-xs"
                      tick={{ fill: "hsl(var(--foreground))" }}
                    />
                    <PolarRadiusAxis
                      angle={90}
                      domain={[0, 100]}
                      className="text-xs"
                    />
                    <Radar
                      name="平均分"
                      dataKey="score"
                      stroke="#3b82f6"
                      fill="#3b82f6"
                      fillOpacity={0.6}
                    />
                    <Tooltip />
                  </RadarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </motion.div>

          {/* Top Students */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.0 }}
          >
            <Card>
              <CardHeader>
                <CardTitle>优秀学生排行</CardTitle>
                <CardDescription>本月表现最佳学生</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {topStudentsList.map((student, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-3 rounded-lg bg-muted/50"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-sm font-bold">
                          {index + 1}
                        </div>
                        <div>
                          <p className="font-medium">{student.name}</p>
                          <p className="text-xs text-muted-foreground">
                            进度 {student.progress}%
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-bold">{student.score}</p>
                        <div className="flex items-center gap-1 text-xs">
                          {student.trend === "up" && (
                            <>
                              <TrendingUp className="w-3 h-3 text-green-600" />
                              <span className="text-green-600">上升</span>
                            </>
                          )}
                          {student.trend === "down" && (
                            <>
                              <TrendingUp className="w-3 h-3 text-red-600 rotate-180" />
                              <span className="text-red-600">下降</span>
                            </>
                          )}
                          {student.trend === "stable" && (
                            <span className="text-muted-foreground">稳定</span>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* AI Usage Stats */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.1 }}
          >
            <Card>
              <CardHeader>
                <CardTitle>AI功能使用统计</CardTitle>
                <CardDescription>各功能使用频率</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>智能问答</span>
                      <span className="font-medium">68%</span>
                    </div>
                    <Progress value={68} className="h-2" />
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>题目生成</span>
                      <span className="font-medium">45%</span>
                    </div>
                    <Progress value={45} className="h-2" />
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>自动批改</span>
                      <span className="font-medium">82%</span>
                    </div>
                    <Progress value={82} className="h-2" />
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>知识推荐</span>
                      <span className="font-medium">35%</span>
                    </div>
                    <Progress value={35} className="h-2" />
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>学习路径</span>
                      <span className="font-medium">52%</span>
                    </div>
                    <Progress value={52} className="h-2" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>
    </DashboardLayout>
  )
}