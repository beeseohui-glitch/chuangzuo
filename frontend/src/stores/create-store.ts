import { create } from 'zustand';
import { Platform, TaskStatus, MaterialPack, TitleOption, NoteOutput, ComplianceReport } from '@/types';
import { createApi } from '@/lib/api';

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
  regenerateArticle: () => Promise<void>;
  refreshTitles: () => Promise<void>;
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
  selectTitle: (titleIndex: number) => Promise<void>;
  confirmP2Decision: (accept: boolean) => Promise<void>;
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

// 轮询任务状态的辅助函数
function _pollTaskStatus(
  taskId: string,
  set: (partial: Partial<CreateStore>) => void,
) {
  const poll = async () => {
    try {
      const res = await createApi.getTaskStatus(taskId);
      if (!res.success || !res.data) return;

      const data = res.data as { status: string; progress?: number; current_step?: string };
      if (data.status === 'completed') {
        // 获取结果
        const resultRes = await createApi.getTaskResult(taskId);
        if (resultRes.success && resultRes.data) {
          const result = (resultRes.data as { result?: Record<string, unknown> }).result || resultRes.data;
          set({
            materialPack: (result as Record<string, unknown>).material_pack as MaterialPack || null,
            materialMissing: (result as Record<string, unknown>).material_pack ? [] : ['素材包未返回'],
            titleOptions: (result as Record<string, unknown>).title_options as TitleOption[] || [],
            article: (result as Record<string, unknown>).article as string || '',
            aiScore: (result as Record<string, unknown>).ai_flavor_score as number || 0,
            tags: (result as Record<string, unknown>).tags as string[] || [],
            complianceReport: (result as Record<string, unknown>).compliance_report as ComplianceReport || null,
            taskStatus: 'completed' as TaskStatus,
            isProcessing: false,
          });
        }
      } else if (data.status === 'failed') {
        set({ error: '创作失败', isProcessing: false, taskStatus: 'failed' as TaskStatus });
      } else {
        // 继续轮询
        setTimeout(poll, 2000);
      }
    } catch {
      setTimeout(poll, 3000);
    }
  };
  setTimeout(poll, 1000);
}

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

  regenerateArticle: async () => {
    const state = get();
    if (state.articleRetries >= state.maxArticleRetries) return;

    set({ isProcessing: true, articleRetries: state.articleRetries + 1 });

    // 模拟重新生成（开发模式）
    await new Promise((r) => setTimeout(r, 1500));

    const variants = [
      "姐妹们我真的要跪谢这款护肝片了！连续加班一个月，每天凌晨才睡，多亏它续命。吃之前每天早上起来跟行尸走肉似的，现在精神状态好太多了。不过每个人体质不一样，效果因人而异哈，别杠。",
      "打工人自救好物分享！这款护肝片我已经吃第二瓶了，最直观的变化就是熬夜之后第二天没那么难受了。成分主要是水飞蓟素，查了一下确实有研究支持。当然不是让你放心熬夜啊，能早睡还是早睡！",
      "被同事安利的护肝片，本来没抱希望，结果真香了。连续吃了三周，感觉整个人没那么容易疲惫了。配料表很干净，水飞蓟素+姜黄素，都是护肝的好东西。不过孕妇和哺乳期的姐妹就别吃了哈。",
    ];

    const idx = state.articleRetries % variants.length;
    const newScore = 75 + Math.floor(Math.random() * 15);

    set({
      article: variants[idx],
      aiScore: newScore,
      aiScoreDetails: {
        '去AI味': 80 + Math.floor(Math.random() * 15),
        '口语化': 75 + Math.floor(Math.random() * 15),
        '情感共鸣': 70 + Math.floor(Math.random() * 20),
        '信息密度': 75 + Math.floor(Math.random() * 15),
        '可读性': 80 + Math.floor(Math.random() * 15),
      },
      isProcessing: false,
    });
  },

  refreshTitles: async () => {
    const state = get();
    if (state.titleRetries >= state.maxTitleRetries) return;

    set({ isProcessing: true, titleRetries: state.titleRetries + 1, selectedTitles: [] });

    await new Promise((r) => setTimeout(r, 1200));

    const batches = [
      [
        { title: "被问了100遍的护肝片，终于来交作业了", strategy: "悬念型", score: 90, reason: "利用好奇心驱动点击" },
        { title: "打工人の肝脏保卫战｜真实体验分享", strategy: "人设型", score: 87, reason: "人设代入感强" },
        { title: "这款护肝片凭什么让我回购三次？", strategy: "反问型", score: 85, reason: "反问引发思考" },
        { title: "熬夜党的救星！亲测30天护肝片效果", strategy: "数据型", score: 83, reason: "具体数据增加可信度" },
      ],
      [
        { title: "别再交智商税了！护肝片就选这一款", strategy: "否定型", score: 91, reason: "否定常见认知引发关注" },
        { title: "我的肝脏是怎么被这款片救回来的", strategy: "故事型", score: 88, reason: "叙事驱动，情感共鸣" },
        { title: "护肝片选购避坑指南｜成分党必看", strategy: "清单型", score: 86, reason: "干货价值感强" },
        { title: "从怀疑到真香｜我与护肝片的故事", strategy: "转变型", score: 84, reason: "心态转变引发共鸣" },
      ],
      [
        { title: "同事问我最近气色怎么变好了", strategy: "场景型", score: 89, reason: "场景化描述引发好奇" },
        { title: "这瓶护肝片我愿称之为加班神器", strategy: "评价型", score: 86, reason: "强烈推荐感" },
        { title: "护肝片到底有没有用？30天实测告诉你", strategy: "问答型", score: 84, reason: "解答用户疑问" },
        { title: "熬夜不伤肝的秘密武器", strategy: "利益型", score: 82, reason: "直接点明利益点" },
      ],
    ];

    const batchIdx = state.titleRetries % batches.length;
    set({
      titleOptions: batches[batchIdx],
      isProcessing: false,
    });
  },

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

  selectTitle: async (titleIndex: number) => {
    const { taskId } = get();
    if (!taskId) return;

    set({ isProcessing: true });
    try {
      const res = await createApi.selectTitle(taskId, titleIndex);
      if (!res.success) {
        set({ error: res.error || '标题选择失败', isProcessing: false });
      }
      // 后端收到后会继续执行，WebSocket 会推送后续消息
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '网络错误', isProcessing: false });
    }
  },

  confirmP2Decision: async (accept: boolean) => {
    const { taskId } = get();
    if (!taskId) return;

    set({ isProcessing: true });
    try {
      const res = await createApi.p2Decision(taskId, accept);
      if (!res.success) {
        set({ error: res.error || '决策提交失败', isProcessing: false });
      }
      // 后端收到后会继续执行，WebSocket 会推送 completed 消息
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '网络错误', isProcessing: false });
    }
  },

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
    const state = get();
    set({ isProcessing: true, error: null });

    try {
      // 调用后端创建接口
      const res = await createApi.startCreation({
        product: state.product,
        scene: state.scene,
        persona: state.intent,
        platform: state.platform || 'xiaohongshu',
      });

      if (!res.success || !res.data) {
        set({ error: res.error || '创作请求失败', isProcessing: false });
        return;
      }

      // 后端返回 task_id，连接 WebSocket 监听进度
      const taskData = res.data as { task_id: string; status: string };
      const taskId = taskData.task_id;
      set({ taskId, taskStatus: 'processing' as TaskStatus });

      // 连接 WebSocket
      const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const wsBase = apiBase.replace(/^http/, 'ws');
      const wsUrl = `${wsBase}/api/v1/create/ws/${taskId}`;
      try {
        const ws = new WebSocket(wsUrl);

        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);

          switch (data.type) {
            case 'progress':
              set({ isProcessing: true });
              break;

            case 'material_ready':
              set({
                materialPack: data.material_pack || null,
                materialMissing: data.missing_fields || [],
                isProcessing: false,
              });
              break;

            case 'awaiting_title_selection':
              set({
                titleOptions: data.title_options || [],
                taskStatus: 'awaiting_title_selection' as TaskStatus,
                isProcessing: false,
              });
              break;

            case 'title_selected':
              set({ taskStatus: 'running' as TaskStatus, isProcessing: true });
              break;

            case 'article_ready':
              set({
                article: data.article || '',
                aiScore: data.ai_flavor_score || 0,
                isProcessing: false,
              });
              break;

            case 'compliance_issues':
              set({
                complianceReport: {
                  status: 'has_issues',
                  p0_issues: data.p0_issues || [],
                  p1_issues: [],
                  p2_issues: [],
                  suggestions: [],
                },
                taskStatus: 'awaiting_p2_decision' as TaskStatus,
                isProcessing: false,
              });
              break;

            case 'completed':
              if (data.result) {
                const result = data.result;
                set({
                  materialPack: result.material_pack || null,
                  materialMissing: result.material_pack ? [] : ['素材包未返回'],
                  titleOptions: result.title_options || [],
                  article: result.article || '',
                  aiScore: result.ai_flavor_score || 0,
                  tags: result.tags || [],
                  complianceReport: result.compliance_report || null,
                  taskStatus: 'completed' as TaskStatus,
                  isProcessing: false,
                });
              }
              ws.close();
              break;

            case 'failed':
              set({ error: data.error || '创作失败', isProcessing: false, taskStatus: 'failed' as TaskStatus });
              ws.close();
              break;
          }
        };

        ws.onerror = () => {
          // WebSocket 连接失败，轮询状态
          console.warn('WebSocket 连接失败，使用轮询');
          _pollTaskStatus(taskId, set);
        };

        ws.onclose = () => {
          // 如果还在处理中，用轮询兜底
          const currentState = get();
          if (currentState.isProcessing) {
            _pollTaskStatus(taskId, set);
          }
        };
      } catch {
        // WebSocket 不可用，直接轮询
        _pollTaskStatus(taskId, set);
      }
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : '网络错误',
        isProcessing: false,
      });
    }
  },

  reset: () => set(INITIAL_STATE),
}));
