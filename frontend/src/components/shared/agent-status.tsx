'use client';

import { cn } from '@/lib/utils';
import { Loader2, CheckCircle2, XCircle, Clock } from 'lucide-react';

export type AgentStatusType = 'idle' | 'running' | 'completed' | 'failed';

interface AgentStatusProps {
  status: AgentStatusType;
  label?: string;
  agentName?: string;
  className?: string;
}

const statusConfig: Record<AgentStatusType, { icon: typeof Loader2; label: string; className: string }> = {
  idle: {
    icon: Clock,
    label: '等待中',
    className: 'text-muted-foreground',
  },
  running: {
    icon: Loader2,
    label: '执行中',
    className: 'text-blue-500',
  },
  completed: {
    icon: CheckCircle2,
    label: '已完成',
    className: 'text-green-500',
  },
  failed: {
    icon: XCircle,
    label: '失败',
    className: 'text-destructive',
  },
};

export function AgentStatus({ status, label, agentName, className }: AgentStatusProps) {
  const config = statusConfig[status];
  const Icon = config.icon;

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <Icon
        className={cn(
          'h-4 w-4',
          config.className,
          status === 'running' && 'animate-spin'
        )}
      />
      {agentName && (
        <span className="text-sm font-medium">{agentName}</span>
      )}
      <span className={cn('text-sm', config.className)}>
        {label || config.label}
      </span>
    </div>
  );
}

export function AgentStatusCompact({
  status,
  className,
}: {
  status: AgentStatusType;
  className?: string;
}) {
  const config = statusConfig[status];
  const Icon = config.icon;

  return (
    <Icon
      className={cn(
        'h-4 w-4',
        config.className,
        status === 'running' && 'animate-spin',
        className
      )}
    />
  );
}
