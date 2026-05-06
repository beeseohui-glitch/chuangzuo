# 智创笔记 - 前端

基于 Next.js 14 的 AI 内容创作平台前端。

## 技术栈

- **框架**: Next.js 14 (App Router)
- **语言**: TypeScript
- **UI 组件**: shadcn/ui
- **样式**: Tailwind CSS
- **状态管理**: Zustand
- **数据获取**: @tanstack/react-query
- **图标**: Lucide React

## 项目结构

```
src/
├── app/                    # Next.js App Router 页面
│   ├── login/             # 登录页
│   ├── dashboard/         # 工作台
│   ├── create/            # 创作中心
│   ├── knowledge/         # 知识库管理
│   ├── analytics/         # 数据看板
│   └── settings/          # 设置
├── components/
│   ├── ui/                # shadcn/ui 组件
│   ├── layout/            # 布局组件（侧边栏、导航）
│   └── providers.tsx      # 全局 Providers
├── lib/
│   ├── api.ts             # API 客户端
│   ├── auth.ts            # 认证工具
│   └── utils.ts           # 工具函数
├── stores/                # Zustand stores
│   ├── auth-store.ts      # 认证状态
│   └── sidebar-store.ts   # 侧边栏状态
└── types/
    └── index.ts           # TypeScript 类型定义
```

## 快速开始

### 安装依赖

```bash
npm install
```

### 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:3000

### 构建生产版本

```bash
npm run build
npm start
```

## 环境变量

创建 `.env.local` 文件：

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 主题

默认使用深色主题，accent 颜色为蓝色。

## 认证

- 登录后 token 存储在 localStorage
- 自动在 API 请求中注入 token
- 401 错误时自动跳转登录页
