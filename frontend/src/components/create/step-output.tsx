'use client';

import { useCreateStore } from '@/stores/create-store';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AIScoreRing } from '@/components/shared/ai-score-ring';
import { ComplianceBadge } from '@/components/shared/compliance-badge';
import {
  Copy, FileDown, RefreshCw, CheckCircle2, ArrowLeft,
} from 'lucide-react';
import { toast } from 'sonner';

export function StepOutput() {
  const {
    selectedTitles, customTitle, article, tags,
    aiScore, complianceReport, brand, product, reset, prevStep,
  } = useCreateStore();

  const finalTitle = customTitle || selectedTitles[0] || '';

  const handleCopy = () => {
    const text = `${finalTitle}\n\n${article}\n\n${tags.map((t) => `#${t}`).join(' ')}`;
    navigator.clipboard.writeText(text);
    toast.success('已复制到剪贴板');
  };

  const handleExportMarkdown = () => {
    const md = `# ${finalTitle}\n\n${article}\n\n---\n\n${tags.map((t) => `#${t}`).join(' ')}`;
    const blob = new Blob([md], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${product || '笔记'}.md`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('已导出 Markdown 文件');
  };

  const handleReset = () => {
    reset();
  };

  return (
    <div className="space-y-6">
      {/* 成功提示 */}
      <div className="flex flex-col items-center py-4">
        <CheckCircle2 className="h-16 w-16 text-green-500" />
        <h2 className="mt-4 text-xl font-bold">创作完成！</h2>
        <p className="mt-1 text-muted-foreground">
          {brand && `${brand} · `}{product} · 小红书笔记
        </p>
      </div>

      {/* 笔记包概览 */}
      <div className="grid grid-cols-2 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm text-muted-foreground">标题</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="font-medium">{finalTitle}</p>
            {selectedTitles.length > 1 && (
              <p className="mt-1 text-sm text-muted-foreground">
                备选: {selectedTitles[1]}
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm text-muted-foreground">质量指标</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <AIScoreRing score={aiScore} size={60} strokeWidth={5} showLabel={false} />
              <div className="space-y-1">
                <p className="text-sm">AI味评分: <span className="font-bold">{aiScore}</span></p>
                {complianceReport && (
                  <ComplianceBadge status={complianceReport.status} />
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="col-span-2">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm text-muted-foreground">正文预览</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm line-clamp-6 text-muted-foreground">{article}</p>
            <p className="mt-2 text-xs text-muted-foreground">{article.length} 字</p>
          </CardContent>
        </Card>

        <Card className="col-span-2">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm text-muted-foreground">标签</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {tags.map((tag) => (
                <Badge key={tag} variant="secondary">#{tag}</Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 操作按钮 */}
      <div className="flex items-center justify-between">
        <Button variant="outline" onClick={prevStep}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          返回修改
        </Button>
        <div className="flex gap-3">
          <Button variant="outline" onClick={handleCopy}>
            <Copy className="mr-2 h-4 w-4" />
            复制全文
          </Button>
          <Button variant="outline" onClick={handleExportMarkdown}>
            <FileDown className="mr-2 h-4 w-4" />
            导出 Markdown
          </Button>
          <Button onClick={handleReset}>
            <RefreshCw className="mr-2 h-4 w-4" />
            再创作一篇
          </Button>
        </div>
      </div>
    </div>
  );
}
