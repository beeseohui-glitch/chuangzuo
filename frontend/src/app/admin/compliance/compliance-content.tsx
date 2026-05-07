'use client';

import { useState } from 'react';
import { useAdminComplianceWords, useCreateAdminComplianceWord, useDeleteAdminComplianceWord } from '@/hooks/use-admin';
import { useToast } from '@/components/ui/toast';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter, DialogClose } from '@/components/ui/dialog';
import {
  Plus,
  Search,
  Trash2,
  ShieldAlert,
  ShieldCheck,
  Upload,
} from 'lucide-react';

const LEVELS = [
  { id: 'all', name: '全部', icon: ShieldCheck },
  { id: 'P0', name: 'P0 违禁词', icon: ShieldAlert },
  { id: 'P1', name: 'P1 敏感词', icon: ShieldCheck },
];

export default function ComplianceContent() {
  const { data: items, isLoading } = useAdminComplianceWords();
  const createMutation = useCreateAdminComplianceWord();
  const deleteMutation = useDeleteAdminComplianceWord();
  const { toast } = useToast();

  const [selectedLevel, setSelectedLevel] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({ word: '', level: 'P0', category: '', description: '' });
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [showImportDialog, setShowImportDialog] = useState(false);

  const filteredItems = (items || []).filter((item) => {
    if (selectedLevel !== 'all' && item.level !== selectedLevel) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return item.word.toLowerCase().includes(q) || item.category.toLowerCase().includes(q);
    }
    return true;
  });

  function handleCreate() {
    if (!formData.word) return;
    createMutation.mutate({
      word: formData.word,
      level: formData.level,
      category: formData.category || undefined,
      description: formData.description || undefined,
    }, {
      onSuccess: () => {
        toast('success', '合规词汇添加成功');
        setFormData({ word: '', level: 'P0', category: '', description: '' });
        setShowForm(false);
      },
      onError: () => {
        toast('error', '添加失败，请重试');
      },
    });
  }

  function handleDelete() {
    if (!deleteId) return;
    deleteMutation.mutate(deleteId, {
      onSuccess: () => {
        toast('success', '合规词汇已删除');
        setDeleteId(null);
      },
      onError: () => {
        toast('error', '删除失败，请重试');
      },
    });
  }

  const p0Count = (items || []).filter((w) => w.level === 'P0').length;
  const p1Count = (items || []).filter((w) => w.level === 'P1').length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold">合规词库</h1>
          <p className="text-muted-foreground">管理违禁词库(P0)和敏感词库(P1)</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" className="text-amber-500 border-amber-500/30 hover:bg-amber-500/10" onClick={() => setShowImportDialog(true)}>
            <Upload className="mr-2 h-4 w-4" />
            批量导入
          </Button>
          <Button size="sm" className="bg-amber-600 hover:bg-amber-700" onClick={() => setShowForm(true)}>
            <Plus className="mr-2 h-4 w-4" />
            新增词汇
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid gap-4 grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">违禁词(P0)</p>
            <p className="text-2xl font-bold text-destructive">{p0Count}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">敏感词(P1)</p>
            <p className="text-2xl font-bold text-amber-500">{p1Count}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">总计</p>
            <p className="text-2xl font-bold">{(items || []).length}</p>
          </CardContent>
        </Card>
      </div>

      {/* Create form */}
      {showForm && (
        <Card className="border-amber-500/30">
          <CardHeader>
            <CardTitle className="text-base">新增合规词汇</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="text-sm font-medium">词汇</label>
                <input
                  type="text"
                  value={formData.word}
                  onChange={(e) => setFormData({ ...formData, word: e.target.value })}
                  className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  placeholder="输入违禁/敏感词"
                />
              </div>
              <div>
                <label className="text-sm font-medium">级别</label>
                <select
                  value={formData.level}
                  onChange={(e) => setFormData({ ...formData, level: e.target.value })}
                  className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  <option value="P0">P0 违禁词</option>
                  <option value="P1">P1 敏感词</option>
                </select>
              </div>
            </div>
            <div>
              <label className="text-sm font-medium">分类</label>
              <input
                type="text"
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                placeholder="如：绝对化用语、疗效暗示"
              />
            </div>
            <div>
              <label className="text-sm font-medium">描述</label>
              <input
                type="text"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                placeholder="说明该词汇为何被列为合规词"
              />
            </div>
            <div className="flex gap-2 justify-end">
              <Button variant="outline" size="sm" onClick={() => setShowForm(false)}>取消</Button>
              <Button size="sm" className="bg-amber-600 hover:bg-amber-700" onClick={handleCreate}>创建</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
        <div className="flex gap-2">
          {LEVELS.map((level) => {
            const Icon = level.icon;
            return (
              <button
                key={level.id}
                onClick={() => setSelectedLevel(level.id)}
                className={cn(
                  'flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm transition-colors',
                  selectedLevel === level.id
                    ? 'bg-amber-500/20 text-amber-100 font-medium'
                    : 'text-muted-foreground hover:bg-muted'
                )}
              >
                <Icon className="h-4 w-4" />
                {level.name}
              </button>
            );
          })}
        </div>
        <div className="relative sm:ml-auto">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            placeholder="搜索词汇..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="h-9 w-64 rounded-md border border-input bg-background pl-9 pr-3 text-sm"
          />
        </div>
      </div>

      {/* Word list */}
      {isLoading ? (
        <div className="flex h-32 items-center justify-center">
          <div className="h-6 w-6 animate-spin rounded-full border-4 border-amber-500 border-t-transparent" />
        </div>
      ) : filteredItems.length === 0 ? (
        <Card>
          <CardContent className="p-8 text-center text-muted-foreground">
            暂无合规词汇
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="p-0">
            <div className="divide-y divide-border">
              {/* Table header */}
              <div className="grid grid-cols-[1fr_80px_120px_1fr_80px] gap-4 px-4 py-3 text-sm font-medium text-muted-foreground">
                <span>词汇</span>
                <span>级别</span>
                <span>分类</span>
                <span>描述</span>
                <span className="text-right">操作</span>
              </div>
              {/* Rows */}
              {filteredItems.map((item) => (
                <div key={item.id} className="grid grid-cols-[1fr_80px_120px_1fr_80px] gap-4 px-4 py-3 text-sm items-center hover:bg-muted/50">
                  <span className="font-medium">{item.word}</span>
                  <span>
                    <Badge
                      variant={item.level === 'P0' ? 'destructive' : 'secondary'}
                      className="text-xs"
                    >
                      {item.level}
                    </Badge>
                  </span>
                  <span className="text-muted-foreground">{item.category}</span>
                  <span className="text-muted-foreground truncate">{item.description}</span>
                  <div className="text-right">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 px-2 text-destructive hover:bg-destructive/10"
                      onClick={() => setDeleteId(item.id)}
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Delete confirmation dialog */}
      <Dialog open={deleteId !== null} onOpenChange={(open) => { if (!open) setDeleteId(null); }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>确认删除</DialogTitle>
            <DialogDescription>确定要删除这个合规词汇吗？此操作不可撤销。</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <DialogClose render={<Button variant="outline" size="sm" />}>取消</DialogClose>
            <Button size="sm" className="bg-destructive hover:bg-destructive/90 text-destructive-foreground" onClick={handleDelete}>
              确认删除
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Batch import dialog */}
      <Dialog open={showImportDialog} onOpenChange={setShowImportDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>批量导入</DialogTitle>
            <DialogDescription>批量导入功能开发中，敬请期待。</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <DialogClose render={<Button size="sm" className="bg-amber-600 hover:bg-amber-700" />}>知道了</DialogClose>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
