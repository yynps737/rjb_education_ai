# 智能教育平台前端

基于 Next.js 14 + shadcn/ui + Framer Motion 构建的现代化教育平台前端。

## 技术栈

- **框架**: Next.js 14 (App Router)
- **UI组件**: shadcn/ui + Radix UI
- **样式**: Tailwind CSS
- **动画**: Framer Motion
- **状态管理**: Zustand
- **HTTP客户端**: Axios
- **表单验证**: React Hook Form + Zod

## 设计特色

1. **顶级交互设计**
   - 流畅的页面过渡动画
   - 玻璃态和渐变效果
   - 响应式设计，支持移动端

2. **AI聊天界面**
   - 实时打字效果
   - Markdown渲染
   - 代码高亮

3. **数据可视化**
   - 动态图表
   - 实时数据更新
   - 交互式热力图

## 快速开始

```bash
# 安装依赖
cd frontend
npm install

# 启动开发服务器
npm run dev
```

访问 http://localhost:3000

## 核心页面

- `/login` - 登录页面
- `/dashboard` - 仪表盘
- `/dashboard/chat` - AI智能问答
- `/dashboard/questions` - 题目生成
- `/dashboard/analytics` - 数据分析

## 测试账号

- 学生: student / student123
- 教师: teacher / teacher123
- 管理员: admin / admin123
