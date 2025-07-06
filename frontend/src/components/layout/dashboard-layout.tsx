"use client"

import { useState, useEffect } from "react"
import { useRouter, usePathname } from "next/navigation"
import { motion, AnimatePresence } from "framer-motion"
import Image from "next/image"
import {
  Home,
  BookOpen,
  FileText,
  Users,
  Settings,
  BarChart3,
  LogOut,
  Menu,
  X,
  Brain,
  UserCircle,
  FolderOpen,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar"
import { useAuthStore } from "@/stores/auth-store"
import { cn } from "@/lib/utils"

interface NavItem {
  title: string
  href: string
  icon: React.ElementType
  roles: string[]
}

const navItems: NavItem[] = [
  { title: "概览", href: "/dashboard", icon: Home, roles: ["student", "teacher", "admin"] },
  
  // 学生路由 - 对应后端 /api/student/*
  { title: "我的课程", href: "/dashboard/student/courses", icon: BookOpen, roles: ["student"] },
  { title: "我的作业", href: "/dashboard/student/assignments", icon: FileText, roles: ["student"] },
  { title: "学习中心", href: "/dashboard/student/learning", icon: Brain, roles: ["student"] },
  { title: "个人资料", href: "/dashboard/student/profile", icon: UserCircle, roles: ["student"] },
  
  // 教师路由 - 对应后端 /api/teacher/*
  { title: "课程设计", href: "/dashboard/teacher/course", icon: BookOpen, roles: ["teacher"] },
  { title: "作业管理", href: "/dashboard/teacher/assignments", icon: FileText, roles: ["teacher"] },
  { title: "学生管理", href: "/dashboard/teacher/students", icon: Users, roles: ["teacher"] },
  
  // 管理员路由 - 对应后端 /api/admin/*
  { title: "用户管理", href: "/dashboard/admin/users", icon: Users, roles: ["admin"] },
  { title: "课程管理", href: "/dashboard/admin/courses", icon: BookOpen, roles: ["admin"] },
  { title: "数据分析", href: "/dashboard/admin/analytics", icon: BarChart3, roles: ["admin"] },
  { title: "系统管理", href: "/dashboard/admin/system", icon: Settings, roles: ["admin"] },
  
  // 通用路由 - 对应后端 /api/knowledge
  { title: "知识库", href: "/dashboard/knowledge", icon: FolderOpen, roles: ["student", "teacher", "admin"] },
]

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()
  const { user, logout } = useAuthStore()
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  // 只显示用户角色对应的菜单项
  const filteredNavItems = navItems.filter((item) =>
    item.roles.includes(user?.role || "")
  )

  const handleLogout = () => {
    logout()
    router.push("/login")
  }

  // 如果还没有挂载，不渲染任何内容，避免SSR问题
  if (!mounted) {
    return null
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Mobile Menu Button */}
      <div className="lg:hidden fixed top-4 left-4 z-50">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setIsSidebarOpen(!isSidebarOpen)}
          className="glass"
        >
          {isSidebarOpen ? <X size={20} /> : <Menu size={20} />}
        </Button>
      </div>

      {/* Desktop Sidebar - Always visible on large screens */}
      <aside className="hidden lg:block fixed left-0 top-0 h-full w-[280px] bg-card border-r z-40">
        <SidebarContent
          filteredNavItems={filteredNavItems}
          pathname={pathname}
          user={user}
          router={router}
          handleLogout={handleLogout}
          onNavigate={() => {}}
        />
      </aside>

      {/* Mobile Sidebar - Only visible when open */}
      <AnimatePresence>
        {isSidebarOpen && (
          <>
            <motion.aside
              initial={{ x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
              className="lg:hidden fixed left-0 top-0 h-full w-[280px] bg-card border-r z-40"
            >
              <SidebarContent
                filteredNavItems={filteredNavItems}
                pathname={pathname}
                user={user}
                router={router}
                handleLogout={handleLogout}
                onNavigate={() => setIsSidebarOpen(false)}
              />
            </motion.aside>
            
            {/* Mobile Overlay */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="lg:hidden fixed inset-0 bg-black/50 z-30"
              onClick={() => setIsSidebarOpen(false)}
            />
          </>
        )}
      </AnimatePresence>

      {/* Main Content */}
      <main className="min-h-screen lg:pl-[280px]">
        <div className="p-6 lg:p-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            {children}
          </motion.div>
        </div>
      </main>
    </div>
  )
}

// Sidebar content component
function SidebarContent({ 
  filteredNavItems, 
  pathname, 
  user, 
  router, 
  handleLogout,
  onNavigate
}: {
  filteredNavItems: NavItem[]
  pathname: string
  user: any
  router: any
  handleLogout: () => void
  onNavigate: () => void
}) {
  return (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className="p-6 border-b">
        <div className="flex items-center gap-3">
          <Image
            src="/school-logo.png"
            alt="武昌首义学院"
            width={48}
            height={48}
            className="rounded-lg"
            priority
          />
          <div>
            <h2 className="font-bold text-lg">智能教育平台</h2>
            <p className="text-xs text-muted-foreground">武昌首义学院</p>
          </div>
        </div>
      </div>

      {/* User Info */}
      <div className="p-4 border-b">
        <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
          <Avatar className="w-10 h-10">
            <AvatarImage src={user?.avatar_url} />
            <AvatarFallback>
              {user?.full_name?.[0] || user?.username?.[0] || <UserCircle className="w-6 h-6" />}
            </AvatarFallback>
          </Avatar>
          <div className="flex-1">
            <p className="font-medium text-sm">{user?.full_name || "未登录"}</p>
            <p className="text-xs text-muted-foreground">
              {user?.role === "student" && "学生"}
              {user?.role === "teacher" && "教师"}
              {user?.role === "admin" && "管理员"}
            </p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto p-4 space-y-1">
        {filteredNavItems.map((item) => {
          const isActive = pathname === item.href
          const Icon = item.icon
          
          return (
            <motion.button
              key={item.href}
              onClick={() => {
                router.push(item.href)
                onNavigate()
              }}
              className={cn(
                "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200",
                "hover:bg-accent hover:text-accent-foreground",
                isActive && "bg-primary text-primary-foreground shadow-sm"
              )}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <Icon className="w-5 h-5" />
              <span className="flex-1 text-left">{item.title}</span>
              {isActive && (
                <motion.div
                  layoutId="activeIndicator"
                  className="w-1.5 h-1.5 bg-current rounded-full"
                />
              )}
            </motion.button>
          )
        })}
      </nav>

      {/* Logout Button */}
      <div className="p-4 border-t">
        <Button
          variant="ghost"
          className="w-full justify-start gap-3"
          onClick={handleLogout}
        >
          <LogOut className="w-5 h-5" />
          退出登录
        </Button>
      </div>
    </div>
  )
}