// 用户相关类型
export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  enterprise_id: string | null;
  avatar_url?: string;
  created_at: string;
  updated_at: string;
}

export type UserRole = 'platform_admin' | 'platform_operator' | 'tenant_admin' | 'tenant_user';

// 企业相关类型
export interface Enterprise {
  id: string;
  name: string;
  plan: PlanType;
  quota_monthly: number;
  quota_used: number;
  status: EnterpriseStatus;
  created_at: string;
  updated_at: string;
}

export type PlanType = 'free' | 'basic' | 'professional' | 'enterprise';
export type EnterpriseStatus = 'active' | 'suspended' | 'terminated';

export interface EnterpriseQuota {
  monthly_limit: number;
  used: number;
  reset_date: string;
}

// 知识库相关类型
export interface KnowledgeEntry {
  id: string;
  data_level?: DataLevel;
  platform_category?: PlatformCategory | null;
  enterprise_id?: string | null;
  category?: string | null;
  title: string;
  content: string;
  source?: string | null;
  source_url?: string | null;
  tags?: string[];
  metadata?: Record<string, unknown>;
  created_by?: string | null;
  updated_by?: string | null;
  created_at?: string;
  updated_at?: string;
}

export type DataLevel = 'platform' | 'tenant';
export type PlatformCategory = 'public' | 'industry' | 'template';

export interface KnowledgeStats {
  total_entries: number;
  by_category: Record<string, number>;
  recent_updates: KnowledgeEntry[];
}

// 创作任务相关类型
export interface CreateTask {
  id: string;
  platform: Platform;
  product: string;
  scene: string;
  style?: string;
  status: TaskStatus;
  enterprise_id: string;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export type Platform = 'xiaohongshu' | 'wechat' | 'douyin';
export type TaskStatus = 'pending' | 'processing' | 'awaiting_title_selection' | 'awaiting_p2_decision' | 'completed' | 'failed';

export type AgentStatusType = 'idle' | 'running' | 'completed' | 'failed';

// 笔记输出相关类型
export interface NoteOutput {
  id: string;
  task_id: string;
  platform: Platform;
  titles: TitleOption[];
  selected_title: string;
  article: string;
  paragraphs: Paragraph[];
  tags: string[];
  ai_flavor_score: number;
  compliance_report: ComplianceReport;
  created_at: string;
}

export interface TitleOption {
  title: string;
  strategy: string;
  score: number;
  reason: string;
}

export interface Paragraph {
  content: string;
  function: string;
}

// 合规相关类型
export interface ComplianceReport {
  status: ComplianceStatus;
  p0_issues: ComplianceIssue[];
  p1_issues: ComplianceIssue[];
  p2_issues: ComplianceIssue[];
  suggestions: string[];
}

export type ComplianceStatus = 'passed' | 'needs_revision' | 'failed' | 'has_issues';

export interface ComplianceIssue {
  type: string;
  description: string;
  location?: string;
  severity: 'p0' | 'p1' | 'p2';
}

// 素材包相关类型
export interface MaterialPack {
  brand: BrandInfo;
  product: ProductInfo;
  persona: PersonaInfo;
  scene: SceneInfo;
  compliance: ComplianceInfo;
}

export interface BrandInfo {
  name: string;
  tone: string[];
  taboos: string[];
}

export interface ProductInfo {
  name: string;
  selling_points: string[];
  ingredients: string[];
  evidence: Record<string, unknown>;
}

export interface PersonaInfo {
  profile: string;
  pain_points: string[];
  language_style: string;
}

export interface SceneInfo {
  description: string;
  usage_method: string;
}

export interface ComplianceInfo {
  rules: string[];
  forbidden_groups: string[];
}

// 数据分析相关类型
export interface AnalyticsData {
  summary: string;
  top_notes: TopNote[];
  topic_ranking: TopicRanking[];
  insights: string[];
  recommendations: string[];
}

export interface TopNote {
  title: string;
  metric: string;
  value: number;
}

export interface TopicRanking {
  topic: string;
  avg_engagement: number;
}

// API 响应类型
export interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  error: string | null;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// 认证相关类型
export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}
