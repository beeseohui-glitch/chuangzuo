'use client';

import {
  StepIndicator,
  UsageQuota,
  AgentStatus,
  AIScoreRing,
  AIScoreBadge,
  ComplianceBadge,
  ComplianceSummary,
} from '@/components/shared';

export default function TestComponentsPage() {
  return (
    <div className="min-h-screen bg-background p-8">
      <h1 className="text-2xl font-bold mb-8">通用组件测试页</h1>

      <div className="space-y-10 max-w-3xl">
        {/* StepIndicator */}
        <Section title="StepIndicator - 创作流程步骤指示器">
          <Label>全部待定</Label>
          <StepIndicator
            steps={[
              { label: '素材检索', status: 'pending' },
              { label: '标题创作', status: 'pending' },
              { label: '正文创作', status: 'pending' },
              { label: '标签生成', status: 'pending' },
              { label: '合规检查', status: 'pending' },
              { label: '最终输出', status: 'pending' },
            ]}
          />

          <Label>进行中（步骤3）</Label>
          <StepIndicator
            steps={[
              { label: '素材检索', status: 'completed' },
              { label: '标题创作', status: 'completed' },
              { label: '正文创作', status: 'active' },
              { label: '标签生成', status: 'pending' },
              { label: '合规检查', status: 'pending' },
              { label: '最终输出', status: 'pending' },
            ]}
          />

          <Label>含错误状态</Label>
          <StepIndicator
            steps={[
              { label: '素材检索', status: 'completed' },
              { label: '标题创作', status: 'completed' },
              { label: '正文创作', status: 'error' },
              { label: '标签生成', status: 'pending' },
              { label: '合规检查', status: 'pending' },
              { label: '最终输出', status: 'pending' },
            ]}
          />

          <Label>全部完成</Label>
          <StepIndicator
            steps={[
              { label: '素材检索', status: 'completed' },
              { label: '标题创作', status: 'completed' },
              { label: '正文创作', status: 'completed' },
              { label: '标签生成', status: 'completed' },
              { label: '合规检查', status: 'completed' },
              { label: '最终输出', status: 'completed' },
            ]}
          />
        </Section>

        {/* UsageQuota */}
        <Section title="UsageQuota - 额度进度条">
          <Label>正常 (2/5)</Label>
          <div className="w-64">
            <UsageQuota used={2} total={5} label="本月创作额度" />
          </div>

          <Label>警告 (4/5)</Label>
          <div className="w-64">
            <UsageQuota used={4} total={5} label="本月创作额度" />
          </div>

          <Label>危险 (5/5)</Label>
          <div className="w-64">
            <UsageQuota used={5} total={5} label="本月创作额度" />
          </div>

          <Label>无标签</Label>
          <div className="w-64">
            <UsageQuota used={3} total={10} />
          </div>
        </Section>

        {/* AgentStatus */}
        <Section title="AgentStatus - Agent 执行状态指示器">
          <Label>等待中</Label>
          <AgentStatus status="idle" agentName="标题Agent" />

          <Label>执行中</Label>
          <AgentStatus status="running" agentName="正文Agent" label="正在生成内容..." />

          <Label>已完成</Label>
          <AgentStatus status="completed" agentName="合规Agent" />

          <Label>失败</Label>
          <AgentStatus status="failed" agentName="素材Agent" label="检索超时" />
        </Section>

        {/* AIScoreRing */}
        <Section title="AIScoreRing - AI 味评分环形图">
          <div className="flex items-center gap-8">
            <div className="text-center">
              <AIScoreRing score={92} />
              <Label>优秀 (92)</Label>
            </div>
            <div className="text-center">
              <AIScoreRing score={75} />
              <Label>良好 (75)</Label>
            </div>
            <div className="text-center">
              <AIScoreRing score={50} />
              <Label>一般 (50)</Label>
            </div>
            <div className="text-center">
              <AIScoreRing score={25} />
              <Label>较差 (25)</Label>
            </div>
          </div>

          <Label>不同尺寸</Label>
          <div className="flex items-center gap-8">
            <AIScoreRing score={85} size={48} strokeWidth={4} />
            <AIScoreRing score={85} size={80} />
            <AIScoreRing score={85} size={120} strokeWidth={8} />
          </div>

          <Label>AIScoreBadge 徽章</Label>
          <div className="flex gap-3">
            <AIScoreBadge score={90} />
            <AIScoreBadge score={70} />
            <AIScoreBadge score={40} />
          </div>
        </Section>

        {/* ComplianceBadge */}
        <Section title="ComplianceBadge - 合规状态徽章">
          <Label>状态徽章</Label>
          <div className="flex gap-3">
            <ComplianceBadge status="passed" />
            <ComplianceBadge status="needs_revision" />
            <ComplianceBadge status="failed" />
          </div>

          <Label>不显示图标</Label>
          <div className="flex gap-3">
            <ComplianceBadge status="passed" showIcon={false} />
            <ComplianceBadge status="needs_revision" showIcon={false} />
            <ComplianceBadge status="failed" showIcon={false} />
          </div>

          <Label>合规摘要</Label>
          <ComplianceSummary passed={3} needsRevision={1} failed={0} />
          <ComplianceSummary passed={0} needsRevision={2} failed={1} />
        </Section>
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-border bg-card p-6 space-y-4">
      <h2 className="text-lg font-semibold text-card-foreground border-b border-border pb-3">
        {title}
      </h2>
      <div className="space-y-4">{children}</div>
    </div>
  );
}

function Label({ children }: { children: React.ReactNode }) {
  return <p className="text-sm text-muted-foreground">{children}</p>;
}
