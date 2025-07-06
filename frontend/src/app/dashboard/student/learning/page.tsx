"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import {
  Brain,
  MessageSquare,
  Target,
  TrendingUp,
  BookOpen,
  Clock,
  Award,
  ChevronRight,
} from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import DashboardLayout from "@/components/layout/dashboard-layout"
import api from "@/lib/api"
import toast from "react-hot-toast"
import { useRouter } from "next/navigation"

interface LearningData {
  current_course?: {
    id: number
    title: string
    progress: number
    last_accessed: string
  }
  study_streak: number
  total_study_time: number
  completed_lessons: number
  achievements: Achievement[]
}

interface Achievement {
  id: number
  title: string
  description: string
  icon: string
  earned_at: string
}

export default function StudentLearningPage() {
  const router = useRouter()
  const [learningData, setLearningData] = useState<LearningData>({
    study_streak: 0,
    total_study_time: 0,
    completed_lessons: 0,
    achievements: [],
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchLearningData()
  }, [])

  const fetchLearningData = async () => {
    try {
      const response = await api.get("/api/student/learning/dashboard")
      setLearningData(response.data)
    } catch (error) {
      // 如果API不存在，使用模拟数据
      setLearningData({
        current_course: {
          id: 1,
          title: "Python编程基础",
          progress: 65,
          last_accessed: new Date().toISOString(),
        },
        study_streak: 7,
        total_study_time: 1250,
        completed_lessons: 15,
        achievements: [
          {
            id: 1,
            title: "连续学习7天",
            description: "保持学习热情！",
            icon: "🔥",
            earned_at: new Date().toISOString(),
          },
        ],
      })
    } finally {
      setLoading(false)
    }
  }

  const handleStartChat = () => {
    router.push("/dashboard/student/learning/chat")
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold">学习中心</h1>
          <p className="text-muted-foreground mt-1">AI驱动的个性化学习体验</p>
        </div>

        {/* AI Chat Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Card className="bg-gradient-to-r from-blue-500 to-purple-600 text-white">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Brain className="w-6 h-6" />
                AI学习助手
              </CardTitle>
              <CardDescription className="text-white/90">
                随时随地获得个性化学习指导
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="mb-4 text-white/80">
                我是你的AI学习助手，可以帮你解答问题、生成练习题、制定学习计划。
              </p>
              <Button 
                onClick={handleStartChat}
                variant="secondary"
                className="bg-white text-gray-900 hover:bg-gray-100"
              >
                <MessageSquare className="w-4 h-4 mr-2" />
                开始对话
              </Button>
            </CardContent>
          </Card>
        </motion.div>

        {/* Stats Grid */}
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">学习连续天数</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold flex items-center gap-2">
                {learningData.study_streak}
                <span className="text-lg">🔥</span>
              </div>
              <p className="text-xs text-muted-foreground mt-1">继续保持！</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">总学习时长</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {Math.round(learningData.total_study_time / 60)}小时
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                <Clock className="w-3 h-3 inline mr-1" />
                今日45分钟
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">完成课程</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{learningData.completed_lessons}</div>
              <p className="text-xs text-muted-foreground mt-1">
                <TrendingUp className="w-3 h-3 inline mr-1 text-green-600" />
                本周+3
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">获得成就</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{learningData.achievements.length}</div>
              <p className="text-xs text-muted-foreground mt-1">
                <Award className="w-3 h-3 inline mr-1" />
                查看全部
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Current Course Progress */}
        {learningData.current_course && (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg">继续学习</CardTitle>
                  <CardDescription>{learningData.current_course.title}</CardDescription>
                </div>
                <Button variant="outline" size="sm">
                  <BookOpen className="w-4 h-4 mr-2" />
                  查看课程
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span>课程进度</span>
                  <span className="font-medium">{learningData.current_course.progress}%</span>
                </div>
                <Progress value={learningData.current_course.progress} className="h-2" />
              </div>
            </CardContent>
          </Card>
        )}

        {/* Achievements */}
        {learningData.achievements.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>最新成就</CardTitle>
              <CardDescription>继续努力，解锁更多成就！</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {learningData.achievements.map((achievement) => (
                  <div
                    key={achievement.id}
                    className="flex items-center gap-3 p-3 rounded-lg bg-muted/50"
                  >
                    <span className="text-2xl">{achievement.icon}</span>
                    <div className="flex-1">
                      <p className="font-medium">{achievement.title}</p>
                      <p className="text-sm text-muted-foreground">
                        {achievement.description}
                      </p>
                    </div>
                    <ChevronRight className="w-4 h-4 text-muted-foreground" />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Learning Features */}
        <div className="grid gap-4 md:grid-cols-3">
          <Card className="cursor-pointer hover:shadow-lg transition-shadow">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Target className="w-5 h-5 text-orange-600" />
                学习目标
              </CardTitle>
              <CardDescription>设定并追踪你的学习目标</CardDescription>
            </CardHeader>
          </Card>
          <Card className="cursor-pointer hover:shadow-lg transition-shadow">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Brain className="w-5 h-5 text-purple-600" />
                智能练习
              </CardTitle>
              <CardDescription>AI生成的个性化练习题</CardDescription>
            </CardHeader>
          </Card>
          <Card className="cursor-pointer hover:shadow-lg transition-shadow">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-green-600" />
                学习报告
              </CardTitle>
              <CardDescription>查看详细的学习分析报告</CardDescription>
            </CardHeader>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  )
}