'use client';

import { cn } from '@/lib/utils';
import { Check, Loader2 } from 'lucide-react';

export type StepStatus = 'pending' | 'active' | 'completed' | 'error';

export interface StepItem {
  label: string;
  status: StepStatus;
}

interface StepIndicatorProps {
  steps: StepItem[];
  className?: string;
}

export function StepIndicator({ steps, className }: StepIndicatorProps) {
  return (
    <div className={cn('flex items-center gap-2', className)}>
      {steps.map((step, index) => {
        const isLast = index === steps.length - 1;

        return (
          <div key={step.label} className="flex items-center gap-2">
            <StepDot status={step.status} label={step.label} index={index + 1} />
            {!isLast && <StepConnector status={step.status} />}
          </div>
        );
      })}
    </div>
  );
}

function StepDot({
  status,
  label,
  index,
}: {
  status: StepStatus;
  label: string;
  index: number;
}) {
  return (
    <div className="flex items-center gap-2">
      <div
        className={cn(
          'flex h-8 w-8 items-center justify-center rounded-full text-xs font-medium transition-colors',
          status === 'completed' && 'bg-green-500 text-white',
          status === 'active' && 'bg-primary text-primary-foreground',
          status === 'pending' && 'bg-muted text-muted-foreground',
          status === 'error' && 'bg-destructive text-destructive-foreground'
        )}
      >
        {status === 'completed' ? (
          <Check className="h-4 w-4" />
        ) : status === 'active' ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          index
        )}
      </div>
      <span
        className={cn(
          'text-sm whitespace-nowrap',
          status === 'active' && 'font-medium text-foreground',
          status === 'completed' && 'text-muted-foreground',
          status === 'pending' && 'text-muted-foreground',
          status === 'error' && 'text-destructive'
        )}
      >
        {label}
      </span>
    </div>
  );
}

function StepConnector({ status }: { status: StepStatus }) {
  return (
    <div
      className={cn(
        'h-px w-8',
        status === 'completed' ? 'bg-green-500' : 'bg-muted'
      )}
    />
  );
}
