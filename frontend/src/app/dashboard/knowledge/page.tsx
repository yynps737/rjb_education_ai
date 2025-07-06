"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import {
  Search,
  Plus,
  BookOpen,
  FileText,
  Folder,
  Upload,
  Download,
  Eye,
  Edit,
  Trash,
  Star,
  Clock,
  Tag,
  Filter,
  MoreVertical,
  Grid,
  List,
  ChevronRight,
  Home,
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Checkbox } from "@/components/ui/checkbox"
import api from "@/lib/api"
import toast from "react-hot-toast"
import { useAuthStore } from "@/stores/auth-store"
import { cn } from "@/lib/utils"
import { format } from "date-fns"
import { zhCN } from "date-fns/locale"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

interface KnowledgeItem {
  id: number
  title: string
  content: string
  type: "article" | "video" | "document" | "link"
  category_id: number
  category_name: string
  tags: string[]
  author_id: number
  author_name: string
  view_count: number
  is_starred: boolean
  is_public: boolean
  file_url?: string
  file_path?: string
  file_size?: number
  meta_data?: {
    processed?: boolean
    word_count?: number
    page_count?: number
    [key: string]: any
  }
  created_at: string
  updated_at: string
}

interface Category {
  id: number
  name: string
  description: string
  parent_id?: number
  item_count: number
  icon?: string
}

interface KnowledgeStats {
  total_items: number
  total_views: number
  starred_items: number
  recent_items: number
}

const typeIcons = {
  article: <FileText className="w-4 h-4" />,
  video: <FileText className="w-4 h-4" />,
  document: <FileText className="w-4 h-4" />,
  link: <FileText className="w-4 h-4" />,
}

const typeColors = {
  article: "bg-blue-100 text-blue-700",
  video: "bg-purple-100 text-purple-700",
  document: "bg-green-100 text-green-700",
  link: "bg-yellow-100 text-yellow-700",
}

// 安全的日期格式化函数
const formatSafeDate = (dateStr: string | null | undefined, fallback = '-') => {
  if (!dateStr) return fallback
  try {
    const date = new Date(dateStr)
    if (isNaN(date.getTime())) return fallback
    return format(date, "MM-dd", { locale: zhCN })
  } catch {
    return fallback
  }
}

export default function KnowledgeBasePage() {
  const { user } = useAuthStore()
  const [items, setItems] = useState<KnowledgeItem[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [stats, setStats] = useState<KnowledgeStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedCategory, setSelectedCategory] = useState<string>("all")
  const [selectedType, setSelectedType] = useState<string>("all")
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid")
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [selectedItem, setSelectedItem] = useState<KnowledgeItem | null>(null)
  const [currentPath, setCurrentPath] = useState<{ id: string; name: string }[]>([
    { id: "all", name: "全部" }
  ])
  const [activeTab, setActiveTab] = useState("browse")
  const [question, setQuestion] = useState("")
  const [answer, setAnswer] = useState("")
  const [answerSources, setAnswerSources] = useState<any[]>([])
  const [isAsking, setIsAsking] = useState(false)
  const [selectedItems, setSelectedItems] = useState<Set<number>>(new Set())
  const [isSelectionMode, setIsSelectionMode] = useState(false)
  
  const [formData, setFormData] = useState({
    title: "",
    content: "",
    type: "article",
    category_id: "",
    tags: "",
    is_public: true,
    file: null as File | null,
  })
  const [uploadProgress, setUploadProgress] = useState(0)
  const [isUploading, setIsUploading] = useState(false)

  useEffect(() => {
    fetchItems()
    fetchCategories()
    fetchStats()
  }, [selectedCategory, selectedType])

  const fetchItems = async () => {
    try {
      const params: any = {}
      if (selectedCategory !== "all") params.category_id = selectedCategory
      if (selectedType !== "all") params.type = selectedType
      if (searchQuery) params.search = searchQuery
      
      const response = await api.get("/api/knowledge", { params })
      const data = response.data.data || response.data
      setItems(data.items || [])
    } catch (error) {
      toast.error("获取知识库内容失败")
    } finally {
      setLoading(false)
    }
  }

  const fetchCategories = async () => {
    try {
      const response = await api.get("/api/knowledge/categories")
      const data = response.data.data || response.data
      setCategories(Array.isArray(data) ? data : [])
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.log("获取分类失败", error)
      }
    }
  }

  const fetchStats = async () => {
    try {
      const response = await api.get("/api/knowledge/stats")
      const data = response.data.data || response.data
      setStats(data)
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.log("获取统计数据失败", error)
      }
    }
  }

  const handleCreateItem = async () => {
    try {
      const formDataToSend = new FormData()
      formDataToSend.append("title", formData.title)
      formDataToSend.append("content", formData.content)
      formDataToSend.append("type", formData.type)
      formDataToSend.append("category_id", formData.category_id)
      formDataToSend.append("tags", formData.tags)
      formDataToSend.append("is_public", String(formData.is_public))
      
      if (formData.file) {
        formDataToSend.append("file", formData.file)
      }

      const response = await api.post("/api/knowledge/create", formDataToSend, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      })
      
      // 提取响应数据
      const newItem = response.data?.data || response.data
      
      // 创建完整的项目对象以匹配列表格式
      const createdItem = {
        id: newItem.id,
        title: newItem.title,
        content: formData.content,
        type: newItem.type || formData.type,
        category: formData.category_id,
        tags: formData.tags.split(",").map(t => t.trim()).filter(t => t),
        author: { id: user?.id, name: user?.full_name || user?.username },
        isPublic: formData.is_public,
        createdAt: new Date().toISOString(),
        stats: {
          views: 0,
          likes: 0,
          shares: 0
        }
      }
      
      setItems([createdItem, ...items])
      toast.success("知识库文档创建成功")
      setIsCreateDialogOpen(false)
      resetForm()
      fetchItems()
      fetchStats()
    } catch (error) {
      console.error("创建失败:", error)
      toast.error("创建失败，请重试")
    }
  }

  const handleUpdateItem = async () => {
    if (!selectedItem) return

    try {
      const response = await api.put(`/api/knowledge/${selectedItem.id}`, {
        title: formData.title,
        content: formData.content,
        type: formData.type,
        category_id: parseInt(formData.category_id),
        tags: formData.tags.split(",").map(t => t.trim()),
        is_public: formData.is_public,
      })
      
      setItems(items.map(item => 
        item.id === selectedItem.id ? response.data : item
      ))
      toast.success("内容更新成功")
      setIsEditDialogOpen(false)
      setSelectedItem(null)
    } catch (error) {
      toast.error("更新失败，请重试")
    }
  }

  const handleDeleteItem = async (itemId: number) => {
    if (!confirm("确定要删除这个内容吗？")) return

    try {
      await api.delete(`/api/knowledge/${itemId}`)
      setItems(items.filter(item => item.id !== itemId))
      toast.success("内容已删除")
      fetchStats()
    } catch (error) {
      toast.error("删除失败，请重试")
    }
  }

  const handleBatchDelete = async () => {
    if (selectedItems.size === 0) {
      toast.error("请先选择要删除的内容")
      return
    }

    if (!confirm(`确定要删除选中的 ${selectedItems.size} 个内容吗？`)) return

    try {
      const itemIds = Array.from(selectedItems)
      await api.post('/api/knowledge/batch-delete', { ids: itemIds })
      setItems(items.filter(item => !selectedItems.has(item.id)))
      setSelectedItems(new Set())
      setIsSelectionMode(false)
      toast.success(`成功删除 ${itemIds.length} 个内容`)
      fetchStats()
    } catch (error) {
      toast.error("批量删除失败，请重试")
    }
  }

  const handleSelectItem = (itemId: number) => {
    const newSelected = new Set(selectedItems)
    if (newSelected.has(itemId)) {
      newSelected.delete(itemId)
    } else {
      newSelected.add(itemId)
    }
    setSelectedItems(newSelected)
  }

  const handleSelectAll = () => {
    if (selectedItems.size === filteredItems.length) {
      setSelectedItems(new Set())
    } else {
      setSelectedItems(new Set(filteredItems.map(item => item.id)))
    }
  }

  const handleToggleStar = async (item: KnowledgeItem) => {
    try {
      await api.post(`/api/knowledge/${item.id}/star`)
      setItems(items.map(i => 
        i.id === item.id ? { ...i, is_starred: !i.is_starred } : i
      ))
    } catch (error) {
      toast.error("操作失败")
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0]
      
      // 检查文件大小（最大50MB）
      const maxSize = 50 * 1024 * 1024
      if (file.size > maxSize) {
        toast.error("文件大小不能超过50MB")
        e.target.value = ""
        return
      }
      
      setFormData({ ...formData, file: file })
    }
  }
  
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const resetForm = () => {
    setFormData({
      title: "",
      content: "",
      type: "article",
      category_id: "",
      tags: "",
      is_public: true,
      file: null,
    })
  }

  const filteredItems = items.filter(item => {
    const matchesSearch = searchQuery.toLowerCase() === "" ||
      item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
    
    return matchesSearch
  })

  const getItemTypeLabel = (type: string) => {
    const labels = {
      article: "文章",
      video: "视频",
      document: "文档",
      link: "链接",
    }
    return labels[type as keyof typeof labels] || type
  }

  const canEdit = (item: KnowledgeItem) => {
    return user?.role === "admin" || user?.role === "teacher" || item.author_id === user?.id
  }

  const handleAskQuestion = async () => {
    if (!question.trim()) {
      toast.error("请输入问题")
      return
    }

    setIsAsking(true)
    setAnswer("")
    setAnswerSources([])

    try {
      const response = await api.post("/api/knowledge/ask", {
        query: question,
        context_type: "general",
        course_id: null
      })
      
      const data = response.data?.data || response.data
      if (data) {
        setAnswer(data.answer || "抱歉，我无法回答这个问题。")
        setAnswerSources(data.sources || [])
      }
    } catch (error) {
      console.error("提问失败:", error)
      toast.error("提问失败，请重试")
    } finally {
      setIsAsking(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">知识库</h1>
          <p className="text-muted-foreground mt-1">浏览和管理学习资源</p>
        </div>
        {(user?.role === "teacher" || user?.role === "admin") && (
            <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="w-4 h-4" />
                  创建内容
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl">
                <DialogHeader>
                  <DialogTitle>创建新内容</DialogTitle>
                  <DialogDescription>
                    添加新的学习资源到知识库
                  </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="grid gap-2">
                    <Label htmlFor="title">标题</Label>
                    <Input
                      id="title"
                      value={formData.title}
                      onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                      placeholder="输入标题"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="grid gap-2">
                      <Label htmlFor="type">类型</Label>
                      <Select
                        value={formData.type}
                        onValueChange={(value) => setFormData({ ...formData, type: value })}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="article">文章</SelectItem>
                          <SelectItem value="video">视频（需上传）</SelectItem>
                          <SelectItem value="document">文档（需上传）</SelectItem>
                          <SelectItem value="link">链接</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="grid gap-2">
                      <Label htmlFor="category">分类</Label>
                      <Select
                        value={formData.category_id}
                        onValueChange={(value) => setFormData({ ...formData, category_id: value })}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="选择分类" />
                        </SelectTrigger>
                        <SelectContent>
                          {categories.map((category) => (
                            <SelectItem key={category.id} value={String(category.id)}>
                              {category.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="content">内容</Label>
                    <Textarea
                      id="content"
                      value={formData.content}
                      onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                      rows={6}
                      placeholder={
                        formData.type === "link" 
                          ? "输入链接地址" 
                          : "输入详细内容..."
                      }
                    />
                  </div>
                  {(formData.type === "document" || formData.type === "video") && (
                    <div className="grid gap-2 p-4 border-2 border-dashed rounded-lg bg-muted/30">
                      <Label htmlFor="file" className="text-base font-semibold">
                        <Upload className="w-4 h-4 inline mr-2" />
                        上传文件
                      </Label>
                      <Input
                        id="file"
                        type="file"
                        onChange={handleFileChange}
                        accept={formData.type === "video" ? "video/*" : ".pdf,.doc,.docx,.ppt,.pptx,.xlsx,.xls,.txt,.md,.json,.csv"}
                        className="cursor-pointer"
                      />
                      <p className="text-sm text-muted-foreground">
                        {formData.type === "video" 
                          ? "支持格式：MP4, AVI, MOV等视频格式（最大50MB）" 
                          : "支持格式：PDF, Word, PowerPoint, Excel, TXT, Markdown, JSON, CSV（最大50MB）"}
                      </p>
                      {formData.file && (
                        <div className="mt-2 p-3 bg-muted rounded-lg">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <FileText className="w-4 h-4 text-muted-foreground" />
                              <span className="text-sm font-medium truncate max-w-[200px]">
                                {formData.file.name}
                              </span>
                            </div>
                            <span className="text-sm text-muted-foreground">
                              {formatFileSize(formData.file.size)}
                            </span>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                  <div className="grid gap-2">
                    <Label htmlFor="tags">标签（逗号分隔）</Label>
                    <Input
                      id="tags"
                      value={formData.tags}
                      onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
                      placeholder="例如：编程, Python, 入门"
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="is_public"
                      checked={formData.is_public}
                      onChange={(e) => setFormData({ ...formData, is_public: e.target.checked })}
                      className="rounded"
                    />
                    <Label htmlFor="is_public">公开内容（所有用户可见）</Label>
                  </div>
                </div>
                <div className="flex justify-end gap-2">
                  <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                    取消
                  </Button>
                  <Button onClick={handleCreateItem}>创建</Button>
                </div>
              </DialogContent>
            </Dialog>
          )}
        </div>

        {/* Stats */}
        {stats && (
          <div className="grid gap-4 md:grid-cols-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">总内容数</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.total_items}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">总浏览量</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.total_views}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">收藏内容</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.starred_items}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">本周新增</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.recent_items}</div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Tabs for Browse and Q&A */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-2 max-w-[400px]">
            <TabsTrigger value="browse">浏览知识库</TabsTrigger>
            <TabsTrigger value="qa">知识问答</TabsTrigger>
          </TabsList>

          {/* Browse Tab */}
          <TabsContent value="browse" className="space-y-6">
            {/* Filters and Search */}
            <div className="space-y-4">
              <div className="flex flex-wrap items-center gap-4">
                <div className="relative flex-1 min-w-[200px]">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    placeholder="搜索标题、内容或标签..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10"
                  />
                </div>
                
                {/* 批量操作按钮 */}
                {isSelectionMode ? (
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleSelectAll}
                    >
                      {selectedItems.size === filteredItems.length ? "取消全选" : "全选"}
                    </Button>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={handleBatchDelete}
                      disabled={selectedItems.size === 0}
                    >
                      <Trash className="w-4 h-4 mr-2" />
                      删除 ({selectedItems.size})
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setIsSelectionMode(false)
                        setSelectedItems(new Set())
                      }}
                    >
                      取消
                    </Button>
                  </div>
                ) : (
                  <Button
                    variant="outline"
                    onClick={() => setIsSelectionMode(true)}
                    className="bg-primary/10 hover:bg-primary/20"
                  >
                    <div className="w-4 h-4 mr-2 border rounded-sm" />
                    批量管理
                  </Button>
                )}
              </div>
              
              <div className="flex flex-wrap items-center gap-4">
                <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                  <SelectTrigger className="w-[180px]">
                    <SelectValue placeholder="筛选分类" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">所有分类</SelectItem>
                    {categories.map((category) => (
                      <SelectItem key={category.id} value={String(category.id)}>
                        {category.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Select value={selectedType} onValueChange={setSelectedType}>
                  <SelectTrigger className="w-[140px]">
                    <SelectValue placeholder="筛选类型" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">所有类型</SelectItem>
                    <SelectItem value="article">文章</SelectItem>
                    <SelectItem value="video">视频</SelectItem>
                    <SelectItem value="document">文档</SelectItem>
                    <SelectItem value="link">链接</SelectItem>
                  </SelectContent>
                </Select>
                <div className="flex items-center border rounded-lg">
                  <Button
                    variant={viewMode === "grid" ? "default" : "ghost"}
                    size="sm"
                    onClick={() => setViewMode("grid")}
                    className="rounded-r-none"
                  >
                    <Grid className="w-4 h-4" />
                  </Button>
                  <Button
                    variant={viewMode === "list" ? "default" : "ghost"}
                    size="sm"
                    onClick={() => setViewMode("list")}
                    className="rounded-l-none"
                  >
                    <List className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </div>

        {/* Content */}
        {viewMode === "grid" ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filteredItems.map((item, index) => (
              <motion.div
                key={item.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <Card className={cn(
                  "h-full hover:shadow-lg transition-shadow",
                  isSelectionMode && selectedItems.has(item.id) && "ring-2 ring-primary"
                )}>
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3 flex-1">
                        {isSelectionMode && (
                          <Checkbox
                            checked={selectedItems.has(item.id)}
                            onCheckedChange={() => handleSelectItem(item.id)}
                            className="mt-1"
                          />
                        )}
                        <div className="space-y-1 flex-1">
                          <CardTitle className="text-base line-clamp-2">
                            {item.title}
                          </CardTitle>
                          <div className="flex items-center gap-2 text-sm text-muted-foreground">
                            <Badge variant="secondary" className={typeColors[item.type]}>
                              {typeIcons[item.type]}
                              {getItemTypeLabel(item.type)}
                            </Badge>
                            <span>{item.category_name}</span>
                          </div>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleToggleStar(item)}
                      >
                        <Star className={cn(
                          "w-4 h-4",
                          item.is_starred && "fill-yellow-400 text-yellow-400"
                        )} />
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground line-clamp-3 mb-4">
                      {item.content}
                    </p>
                    {item.meta_data?.processed && (
                      <div className="flex items-center gap-3 text-xs text-muted-foreground mb-2">
                        {item.meta_data.page_count > 0 && (
                          <span className="flex items-center gap-1">
                            <FileText className="w-3 h-3" />
                            {item.meta_data.page_count} 页
                          </span>
                        )}
                        {item.meta_data.word_count > 0 && (
                          <span className="flex items-center gap-1">
                            {item.meta_data.word_count} 词
                          </span>
                        )}
                        {item.file_size && (
                          <span className="flex items-center gap-1">
                            {formatFileSize(item.file_size)}
                          </span>
                        )}
                      </div>
                    )}
                    <div className="flex flex-wrap gap-1 mb-4">
                      {item.tags.map((tag) => (
                        <Badge key={tag} variant="outline" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                    <div className="flex items-center justify-between text-sm text-muted-foreground">
                      <div className="flex items-center gap-2">
                        <span>{item.author_name}</span>
                        <span>•</span>
                        <span className="flex items-center gap-1">
                          <Eye className="w-3 h-3" />
                          {item.view_count}
                        </span>
                      </div>
                      {canEdit(item) && (
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreVertical className="w-4 h-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            {item.file_url && (
                              <>
                                <DropdownMenuItem onClick={() => {
                                  window.open(api.defaults.baseURL + item.file_url, '_blank')
                                }}>
                                  <Download className="w-4 h-4 mr-2" />
                                  下载文件
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                              </>
                            )}
                            <DropdownMenuItem onClick={() => {
                              setSelectedItem(item)
                              setFormData({
                                title: item.title,
                                content: item.content,
                                type: item.type,
                                category_id: String(item.category_id),
                                tags: item.tags.join(", "),
                                is_public: item.is_public,
                                file: null,
                              })
                              setIsEditDialogOpen(true)
                            }}>
                              <Edit className="w-4 h-4 mr-2" />
                              编辑
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem 
                              onClick={() => handleDeleteItem(item.id)}
                              className="text-destructive"
                            >
                              <Trash className="w-4 h-4 mr-2" />
                              删除
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        ) : (
          <Card>
            <CardContent className="p-0">
              <div className="divide-y">
                {filteredItems.map((item) => (
                  <div key={item.id} className={cn(
                    "p-4 hover:bg-muted/50 transition-colors",
                    isSelectionMode && selectedItems.has(item.id) && "bg-muted/50"
                  )}>
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3 flex-1">
                        {isSelectionMode && (
                          <Checkbox
                            checked={selectedItems.has(item.id)}
                            onCheckedChange={() => handleSelectItem(item.id)}
                            className="mt-1"
                          />
                        )}
                        <div className="flex-1 space-y-2">
                          <div className="flex items-center gap-3">
                            <Badge variant="secondary" className={typeColors[item.type]}>
                              {typeIcons[item.type]}
                              {getItemTypeLabel(item.type)}
                            </Badge>
                            <h3 className="font-medium">{item.title}</h3>
                            <Button
                              variant="ghost"
                            size="icon"
                            className="h-6 w-6"
                            onClick={() => handleToggleStar(item)}
                          >
                            <Star className={cn(
                              "w-4 h-4",
                              item.is_starred && "fill-yellow-400 text-yellow-400"
                            )} />
                          </Button>
                        </div>
                        <p className="text-sm text-muted-foreground line-clamp-2">
                          {item.content}
                        </p>
                        <div className="flex items-center gap-4 text-sm text-muted-foreground">
                          <span>{item.category_name}</span>
                          <span>{item.author_name}</span>
                          <span className="flex items-center gap-1">
                            <Eye className="w-3 h-3" />
                            {item.view_count}
                          </span>
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {formatSafeDate(item.created_at)}
                          </span>
                        </div>
                      </div>
                    </div>
                    {canEdit(item) && (
                      <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreVertical className="w-4 h-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            {item.file_url && (
                              <>
                                <DropdownMenuItem onClick={() => {
                                  window.open(api.defaults.baseURL + item.file_url, '_blank')
                                }}>
                                  <Download className="w-4 h-4 mr-2" />
                                  下载文件
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                              </>
                            )}
                            <DropdownMenuItem onClick={() => {
                              setSelectedItem(item)
                              setFormData({
                                title: item.title,
                                content: item.content,
                                type: item.type,
                                category_id: String(item.category_id),
                                tags: item.tags.join(", "),
                                is_public: item.is_public,
                                file: null,
                              })
                              setIsEditDialogOpen(true)
                            }}>
                              <Edit className="w-4 h-4 mr-2" />
                              编辑
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem 
                              onClick={() => handleDeleteItem(item.id)}
                              className="text-destructive"
                            >
                              <Trash className="w-4 h-4 mr-2" />
                              删除
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {filteredItems.length === 0 && (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <BookOpen className="w-12 h-12 text-muted-foreground mb-4" />
              <p className="text-muted-foreground">
                {searchQuery ? "没有找到匹配的内容" : "暂无内容"}
              </p>
            </CardContent>
          </Card>
        )}

        {/* Edit Dialog */}
        <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>编辑内容</DialogTitle>
              <DialogDescription>
                修改知识库内容
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="edit-title">标题</Label>
                <Input
                  id="edit-title"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="edit-type">类型</Label>
                  <Select
                    value={formData.type}
                    onValueChange={(value) => setFormData({ ...formData, type: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="article">文章</SelectItem>
                      <SelectItem value="video">视频</SelectItem>
                      <SelectItem value="document">文档</SelectItem>
                      <SelectItem value="link">链接</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="edit-category">分类</Label>
                  <Select
                    value={formData.category_id}
                    onValueChange={(value) => setFormData({ ...formData, category_id: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {categories.map((category) => (
                        <SelectItem key={category.id} value={String(category.id)}>
                          {category.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid gap-2">
                <Label htmlFor="edit-content">内容</Label>
                <Textarea
                  id="edit-content"
                  value={formData.content}
                  onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                  rows={6}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="edit-tags">标签（逗号分隔）</Label>
                <Input
                  id="edit-tags"
                  value={formData.tags}
                  onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
                />
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="edit-is_public"
                  checked={formData.is_public}
                  onChange={(e) => setFormData({ ...formData, is_public: e.target.checked })}
                  className="rounded"
                />
                <Label htmlFor="edit-is_public">公开内容</Label>
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
                取消
              </Button>
              <Button onClick={handleUpdateItem}>保存</Button>
            </div>
          </DialogContent>
        </Dialog>
          </TabsContent>

          {/* Q&A Tab */}
          <TabsContent value="qa" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>知识问答</CardTitle>
                <CardDescription>
                  基于知识库内容的智能问答系统
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Question Input */}
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="question">提出您的问题</Label>
                    <div className="flex gap-2">
                      <Textarea
                        id="question"
                        value={question}
                        onChange={(e) => setQuestion(e.target.value)}
                        placeholder="请输入您想了解的问题..."
                        className="min-h-[100px]"
                        disabled={isAsking}
                      />
                    </div>
                    <Button 
                      onClick={handleAskQuestion}
                      disabled={isAsking || !question.trim()}
                      className="w-full"
                    >
                      {isAsking ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                          正在思考...
                        </>
                      ) : (
                        <>提交问题</>
                      )}
                    </Button>
                  </div>
                </div>

                {/* Answer Display */}
                {(answer || isAsking) && (
                  <div className="space-y-4 border-t pt-6">
                    <div className="space-y-2">
                      <h3 className="font-semibold text-lg">AI 回答：</h3>
                      {isAsking ? (
                        <div className="space-y-2">
                          <div className="flex items-center gap-2 text-muted-foreground">
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-500" />
                            <span>正在生成回答...</span>
                          </div>
                        </div>
                      ) : (
                        <div className="prose prose-sm max-w-none dark:prose-invert">
                          <ReactMarkdown 
                            remarkPlugins={[remarkGfm]}
                            components={{
                              h1: ({children}) => <h1 className="text-2xl font-bold mt-6 mb-4">{children}</h1>,
                              h2: ({children}) => <h2 className="text-xl font-semibold mt-5 mb-3">{children}</h2>,
                              h3: ({children}) => <h3 className="text-lg font-medium mt-4 mb-2">{children}</h3>,
                              p: ({children}) => <p className="mb-4 leading-relaxed">{children}</p>,
                              ul: ({children}) => <ul className="list-disc list-inside mb-4 space-y-1">{children}</ul>,
                              ol: ({children}) => <ol className="list-decimal list-inside mb-4 space-y-1">{children}</ol>,
                              li: ({children}) => <li className="ml-4">{children}</li>,
                              strong: ({children}) => <span className="font-semibold">{children}</span>,
                              blockquote: ({children}) => (
                                <blockquote className="border-l-4 border-primary pl-4 my-4 italic">
                                  {children}
                                </blockquote>
                              ),
                              code: ({inline, children}) => 
                                inline ? (
                                  <code className="bg-muted px-1 py-0.5 rounded text-sm">{children}</code>
                                ) : (
                                  <pre className="bg-muted p-3 rounded-lg overflow-x-auto">
                                    <code>{children}</code>
                                  </pre>
                                ),
                              hr: () => <hr className="my-6 border-t border-muted-foreground/20" />,
                            }}
                          >
                            {answer}
                          </ReactMarkdown>
                        </div>
                      )}
                    </div>

                    {/* Sources Display */}
                    {answerSources.length > 0 && (
                      <div className="space-y-2">
                        <h4 className="font-medium text-sm text-muted-foreground">参考来源：</h4>
                        <div className="space-y-2">
                          {answerSources.map((source, index) => (
                            <Card key={index} className="p-3">
                              <div className="flex items-start gap-3">
                                <Badge variant="outline" className="mt-0.5">
                                  {index + 1}
                                </Badge>
                                <div className="flex-1 space-y-1">
                                  <p className="text-sm font-medium">{source.title}</p>
                                  <p className="text-sm text-muted-foreground line-clamp-2">
                                    {source.content}
                                  </p>
                                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                    <span>{source.type}</span>
                                    <span>•</span>
                                    <span>{source.category}</span>
                                  </div>
                                </div>
                              </div>
                            </Card>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Help Text */}
                {!answer && !isAsking && (
                  <div className="text-center py-8 text-muted-foreground">
                    <BookOpen className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p className="text-sm">
                      输入您的问题，AI 将基于知识库内容为您提供准确的答案
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
    </div>
  )
}