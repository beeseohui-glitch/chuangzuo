# 迭代式开发规则

## 核心原则
小步快跑，每次只做一件事，做完验证，再做下一步。

## 工作流程
1. 明确当前要完成的单个任务
2. 完成这个任务的代码
3. 运行验证（测试/手动测试）
4. 验证通过 → 继续下一个任务
5. 验证不通过 → 修复 → 重新验证

## 禁止事项
- 禁止一次性生成多个文件（除非它们是紧密耦合的数据模型）
- 禁止跳过验证步骤
- 禁止在上一个文件还没验证通过时就开始写下一个文件

## 文件开发顺序
对于每个模块，按以下顺序开发：
1. 数据模型（models/）→ 验证序列化
2. Prompt 文件（prompts/）→ 人工审核
3. 工具代码（tools/）→ 运行测试
4. Agent 代码（agents/）→ 运行测试
5. Task 代码（tasks/）→ 运行测试
6. Crew 代码（crews/）→ 运行测试
7. Flow 代码（flows/）→ 运行测试

## 验证方式
- 代码文件：运行 pytest
- Prompt 文件：输出内容让人工审核
- 配置文件：运行脚本验证连接

## 示例对话
用户："开发合规Agent"
正确的做法：
  1. 先写 models/compliance_report.py → 验证
  2. 再写 prompts/compliance_agent.md → 人工审核
  3. 再写 tools/compliance_tools.py → 测试
  4. 再写 agents/compliance_agent.py → 测试
  5. 最后写 tests/test_compliance_agent.py → 运行

错误的做法：
  一次性输出所有5个文件
