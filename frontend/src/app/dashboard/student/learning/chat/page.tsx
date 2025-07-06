"use client"

import { useState, useRef, useEffect } from "react"
import { flushSync } from "react-dom"
import { motion, AnimatePresence } from "framer-motion"
import {
  Send,
  Bot,
  User,
  Sparkles,
  Copy,
  ThumbsUp,
  ThumbsDown,
  RotateCw,
  BookOpen,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { ScrollArea } from "@/components/ui/scroll-area"
import DashboardLayout from "@/components/layout/dashboard-layout"
import api from "@/lib/api"
import { extractData } from "@/lib/api-utils"
import toast from "react-hot-toast"
import { cn } from "@/lib/utils"
import { streamAskQuestion } from "@/lib/streamApi"

// 降级到非流式API的辅助函数
const fallbackToNonStream = async (question: string, token: string | null) => {
  const response = await api.post("/api/student/learning/ask", {
    question: question,
    course_id: null,
  })
  
  const responseData = extractData(response)
  let answerContent = "抱歉，我暂时无法回答这个问题。"
  
  if (responseData && responseData.answer) {
    answerContent = responseData.answer
  }
  
  return answerContent
}

interface Message {
  id: string
  content: string
  role: "user" | "assistant"
  timestamp: Date
  isTyping?: boolean
}

interface QuickPrompt {
  label: string
  prompt: string
  icon: React.ComponentType<{ className?: string }>
}

const quickPrompts: QuickPrompt[] = [
  {
    label: "解释概念",
    prompt: "请解释一下",
    icon: BookOpen,
  },
  {
    label: "代码示例",
    prompt: "能给我一个代码示例吗？",
    icon: Sparkles,
  },
  {
    label: "最佳实践",
    prompt: "这方面的最佳实践是什么？",
    icon: ThumbsUp,
  },
]

// 生成唯一ID的辅助函数
let idCounter = 0
const generateUniqueId = (prefix: string = 'msg') => {
  idCounter += 1
  return `${prefix}-${Date.now()}-${idCounter}-${Math.random().toString(36).substr(2, 9)}`
}

export default function AIAssistantPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "initial-message",
      content: "你好！我是你的AI学习助手。有什么可以帮助你的吗？",
      role: "assistant",
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [streamingMessageId, setStreamingMessageId] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const streamingMessageRef = useRef<string>("")  // 用于存储流式消息内容

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    // 使用更唯一的ID生成方式，避免重复
    const userMessage: Message = {
      id: generateUniqueId('user'),
      content: input,
      role: "user",
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput("")
    setIsLoading(true)

    // 创建助手消息（初始为空）
    const assistantMessageId = generateUniqueId('assistant')
    const assistantMessage: Message = {
      id: assistantMessageId,
      content: "",
      role: "assistant",
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, assistantMessage])
    setStreamingMessageId(assistantMessageId)

    try {
      const token = localStorage.getItem('token')
      let sources: any[] = []
      let useStream = true
      
      // 重置流式消息引用
      streamingMessageRef.current = ""
      
      try {
        // 尝试使用流式API - 明确指定使用 student 端点
        for await (const data of streamAskQuestion(userMessage.content, undefined, token || undefined, 'student')) {
        switch (data.type) {
          case 'metadata':
            sources = data.sources
            break
            
          case 'content':
            // 累积内容到 ref
            streamingMessageRef.current += data.content
            const currentContent = streamingMessageRef.current
            
            // 使用 requestAnimationFrame 确保浏览器渲染
            requestAnimationFrame(() => {
              setMessages((prev) => 
                prev.map(msg => 
                  msg.id === assistantMessageId 
                    ? { ...msg, content: currentContent }
                    : msg
                )
              )
            })
            break
            
          case 'done':
            // 流式传输完成，不再自动添加参考来源
            // AI 会在需要时自行添加
            break
            
          case 'error':
            throw new Error(data.error)
        }
      }
      } catch (streamError) {
        // 流式API失败，尝试降级到非流式API
        useStream = false
        try {
          const answer = await fallbackToNonStream(userMessage.content, token)
          setMessages((prev) => 
            prev.map(msg => 
              msg.id === assistantMessageId 
                ? { ...msg, content: answer }
                : msg
            )
          )
        } catch (fallbackError) {
          throw fallbackError // 如果降级也失败，抛出错误
        }
      }
    } catch (error) {
      // 更新消息为错误状态
      let errorMessage = "抱歉，发生了错误。请稍后再试。"
      
      if (error instanceof Error) {
        // 检查是否是认证错误
        if (error.message.includes('401') || error.message.includes('403')) {
          errorMessage = "认证失败，请重新登录。"
          // 可选：自动跳转到登录页
          // window.location.href = '/login'
        } else if (error.message.includes('404')) {
          errorMessage = "服务端点未找到，请联系管理员。"
        } else if (error.message.includes('500')) {
          errorMessage = "服务器错误，请稍后再试。"
        }
      }
      
      setMessages((prev) => 
        prev.map(msg => 
          msg.id === assistantMessageId 
            ? { ...msg, content: errorMessage }
            : msg
        )
      )
      toast.error("发送失败，请重试")
    } finally {
      setIsLoading(false)
      setStreamingMessageId(null)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleCopy = async (content: string) => {
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(content)
        toast.success("已复制到剪贴板")
      } else {
        // 降级方案：使用传统的复制方法
        const textArea = document.createElement("textarea")
        textArea.value = content
        textArea.style.position = "fixed"
        textArea.style.left = "-999999px"
        document.body.appendChild(textArea)
        textArea.focus()
        textArea.select()
        
        try {
          document.execCommand('copy')
          toast.success("已复制到剪贴板")
        } catch (err) {
          toast.error("复制失败，请手动复制")
        }
        
        document.body.removeChild(textArea)
      }
    } catch (err) {
      toast.error("复制失败，请手动复制")
    }
  }

  const handleQuickPrompt = (prompt: string) => {
    setInput(prompt)
    textareaRef.current?.focus()
  }

  return (
    <DashboardLayout>
      <div className="flex flex-col h-[calc(100vh-6rem)]">
        <div className="mb-6">
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Bot className="w-8 h-8 text-primary" />
            AI 学习助手
          </h1>
          <p className="text-muted-foreground mt-1">
            随时为你答疑解惑，助力学习进步
          </p>
        </div>

        <Card className="flex-1 flex flex-col overflow-hidden">
          <CardHeader className="border-b">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">对话</CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setMessages([
                    {
                      id: generateUniqueId('initial'),
                      content: "你好！我是你的AI学习助手。有什么可以帮助你的吗？",
                      role: "assistant",
                      timestamp: new Date(),
                    },
                  ])
                }}
              >
                <RotateCw className="w-4 h-4 mr-2" />
                新对话
              </Button>
            </div>
          </CardHeader>

          <ScrollArea className="flex-1 p-4">
            <div className="space-y-4">
              <AnimatePresence>
                {messages.map((message) => (
                  <motion.div
                    key={message.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className={cn(
                      "flex gap-3",
                      message.role === "user" ? "justify-end" : "justify-start"
                    )}
                  >
                    {message.role === "assistant" && (
                      <Avatar className="w-8 h-8">
                        <AvatarFallback className="bg-primary text-primary-foreground">
                          <Bot className="w-4 h-4" />
                        </AvatarFallback>
                      </Avatar>
                    )}

                    <div
                      className={cn(
                        "max-w-[70%] rounded-lg p-3",
                        message.role === "user"
                          ? "bg-primary text-primary-foreground"
                          : "bg-muted"
                      )}
                    >
                      {message.isTyping ? (
                        <div className="flex gap-1">
                          <span className="w-2 h-2 bg-current rounded-full animate-bounce" />
                          <span className="w-2 h-2 bg-current rounded-full animate-bounce delay-100" />
                          <span className="w-2 h-2 bg-current rounded-full animate-bounce delay-200" />
                        </div>
                      ) : (
                        <>
                          <p className="whitespace-pre-wrap">
                            {message.content}
                            {/* 为正在流式输出的消息添加光标 */}
                            {message.role === "assistant" && 
                             message.id === streamingMessageId && 
                             isLoading && 
                             <span className="inline-block w-1 h-5 bg-current animate-pulse ml-0.5" />
                            }
                          </p>
                          {message.role === "assistant" && (
                            <div className="flex items-center gap-2 mt-2 pt-2 border-t border-border/50">
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-6 w-6"
                                onClick={() => handleCopy(message.content)}
                              >
                                <Copy className="w-3 h-3" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-6 w-6"
                              >
                                <ThumbsUp className="w-3 h-3" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-6 w-6"
                              >
                                <ThumbsDown className="w-3 h-3" />
                              </Button>
                            </div>
                          )}
                        </>
                      )}
                    </div>

                    {message.role === "user" && (
                      <Avatar className="w-8 h-8">
                        <AvatarFallback>
                          <User className="w-4 h-4" />
                        </AvatarFallback>
                      </Avatar>
                    )}
                  </motion.div>
                ))}
              </AnimatePresence>
              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>

          <CardContent className="border-t p-4 space-y-4">
            {/* 快捷提示 */}
            <div className="flex gap-2 flex-wrap">
              {quickPrompts.map((prompt, index) => (
                <Button
                  key={index}
                  variant="outline"
                  size="sm"
                  onClick={() => handleQuickPrompt(prompt.prompt)}
                  disabled={isLoading}
                >
                  <prompt.icon className="w-3 h-3 mr-1" />
                  {prompt.label}
                </Button>
              ))}
            </div>

            {/* 输入区域 */}
            <div className="flex gap-2">
              <Textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="输入你的问题..."
                className="min-h-[60px] max-h-[120px] resize-none"
                disabled={isLoading}
              />
              <Button
                onClick={handleSend}
                disabled={!input.trim() || isLoading}
                size="icon"
                className="h-[60px] w-[60px]"
              >
                <Send className="w-5 h-5" />
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  )
}