import { create } from 'zustand';
import { Platform, TaskStatus, MaterialPack, TitleOption, NoteOutput, ComplianceReport } from '@/types';

export type CreateStep = 'input' | 'material' | 'title' | 'article' | 'tags' | 'output';

export interface StepStatus {
  step: CreateStep;
  label: string;
  status: 'pending' | 'active' | 'completed' | 'error';
}

export type AgentStatusType = 'idle' | 'running' | 'completed' | 'failed';

export interface AgentState {
  name: string;
  status: AgentStatusType;
  message?: string;
}

interface CreateStore {
  // 流程状态
  platform: Platform | null;
  currentStep: CreateStep;
  steps: StepStatus[];
  taskStatus: TaskStatus;
  taskId: string | null;

  // Step 1 - 输入需求
  brand: string;
  product: string;
  intent: string;
  scene: string;
  style: string;

  // Step 2 - 素材确认
  materialPack: MaterialPack | null;
  materialMissing: string[];

  // Step 3 - 标题选择
  titleOptions: TitleOption[];
  selectedTitles: string[];
  titleRetries: number;
  maxTitleRetries: number;
  customTitle: string;

  // Step 4 - 正文创作
  article: string;
  aiScore: number;
  aiScoreDetails: Record<string, number>;
  articleRetries: number;
  maxArticleRetries: number;
  isEditing: boolean;

  // Step 5 - 标签与合规
  tags: string[];
  customTag: string;
  complianceReport: ComplianceReport | null;
  complianceOverrides: Record<string, 'pass' | 'modify' | 'delete'>;

  // Step 6 - 输出
  output: NoteOutput | null;

  // Agent 状态
  agents: AgentState[];
  isProcessing: boolean;

  // 错误信息
  error: string | null;

  // Actions
  setPlatform: (platform: Platform) => void;
  setBrand: (brand: string) => void;
  setProduct: (product: string) => void;
  setIntent: (intent: string) => void;
  setScene: (scene: string) => void;
  setStyle: (style: string) => void;
  setCurrentStep: (step: CreateStep) => void;
  setStepStatus: (step: CreateStep, status: StepStatus['status']) => void;
  setMaterialPack: (pack: MaterialPack) => void;
  setMaterialMissing: (missing: string[]) => void;
  setTitleOptions: (options: TitleOption[]) => void;
  toggleTitle: (title: string) => void;
  setCustomTitle: (title: string) => void;
  setTitleRetries: (count: number) => void;
  setArticle: (article: string) => void;
  setAiScore: (score: number) => void;
  setAiScoreDetails: (details: Record<string, number>) => void;
  setArticleRetries: (count: number) => void;
  setIsEditing: (editing: boolean) => void;
  setTags: (tags: string[]) => void;
  toggleTag: (tag: string) => void;
  addCustomTag: (tag: string) => void;
  removeTag: (tag: string) => void;
  setCustomTag: (tag: string) => void;
  setComplianceReport: (report: ComplianceReport) => void;
  setComplianceOverride: (issueType: string, action: 'pass' | 'modify' | 'delete') => void;
  setOutput: (output: NoteOutput) => void;
  setTaskId: (id: string) => void;
  setTaskStatus: (status: TaskStatus) => void;
  setAgents: (agents: AgentState[]) => void;
  updateAgent: (name: string, status: AgentStatusType, message?: string) => void;
  setIsProcessing: (processing: boolean) => void;
  setError: (error: string | null) => void;
  goToStep: (step: CreateStep) => void;
  nextStep: () => void;
  prevStep: () => void;
  startCreation: () => Promise<void>;
  reset: () => void;
}

const STEP_ORDER: CreateStep[] = ['input', 'material', 'title', 'article', 'tags', 'output'];

const INITIAL_STEPS: StepStatus[] = [
  { step: 'input', label: '输入需求', status: 'active' },
  { step: 'material', label: '素材确认', status: 'pending' },
  { step: 'title', label: '标题选择', status: 'pending' },
  { step: 'article', label: '正文创作', status: 'pending' },
  { step: 'tags', label: '标签与合规', status: 'pending' },
  { step: 'output', label: '完成交付', status: 'pending' },
];

const INITIAL_STATE = {
  platform: null as Platform | null,
  currentStep: 'input' as CreateStep,
  steps: INITIAL_STEPS,
  taskStatus: 'pending' as TaskStatus,
  taskId: null as string | null,

  brand: '',
  product: '',
  intent: '',
  scene: '',
  style: '',

  materialPack: null as MaterialPack | null,
  materialMissing: [] as string[],

  titleOptions: [] as TitleOption[],
  selectedTitles: [] as string[],
  titleRetries: 0,
  maxTitleRetries: 2,
  customTitle: '',

  article: '',
  aiScore: 0,
  aiScoreDetails: {} as Record<string, number>,
  articleRetries: 0,
  maxArticleRetries: 2,
  isEditing: false,

  tags: [] as string[],
  customTag: '',
  complianceReport: null as ComplianceReport | null,
  complianceOverrides: {} as Record<string, 'pass' | 'modify' | 'delete'>,

  output: null as NoteOutput | null,

  agents: [] as AgentState[],
  isProcessing: false,

  error: null as string | null,
};

export const useCreateStore = create<CreateStore>((set, get) => ({
  ...INITIAL_STATE,

  setPlatform: (platform) => set({ platform }),
  setBrand: (brand) => set({ brand }),
  setProduct: (product) => set({ product }),
  setIntent: (intent) => set({ intent }),
  setScene: (scene) => set({ scene }),
  setStyle: (style) => set({ style }),

  setCurrentStep: (step) => {
    const steps = get().steps.map((s) => {
      const stepIndex = STEP_ORDER.indexOf(s.step);
      const targetIndex = STEP_ORDER.indexOf(step);
      if (stepIndex < targetIndex) return { ...s, status: 'completed' as const };
      if (stepIndex === targetIndex) return { ...s, status: 'active' as const };
      return { ...s, status: 'pending' as const };
    });
    set({ currentStep: step, steps });
  },

  setStepStatus: (step, status) =>
    set((state) => ({
      steps: state.steps.map((s) =>
        s.step === step ? { ...s, status } : s
      ),
    })),

  setMaterialPack: (pack) => set({ materialPack: pack }),
  setMaterialMissing: (missing) => set({ materialMissing: missing }),

  setTitleOptions: (options) => set({ titleOptions: options }),

  toggleTitle: (title) =>
    set((state) => {
      const exists = state.selectedTitles.includes(title);
      if (exists) {
        return { selectedTitles: state.selectedTitles.filter((t) => t !== title) };
      }
      if (state.selectedTitles.length >= 2) return state;
      return { selectedTitles: [...state.selectedTitles, title] };
    }),

  setCustomTitle: (title) => set({ customTitle: title }),
  setTitleRetries: (count) => set({ titleRetries: count }),

  setArticle: (article) => set({ article }),
  setAiScore: (score) => set({ aiScore: score }),
  setAiScoreDetails: (details) => set({ aiScoreDetails: details }),
  setArticleRetries: (count) => set({ articleRetries: count }),
  setIsEditing: (editing) => set({ isEditing: editing }),

  setTags: (tags) => set({ tags }),
  toggleTag: (tag) =>
    set((state) => {
      const exists = state.tags.includes(tag);
      return { tags: exists ? state.tags.filter((t) => t !== tag) : [...state.tags, tag] };
    }),
  addCustomTag: (tag) =>
    set((state) => {
      if (!tag || state.tags.includes(tag)) return state;
      return { tags: [...state.tags, tag], customTag: '' };
    }),
  removeTag: (tag) =>
    set((state) => ({ tags: state.tags.filter((t) => t !== tag) })),
  setCustomTag: (tag) => set({ customTag: tag }),

  setComplianceReport: (report) => set({ complianceReport: report }),
  setComplianceOverride: (issueType, action) =>
    set((state) => ({
      complianceOverrides: { ...state.complianceOverrides, [issueType]: action },
    })),

  setOutput: (output) => set({ output }),
  setTaskId: (id) => set({ taskId: id }),
  setTaskStatus: (status) => set({ taskStatus: status }),
  setAgents: (agents) => set({ agents }),
  updateAgent: (name, status, message) =>
    set((state) => ({
      agents: state.agents.map((a) =>
        a.name === name ? { ...a, status, message } : a
      ),
    })),
  setIsProcessing: (processing) => set({ isProcessing: processing }),
  setError: (error) => set({ error }),

  goToStep: (step) => {
    const { setCurrentStep } = get();
    setCurrentStep(step);
  },

  nextStep: () => {
    const { currentStep, setCurrentStep } = get();
    const index = STEP_ORDER.indexOf(currentStep);
    if (index < STEP_ORDER.length - 1) {
      setCurrentStep(STEP_ORDER[index + 1]);
    }
  },

  prevStep: () => {
    const { currentStep, setCurrentStep } = get();
    const index = STEP_ORDER.indexOf(currentStep);
    if (index > 0) {
      setCurrentStep(STEP_ORDER[index - 1]);
    }
  },

  startCreation: async () => {
    set({ isProcessing: true, error: null });
    await new Promise((r) => setTimeout(r, 1500));
    const state = get();
    set({
      materialPack: {
        brand: { name: state.brand || '默认品牌', tone: ['专业', '亲切'], taboos: ['最好', '第一'] },
        product: { name: state.product, selling_points: ['核心卖点1', '核心卖点2'], ingredients: ['成分A', '成分B'], evidence: {} },
        persona: { profile: '25-35岁都市白领', pain_points: ['工作压力大', '亚健康'], language_style: state.style || '口语化' },
        scene: { description: state.scene, usage_method: '日常使用' },
        compliance: { rules: ['不得使用绝对化用语', '需标注注意事项'], forbidden_groups: ['孕妇', '儿童'] },
      },
      materialMissing: [],
      titleOptions: [
        { title: `${state.product}｜打工人的必备好物`, strategy: '痛点', score: 9, reason: '直击目标人群痛点' },
        { title: `用了${state.product}之后，我的生活变了`, strategy: '故事', score: 8, reason: '引发好奇心' },
        { title: `${state.product}测评｜真实体验分享`, strategy: '测评', score: 8, reason: '信任感强' },
        { title: `为什么我推荐${state.product}？`, strategy: '提问', score: 7, reason: '引导思考' },
        { title: `${state.product}使用指南｜新手必看`, strategy: '教程', score: 7, reason: '实用性强' },
      ],
      article: `作为一个经常加班的打工人，我一直很关注身体健康。\n\n最近开始尝试${state.product}，坚持使用了一段时间，想和大家分享一下我的真实体验。\n\n首先是使用感受，${state.product}的口感还不错，没有奇怪的味道。每天坚持服用，感觉精神状态好了很多，不再像以前那样容易疲惫。\n\n当然，任何产品都需要坚持使用才能看到效果。我建议大家可以配合规律作息和适当运动，效果会更好。\n\n最后提醒大家，购买时一定要选择正规渠道，认准官方旗舰店。`,
      aiScore: 78,
      aiScoreDetails: { '去AI味': 80, '口语化': 75, '情感共鸣': 78, '信息密度': 76, '可读性': 82 },
      tags: [state.product, '好物推荐', '种草', '日常保养', state.scene].filter(Boolean),
      complianceReport: {
        status: 'passed' as const,
        p0_issues: [],
        p1_issues: [],
        p2_issues: [{ type: '表述优化', description: '建议补充产品使用周期说明', severity: 'p2' as const }],
        suggestions: ['可以增加更多使用场景描述', '建议补充购买渠道信息'],
      },
      isProcessing: false,
    });
  },

  reset: () => set(INITIAL_STATE),
}));
