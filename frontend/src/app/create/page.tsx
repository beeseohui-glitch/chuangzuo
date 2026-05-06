'use client';

import { AppLayout } from '@/components/layout/app-layout';
import { useCreateStore } from '@/stores/create-store';
import { PreviewPanel } from '@/components/create/preview-panel';
import { StepInput } from '@/components/create/step-input';
import { StepMaterial } from '@/components/create/step-material';
import { StepTitle } from '@/components/create/step-title';
import { StepArticle } from '@/components/create/step-article';
import { StepTags } from '@/components/create/step-tags';
import { StepOutput } from '@/components/create/step-output';

const STEP_COMPONENTS: Record<string, React.ComponentType> = {
  input: StepInput,
  material: StepMaterial,
  title: StepTitle,
  article: StepArticle,
  tags: StepTags,
  output: StepOutput,
};

export default function CreatePage() {
  const { currentStep, steps } = useCreateStore();

  const StepComponent = STEP_COMPONENTS[currentStep] || StepInput;

  return (
    <AppLayout>
      <div className="flex h-[calc(100vh-7rem)] gap-6">
        {/* 左侧：步骤指示器 */}
        <div className="w-48 shrink-0">
          <div className="sticky top-6">
            <h2 className="text-lg font-bold mb-4">创作流程</h2>
            <StepIndicatorVertical steps={steps} />
          </div>
        </div>

        {/* 中间：主操作区 */}
        <div className="flex-1 overflow-y-auto pr-2">
          <div className="max-w-2xl">
            <StepComponent />
          </div>
        </div>

        {/* 右侧：实时预览 */}
        <div className="w-80 shrink-0 border border-border rounded-lg bg-background overflow-hidden">
          <PreviewPanel />
        </div>
      </div>
    </AppLayout>
  );
}

function StepIndicatorVertical({
  steps,
}: {
  steps: Array<{ label: string; status: 'pending' | 'active' | 'completed' | 'error' }>;
}) {
  return (
    <div className="space-y-1">
      {steps.map((step, index) => {
        const isActive = step.status === 'active';
        const isCompleted = step.status === 'completed';
        const isError = step.status === 'error';

        return (
          <div key={step.label} className="flex items-start gap-3">
            {/* 连接线和圆点 */}
            <div className="flex flex-col items-center">
              <div
                className={
                  'flex h-8 w-8 items-center justify-center rounded-full text-xs font-medium transition-colors ' +
                  (isCompleted
                    ? 'bg-green-500 text-white'
                    : isActive
                      ? 'bg-primary text-primary-foreground'
                      : isError
                        ? 'bg-destructive text-destructive-foreground'
                        : 'bg-muted text-muted-foreground')
                }
              >
                {isCompleted ? '✓' : index + 1}
              </div>
              {index < steps.length - 1 && (
                <div
                  className={
                    'w-0.5 h-6 mt-1 ' +
                    (isCompleted ? 'bg-green-500' : 'bg-muted')
                  }
                />
              )}
            </div>

            {/* 标签 */}
            <div className="pt-1.5">
              <span
                className={
                  'text-sm ' +
                  (isActive
                    ? 'font-medium text-foreground'
                    : isCompleted
                      ? 'text-muted-foreground'
                      : isError
                        ? 'text-destructive'
                        : 'text-muted-foreground')
                }
              >
                {step.label}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
