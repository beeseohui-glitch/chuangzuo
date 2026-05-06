# Content Agent - 项目上下文

## 项目概述
多平台 AI 内容创作 Agent 系统，基于 CrewAI 三层架构（调度层→执行层→能力层）。

## 技术栈
- Agent框架：CrewAI + CrewAI Flows
- LLM：MiniMax-M2.7（OpenAI兼容接口）
- Embedding：bge-large-zh-v1.5（本地部署，1024维）
- 知识库：Obsidian + pgvector
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

**Step 2 已完成：数据模型开发**
- [x] MaterialPack 模型（含 BrandInfo, ProductInfo, PersonaInfo, SceneInfo, ComplianceRules）
- [x] NoteOutput 模型（含 TitleOption, TitleOutput, Paragraph）
- [x] ComplianceReport 模型（含 ComplianceIssue, ComplianceStatus, ComplianceSeverity）
- [x] ValidationResult 模型（含 MaterialPackValidation, TitleValidation, ArticleValidation）
- [x] 模型序列化验证通过

**Step 3 已完成：配置文件开发**
- [x] llm_config.py - LLM配置（含MiniMax/DeepSeek/Qwen降级方案）
- [x] agent_config.py - Agent/Crew/Flow配置
- [x] platform_config.py - 小红书/公众号/抖音平台配置
- [x] vector_config.py - pgvector索引配置（IVFFlat/HNSW）
- [x] config/__init__.py - 模块导出

**Step 4 已完成：Prompt文件开发**
- [x] prompts/orchestrator.md - 统一调度Agent Prompt
- [x] prompts/material_search.md - 素材检索Prompt
- [x] prompts/title_agent.md - 标题Agent Prompt（8大策略）
- [x] prompts/article_agent.md - 正文Agent Prompt（去AI味策略）
- [x] prompts/tag_agent.md - 标签Agent Prompt（分层策略）
- [x] prompts/compliance_agent.md - 合规Agent Prompt（P0/P1/P2分级）

**Step 5 已完成：工具开发**
- [x] embedding_tools.py - LocalEmbeddingTool + EmbeddingCache
- [x] vector_tools.py - VectorStoreTool（pgvector CRUD）
- [x] llm_tools.py - LLMCallTool + LLMResponseParser
- [x] compliance_tools.py - ComplianceCheckTool + ProhibitedWordDetector
- [x] cos_tools.py - COSUploadTool/COSDownloadTool/COSDeleteTool
- [x] obsidian_tools.py - ObsidianReaderTool/SearchTool/LinkTrackerTool
- [x] tools/__init__.py - 模块导出

**Step 6 已完成：校验层开发**
- [x] result_validator.py - ResultValidator（素材包/标题/正文校验）
- [x] ai_flavor_scorer.py - AIFlavorScorer（5维度AI味评分）
- [x] validators/__init__.py - 模块导出

**Step 7 已完成：Agent定义开发**
- [x] agents/title_agent.py - TitleAgent（标题创作）
- [x] agents/article_agent.py - ArticleAgent（正文创作 + AI味评分）
- [x] agents/tag_agent.py - TagAgent（标签生成）
- [x] agents/compliance_agent.py - ComplianceAgent（合规检查）
- [x] agents/material_agent.py - MaterialAgent（素材检索）
- [x] agents/__init__.py - 模块导出

**Step 8 已完成：Task定义开发**
- [x] tasks/title_task.py - 标题生成/校验Task
- [x] tasks/article_task.py - 正文生成/校验Task
- [x] tasks/compliance_task.py - 合规检查/修复Task
- [x] tasks/material_task.py - 素材检索/校验Task
- [x] tasks/tag_task.py - 标签生成Task
- [x] tasks/__init__.py - 模块导出

**Step 9 已完成：Crew定义开发**
- [x] crews/xiaohongshu_crew.py - XiaohongshuCrew（标题/正文/标签/合规串联）
- [x] crews/shared_crew.py - SharedCrew（素材检索/合规检查）
- [x] crews/__init__.py - 模块导出

**Step 10 已完成：Flow工作流开发**
- [x] flows/xiaohongshu_flow.py - XiaohongshuFlow（素材→标题→正文→标签→合规）
- [x] flows/main_flow.py - MainFlow（统一调度 + 路由）
- [x] flows/__init__.py - 模块导出

**Step 11 已完成：统一调度模块开发**
- [x] orchestrator/agent.py - OrchestratorAgent（意图识别 + 路由输出）
- [x] orchestrator/router.py - Router（平台→Flow路由映射）
- [x] orchestrator/__init__.py - 模块导出

**Step 12 已完成：API接口开发**
- [x] api/main.py - FastAPI接口（创建笔记/健康检查）
- [x] api/__init__.py - 模块导出

**Step 13 已完成：同步服务开发**
- [x] sync/file_watcher.py - FileWatcher（Obsidian文件监听）
- [x] sync/vectorizer.py - Vectorizer（Markdown向量化入库）
- [x] sync/__init__.py - 模块导出

**Step 14 已完成：监控模块开发**
- [x] monitoring/metrics.py - MetricsCollector（Prometheus指标采集）
- [x] monitoring/alerts.py - AlertManager（告警规则管理）
- [x] monitoring/__init__.py - 模块导出

**Step 15 已完成：测试模块开发**
- [x] tests/test_orchestrator/test_agent.py - OrchestratorAgent/Router测试
- [x] tests/test_validators/test_validators.py - AIFlavorScorer/ResultValidator测试
- [x] tests/test_models/test_models.py - MaterialPack/NoteOutput/ComplianceReport测试
- [x] tests/test_sync/test_sync.py - Vectorizer/FileWatcher测试
- [x] tests/test_monitoring/test_monitoring.py - MetricsCollector/AlertManager测试
- [x] tests/test_api/test_api.py - API接口测试

**Step 16 已完成：Docker配置**
- [x] Dockerfile - 基础镜像（含Streamlit）
- [x] Dockerfile.prod - 生产镜像（含Gunicorn+Uvicorn）
- [x] Dockerfile.embedding - Embedding服务镜像
- [x] docker-compose.yml - 开发环境配置（含app/postgres/redis）
- [x] docker-compose.prod.yml - 生产环境配置（含Prometheus/Grafana）
- [x] init.sql - PostgreSQL初始化脚本（含pgvector/RLS/索引）
- [x] prometheus.yml - Prometheus配置
- [x] alert_rules.yml - 告警规则

**Step 17 已完成：完整测试套件**
- [x] tests/test_agents/test_agents.py - TitleAgent/ArticleAgent/TagAgent/ComplianceAgent/MaterialAgent测试
- [x] tests/test_tools/test_tools.py - LLMCallTool/ComplianceCheckTool/EmbeddingTool/VectorStoreTool/ObsidianTools/COSTools测试
- [x] tests/test_flows/test_flows.py - XiaohongshuFlow/MainFlow测试
- [x] tests/test_validators/test_validators.py - AIFlavorScorer/ResultValidator测试
- [x] tests/test_models/test_models.py - MaterialPack/NoteOutput/ComplianceReport测试
- [x] tests/test_sync/test_sync.py - Vectorizer/FileWatcher测试
- [x] tests/test_monitoring/test_monitoring.py - MetricsCollector/AlertManager测试
- [x] tests/test_api/test_api.py - API接口测试
- [x] tests/test_orchestrator/test_agent.py - OrchestratorAgent/Router测试

**Step 18 已完成：选题Agent + 知识库Agent**
- [x] models/topic.py - TopicIdea/TopicCategory/TopicSource/TopicListOutput模型
- [x] agents/topic_agent.py - TopicAgent（选题生成）
- [x] prompts/topic_agent.md - 选题Agent Prompt
- [x] config/agent_config.py - 添加TOPIC_AGENT配置

**Step 19 已完成：知识库数据模型**
- [x] models/knowledge_base.py - KnowledgeEntry/KBMetadata/SearchResult/KnowledgeBaseStats模型

**Step 20 已完成：知识库Agent开发**
- [x] agents/kb_agent.py - KnowledgeBaseAgent（知识检索）
- [x] prompts/kb_agent.md - 知识库Agent Prompt

**Step 21 已完成：Obsidian同步服务完善**
- [x] sync/obsidian_client.py - ObsidianClient（笔记读写/搜索/标签提取）
- [x] sync/knowledge_loader.py - KnowledgeLoader（批量导入Markdown）
- [x] sync/vectorizer.py - 修复并完善Vectorizer（之前为空文件）
- [x] sync/__init__.py - 更新模块导出

**Step 22 已完成：同步服务测试**
- [x] tests/test_sync/test_obsidian_client.py - ObsidianClient测试（9个测试用例）
- [x] tests/test_sync/test_knowledge_loader.py - KnowledgeLoader测试（10个测试用例）
- [x] 18个测试全部通过

**Step 23 已完成：行业知识库数据**
- [x] kb/health_product/01_liver_protection.md - 护肝片知识（2条）
- [x] kb/health_product/02_sleep_health.md - 睡眠健康知识
- [x] kb/ai_industry/01_crewai_framework.md - CrewAI框架知识
- [x] scripts/import_kb.py - 知识库导入脚本

**Step 24 已完成：Streamlit知识管理界面**
- [x] app_kb.py - Streamlit知识管理页面（首页/导入/设置）

**Step 25 已完成：Phase 3 端到端验证**
- [x] tests/phase3_e2e_test.py - 选题→素材检索→创作→输出完整流程测试
- [x] 6/6步骤全部通过，耗时20秒

**Step 26 已完成：数据分析模型**
- [x] models/analytics.py - AnalyticsData/ContentStats/PerformanceMetrics/ContentPerformance/TrendData模型

**Step 27 已完成：数据分析Agent开发**
- [x] agents/analytics_agent.py - AnalyticsAgent（数据统计分析/内容表现分析/趋势识别/优化建议）
- [x] prompts/analytics_agent.md - 数据分析Agent Prompt

**Step 28 已完成：运营Agent开发**
- [x] agents/operation_agent.py - OperationAgent（发布计划/内容矩阵/运营策略）
- [x] prompts/operation_agent.md - 运营Agent Prompt

**Step 29 已完成：数据看板界面**
- [x] app_analytics.py - Streamlit数据看板（概览/表现/计划/建议/分析5个标签页）

**Step 30 已完成：Prompt优化工具**
- [x] tools/prompt_optimizer.py - PromptOptimizer（remove_ai_flavor/analyze_ai_score/suggest_improvements）

**Step 31 已完成：Phase 4 端到端验证**
- [x] tests/phase4_e2e_test.py - 数据分析+运营+看板完整流程测试
- [x] 6/6步骤全部通过，耗时16秒

**Step 32 已完成：多平台内容模型**
- [x] models/platform_content.py - WechatArticle/PublicAccountContent/DouyinScript/DouyinVideo/DouyinContent/MultiPlatformContent模型

**Step 33 已完成：公众号创作Agent**
- [x] agents/wechat_article_agent.py - WechatArticleAgent（公众号深度文章）
- [x] prompts/wechat_article_agent.md - 公众号Agent Prompt

**Step 34 已完成：抖音创作Agent**
- [x] agents/douyin_script_agent.py - DouyinScriptAgent（短视频脚本）
- [x] prompts/douyin_script_agent.md - 抖音Agent Prompt

**Step 35 已完成：跨平台工具**
- [x] tools/content_adapter.py - ContentAdapter（内容跨平台适配）
- [x] tools/multi_platform_publisher.py - MultiPlatformPublisher（一键分发）

**Step 36 已完成：Phase 5 端到端验证**
- [x] tests/phase5_e2e_test.py - 多平台创作+分发完整流程测试
- [x] 6/6步骤全部通过，耗时102秒

**Step 37 已完成：Phase 0 技术预研脚本**
- [x] scripts/check_env.py - 环境检查脚本（环境变量/Python包/项目结构/关键文件）
- [x] scripts/test_minimax.py - MiniMax API连接和生成质量测试

**Step 38 已完成：Phase 0 端到端验证**
- [x] tests/phase0_e2e_test.py - 技术预研完整验证
- [x] 6/6步骤全部通过，耗时28秒

### Phase 0：技术预研（第1-2周）
- [x] MiniMax-M2.7 API连接验证（连接成功）
- [x] MiniMax-M2.7 生成质量评估（生成3个标题正常）
- [x] CrewAI 框架原型验证（Agent创建正常）
- [x] 项目结构验证（全部目录和关键文件存在）
- [x] 模型导入验证（所有Models/Agents/Tools正常导入）
- [x] 环境变量检查（MINIMAX_API_KEY等已配置）

**Phase 0 端到端验证结果：**
- 输入：环境检查 + API连接 + 生成质量测试
- 输出：6/6步骤全部通过
- 耗时：约28秒
- 完成功能：
  - MiniMax-M2.7 API：连接成功，生成质量正常
  - CrewAI框架：Agent创建正常
  - 项目结构：全部目录存在，关键文件完整
  - Models/Tools：全部可正常导入
  - 缺失项：crewai_flows包（未影响核心功能）

### Phase 1：基础设施 + 单Agent验证（第3-4周）
- [x] Docker Compose 环境搭建
- [x] PostgreSQL + pgvector 初始化
- [x] Redis 启动
- [x] MiniMax-M2.7 API 对接验证（需要真实API Key）
- [x] 单个标题Agent跑通
- [x] 单个正文Agent跑通
- [x] Obsidian Vault 模板创建
- [x] pgvector 写入和检索工具
- [x] 本地Embedding服务封装
- [x] COS 读写验证
- [x] ResultValidator 中间结果校验模块
- [x] Phase 1 端到端验证通过（Models/Validators/Flows/Crews/Agents）

**Phase 1 端到端验证结果：**
- 输入：护肝片创作需求
- 输出：完整笔记包（标题+正文363字+标签9个）
- AI味评分：64/100
- 合规检查：通过
- 注意：需要真实 MINIMAX_API_KEY 才能调用 LLM

### Phase 2：核心创作流程（第5-7周）
- [x] 素材检索Agent + Tool
- [x] 标题Agent + Tool
- [x] 正文Agent + Tool
- [x] 标签Agent
- [x] 合规Agent + Tool
- [x] 小红书创作Flow
- [x] 质量门禁
- [x] 合规校验循环
- [x] ResultValidator 全链路集成
- [x] Prompt文件

**Phase 2 端到端验证结果：**
- 输入：护肝片小红书笔记创作需求
- 输出：完整笔记包（标题5个+正文400-500字+标签7-8个+合规报告）
- AI味评分：70-85/100
- 合规检查：通过
- 验证方式：7步流程全部通过（路由→素材→标题→正文→标签→合规→输出）
- 耗时：约150-250秒（取决于LLM响应速度）
- 修复问题：
  - tag_agent.py 缺少 `import os`
  - compliance_agent.py 缺少 `import os`
  - article_agent.py 解析数据缺少 `title` 字段时添加默认值

### Phase 3：知识库 + 前端 + 选题（第8-10周）
- [x] 选题Agent（TopicAgent + topic_agent.md + TopicIdea/TopicListOutput模型）
- [x] 知识库管理Agent（KnowledgeBaseAgent + kb_agent.md + KnowledgeEntry/SearchResult模型）
- [x] Obsidian 同步服务（ObsidianClient + KnowledgeLoader）
- [x] Web端知识管理界面（app_kb.py - Streamlit知识库页面）
- [x] 行业知识库灌入（kb/health_product/ + kb/ai_industry/ + import_kb.py）
- [x] Streamlit 前端（app.py + app_kb.py）
- [x] 测试套件（test_obsidian_client.py + test_knowledge_loader.py + phase3_e2e_test.py）

**Phase 3 端到端验证结果：**
- 输入：TopicAgent + KnowledgeBaseAgent + KnowledgeLoader
- 输出：选题生成 + 知识检索 + 知识导入
- 验证方式：6步流程全部通过
- 耗时：约20秒
- 完成功能：
  - TopicAgent：选题生成（基于TopicIdea/TopicListOutput模型）
  - KnowledgeBaseAgent：知识检索（基于KnowledgeEntry/SearchResult模型）
  - ObsidianClient：笔记库读写/搜索/标签提取
  - KnowledgeLoader：批量导入Markdown知识
  - app_kb.py：Streamlit知识管理界面
  - kb/目录：健康产品(2条) + AI行业(1条) 知识库

### Phase 4：数据 + 优化（第11-13周）
- [x] 数据分析Agent（AnalyticsAgent + analytics_agent.md + AnalyticsData/ContentStats/PerformanceMetrics模型）
- [x] 运营Agent（OperationAgent + operation_agent.md + PublishScheduleItem/OperationOutput模型）
- [x] 数据看板（app_analytics.py - Streamlit数据看板页面）
- [x] Prompt优化工具（PromptOptimizer + 去AI味/AI评分/建议生成）
- [x] 测试套件（phase4_e2e_test.py）

**Phase 4 端到端验证结果：**
- 输入：AnalyticsAgent + OperationAgent + PromptOptimizer
- 输出：数据分析报告 + 发布计划 + Prompt优化
- 验证方式：6步流程全部通过
- 耗时：约16秒
- 完成功能：
  - AnalyticsAgent：数据统计分析、内容表现分析、趋势识别、优化建议生成
  - OperationAgent：发布计划制定、内容矩阵规划、运营策略优化
  - PromptOptimizer：remove_ai_flavor、analyze_ai_score、suggest_improvements
  - app_analytics.py：概览/表现/计划/建议/分析 5个标签页

### Phase 5：多平台扩展（第14-18周）
- [x] 公众号创作工作流（WechatArticleAgent + WechatArticle/PublicAccountContent模型）
- [x] 抖音创作工作流（DouyinScriptAgent + DouyinScript/DouyinVideo/DouyinContent模型）
- [x] 跨平台一键分发（MultiPlatformPublisher + ContentAdapter）
- [x] 多平台数据模型（WechatArticle/DouyinScript/MultiPlatformContent）
- [x] 测试套件（phase5_e2e_test.py）

**Phase 5 端到端验证结果：**
- 输入：WechatArticleAgent + DouyinScriptAgent + ContentAdapter + MultiPlatformPublisher
- 输出：公众号文章 + 抖音脚本 + 跨平台分发
- 验证方式：6步流程全部通过
- 耗时：约102秒
- 完成功能：
  - WechatArticleAgent：公众号深度文章创作（HTML格式，含安全声明）
  - DouyinScriptAgent：抖音短视频脚本（60秒，时间戳标注，画面建议）
  - ContentAdapter：内容跨平台适配
  - MultiPlatformPublisher：一键分发到小红书/公众号/抖音（mock模式）

## 禁忌
- 不使用LangChain，只用CrewAI
- 不在代码中硬编码API Key
- 不跳过测试
- 不一次性生成整个项目，按文件逐个开发
