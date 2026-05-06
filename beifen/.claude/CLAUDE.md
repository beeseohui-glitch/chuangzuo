# Content Agent - 项目上下文

## 项目概述
多平台 AI 内容创作 Agent 系统，基于 CrewAI 三层架构。

## 技术栈
- Agent框架：CrewAI + CrewAI Flows
- LLM：MiniMax-M2.7（OpenAI兼容接口，base_url: https://api.minimax.chat/v1）
- 知识库：Obsidian（企业侧）+ pgvector（向量检索）
- 数据库：PostgreSQL 16 + pgvector 扩展
- 缓存：Redis 7
- 对象存储：腾讯云 COS
- 前端：Streamlit（原型阶段）
- 部署：Docker + Docker Compose

## 架构原则
1. 三层Agent架构：调度层→执行层→能力层
2. 每个Agent必须有独立的Prompt文件（prompts/目录下.md文件）
3. 每个Agent的输出必须用Pydantic模型定义
4. 符合Prompt/Context/Harness标准

## 代码规范
- Python 3.11+
- 类型注解必须
- 每个Tool继承crewai.tools.BaseTool
- 敏感信息通过.env管理，不硬编码

## 目录结构规范
- agents/     → Agent定义
- tasks/      → Task定义
- crews/      → Crew定义
- flows/      → Flow工作流
- tools/      → 自定义工具
- models/     → Pydantic数据模型
- prompts/    → Prompt文件（.md格式）
- config/     → 配置文件
- tests/      → 测试文件
- sync/       → Obsidian同步服务

## 当前进度
- [ ] Phase 1：基础设施 + 单Agent验证
- [ ] Phase 2：核心创作流程
- [ ] Phase 3：选题 + 知识库 + 前端
- [ ] Phase 4：数据 + 优化
- [ ] Phase 5：多平台扩展

## 禁忌
- 不使用LangChain，只用CrewAI
- 不在代码中硬编码API Key
- 不跳过测试
- 不一次性生成整个项目，按文件逐个开发
