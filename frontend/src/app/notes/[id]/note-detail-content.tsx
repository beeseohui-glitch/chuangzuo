'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { AppLayout } from '@/components/layout/app-layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import { ArrowLeft, BarChart3, Shield, Tag, Clock, Edit3, Trash2, Save, X } from 'lucide-react';
import { notesApi } from '@/lib/api';

interface NoteDetail {
  id: string;
  title: string;
  platform: string;
  status: string;
  ai_flavor_score: number;
  created_at: string;
  article?: string;
  tags?: string[];
}

const PLATFORM_LABELS: Record<string, string> = {
  xiaohongshu: '小红书',
  wechat_public: '公众号',
  douyin: '抖音',
};

export default function NoteDetailContent() {
  const params = useParams();
  const router = useRouter();
  const noteId = params.id as string;

  const [note, setNote] = useState<NoteDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState('');
  const [editArticle, setEditArticle] = useState('');
  const [editTags, setEditTags] = useState('');
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [error, setError] = useState('');

  const loadNote = useCallback(async () => {
    setLoading(true);
    try {
      const res = await notesApi.getDetail(noteId);
      if (res.success && res.data) {
        const data = res.data as NoteDetail;
        setNote(data);
      }
    } catch {
      // ignore
    }
    setLoading(false);
  }, [noteId]);

  useEffect(() => {
    loadNote();
  }, [loadNote]);

  const startEdit = () => {
    if (!note) return;
    setEditTitle(note.title || '');
    setEditArticle(note.article || '');
    setEditTags((note.tags || []).join(', '));
    setIsEditing(true);
  };

  const cancelEdit = () => {
    setIsEditing(false);
  };

  const saveEdit = async () => {
    if (!note) return;
    setSaving(true);
    setError('');
    try {
      const tags = editTags.split(/[,，]/).map((t) => t.trim()).filter(Boolean);
      const res = await notesApi.update(noteId, {
        title: editTitle,
        article: editArticle,
        tags,
      });
      if (res.success) {
        setIsEditing(false);
        await loadNote();
      } else {
        setError(res.error || '保存失败');
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : '网络错误');
    }
    setSaving(false);
  };

  const deleteNote = async () => {
    setDeleting(true);
    setError('');
    try {
      const res = await notesApi.delete(noteId);
      if (res.success) {
        router.push('/analytics');
      } else {
        setError(res.error || '删除失败');
        setShowDeleteConfirm(false);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : '网络错误');
      setShowDeleteConfirm(false);
    }
    setDeleting(false);
  };

  const complianceBadge = (status: string) => {
    if (status === 'published') return <Badge className="bg-green-500/10 text-green-500 border-green-500/20">已发布</Badge>;
    if (status === 'draft') return <Badge variant="outline" className="border-yellow-500/30 text-yellow-500">草稿</Badge>;
    return <Badge variant="outline">{status}</Badge>;
  };

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" onClick={() => router.back()}>
              <ArrowLeft className="mr-2 h-4 w-4" />返回
            </Button>
            <div>
              <h1 className="text-2xl font-bold lg:text-3xl">笔记详情</h1>
              <p className="text-muted-foreground">查看创作内容详情</p>
            </div>
          </div>
          {note && !isEditing && (
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={startEdit}>
                <Edit3 className="mr-1.5 h-3.5 w-3.5" />编辑
              </Button>
              <Button variant="outline" size="sm" className="text-destructive hover:bg-destructive/10" onClick={() => setShowDeleteConfirm(true)}>
                <Trash2 className="mr-1.5 h-3.5 w-3.5" />删除
              </Button>
            </div>
          )}
        </div>

        {/* 错误提示 */}
        {error && (
          <Card className="border-destructive/50">
            <CardContent className="p-4 flex items-center justify-between">
              <p className="text-sm text-destructive">{error}</p>
              <Button variant="ghost" size="sm" onClick={() => setError('')}>关闭</Button>
            </CardContent>
          </Card>
        )}

        {/* 删除确认 */}
        {showDeleteConfirm && (
          <Card className="border-destructive/50">
            <CardContent className="p-4 flex items-center justify-between">
              <p className="text-sm">确定要删除这篇笔记吗？此操作不可撤销。</p>
              <div className="flex gap-2">
                <Button variant="ghost" size="sm" onClick={() => setShowDeleteConfirm(false)} disabled={deleting}>取消</Button>
                <Button variant="destructive" size="sm" onClick={deleteNote} disabled={deleting}>
                  {deleting ? '删除中...' : '确认删除'}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {loading ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-16">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
              <p className="mt-4 text-muted-foreground">加载中...</p>
            </CardContent>
          </Card>
        ) : !note ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-16">
              <p className="text-muted-foreground">未找到该笔记</p>
              <Button variant="outline" className="mt-4" onClick={() => router.back()}>返回</Button>
            </CardContent>
          </Card>
        ) : (
          <>
            {/* Header info */}
            <Card>
              <CardContent className="p-6">
                <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
                  <div className="flex-1">
                    {isEditing ? (
                      <Input
                        value={editTitle}
                        onChange={(e) => setEditTitle(e.target.value)}
                        className="text-xl font-bold"
                      />
                    ) : (
                      <h2 className="text-xl font-bold">{note.title}</h2>
                    )}
                    <div className="flex items-center gap-3 mt-3 flex-wrap">
                      <Badge variant="outline">{PLATFORM_LABELS[note.platform] || note.platform}</Badge>
                      {complianceBadge(note.status)}
                      <span className="flex items-center gap-1 text-sm text-muted-foreground">
                        <Clock className="h-3.5 w-3.5" />
                        {new Date(note.created_at).toLocaleDateString('zh-CN')}
                      </span>
                    </div>
                  </div>
                  <div className="flex gap-4">
                    <div className="text-center">
                      <div className="flex items-center gap-1 text-muted-foreground text-xs"><BarChart3 className="h-3.5 w-3.5" />AI 味</div>
                      <p className="text-2xl font-bold">{note.ai_flavor_score}</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <div className="grid gap-6 lg:grid-cols-3">
              {/* Content */}
              <Card className="lg:col-span-2">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base">笔记内容</CardTitle>
                    {isEditing && (
                      <div className="flex gap-2">
                        <Button variant="ghost" size="sm" onClick={cancelEdit}>
                          <X className="mr-1 h-3.5 w-3.5" />取消
                        </Button>
                        <Button size="sm" onClick={saveEdit} disabled={saving}>
                          <Save className="mr-1 h-3.5 w-3.5" />{saving ? '保存中...' : '保存'}
                        </Button>
                      </div>
                    )}
                  </div>
                </CardHeader>
                <CardContent>
                  {isEditing ? (
                    <textarea
                      value={editArticle}
                      onChange={(e) => setEditArticle(e.target.value)}
                      rows={12}
                      className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring resize-none"
                    />
                  ) : note.article ? (
                    <div className="prose prose-sm dark:prose-invert max-w-none">
                      {note.article.split('\n').map((line, i) => (
                        <p key={i} className={line.trim() === '' ? 'h-4' : ''}>{line}</p>
                      ))}
                    </div>
                  ) : (
                    <p className="text-muted-foreground text-sm">暂无详细内容</p>
                  )}
                </CardContent>
              </Card>

              {/* Sidebar */}
              <div className="space-y-4">
                {/* Tags */}
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm flex items-center gap-2">
                      <Tag className="h-4 w-4" />标签
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {isEditing ? (
                      <div className="space-y-2">
                        <Input
                          value={editTags}
                          onChange={(e) => setEditTags(e.target.value)}
                          placeholder="标签用逗号分隔"
                        />
                        <p className="text-xs text-muted-foreground">多个标签用逗号分隔</p>
                      </div>
                    ) : note.tags && note.tags.length > 0 ? (
                      <div className="flex flex-wrap gap-2">
                        {note.tags.map((tag) => (
                          <Badge key={tag} variant="secondary">#{tag}</Badge>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-muted-foreground">暂无标签</p>
                    )}
                  </CardContent>
                </Card>

                {/* Compliance */}
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm flex items-center gap-2">
                      <Shield className="h-4 w-4" />合规状态
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">状态</span>
                        {complianceBadge(note.status)}
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">AI 味评分</span>
                        <span className="font-medium">{note.ai_flavor_score}/100</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </>
        )}
      </div>
    </AppLayout>
  );
}
