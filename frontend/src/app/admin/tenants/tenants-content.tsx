'use client';

import { useState } from 'react';
import {
  useAdminTenants,
  useCreateAdminTenant,
  useUpdateAdminTenant,
  useDeleteAdminTenant,
  useUpdateTenantStatus,
  useUpdateTenantQuota,
  useAdminTenantUsers,
  useCreateTenantUser,
  useResetUserPassword,
  useUpdateUserStatus,
  useUpdateUser,
  useAdminTenantStats,
  useAdminTenantLogs,
  AdminTenant,
  AdminTenantUser,
} from '@/hooks/use-admin';
import { useToast } from '@/components/ui/toast';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogClose,
} from '@/components/ui/dialog';
import {
  Plus,
  Search,
  Building2,
  ChevronDown,
  ChevronRight,
  Edit2,
  Trash2,
  Users,
  BarChart3,
  FileText,
  KeyRound,
  UserPlus,
  Ban,
  CheckCircle,
  ShieldAlert,
} from 'lucide-react';

const PLANS = [
  { id: 'all', name: '全部版本' },
  { id: 'free', name: '免费版' },
  { id: 'basic', name: '基础版' },
  { id: 'professional', name: '专业版' },
  { id: 'enterprise', name: '企业版' },
];

const STATUSES = [
  { id: 'all', name: '全部状态' },
  { id: 'active', name: '正常' },
  { id: 'suspended', name: '已停用' },
  { id: 'terminated', name: '已终止' },
];

const INDUSTRIES = ['保健品', 'AI行业', '美妆护肤', '食品饮料', '教育', '其他'];

function planLabel(plan: string) {
  const map: Record<string, string> = { free: '免费版', basic: '基础版', professional: '专业版', enterprise: '企业版' };
  return map[plan] || plan;
}

function planColor(plan: string) {
  const map: Record<string, string> = { free: 'secondary', basic: 'secondary', professional: 'default', enterprise: 'default' };
  return map[plan] || 'secondary';
}

function statusLabel(status: string) {
  const map: Record<string, string> = { active: '正常', suspended: '已停用', terminated: '已终止' };
  return map[status] || status;
}

function statusColor(status: string) {
  const map: Record<string, string> = { active: 'default', suspended: 'destructive', terminated: 'destructive' };
  return map[status] || 'secondary';
}

function roleLabel(role: string) {
  const map: Record<string, string> = { tenant_admin: '管理员', tenant: '普通用户', tenant_user: '普通用户' };
  return map[role] || role;
}

export default function TenantsContent() {
  const { toast } = useToast();

  // Filters
  const [selectedPlan, setSelectedPlan] = useState('all');
  const [selectedStatus, setSelectedStatus] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const { data: tenantsData, isLoading } = useAdminTenants({
    plan: selectedPlan !== 'all' ? selectedPlan : undefined,
    status: selectedStatus !== 'all' ? selectedStatus : undefined,
    search: searchQuery || undefined,
    page,
    page_size: pageSize,
  });

  const createMutation = useCreateAdminTenant();
  const updateMutation = useUpdateAdminTenant();
  const deleteMutation = useDeleteAdminTenant();
  const statusMutation = useUpdateTenantStatus();
  const quotaMutation = useUpdateTenantQuota();

  // UI state
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editTenant, setEditTenant] = useState<AdminTenant | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [quotaDialogTenant, setQuotaDialogTenant] = useState<AdminTenant | null>(null);
  const [quotaValue, setQuotaValue] = useState('');

  // Create form state
  const [createForm, setCreateForm] = useState({
    name: '', industry: '', plan_type: 'free', quota_monthly: '100',
    admin_email: '', admin_password: '',
    contact_name: '', contact_email: '', contact_phone: '',
  });

  // Edit form state
  const [editForm, setEditForm] = useState({
    name: '', industry: '', plan_type: '', quota_monthly: '',
    status: '', contact_name: '', contact_email: '', contact_phone: '', expire_at: '',
  });

  const tenants = tenantsData?.items || [];
  const total = tenantsData?.total || 0;
  const totalPages = Math.ceil(total / pageSize);

  function handleCreate() {
    if (!createForm.name || !createForm.admin_email) {
      toast('error', '请填写企业名称和管理员邮箱');
      return;
    }
    createMutation.mutate({
      name: createForm.name,
      industry: createForm.industry || undefined,
      plan_type: createForm.plan_type,
      quota_monthly: parseInt(createForm.quota_monthly) || 100,
      admin_email: createForm.admin_email,
      admin_password: createForm.admin_password || undefined,
      contact_name: createForm.contact_name || undefined,
      contact_email: createForm.contact_email || undefined,
      contact_phone: createForm.contact_phone || undefined,
    }, {
      onSuccess: (data) => {
        const d = data as Record<string, unknown>;
        const pwd = d.admin_password as string;
        toast('success', `企业创建成功${pwd ? `，管理员密码: ${pwd}` : ''}`);
        setCreateForm({ name: '', industry: '', plan_type: 'free', quota_monthly: '100', admin_email: '', admin_password: '', contact_name: '', contact_email: '', contact_phone: '' });
        setShowCreateForm(false);
      },
      onError: () => toast('error', '创建企业失败'),
    });
  }

  function openEdit(tenant: AdminTenant) {
    setEditForm({
      name: tenant.name,
      industry: tenant.industry || '',
      plan_type: tenant.plan_type,
      quota_monthly: String(tenant.quota_monthly),
      status: tenant.status,
      contact_name: tenant.contact_name || '',
      contact_email: tenant.contact_email || '',
      contact_phone: tenant.contact_phone || '',
      expire_at: tenant.expire_at ? tenant.expire_at.slice(0, 16) : '',
    });
    setEditTenant(tenant);
  }

  function handleEdit() {
    if (!editTenant) return;
    updateMutation.mutate({
      id: editTenant.id,
      data: {
        name: editForm.name,
        industry: editForm.industry || undefined,
        plan_type: editForm.plan_type,
        quota_monthly: parseInt(editForm.quota_monthly) || undefined,
        status: editForm.status || undefined,
        contact_name: editForm.contact_name || undefined,
        contact_email: editForm.contact_email || undefined,
        contact_phone: editForm.contact_phone || undefined,
        expire_at: editForm.expire_at || undefined,
      },
    }, {
      onSuccess: () => {
        toast('success', '企业信息已更新');
        setEditTenant(null);
      },
      onError: () => toast('error', '更新失败'),
    });
  }

  function handleDelete() {
    if (!deleteId) return;
    deleteMutation.mutate(deleteId, {
      onSuccess: () => {
        toast('success', '企业已停用');
        setDeleteId(null);
        setExpandedId(null);
      },
      onError: () => toast('error', '操作失败'),
    });
  }

  function handleStatusChange(id: string, newStatus: string) {
    statusMutation.mutate({ id, status: newStatus }, {
      onSuccess: () => toast('success', `状态已更新为${statusLabel(newStatus)}`),
      onError: () => toast('error', '状态更新失败'),
    });
  }

  function handleQuotaUpdate() {
    if (!quotaDialogTenant) return;
    const val = parseInt(quotaValue);
    if (isNaN(val) || val < 0) {
      toast('error', '请输入有效的额度值');
      return;
    }
    quotaMutation.mutate({ id: quotaDialogTenant.id, quota_monthly: val }, {
      onSuccess: () => {
        toast('success', '额度已调整');
        setQuotaDialogTenant(null);
        setQuotaValue('');
      },
      onError: () => toast('error', '调整失败'),
    });
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold">租户管理</h1>
          <p className="text-muted-foreground">管理企业租户、用户和额度</p>
        </div>
        <Button size="sm" className="bg-amber-600 hover:bg-amber-700" onClick={() => setShowCreateForm(true)}>
          <Plus className="mr-2 h-4 w-4" />
          新增企业
        </Button>
      </div>

      {/* Stats */}
      <div className="grid gap-4 grid-cols-2 lg:grid-cols-4">
        <Card><CardContent className="p-4"><p className="text-sm text-muted-foreground">企业总数</p><p className="text-2xl font-bold">{total}</p></CardContent></Card>
        <Card><CardContent className="p-4"><p className="text-sm text-muted-foreground">正常</p><p className="text-2xl font-bold text-green-500">{tenants.filter(t => t.status === 'active').length}</p></CardContent></Card>
        <Card><CardContent className="p-4"><p className="text-sm text-muted-foreground">已停用</p><p className="text-2xl font-bold text-amber-500">{tenants.filter(t => t.status === 'suspended').length}</p></CardContent></Card>
        <Card><CardContent className="p-4"><p className="text-sm text-muted-foreground">已终止</p><p className="text-2xl font-bold text-destructive">{tenants.filter(t => t.status === 'terminated').length}</p></CardContent></Card>
      </div>

      {/* Create form */}
      {showCreateForm && (
        <Card className="border-amber-500/30">
          <CardHeader><CardTitle className="text-base">新增企业</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="text-sm font-medium">企业名称 *</label>
                <input type="text" value={createForm.name} onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
                  className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm" placeholder="输入企业名称" />
              </div>
              <div>
                <label className="text-sm font-medium">行业</label>
                <select value={createForm.industry} onChange={(e) => setCreateForm({ ...createForm, industry: e.target.value })}
                  className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
                  <option value="">请选择行业</option>
                  {INDUSTRIES.map(i => <option key={i} value={i}>{i}</option>)}
                </select>
              </div>
              <div>
                <label className="text-sm font-medium">版本</label>
                <select value={createForm.plan_type} onChange={(e) => setCreateForm({ ...createForm, plan_type: e.target.value })}
                  className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
                  {PLANS.filter(p => p.id !== 'all').map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                </select>
              </div>
              <div>
                <label className="text-sm font-medium">月度额度</label>
                <input type="number" value={createForm.quota_monthly} onChange={(e) => setCreateForm({ ...createForm, quota_monthly: e.target.value })}
                  className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm" min="0" />
              </div>
            </div>
            <div className="border-t pt-4">
              <p className="text-sm font-medium mb-3">管理员账号</p>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="text-sm font-medium">管理员邮箱 *</label>
                  <input type="email" value={createForm.admin_email} onChange={(e) => setCreateForm({ ...createForm, admin_email: e.target.value })}
                    className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm" placeholder="admin@example.com" />
                </div>
                <div>
                  <label className="text-sm font-medium">密码（留空自动生成）</label>
                  <input type="text" value={createForm.admin_password} onChange={(e) => setCreateForm({ ...createForm, admin_password: e.target.value })}
                    className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm" placeholder="留空则自动生成" />
                </div>
              </div>
            </div>
            <div className="border-t pt-4">
              <p className="text-sm font-medium mb-3">联系方式（选填）</p>
              <div className="grid gap-4 sm:grid-cols-3">
                <div>
                  <label className="text-sm font-medium">联系人</label>
                  <input type="text" value={createForm.contact_name} onChange={(e) => setCreateForm({ ...createForm, contact_name: e.target.value })}
                    className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm" />
                </div>
                <div>
                  <label className="text-sm font-medium">联系邮箱</label>
                  <input type="email" value={createForm.contact_email} onChange={(e) => setCreateForm({ ...createForm, contact_email: e.target.value })}
                    className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm" />
                </div>
                <div>
                  <label className="text-sm font-medium">联系电话</label>
                  <input type="text" value={createForm.contact_phone} onChange={(e) => setCreateForm({ ...createForm, contact_phone: e.target.value })}
                    className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm" />
                </div>
              </div>
            </div>
            <div className="flex gap-2 justify-end">
              <Button variant="outline" size="sm" onClick={() => setShowCreateForm(false)}>取消</Button>
              <Button size="sm" className="bg-amber-600 hover:bg-amber-700" onClick={handleCreate} disabled={createMutation.isPending}>
                {createMutation.isPending ? '创建中...' : '创建企业'}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
        <div className="flex gap-2 flex-wrap">
          {PLANS.map((plan) => (
            <button key={plan.id} onClick={() => { setSelectedPlan(plan.id); setPage(1); }}
              className={cn('px-3 py-1.5 rounded-md text-sm transition-colors',
                selectedPlan === plan.id ? 'bg-amber-500/20 text-amber-100 font-medium' : 'text-muted-foreground hover:bg-muted')}>
              {plan.name}
            </button>
          ))}
        </div>
        <div className="flex gap-2 flex-wrap">
          {STATUSES.map((s) => (
            <button key={s.id} onClick={() => { setSelectedStatus(s.id); setPage(1); }}
              className={cn('px-3 py-1.5 rounded-md text-sm transition-colors',
                selectedStatus === s.id ? 'bg-amber-500/20 text-amber-100 font-medium' : 'text-muted-foreground hover:bg-muted')}>
              {s.name}
            </button>
          ))}
        </div>
        <div className="relative sm:ml-auto">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input type="text" placeholder="搜索企业名..." value={searchQuery}
            onChange={(e) => { setSearchQuery(e.target.value); setPage(1); }}
            className="h-9 w-64 rounded-md border border-input bg-background pl-9 pr-3 text-sm" />
        </div>
      </div>

      {/* Tenant list */}
      {isLoading ? (
        <div className="flex h-32 items-center justify-center">
          <div className="h-6 w-6 animate-spin rounded-full border-4 border-amber-500 border-t-transparent" />
        </div>
      ) : tenants.length === 0 ? (
        <Card><CardContent className="p-8 text-center text-muted-foreground">暂无企业数据</CardContent></Card>
      ) : (
        <Card>
          <CardContent className="p-0">
            <div className="divide-y divide-border">
              {/* Table header */}
              <div className="hidden lg:grid lg:grid-cols-[2fr_1fr_1fr_1fr_1fr_1fr_80px] gap-4 px-4 py-3 text-sm font-medium text-muted-foreground">
                <span>企业名称</span>
                <span>版本</span>
                <span>状态</span>
                <span>额度使用</span>
                <span>用户数</span>
                <span>创建时间</span>
                <span className="text-right">操作</span>
              </div>
              {/* Rows */}
              {tenants.map((tenant) => (
                <TenantRow
                  key={tenant.id}
                  tenant={tenant}
                  expanded={expandedId === tenant.id}
                  onToggle={() => setExpandedId(expandedId === tenant.id ? null : tenant.id)}
                  onEdit={() => openEdit(tenant)}
                  onDelete={() => setDeleteId(tenant.id)}
                  onStatusChange={(s) => handleStatusChange(tenant.id, s)}
                  onQuota={() => { setQuotaDialogTenant(tenant); setQuotaValue(String(tenant.quota_monthly)); }}
                />
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">共 {total} 家企业</p>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>上一页</Button>
            <span className="flex items-center px-3 text-sm">{page} / {totalPages}</span>
            <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage(page + 1)}>下一页</Button>
          </div>
        </div>
      )}

      {/* Edit dialog */}
      <Dialog open={editTenant !== null} onOpenChange={(open) => { if (!open) setEditTenant(null); }}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>编辑企业</DialogTitle>
            <DialogDescription>修改企业信息、版本和状态</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="text-sm font-medium">企业名称</label>
                <input type="text" value={editForm.name} onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                  className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="text-sm font-medium">行业</label>
                <select value={editForm.industry} onChange={(e) => setEditForm({ ...editForm, industry: e.target.value })}
                  className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
                  <option value="">请选择</option>
                  {INDUSTRIES.map(i => <option key={i} value={i}>{i}</option>)}
                </select>
              </div>
              <div>
                <label className="text-sm font-medium">版本</label>
                <select value={editForm.plan_type} onChange={(e) => setEditForm({ ...editForm, plan_type: e.target.value })}
                  className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
                  {PLANS.filter(p => p.id !== 'all').map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                </select>
              </div>
              <div>
                <label className="text-sm font-medium">月度额度</label>
                <input type="number" value={editForm.quota_monthly} onChange={(e) => setEditForm({ ...editForm, quota_monthly: e.target.value })}
                  className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm" min="0" />
              </div>
              <div>
                <label className="text-sm font-medium">状态</label>
                <select value={editForm.status} onChange={(e) => setEditForm({ ...editForm, status: e.target.value })}
                  className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
                  {STATUSES.filter(s => s.id !== 'all').map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                </select>
              </div>
              <div>
                <label className="text-sm font-medium">到期时间</label>
                <input type="datetime-local" value={editForm.expire_at} onChange={(e) => setEditForm({ ...editForm, expire_at: e.target.value })}
                  className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm" />
              </div>
            </div>
            <div className="border-t pt-4">
              <p className="text-sm font-medium mb-3">联系方式</p>
              <div className="grid gap-4 sm:grid-cols-3">
                <div>
                  <label className="text-sm font-medium">联系人</label>
                  <input type="text" value={editForm.contact_name} onChange={(e) => setEditForm({ ...editForm, contact_name: e.target.value })}
                    className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm" />
                </div>
                <div>
                  <label className="text-sm font-medium">联系邮箱</label>
                  <input type="email" value={editForm.contact_email} onChange={(e) => setEditForm({ ...editForm, contact_email: e.target.value })}
                    className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm" />
                </div>
                <div>
                  <label className="text-sm font-medium">联系电话</label>
                  <input type="text" value={editForm.contact_phone} onChange={(e) => setEditForm({ ...editForm, contact_phone: e.target.value })}
                    className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm" />
                </div>
              </div>
            </div>
          </div>
          <DialogFooter>
            <DialogClose render={<Button variant="outline" size="sm" />}>取消</DialogClose>
            <Button size="sm" className="bg-amber-600 hover:bg-amber-700" onClick={handleEdit} disabled={updateMutation.isPending}>
              {updateMutation.isPending ? '保存中...' : '保存'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete dialog */}
      <Dialog open={deleteId !== null} onOpenChange={(open) => { if (!open) setDeleteId(null); }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>确认停用</DialogTitle>
            <DialogDescription>停用后该企业所有用户将无法登录，确定继续吗？</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <DialogClose render={<Button variant="outline" size="sm" />}>取消</DialogClose>
            <Button size="sm" className="bg-destructive hover:bg-destructive/90 text-destructive-foreground" onClick={handleDelete}>
              确认停用
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Quota dialog */}
      <Dialog open={quotaDialogTenant !== null} onOpenChange={(open) => { if (!open) setQuotaDialogTenant(null); }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>调整额度</DialogTitle>
            <DialogDescription>调整 {quotaDialogTenant?.name} 的月度创作额度</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">当前额度：{quotaDialogTenant?.quota_monthly}</label>
              <p className="text-xs text-muted-foreground">本月已使用：{quotaDialogTenant?.quota_used}</p>
            </div>
            <div>
              <label className="text-sm font-medium">新额度</label>
              <input type="number" value={quotaValue} onChange={(e) => setQuotaValue(e.target.value)}
                className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm" min="0" />
            </div>
          </div>
          <DialogFooter>
            <DialogClose render={<Button variant="outline" size="sm" />}>取消</DialogClose>
            <Button size="sm" className="bg-amber-600 hover:bg-amber-700" onClick={handleQuotaUpdate}>
              确认调整
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// ── Tenant Row Component ──────────────────────────────────

function TenantRow({
  tenant, expanded, onToggle, onEdit, onDelete, onStatusChange, onQuota,
}: {
  tenant: AdminTenant;
  expanded: boolean;
  onToggle: () => void;
  onEdit: () => void;
  onDelete: () => void;
  onStatusChange: (status: string) => void;
  onQuota: () => void;
}) {
  return (
    <div>
      {/* Main row */}
      <div
        className="grid grid-cols-1 lg:grid-cols-[2fr_1fr_1fr_1fr_1fr_1fr_80px] gap-2 lg:gap-4 px-4 py-3 text-sm items-center hover:bg-muted/50 cursor-pointer"
        onClick={onToggle}
      >
        <div className="flex items-center gap-2">
          {expanded ? <ChevronDown className="h-4 w-4 text-muted-foreground" /> : <ChevronRight className="h-4 w-4 text-muted-foreground" />}
          <Building2 className="h-4 w-4 text-amber-500" />
          <span className="font-medium">{tenant.name}</span>
        </div>
        <div className="flex items-center gap-2 lg:block">
          <Badge variant={planColor(tenant.plan_type) as 'secondary' | 'default'} className="text-xs">{planLabel(tenant.plan_type)}</Badge>
        </div>
        <div className="flex items-center gap-2 lg:block">
          <Badge variant={statusColor(tenant.status) as 'default' | 'destructive'} className="text-xs">{statusLabel(tenant.status)}</Badge>
        </div>
        <div className="text-muted-foreground">
          {tenant.quota_used} / {tenant.quota_monthly}
        </div>
        <div className="text-muted-foreground">{tenant.user_count}</div>
        <div className="text-muted-foreground">{tenant.created_at?.slice(0, 10)}</div>
        <div className="flex gap-1 justify-end" onClick={(e) => e.stopPropagation()}>
          <Button variant="ghost" size="sm" className="h-7 px-2" onClick={onEdit}>
            <Edit2 className="h-3 w-3" />
          </Button>
          {tenant.status === 'active' ? (
            <Button variant="ghost" size="sm" className="h-7 px-2 text-amber-500" onClick={() => onStatusChange('suspended')}>
              <Ban className="h-3 w-3" />
            </Button>
          ) : (
            <Button variant="ghost" size="sm" className="h-7 px-2 text-green-500" onClick={() => onStatusChange('active')}>
              <CheckCircle className="h-3 w-3" />
            </Button>
          )}
        </div>
      </div>

      {/* Expanded detail */}
      {expanded && <TenantDetail tenant={tenant} onEdit={onEdit} onDelete={onDelete} onQuota={onQuota} onStatusChange={onStatusChange} />}
    </div>
  );
}

// ── Tenant Detail Component ───────────────────────────────

function TenantDetail({
  tenant, onEdit, onDelete, onQuota, onStatusChange,
}: {
  tenant: AdminTenant;
  onEdit: () => void;
  onDelete: () => void;
  onQuota: () => void;
  onStatusChange: (s: string) => void;
}) {
  const [activeTab, setActiveTab] = useState<'info' | 'users' | 'stats' | 'logs'>('info');

  return (
    <div className="border-t bg-muted/30 px-4 py-4 space-y-4" onClick={(e) => e.stopPropagation()}>
      {/* Tabs */}
      <div className="flex gap-2">
        {[
          { id: 'info' as const, label: '基本信息', icon: Building2 },
          { id: 'users' as const, label: '用户管理', icon: Users },
          { id: 'stats' as const, label: '使用统计', icon: BarChart3 },
          { id: 'logs' as const, label: '操作日志', icon: FileText },
        ].map((tab) => {
          const Icon = tab.icon;
          return (
            <button key={tab.id} onClick={() => setActiveTab(tab.id)}
              className={cn('flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm transition-colors',
                activeTab === tab.id ? 'bg-amber-500/20 text-amber-100 font-medium' : 'text-muted-foreground hover:bg-muted')}>
              <Icon className="h-4 w-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {activeTab === 'info' && <TenantInfoTab tenant={tenant} onEdit={onEdit} onDelete={onDelete} onQuota={onQuota} onStatusChange={onStatusChange} />}
      {activeTab === 'users' && <TenantUsersTab tenantId={tenant.id} />}
      {activeTab === 'stats' && <TenantStatsTab tenantId={tenant.id} />}
      {activeTab === 'logs' && <TenantLogsTab tenantId={tenant.id} />}
    </div>
  );
}

// ── Info Tab ──────────────────────────────────────────────

function TenantInfoTab({
  tenant, onEdit, onDelete, onQuota, onStatusChange,
}: {
  tenant: AdminTenant;
  onEdit: () => void;
  onDelete: () => void;
  onQuota: () => void;
  onStatusChange: (s: string) => void;
}) {
  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <InfoItem label="企业ID" value={tenant.id} />
        <InfoItem label="行业" value={tenant.industry || '未设置'} />
        <InfoItem label="联系人" value={tenant.contact_name || '未设置'} />
        <InfoItem label="联系邮箱" value={tenant.contact_email || '未设置'} />
        <InfoItem label="联系电话" value={tenant.contact_phone || '未设置'} />
        <InfoItem label="到期时间" value={tenant.expire_at?.slice(0, 10) || '未设置'} />
        <InfoItem label="更新时间" value={tenant.updated_at?.slice(0, 16)?.replace('T', ' ') || ''} />
      </div>
      <div className="flex gap-2 flex-wrap">
        <Button variant="outline" size="sm" onClick={onEdit}>
          <Edit2 className="mr-1.5 h-3 w-3" /> 编辑信息
        </Button>
        <Button variant="outline" size="sm" onClick={onQuota}>
          <BarChart3 className="mr-1.5 h-3 w-3" /> 调整额度
        </Button>
        {tenant.status === 'active' ? (
          <Button variant="outline" size="sm" className="text-amber-500" onClick={() => onStatusChange('suspended')}>
            <Ban className="mr-1.5 h-3 w-3" /> 停用企业
          </Button>
        ) : tenant.status === 'suspended' ? (
          <Button variant="outline" size="sm" className="text-green-500" onClick={() => onStatusChange('active')}>
            <CheckCircle className="mr-1.5 h-3 w-3" /> 启用企业
          </Button>
        ) : null}
        {tenant.status !== 'terminated' && (
          <Button variant="outline" size="sm" className="text-destructive" onClick={onDelete}>
            <Trash2 className="mr-1.5 h-3 w-3" /> 终止企业
          </Button>
        )}
      </div>
    </div>
  );
}

function InfoItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-sm">{value}</p>
    </div>
  );
}

// ── Users Tab ─────────────────────────────────────────────

function TenantUsersTab({ tenantId }: { tenantId: string }) {
  const { toast } = useToast();
  const { data: users, isLoading } = useAdminTenantUsers(tenantId);
  const createUserMutation = useCreateTenantUser();
  const resetPwdMutation = useResetUserPassword();
  const updateUserStatusMutation = useUpdateUserStatus();
  const updateUserMutation = useUpdateUser();

  const [showAddUser, setShowAddUser] = useState(false);
  const [addUserForm, setAddUserForm] = useState({ email: '', name: '', password: '', role: 'tenant' });
  const [resetPwdUser, setResetPwdUser] = useState<AdminTenantUser | null>(null);
  const [editUserRole, setEditUserRole] = useState<AdminTenantUser | null>(null);
  const [newRole, setNewRole] = useState('');

  function handleAddUser() {
    if (!addUserForm.email || !addUserForm.name) {
      toast('error', '请填写邮箱和姓名');
      return;
    }
    createUserMutation.mutate({
      tenantId,
      data: {
        email: addUserForm.email,
        name: addUserForm.name,
        password: addUserForm.password || undefined,
        role: addUserForm.role,
      },
    }, {
      onSuccess: (data) => {
        const d = data as Record<string, unknown>;
        const pwd = d.password as string;
        toast('success', `用户创建成功${pwd ? `，密码: ${pwd}` : ''}`);
        setAddUserForm({ email: '', name: '', password: '', role: 'tenant' });
        setShowAddUser(false);
      },
      onError: () => toast('error', '创建用户失败'),
    });
  }

  function handleResetPassword() {
    if (!resetPwdUser) return;
    resetPwdMutation.mutate({ userId: resetPwdUser.id }, {
      onSuccess: (data) => {
        const d = data as Record<string, unknown>;
        toast('success', `密码已重置，新密码: ${d.new_password}`);
        setResetPwdUser(null);
      },
      onError: () => toast('error', '重置密码失败'),
    });
  }

  function handleToggleStatus(user: AdminTenantUser) {
    const newStatus = user.status === 'active' ? 'disabled' : 'active';
    updateUserStatusMutation.mutate({ userId: user.id, status: newStatus }, {
      onSuccess: () => toast('success', `用户已${newStatus === 'active' ? '启用' : '禁用'}`),
      onError: () => toast('error', '操作失败'),
    });
  }

  function handleEditRole() {
    if (!editUserRole) return;
    updateUserMutation.mutate({ userId: editUserRole.id, data: { role: newRole } }, {
      onSuccess: () => {
        toast('success', '角色已更新');
        setEditUserRole(null);
      },
      onError: () => toast('error', '更新失败'),
    });
  }

  if (isLoading) return <div className="text-sm text-muted-foreground">加载中...</div>;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">共 {users?.length || 0} 个用户</p>
        <Button size="sm" className="bg-amber-600 hover:bg-amber-700" onClick={() => setShowAddUser(true)}>
          <UserPlus className="mr-1.5 h-3 w-3" /> 新增用户
        </Button>
      </div>

      {/* Add user form */}
      {showAddUser && (
        <Card className="border-amber-500/30">
          <CardContent className="p-4 space-y-3">
            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <label className="text-sm font-medium">邮箱 *</label>
                <input type="email" value={addUserForm.email} onChange={(e) => setAddUserForm({ ...addUserForm, email: e.target.value })}
                  className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="text-sm font-medium">姓名 *</label>
                <input type="text" value={addUserForm.name} onChange={(e) => setAddUserForm({ ...addUserForm, name: e.target.value })}
                  className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="text-sm font-medium">密码（留空自动生成）</label>
                <input type="text" value={addUserForm.password} onChange={(e) => setAddUserForm({ ...addUserForm, password: e.target.value })}
                  className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="text-sm font-medium">角色</label>
                <select value={addUserForm.role} onChange={(e) => setAddUserForm({ ...addUserForm, role: e.target.value })}
                  className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
                  <option value="tenant">普通用户</option>
                  <option value="tenant_admin">管理员</option>
                </select>
              </div>
            </div>
            <div className="flex gap-2 justify-end">
              <Button variant="outline" size="sm" onClick={() => setShowAddUser(false)}>取消</Button>
              <Button size="sm" className="bg-amber-600 hover:bg-amber-700" onClick={handleAddUser} disabled={createUserMutation.isPending}>
                {createUserMutation.isPending ? '创建中...' : '创建'}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Users list */}
      <div className="divide-y divide-border rounded-md border">
        <div className="grid grid-cols-[1fr_1fr_100px_100px_120px] gap-4 px-4 py-2 text-xs font-medium text-muted-foreground">
          <span>姓名</span>
          <span>邮箱</span>
          <span>角色</span>
          <span>状态</span>
          <span className="text-right">操作</span>
        </div>
        {(users || []).map((u) => (
          <div key={u.id} className="grid grid-cols-[1fr_1fr_100px_100px_120px] gap-4 px-4 py-2 text-sm items-center">
            <span>{u.name}</span>
            <span className="text-muted-foreground truncate">{u.email}</span>
            <span>
              <Badge variant="secondary" className="text-xs cursor-pointer" onClick={() => { setEditUserRole(u); setNewRole(u.role); }}>
                {roleLabel(u.role)}
              </Badge>
            </span>
            <span>
              <Badge variant={u.status === 'active' ? 'default' : 'destructive'} className="text-xs">
                {u.status === 'active' ? '正常' : '已禁用'}
              </Badge>
            </span>
            <div className="flex gap-1 justify-end">
              <Button variant="ghost" size="sm" className="h-7 px-2" title="重置密码" onClick={() => setResetPwdUser(u)}>
                <KeyRound className="h-3 w-3" />
              </Button>
              <Button variant="ghost" size="sm" className="h-7 px-2" title={u.status === 'active' ? '禁用' : '启用'} onClick={() => handleToggleStatus(u)}>
                {u.status === 'active' ? <Ban className="h-3 w-3 text-amber-500" /> : <CheckCircle className="h-3 w-3 text-green-500" />}
              </Button>
            </div>
          </div>
        ))}
      </div>

      {/* Reset password dialog */}
      <Dialog open={resetPwdUser !== null} onOpenChange={(open) => { if (!open) setResetPwdUser(null); }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>重置密码</DialogTitle>
            <DialogDescription>确定要重置 {resetPwdUser?.name} 的密码吗？系统将自动生成新密码。</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <DialogClose render={<Button variant="outline" size="sm" />}>取消</DialogClose>
            <Button size="sm" className="bg-amber-600 hover:bg-amber-700" onClick={handleResetPassword}>
              确认重置
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit role dialog */}
      <Dialog open={editUserRole !== null} onOpenChange={(open) => { if (!open) setEditUserRole(null); }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>修改角色</DialogTitle>
            <DialogDescription>修改 {editUserRole?.name} 的角色</DialogDescription>
          </DialogHeader>
          <div>
            <select value={newRole} onChange={(e) => setNewRole(e.target.value)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
              <option value="tenant">普通用户</option>
              <option value="tenant_admin">管理员</option>
            </select>
          </div>
          <DialogFooter>
            <DialogClose render={<Button variant="outline" size="sm" />}>取消</DialogClose>
            <Button size="sm" className="bg-amber-600 hover:bg-amber-700" onClick={handleEditRole}>确认</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// ── Stats Tab ─────────────────────────────────────────────

function TenantStatsTab({ tenantId }: { tenantId: string }) {
  const { data: stats, isLoading } = useAdminTenantStats(tenantId);

  if (isLoading) return <div className="text-sm text-muted-foreground">加载中...</div>;
  if (!stats) return <div className="text-sm text-muted-foreground">暂无统计数据</div>;

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <Card>
        <CardContent className="p-4">
          <p className="text-sm text-muted-foreground">本月创作</p>
          <p className="text-2xl font-bold">{stats.monthly_notes}</p>
          <p className="text-xs text-muted-foreground">篇</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-4">
          <p className="text-sm text-muted-foreground">AI味均分</p>
          <p className="text-2xl font-bold">{stats.monthly_avg_ai_score}</p>
          <p className="text-xs text-muted-foreground">/ 100</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-4">
          <p className="text-sm text-muted-foreground">合规率</p>
          <p className="text-2xl font-bold">{stats.monthly_compliance_rate}%</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-4">
          <p className="text-sm text-muted-foreground">累计创作</p>
          <p className="text-2xl font-bold">{stats.total_notes}</p>
          <p className="text-xs text-muted-foreground">篇</p>
        </CardContent>
      </Card>
    </div>
  );
}

// ── Logs Tab ──────────────────────────────────────────────

function TenantLogsTab({ tenantId }: { tenantId: string }) {
  const [logPage, setLogPage] = useState(1);
  const { data: logsData, isLoading } = useAdminTenantLogs(tenantId, logPage);
  const logs = logsData?.items || [];
  const totalLogs = logsData?.total || 0;
  const logTotalPages = Math.ceil(totalLogs / 20);

  if (isLoading) return <div className="text-sm text-muted-foreground">加载中...</div>;

  return (
    <div className="space-y-4">
      {logs.length === 0 ? (
        <p className="text-sm text-muted-foreground">暂无操作日志</p>
      ) : (
        <>
          <div className="divide-y divide-border rounded-md border text-sm">
            {logs.map((log) => (
              <div key={log.id} className="px-4 py-2 flex items-center gap-4">
                <Badge variant="secondary" className="text-xs shrink-0">{log.action}</Badge>
                <span className="text-muted-foreground">{log.resource_type}</span>
                <span className="text-muted-foreground truncate flex-1">{log.user_name || log.user_id}</span>
                <span className="text-xs text-muted-foreground shrink-0">{log.created_at?.slice(0, 16)?.replace('T', ' ')}</span>
              </div>
            ))}
          </div>
          {logTotalPages > 1 && (
            <div className="flex items-center justify-between">
              <p className="text-xs text-muted-foreground">共 {totalLogs} 条</p>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" disabled={logPage <= 1} onClick={() => setLogPage(logPage - 1)}>上一页</Button>
                <span className="flex items-center px-2 text-xs">{logPage}/{logTotalPages}</span>
                <Button variant="outline" size="sm" disabled={logPage >= logTotalPages} onClick={() => setLogPage(logPage + 1)}>下一页</Button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
