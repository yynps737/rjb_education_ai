"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { motion } from "framer-motion"
import { Eye, EyeOff, GraduationCap, Sparkles } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useAuthStore } from "@/stores/auth-store"
import toast from "react-hot-toast"
import Image from "next/image"

export default function LoginPage() {
  const router = useRouter()
  const { login } = useAuthStore()
  const [isLoading, setIsLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [formData, setFormData] = useState({
    username: "",
    password: "",
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    try {
      await login(formData.username, formData.password)
      toast.success("登录成功！")
      
      // 延迟一下确保状态已更新
      setTimeout(() => {
        router.push("/dashboard")
        // 如果路由跳转失败，使用window.location
        setTimeout(() => {
          if (window.location.pathname === "/login") {
            window.location.href = "/dashboard"
          }
        }, 500)
      }, 100)
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "登录失败，请检查用户名和密码")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex">
      {/* Left Panel - Login Form */}
      <div className="flex-1 flex items-center justify-center p-8 relative overflow-hidden">
        {/* Background Pattern */}
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-blue-500/5" />
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-primary/10 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-500/10 rounded-full blur-3xl" />
        
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="w-full max-w-md z-10"
        >
          {/* Logo and Title */}
          <div className="flex items-center gap-4 mb-8">
            <Image
              src="/school-logo.png"
              alt="武昌首义学院"
              width={60}
              height={60}
              className="rounded-xl shadow-md"
            />
            <div>
              <h1 className="text-2xl font-bold gradient-text">智能教育平台</h1>
              <p className="text-sm text-muted-foreground">武昌首义学院</p>
            </div>
          </div>

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <Label htmlFor="username">用户名</Label>
              <Input
                id="username"
                placeholder="请输入用户名"
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                required
                className="h-11"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">密码</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="请输入密码"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  required
                  className="h-11 pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            <Button
              type="submit"
              disabled={isLoading}
              className="w-full h-11"
              variant="gradient"
            >
              {isLoading ? (
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                >
                  <Sparkles className="w-4 h-4" />
                </motion.div>
              ) : (
                "登录"
              )}
            </Button>
          </form>

          {/* Demo Accounts */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="mt-8 p-4 rounded-lg bg-muted/50 space-y-2"
          >
            <p className="text-sm font-medium text-muted-foreground">测试账号：</p>
            <div className="space-y-1 text-xs text-muted-foreground">
              <p>学生：student / student123</p>
              <p>教师：teacher / teacher123</p>
              <p>管理员：admin / admin123</p>
            </div>
          </motion.div>
        </motion.div>
      </div>

      {/* Right Panel - Feature Showcase */}
      <div className="hidden lg:flex flex-1 bg-gradient-to-br from-primary to-blue-600 p-12 items-center justify-center relative overflow-hidden">
        {/* Animated Background */}
        <div className="absolute inset-0">
          <div className="absolute top-20 left-20 w-40 h-40 bg-white/10 rounded-full blur-2xl animate-pulse" />
          <div className="absolute bottom-20 right-20 w-60 h-60 bg-white/10 rounded-full blur-3xl animate-pulse delay-1000" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-80 h-80 bg-white/5 rounded-full blur-3xl animate-pulse delay-500" />
        </div>

        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
          className="max-w-lg text-white z-10"
        >
          <GraduationCap className="w-16 h-16 mb-6" />
          <h2 className="text-4xl font-bold mb-4">AI驱动的智能教育</h2>
          <p className="text-lg mb-8 text-white/90">
            利用先进的人工智能技术，为教师和学生提供个性化的教学体验
          </p>
          
          <div className="space-y-4">
            {[
              { title: "智能题目生成", desc: "根据知识点自动生成多样化题目" },
              { title: "实时批改反馈", desc: "AI辅助批改，提供即时学习反馈" },
              { title: "个性化学习", desc: "基于学习数据的智能推荐系统" },
              { title: "数据驱动决策", desc: "全方位的学习分析和可视化" },
            ].map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 * index + 0.5 }}
                className="flex items-start gap-3"
              >
                <div className="w-2 h-2 bg-white rounded-full mt-2" />
                <div>
                  <h3 className="font-semibold">{feature.title}</h3>
                  <p className="text-sm text-white/80">{feature.desc}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  )
}