'use client';

import { useState } from 'react';
import { useAdminKnowledge, useCreateAdminKnowledge, useDeleteAdminKnowledge, useUpdateAdminKnowledge } from '@/hooks/use-admin';
import { KnowledgeEntry } from '@/types';
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
  Edit3,
  ChevronDown,
  ChevronUp,
  Globe,
  BookOpen,
  ShieldCheck,
  FileText,
  Upload,
} from 'lucide-react';

const CATEGORIES = [
  { id: 'all', name: '全部', icon: Globe },
  { id: 'rule', name: '平台规则', icon: ShieldCheck },
  { id: 'methodology', name: '创作方法论', icon: BookOpen },
  { id: 'compliance', name: '合规通用规则', icon: FileText },
];

export default function PublicContent() {
  const { data: items, isLoading } = useAdminKnowledge('public');
  const createMutation = useCreateAdminKnowledge();
  const deleteMutation = useDeleteAdminKnowledge();
  const updateMutation = useUpdateAdminKnowledge();
  const { toast } = useToast();

  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState({ title: '', content: '', category: 'rule', tags: '' });
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [showImportDialog, setShowImportDialog] = useState(false);

  const filteredItems = (items || []).filter((item) => {
    if (selectedCategory !== 'all' && item.category !== selectedCategory) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return item.title.toLowerCase().includes(q) || item.tags?.some((t) => t.includes(q));
    }
    return true;
  });

  function handleCreate() {
    if (!formData.title || !formData.content) return;
    createMutation.mutate({
      title: formData.title,
      content: formData.content,
      platform_category: 'public',
      category: formData.category,
      tags: formData.tags ? formData.tags.split(',').map((t) => t.trim()) : [],
    }, {
      onSuccess: () => {
        toast('success', '知识条目创建成功');
        resetForm();
      },
      onError: () => {
        toast('error', '创建失败，请重试');
      },
    });
  }

  function handleUpdate() {
    if (!editingId || !formData.title) return;
    updateMutation.mutate({
      id: editingId,
      data: {
        title: formData.title,
        content: formData.content,
        tags: formData.tags ? formData.tags.split(',').map((t) => t.trim()) : [],
      },
      platformCategory: 'public',
    }, {
      onSuccess: () => {
        toast('success', '知识条目已更新');
        resetForm();
      },
      onError: () => {
        toast('error', '更新失败，请重试');
      },
    });
  }

  function handleDelete() {
    if (!deleteId) return;
    deleteMutation.mutate({ id: deleteId, platformCategory: 'public' }, {
      onSuccess: () => {
        toast('success', '知识条目已删除');
        setDeleteId(null);
      },
      onError: () => {
        toast('error', '删除失败，请重试');
      },
    });
  }

  function handleEdit(item: KnowledgeEntry) {
    setEditingId(item.id);
    setFormData({
      title: item.title,
      content: item.content,
      category: item.category || 'rule',
      tags: item.tags?.join(', ') || '',
    });
    setShowForm(true);
  }

  function resetForm() {
    setFormData({ title: '', content: '', category: 'rule', tags: '' });
    setShowForm(false);
    setEditingId(null);
  }

  function getCategoryLabel(cat: string | null | undefined) {
    if (!cat) return '未分类';
    const found = CATEGORIES.find((c) => c.id === cat);
    return found?.name || cat;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold">公共知识库</h1>
          <p className="text-muted-foreground">管理平台规则、创作方法论、合规通用规则</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" className="text-amber-500 border-amber-500/30 hover:bg-amber-500/10" onClick={() => setShowImportDialog(true)}>
            <Upload className="mr-2 h-4 w-4" />
            批量导入
          </Button>
          <Button size="sm" className="bg-amber-600 hover:bg-amber-700" onClick={() => { resetForm(); setShowForm(true); }}>
            <Plus className="mr-2 h-4 w-4" />
            新增知识
          </Button>
        </div>
      </div>

      {/* Create/Edit form */}
      {showForm && (
        <Card className="border-amber-500/30">
          <CardHeader>
            <CardTitle className="text-base">{editingId ? '编辑知识条目' : '新增知识条目'}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium">标题</label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                placeholder="输入知识标题"
              />
            </div>
            <div>
              <label className="text-sm font-medium">分类</label>
              <select
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="rule">平台规则</option>
                <option value="methodology">创作方法论</option>
                <option value="compliance">合规通用规则</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium">内容</label>
              <textarea
                value={formData.content}
                onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm min-h-[120px]"
                placeholder="输入知识内容（支持 Markdown）"
              />
            </div>
            <div>
              <label className="text-sm font-medium">标签（逗号分隔）</label>
              <input
                type="text"
                value={formData.tags}
                onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
                className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                placeholder="标签1, 标签2, 标签3"
              />
            </div>
            <div className="flex gap-2 justify-end">
              <Button variant="outline" size="sm" onClick={resetForm}>取消</Button>
              <Button size="sm" className="bg-amber-600 hover:bg-amber-700" onClick={editingId ? handleUpdate : handleCreate}>
                {editingId ? '保存修改' : '创建'}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
        <div className="flex gap-2 flex-wrap">
          {CATEGORIES.map((cat) => {
            const Icon = cat.icon;
            return (
              <button
                key={cat.id}
                onClick={() => setSelectedCategory(cat.id)}
                className={cn(
                  'flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm transition-colors',
                  selectedCategory === cat.id
                    ? 'bg-amber-500/20 text-amber-100 font-medium'
                    : 'text-muted-foreground hover:bg-muted'
                )}
              >
                <Icon className="h-4 w-4" />
                {cat.name}
              </button>
            );
          })}
        </div>
        <div className="relative sm:ml-auto">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            placeholder="搜索..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="h-9 w-64 rounded-md border border-input bg-background pl-9 pr-3 text-sm"
          />
        </div>
      </div>

      {/* List */}
      {isLoading ? (
        <div className="flex h-32 items-center justify-center">
          <div className="h-6 w-6 animate-spin rounded-full border-4 border-amber-500 border-t-transparent" />
        </div>
      ) : filteredItems.length === 0 ? (
        <Card>
          <CardContent className="p-8 text-center text-muted-foreground">
            暂无知识条目
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {filteredItems.map((item) => {
            const isExpanded = expandedId === item.id;
            return (
              <Card key={item.id} className="hover:border-amber-500/30 transition-colors">
                <CardContent className="p-4">
                  <div
                    className="flex items-start justify-between cursor-pointer"
                    onClick={() => setExpandedId(isExpanded ? null : item.id)}
                  >
                    <div className="space-y-1 flex-1">
                      <div className="flex items-center gap-2">
                        <h3 className="font-medium">{item.title}</h3>
                        <Badge variant="secondary" className="text-xs">{getCategoryLabel(item.category)}</Badge>
                      </div>
                      {!isExpanded && (
                        <p className="text-sm text-muted-foreground line-clamp-1">{item.content}</p>
                      )}
                    </div>
                    <div className="flex items-center gap-2 ml-4">
                      {item.tags?.slice(0, 2).map((tag) => (
                        <Badge key={tag} variant="outline" className="text-xs">#{tag}</Badge>
                      ))}
                      {isExpanded ? <ChevronUp className="h-4 w-4 text-muted-foreground" /> : <ChevronDown className="h-4 w-4 text-muted-foreground" />}
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="mt-4 space-y-3">
                      <div className="text-sm whitespace-pre-wrap bg-muted/50 rounded-md p-3">{item.content}</div>
                      <div className="flex items-center gap-2">
                        {item.tags?.map((tag) => (
                          <Badge key={tag} variant="outline" className="text-xs">#{tag}</Badge>
                        ))}
                      </div>
                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <span>来源: {item.source || '未指定'} | 更新: {item.updated_at ? new Date(item.updated_at).toLocaleDateString('zh-CN') : '--'}</span>
                        <div className="flex gap-2">
                          <Button variant="outline" size="sm" onClick={(e) => { e.stopPropagation(); handleEdit(item); }}>
                            <Edit3 className="mr-1 h-3 w-3" /> 编辑
                          </Button>
                          <Button variant="outline" size="sm" className="text-destructive hover:bg-destructive/10" onClick={(e) => { e.stopPropagation(); setDeleteId(item.id); }}>
                            <Trash2 className="mr-1 h-3 w-3" /> 删除
                          </Button>
                        </div>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Delete confirmation dialog */}
      <Dialog open={deleteId !== null} onOpenChange={(open) => { if (!open) setDeleteId(null); }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>确认删除</DialogTitle>
            <DialogDescription>确定要删除这条知识条目吗？此操作不可撤销。</DialogDescription>
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
