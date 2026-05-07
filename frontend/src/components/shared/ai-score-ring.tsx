'use client';

import { cn } from '@/lib/utils';
import { getScoreColor, getScoreBadgeColor, getScoreLabel } from '@/lib/score-utils';

interface AIScoreRingProps {
  score: number;
  size?: number;
  strokeWidth?: number;
  className?: string;
  showLabel?: boolean;
}

export function AIScoreRing({
  score,
  size = 80,
  strokeWidth = 6,
  className,
  showLabel = true,
}: AIScoreRingProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className={cn('relative inline-flex items-center justify-center', className)}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          className="text-muted"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className={cn('transition-all duration-500', getScoreColor(score))}
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className={cn('text-lg font-bold', getScoreColor(score))}>
          {score}
        </span>
        {showLabel && (
          <span className="text-xs text-muted-foreground">
            {getScoreLabel(score)}
          </span>
        )}
      </div>
    </div>
  );
}

export function AIScoreBadge({
  score,
  className,
}: {
  score: number;
  className?: string;
}) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium',
        getScoreBadgeColor(score),
        className
      )}
    >
      AI味: {score}分
    </span>
  );
}
