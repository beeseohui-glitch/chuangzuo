# 任务：前端从 Streamlit 迁移到 Next.js

## 背景
当前前端基于 Streamlit（Phase 3 原型），已完成核心流程验证。
现在需要迁移到 Next.js + shadcn/ui，构建正式产品前端。

## 技术栈
- Next.js 14（App Router）
- TypeScript
- shadcn/ui 组件库
- Tailwind CSS
- Zustand（全局状态）
- React Query（服务端数据）
- 后端 API 已有 FastAPI

## 迁移范围
1. 工作台（Dashboard）
2. 创作中心（核心流程，6步分步式）
3. 知识库管理
4. 数据看板
5. 账号设置
6. 登录/注册

## 约束
- 后端 FastAPI 接口不变，前端只对接已有 API
- 保留 Streamlit 版本作为内部工具，不删除
- 新项目放在 frontend/ 目录下
