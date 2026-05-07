'use client';

import { useState, useRef } from 'react';
import { AppLayout } from '@/components/layout/app-layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  useKnowledgeList, useKnowledgeStats, useSearchKnowledge,
  useCreateKnowledge, useUpdateKnowledge, useDeleteKnowledge, useUploadKnowledge,
  useResyncKnowledge,
} from '@/hooks/use-knowledge';
import { useToast } from '@/components/ui/toast';
import {
  BookOpen, Upload, Search, Plus, FolderOpen, FileText,
  Trash2, Edit3, X, ChevronRight, Database, Shield, RefreshCw,
} from 'lucide-react';
import { cn } from '@/lib/utils';

const CATEGORIES = [
  { id: 'all', name: '全部知识', icon: BookOpen },
  { id: 'product', name: '产品知识', icon: FileText },
  { id: 'industry', name: '行业知识', icon: Database },
  { id: 'brand', name: '品牌规范', icon: Shield },
  { id: 'template', name: '内容模板', icon: FolderOpen },
  { id: 'compliance', name: '合规规则', icon: Shield },
];

interface FormData {
  title: string;
  content: string;
  category: string;
  tags: string;
}

const EMPTY_FORM: FormData = { title: '', content: '', category: 'product', tags: '' };

export default function KnowledgeContent() {
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [showUpload, setShowUpload] = useState(false);
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);

  // Dialog state
  const [showForm, setShowForm] = useState(false);
  const [editingItem, setEditingItem] = useState<{ id: string } & FormData & { tags: string } | null>(null);
  const [form, setForm] = useState<FormData>(EMPTY_FORM);
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();
  const showToast = (msg: string, type: 'success' | 'error' = 'success') => toast(type, msg);

  const { data: items = [], isLoading } = useKnowledgeList(selectedCategory);
  const { data: stats } = useKnowledgeStats();
  const { data: searchResults } = useSearchKnowledge(searchQuery);

  const createMutation = useCreateKnowledge();
  const updateMutation = useUpdateKnowledge();
  const deleteMutation = useDeleteKnowledge();
  const uploadMutation = useUploadKnowledge();
  const resyncMutation = useResyncKnowledge();

  const displayItems = searchQuery.length > 0 ? searchResults : items;

  const getCategoryCount = (id: string) => {
    if (!stats?.by_category) return 0;
    if (id === 'all') return stats.total_entries || 0;
    return stats.by_category[id] || 0;
  };

  // Open create dialog
  const handleAdd = () => {
    setEditingItem(null);
    setForm(EMPTY_FORM);
    setShowForm(true);
  };

  // Open edit dialog
  const handleEdit = (item: { id: string; title: string; content: string; category?: string | null; tags?: string[] }) => {
    setEditingItem({
      id: item.id,
      title: item.title,
      content: item.content,
      category: item.category || 'product',
      tags: item.tags?.join(', ') || '',
    });
    setForm({
      title: item.title,
      content: item.content,
      category: item.category || 'product',
      tags: item.tags?.join(', ') || '',
    });
    setShowForm(true);
  };

  // Submit create/edit
  const handleSubmit = () => {
    if (!form.title.trim() || !form.content.trim()) {
      showToast('请填写标题和内容', 'error');
      return;
    }
    const tags = form.tags.split(/[,，\s]+/).filter(Boolean);
    const payload = { title: form.title, content: form.content, category: form.category, tags };

    if (editingItem) {
      updateMutation.mutate({ id: editingItem.id, data: payload }, {
        onSuccess: () => {
          showToast('更新成功');
          setShowForm(false);
          setEditingItem(null);
        },
        onError: () => showToast('更新失败', 'error'),
      });
    } else {
      createMutation.mutate(payload, {
        onSuccess: () => {
          showToast('创建成功');
          setShowForm(false);
        },
        onError: () => showToast('创建失败', 'error'),
      });
    }
  };

  // Delete
  const handleDelete = (id: string) => {
    deleteMutation.mutate(id, {
      onSuccess: () => {
        showToast('删除成功');
        setDeleteTarget(null);
        if (selectedItemId === id) setSelectedItemId(null);
      },
      onError: () => showToast('删除失败', 'error'),
    });
  };

  // File upload
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    uploadMutation.mutate(formData, {
      onSuccess: () => {
        showToast('上传成功');
        setShowUpload(false);
      },
      onError: () => showToast('上传失败', 'error'),
    });
    e.target.value = '';
  };

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold lg:text-3xl">知识库管理</h1>
            <p className="text-muted-foreground">管理您的企业私有知识库，支撑 AI 创作</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => setShowUpload(!showUpload)}>
              <Upload className="mr-2 h-4 w-4" />上传知识
            </Button>
            <Button onClick={handleAdd}><Plus className="mr-2 h-4 w-4" />新增条目</Button>
          </div>
        </div>

        {/* Upload area */}
        {showUpload && (
          <Card className="border-dashed">
            <CardContent className="pt-6">
              <div
                className="flex flex-col items-center justify-center py-8 space-y-3"
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => {
                  e.preventDefault();
                  const file = e.dataTransfer.files[0];
                  if (file) {
                    const formData = new FormData();
                    formData.append('file', file);
                    uploadMutation.mutate(formData, {
                      onSuccess: () => { showToast('上传成功'); setShowUpload(false); },
                      onError: () => showToast('上传失败', 'error'),
                    });
                  }
                }}
              >
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-muted">
                  <Upload className="h-8 w-8 text-muted-foreground" />
                </div>
                <div className="text-center">
                  <p className="font-medium">拖拽文件到此处，或点击上传</p>
                  <p className="text-sm text-muted-foreground mt-1">支持 .md、.txt、.docx 格式，单文件最大 10MB</p>
                </div>
                <div className="flex gap-2">
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".md,.txt,.docx"
                    className="hidden"
                    onChange={handleFileChange}
                  />
                  <Button size="sm" onClick={() => fileInputRef.current?.click()} disabled={uploadMutation.isPending}>
                    {uploadMutation.isPending ? '上传中...' : '选择文件'}
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => setShowUpload(false)}>
                    <X className="mr-1 h-3.5 w-3.5" />取消
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Stats */}
        <div className="grid gap-4 grid-cols-2 lg:grid-cols-3">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">知识条目</CardTitle>
              <BookOpen className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.total_entries || 0}</div>
              <p className="text-xs text-muted-foreground">条企业私有知识</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">分类数量</CardTitle>
              <FolderOpen className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.by_category ? Object.keys(stats.by_category).length : 0}</div>
              <p className="text-xs text-muted-foreground">个知识分类</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">最近更新</CardTitle>
              <Database className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.recent_updates?.[0]?.title?.slice(0, 6) || '--'}</div>
              <p className="text-xs text-muted-foreground truncate">{stats?.recent_updates?.[0]?.title || '暂无更新'}</p>
            </CardContent>
          </Card>
        </div>

        {/* Main content */}
        <div className="grid gap-6 lg:grid-cols-[240px_1fr]">
          {/* Category tree */}
          <Card className="h-fit">
            <CardHeader className="pb-3"><CardTitle className="text-sm">知识分类</CardTitle></CardHeader>
            <CardContent className="space-y-1">
              {CATEGORIES.map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => setSelectedCategory(cat.id)}
                  className={cn(
                    'flex w-full items-center justify-between rounded-md px-3 py-2 text-sm transition-colors',
                    selectedCategory === cat.id
                      ? 'bg-primary/10 text-primary'
                      : 'hover:bg-muted text-muted-foreground hover:text-foreground'
                  )}
                >
                  <div className="flex items-center gap-2">
                    <cat.icon className="h-4 w-4" />
                    <span>{cat.name}</span>
                  </div>
                  <span className="text-xs">{getCategoryCount(cat.id)}</span>
                </button>
              ))}
            </CardContent>
          </Card>

          {/* Content list */}
          <div className="space-y-4">
            <div className="flex gap-3">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="搜索知识标题或标签..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9"
                />
              </div>
              <Button
                variant="outline"
                onClick={() => {
                  if (searchQuery.trim()) {
                    // search is already reactive via useSearchKnowledge
                  }
                }}
              >
                语义搜索
              </Button>
            </div>

            {isLoading ? (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-16">
                  <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
                  <p className="mt-4 text-muted-foreground">加载中...</p>
                </CardContent>
              </Card>
            ) : !displayItems || displayItems.length === 0 ? (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-16">
                  <BookOpen className="h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">暂无匹配的知识条目</p>
                  <p className="text-sm text-muted-foreground mt-1">点击&ldquo;上传知识&rdquo;或&ldquo;新增条目&rdquo;开始添加</p>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-3">
                {displayItems.map((item) => (
                  <Card
                    key={item.id}
                    className={cn(
                      'cursor-pointer transition-colors hover:border-primary/50',
                      selectedItemId === item.id && 'border-primary'
                    )}
                    onClick={() => setSelectedItemId(selectedItemId === item.id ? null : item.id)}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <p className="font-medium text-sm">{item.title}</p>
                            <Badge variant="outline" className="text-xs">
                              {CATEGORIES.find((c) => c.id === item.category)?.name || item.category}
                            </Badge>
                            {item.sync_status === 'pending' && (
                              <Badge variant="secondary" className="text-xs bg-yellow-100 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400">向量化中</Badge>
                            )}
                            {item.sync_status === 'failed' && (
                              <Badge variant="secondary" className="text-xs bg-red-100 text-red-700 dark:bg-red-900/20 dark:text-red-400">同步失败</Badge>
                            )}
                          </div>
                          {selectedItemId === item.id ? (
                            <div className="mt-3 space-y-3">
                              <p className="text-sm text-muted-foreground leading-relaxed">{item.content}</p>
                              <div className="flex items-center gap-4 text-xs text-muted-foreground">
                                <span>来源：{item.source || '未知'}</span>
                              </div>
                              <div className="flex gap-2">
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={(e) => { e.stopPropagation(); handleEdit(item); }}
                                >
                                  <Edit3 className="mr-1 h-3.5 w-3.5" />编辑
                                </Button>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  className="text-destructive hover:text-destructive"
                                  onClick={(e) => { e.stopPropagation(); setDeleteTarget(item.id); }}
                                >
                                  <Trash2 className="mr-1 h-3.5 w-3.5" />删除
                                </Button>
                                {item.sync_status === 'failed' && (
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={(e) => { e.stopPropagation(); resyncMutation.mutate(item.id); }}
                                  >
                                    <RefreshCw className="mr-1 h-3.5 w-3.5" />重试向量化
                                  </Button>
                                )}
                              </div>
                            </div>
                          ) : (
                            <p className="text-xs text-muted-foreground mt-1 truncate">{item.content}</p>
                          )}
                          <div className="flex items-center gap-2 mt-2">
                            {item.tags?.slice(0, 3).map((tag) => (
                              <Badge key={tag} variant="secondary" className="text-xs">#{tag}</Badge>
                            ))}
                          </div>
                        </div>
                        <ChevronRight className={cn(
                          'h-4 w-4 text-muted-foreground transition-transform ml-2 flex-shrink-0',
                          selectedItemId === item.id && 'rotate-90'
                        )} />
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Create/Edit Dialog */}
      {showForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setShowForm(false)}>
          <div className="bg-background rounded-lg shadow-lg w-full max-w-lg mx-4 p-6" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold">{editingItem ? '编辑知识条目' : '新增知识条目'}</h2>
              <Button variant="ghost" size="sm" onClick={() => setShowForm(false)}>
                <X className="h-4 w-4" />
              </Button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-1 block">标题</label>
                <Input
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  placeholder="输入知识标题"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-1 block">分类</label>
                <select
                  className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                  value={form.category}
                  onChange={(e) => setForm({ ...form, category: e.target.value })}
                >
                  {CATEGORIES.filter((c) => c.id !== 'all').map((c) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-sm font-medium mb-1 block">内容</label>
                <textarea
                  className="w-full rounded-md border bg-background px-3 py-2 text-sm min-h-[120px] resize-y"
                  value={form.content}
                  onChange={(e) => setForm({ ...form, content: e.target.value })}
                  placeholder="输入知识内容"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-1 block">标签（逗号分隔）</label>
                <Input
                  value={form.tags}
                  onChange={(e) => setForm({ ...form, tags: e.target.value })}
                  placeholder="标签1, 标签2, 标签3"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <Button variant="outline" onClick={() => setShowForm(false)}>取消</Button>
              <Button onClick={handleSubmit} disabled={createMutation.isPending || updateMutation.isPending}>
                {(createMutation.isPending || updateMutation.isPending) ? '保存中...' : '保存'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      {deleteTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setDeleteTarget(null)}>
          <div className="bg-background rounded-lg shadow-lg w-full max-w-sm mx-4 p-6" onClick={(e) => e.stopPropagation()}>
            <h2 className="text-lg font-bold mb-2">确认删除</h2>
            <p className="text-sm text-muted-foreground mb-6">删除后无法恢复，确定要删除这条知识吗？</p>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setDeleteTarget(null)}>取消</Button>
              <Button
                variant="destructive"
                onClick={() => handleDelete(deleteTarget)}
                disabled={deleteMutation.isPending}
              >
                {deleteMutation.isPending ? '删除中...' : '删除'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </AppLayout>
  );
}
