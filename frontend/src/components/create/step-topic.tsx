'use client';

import { useCreateStore, TopicOption } from '@/stores/create-store';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { Lightbulb, Check } from 'lucide-react';

export function StepTopic() {
  const {
    topicOptions, selectedTopic,
    selectTopic, nextStep, prevStep, isProcessing,
  } = useCreateStore();

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium flex items-center gap-2">
          <Lightbulb className="h-5 w-5 text-yellow-500" />
          选题推荐
        </h3>
        <p className="mt-1 text-sm text-muted-foreground">
          基于您的产品和场景，AI 为您推荐以下选题方向
        </p>
      </div>

      {isProcessing ? (
        <div className="flex items-center justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <span className="ml-3 text-muted-foreground">正在生成选题...</span>
        </div>
      ) : topicOptions.length === 0 ? (
        <div className="rounded-lg border border-dashed p-8 text-center text-muted-foreground">
          暂无选题推荐，请返回上一步调整需求
        </div>
      ) : (
        <div className="space-y-3">
          {topicOptions.map((topic, index) => (
            <TopicCard
              key={index}
              topic={topic}
              isSelected={selectedTopic === topic.title}
              onSelect={() => selectTopic(topic.title)}
            />
          ))}
        </div>
      )}

      <div className="flex gap-3">
        <Button variant="outline" onClick={prevStep} className="flex-1">
          上一步
        </Button>
        <Button
          onClick={nextStep}
          disabled={!selectedTopic}
          className="flex-1"
        >
          下一步：确认素材
        </Button>
      </div>
    </div>
  );
}

function TopicCard({
  topic,
  isSelected,
  onSelect,
}: {
  topic: TopicOption;
  isSelected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      onClick={onSelect}
      className={cn(
        'w-full rounded-lg border-2 p-4 text-left transition-all',
        isSelected
          ? 'border-primary bg-primary/5'
          : 'border-border hover:border-primary/50'
      )}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="font-medium">{topic.title}</p>
          <p className="mt-1 text-sm text-muted-foreground">{topic.angle}</p>
          {topic.keywords.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {topic.keywords.map((kw, i) => (
                <span
                  key={i}
                  className="rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground"
                >
                  {kw}
                </span>
              ))}
            </div>
          )}
        </div>
        <div className="ml-3 flex items-center gap-2">
          <span className="text-sm font-medium text-primary">{topic.score}分</span>
          {isSelected && (
            <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary">
              <Check className="h-4 w-4 text-primary-foreground" />
            </div>
          )}
        </div>
      </div>
    </button>
  );
}
