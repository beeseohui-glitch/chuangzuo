'use client';

import { useState } from 'react';
import { useAdminTemplates, useCreateAdminTemplate, useDeleteAdminTemplate } from '@/hooks/use-admin';
import type { AdminTemplate } from '@/hooks/use-admin';
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
  FileText,
  Tag,
  Users,
  ShoppingBag,
  Calendar,
} from 'lucide-react';

const TEMPLATE_CATEGORIES = [
  { id: 'all', name: '全部', icon: FileText },
  { id: 'brand', name: '品牌模板', icon: Tag },
  { id: 'product', name: '产品模板', icon: ShoppingBag },
  { id: 'persona', name: '人群模板', icon: Users },
  { id: 'scene', name: '场景模板', icon: Calendar },
];

export default function TemplatesContent() {
  const { data: items, isLoading } = useAdminTemplates();
  const createMutation = useCreateAdminTemplate();
  const deleteMutation = useDeleteAdminTemplate();
  const { toast } = useToast();

  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState({ title: '', content: '', category: 'product', variables: '' });
  const [deleteId, setDeleteId] = useState<string | null>(null);

  const filteredItems = (items || []).filter((item) => {
    if (selectedCategory !== 'all' && item.category !== selectedCategory) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return item.title.toLowerCase().includes(q);
    }
    return true;
  });

  function handleCreate() {
    if (!formData.title || !formData.content) return;
    createMutation.mutate({
      title: formData.title,
      content: formData.content,
      category: formData.category,
    }, {
      onSuccess: () => {
        toast('success', '模板创建成功');
        resetForm();
      },
      onError: () => {
        toast('error', '创建失败，请重试');
      },
    });
  }

  function handleDelete() {
    if (!deleteId) return;
    deleteMutation.mutate(String(deleteId), {
      onSuccess: () => {
        toast('success', '模板已删除');
        setDeleteId(null);
      },
      onError: () => {
        toast('error', '删除失败，请重试');
      },
    });
  }

  function handleEdit(template: AdminTemplate) {
    setEditingId(template.id);
    setFormData({
      title: template.title,
      content: template.content,
      category: template.category,
      variables: (template.variables || []).join(', '),
    });
    setShowForm(true);
  }

  function resetForm() {
    setFormData({ title: '', content: '', category: 'product', variables: '' });
    setShowForm(false);
    setEditingId(null);
  }

  function getCategoryLabel(cat: string) {
    return TEMPLATE_CATEGORIES.find((c) => c.id === cat)?.name || cat;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold">内置模板</h1>
          <p className="text-muted-foreground">管理品牌、产品、人群、场景类内容模板</p>
        </div>
        <Button size="sm" className="bg-amber-600 hover:bg-amber-700" onClick={() => { resetForm(); setShowForm(true); }}>
          <Plus className="mr-2 h-4 w-4" />
          新增模板
        </Button>
      </div>

      {/* Create/Edit form */}
      {showForm && (
        <Card className="border-amber-500/30">
          <CardHeader>
            <CardTitle className="text-base">{editingId ? '编辑模板' : '新增模板'}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="text-sm font-medium">标题</label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  placeholder="模板名称"
                />
              </div>
              <div>
                <label className="text-sm font-medium">分类</label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  <option value="brand">品牌模板</option>
                  <option value="product">产品模板</option>
                  <option value="persona">人群模板</option>
                  <option value="scene">场景模板</option>
                </select>
              </div>
            </div>
            <div>
              <label className="text-sm font-medium">模板内容</label>
              <textarea
                value={formData.content}
                onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm min-h-[160px]"
                placeholder="输入模板内容（使用【】标注结构段落）"
              />
            </div>
            <div>
              <label className="text-sm font-medium">变量（逗号分隔）</label>
              <input
                type="text"
                value={formData.variables}
                onChange={(e) => setFormData({ ...formData, variables: e.target.value })}
                className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                placeholder="产品名称, 核心卖点, 使用感受"
              />
            </div>
            <div className="flex gap-2 justify-end">
              <Button variant="outline" size="sm" onClick={resetForm}>取消</Button>
              <Button size="sm" className="bg-amber-600 hover:bg-amber-700" onClick={handleCreate}>
                {editingId ? '保存修改' : '创建'}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Category filters */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
        <div className="flex gap-2 flex-wrap">
          {TEMPLATE_CATEGORIES.map((cat) => {
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
            placeholder="搜索模板..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="h-9 w-64 rounded-md border border-input bg-background pl-9 pr-3 text-sm"
          />
        </div>
      </div>

      {/* Template list */}
      {isLoading ? (
        <div className="flex h-32 items-center justify-center">
          <div className="h-6 w-6 animate-spin rounded-full border-4 border-amber-500 border-t-transparent" />
        </div>
      ) : filteredItems.length === 0 ? (
        <Card>
          <CardContent className="p-8 text-center text-muted-foreground">
            暂无模板
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filteredItems.map((item) => {
            const isExpanded = expandedId === item.id;
            return (
              <Card key={item.id} className="hover:border-amber-500/30 transition-colors flex flex-col">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <CardTitle className="text-base">{item.title}</CardTitle>
                      <div className="flex items-center gap-2">
                        <Badge variant="secondary" className="text-xs">{getCategoryLabel(item.category)}</Badge>
                        <span className="text-xs text-muted-foreground">v{item.version}</span>
                      </div>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="flex-1 flex flex-col">
                  <div
                    className="cursor-pointer flex-1"
                    onClick={() => setExpandedId(isExpanded ? null : item.id)}
                  >
                    {isExpanded ? (
                      <div className="text-sm whitespace-pre-wrap bg-muted/50 rounded-md p-3 mb-3">{item.content}</div>
                    ) : (
                      <p className="text-sm text-muted-foreground line-clamp-3 mb-3">{item.content}</p>
                    )}
                  </div>

                  {/* Variables */}
                  {item.variables?.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-3">
                      {item.variables.map((v) => (
                        <Badge key={v} variant="outline" className="text-xs text-amber-500 border-amber-500/30">{`{{${v}}}`}</Badge>
                      ))}
                    </div>
                  )}

                  {/* Actions */}
                  <div className="flex items-center justify-between text-xs text-muted-foreground mt-auto pt-2 border-t border-border">
                    <span>更新: {new Date(item.updated_at).toLocaleDateString('zh-CN')}</span>
                    <div className="flex gap-1">
                      <Button variant="ghost" size="sm" className="h-7 px-2" onClick={() => handleEdit(item)}>
                        <Edit3 className="h-3 w-3" />
                      </Button>
                      <Button variant="ghost" size="sm" className="h-7 px-2 text-destructive hover:bg-destructive/10" onClick={() => setDeleteId(item.id)}>
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
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
            <DialogDescription>确定要删除这个模板吗？此操作不可撤销。</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <DialogClose render={<Button variant="outline" size="sm" />}>取消</DialogClose>
            <Button size="sm" className="bg-destructive hover:bg-destructive/90 text-destructive-foreground" onClick={handleDelete}>
              确认删除
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
