/**
 * Agent Meet 前端交互逻辑
 */

// ========== SVG Icon Helpers ==========
const ICONS = {
  mic: '<svg class="icon-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>',
  fileText: '<svg class="icon-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>',
  book: '<svg class="icon-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>',
  list: '<svg class="icon-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>',
  trash: '<svg class="icon-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>',
  refresh: '<svg class="icon-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>',
  search: '<svg class="icon-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
  upload: '<svg class="icon-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>',
  arrowLeft: '<svg class="icon-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg>',
  warning: '<svg class="icon-lg text-amber-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
  check: '<svg class="icon-sm text-emerald-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
  info: '<svg class="icon-sm text-blue-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
  error: '<svg class="icon-sm text-red-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
  brain: '<svg class="icon-sm text-purple-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.98-3A2.5 2.5 0 0 1 9.5 2z"/><path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.98-3A2.5 2.5 0 0 0 14.5 2z"/></svg>',
  lightbulb: '<svg class="icon-sm text-amber-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18h6"/><path d="M10 22h4"/><path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14"/></svg>',
  barChart: '<svg class="icon-lg text-primary-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="20" x2="12" y2="10"/><line x1="18" y1="20" x2="18" y2="4"/><line x1="6" y1="20" x2="6" y2="16"/></svg>',
  target: '<svg class="icon-lg text-primary-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>',
  zap: '<svg class="icon-sm text-amber-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
  user: '<svg class="icon-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
  chevronRight: '<svg class="icon-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>',
  sparkles: '<svg class="icon-sm text-primary-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/><path d="M5 3v4"/><path d="M19 17v4"/><path d="M3 5h4"/><path d="M17 19h4"/></svg>',
};

// ========== 状态管理 ==========
const State = {
  tab: 'interview', // interview | resume | kb | sessions
  // 面试
  sessionId: '', skillId: 'java-backend', difficulty: 'medium', questions: [],
  resumeText: '', agentMode: true, started: false, done: false,
  currentQuestion: null, currentIndex: 0, evaluation: null,
  agentReasoning: null, interviewStrategy: null, hint: '',
  report: null, candidateProfile: null, topicPerformance: null, history: [],
  // 简历
  resumes: [], resumeDetail: null,
  // 知识库
  kbList: [], kbDetail: null, kbQueryResult: null, kbStats: null,
  // 会话
  sessions: [], sessionDetail: null,
  // 技能
  skills: [],
};

// ========== 工具函数 ==========
function uuid() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const r = Math.random() * 16 | 0;
    return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
  });
}
function escapeHtml(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
function scoreColor(s) { return s >= 8 ? 'text-emerald-400' : s >= 6 ? 'text-amber-400' : s >= 4 ? 'text-orange-400' : 'text-red-400'; }
function scoreBgColor(s) { return s >= 8 ? 'bg-emerald-500' : s >= 6 ? 'bg-amber-500' : s >= 4 ? 'bg-orange-500' : 'bg-red-500'; }
function scoreGlow(s) { return s >= 8 ? 'shadow-emerald-500/20' : s >= 6 ? 'shadow-amber-500/20' : s >= 4 ? 'shadow-orange-500/20' : 'shadow-red-500/20'; }
function statusBadge(st) {
  const m = {
    COMPLETED: 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/20',
    EVALUATED: 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/20',
    IN_PROGRESS: 'bg-blue-500/15 text-blue-400 border border-blue-500/20',
    PENDING: 'bg-amber-500/15 text-amber-400 border border-amber-500/20',
    PROCESSING: 'bg-amber-500/15 text-amber-400 border border-amber-500/20',
    FAILED: 'bg-red-500/15 text-red-400 border border-red-500/20'
  };
  return `<span class="status-badge ${m[st] || 'bg-slate-100 dark:bg-slate-800/50 text-slate-500 dark:text-slate-400 border border-slate-200 dark:border-slate-700/30'}">${st}</span>`;
}
function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / 1024 / 1024).toFixed(1) + ' MB';
}
function formatTime(ts) {
  if (!ts) return '-';
  return new Date(ts).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
}
function showToast(msg, type = 'info') {
  const el = document.getElementById('toast');
  const colors = {
    info: 'border-blue-500/40',
    error: 'border-red-500/40',
    success: 'border-emerald-500/40'
  };
  const icon = { info: ICONS.info, error: ICONS.error, success: ICONS.check };
  el.innerHTML = `<div class="glass-card ${colors[type] || colors.info} px-4 py-3 text-sm max-w-sm flex items-center gap-3 fade-in">
    <span class="flex-shrink-0">${icon[type] || ICONS.info}</span>
    <span class="text-slate-800 dark:text-slate-200">${escapeHtml(msg)}</span>
  </div>`;
  el.classList.remove('hidden');
  clearTimeout(el._timer);
  el._timer = setTimeout(() => el.classList.add('hidden'), type === 'error' ? 5000 : 3000);
}

// ========== UI ==========
const UI = {
  root() { return document.getElementById('app'); },

  render() {
    // Update sidebar nav active state + chevron visibility
    document.querySelectorAll('.nav-item[data-tab]').forEach(btn => {
      const isActive = btn.dataset.tab === State.tab;
      btn.classList.toggle('active', isActive);
      const chevron = btn.querySelector('.nav-chevron');
      if (chevron) chevron.classList.toggle('hidden', !isActive);
    });
    switch (State.tab) {
      case 'interview': State.started ? (State.done ? this.renderReport() : this.renderInterview()) : this.renderInterviewConfig(); break;
      case 'resume': State.resumeDetail ? this.renderResumeDetail() : this.renderResumeList(); break;
      case 'kb': State.kbDetail ? this.renderKbDetail() : this.renderKbList(); break;
      case 'sessions': State.sessionDetail ? this.renderSessionDetail() : this.renderSessionList(); break;
    }
  },

  showLoading(text = '加载中...') {
    this.root().innerHTML = `
      <div class="flex flex-col items-center justify-center h-full text-slate-400 dark:text-slate-500 gap-3">
        <div class="w-8 h-8 border-2 border-slate-700 border-t-primary-500 rounded-full animate-spin"></div>
        <span class="text-sm">${text}</span>
      </div>`;
  },

  showError(msg, retry) {
    const retryBtn = retry ? `<button onclick="${retry}" class="btn-secondary px-4 py-2 text-sm mt-3 inline-flex items-center gap-1.5">${ICONS.refresh} 重试</button>` : '';
    this.root().innerHTML = `
      <div class="flex flex-col items-center justify-center h-full text-slate-400 dark:text-slate-500 gap-2">
        ${ICONS.warning}
        <p class="text-sm text-slate-500 dark:text-slate-400">${escapeHtml(msg)}</p>
        ${retryBtn}
      </div>`;
  },


  // ==================== 面试配置 ====================
  renderInterviewConfig() {
    const self = this;
    this.root().innerHTML = `
      <div class="max-w-2xl mx-auto fade-in">
        <!-- Header -->
        <div class="text-center mb-8">
          <div class="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-primary-500/20 to-primary-600/20 border border-primary-500/20 mb-4">
            ${ICONS.target}
          </div>
          <h2 class="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-2 tracking-tight" style="">准备好了吗？</h2>
          <p class="text-slate-500 dark:text-slate-400 text-sm">配置面试参数，开始 AI 模拟面试</p>
        </div>

        <!-- Config Card -->
        <div class="glass-card-lg p-6 space-y-5">
          <!-- Session ID -->
          <div>
            <label class="block text-sm text-slate-500 dark:text-slate-400 mb-2 font-medium">会话 ID</label>
            <div class="flex gap-2">
              <input id="cfg-session" type="text" value="${uuid()}" class="input-field font-mono text-slate-500 dark:text-slate-400" readonly>
              <button onclick="document.getElementById('cfg-session').value=uuid()" class="btn-secondary px-3 py-2 text-sm inline-flex items-center gap-1.5 shrink-0">${ICONS.refresh} 刷新</button>
            </div>
          </div>

          <!-- Skill -->
          <div>
            <label class="block text-sm text-slate-500 dark:text-slate-400 mb-2 font-medium">技能方向</label>
            <select id="cfg-skill" class="input-field">
              <option value="">加载中...</option>
            </select>
          </div>

          <!-- Difficulty -->
          <div>
            <label class="block text-sm text-slate-500 dark:text-slate-400 mb-2 font-medium">难度等级</label>
            <div class="grid grid-cols-3 gap-3" id="cfg-difficulty">
              ${['easy', 'medium', 'hard'].map(d => {
                const labels = { easy: '简单', medium: '中等', hard: '困难' };
                const descs = { easy: '基础概念', medium: '综合应用', hard: '深度原理' };
                const selected = State.difficulty === d;
                return `<div class="selection-card ${selected ? 'selected' : ''}" onclick="State.difficulty='${d}';UI.render()">
                  <div class="text-sm font-medium ${selected ? 'text-primary-600 dark:text-primary-400' : 'text-slate-700 dark:text-slate-300'}">${labels[d]}</div>
                  <div class="text-[11px] ${selected ? 'text-primary-500/70 dark:text-primary-400/70' : 'text-slate-400 dark:text-slate-500'} mt-0.5">${descs[d]}</div>
                </div>`;
              }).join('')}
            </div>
          </div>

          <!-- Question Count -->
          <div>
            <label class="block text-sm text-slate-500 dark:text-slate-400 mb-2 font-medium">题目数量 <span class="text-slate-400 dark:text-slate-500 text-xs font-normal">留空则自动出题</span></label>
            <input id="cfg-count" type="number" value="5" min="1" max="20" class="input-field">
          </div>

          <!-- Resume -->
          <div>
            <label class="block text-sm text-slate-500 dark:text-slate-400 mb-2 font-medium">简历文本 <span class="text-slate-400 dark:text-slate-500 text-xs font-normal">可选，有简历时 60% 简历题 + 40% 方向题</span></label>
            <textarea id="cfg-resume" rows="3" class="input-field resize-none" placeholder="粘贴简历内容..."></textarea>
          </div>

          <!-- Agent Mode -->
          <label class="flex items-center gap-3 cursor-pointer group">
            <div class="relative">
              <input id="cfg-agent" type="checkbox" checked class="sr-only peer">
              <div class="w-9 h-5 bg-slate-200 dark:bg-slate-700 peer-checked:bg-primary-600 rounded-full transition-colors"></div>
              <div class="absolute left-0.5 top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform peer-checked:translate-x-4"></div>
            </div>
            <div>
              <span class="text-sm text-slate-800 dark:text-slate-200 font-medium">Agent 模式</span>
              <span class="text-xs text-slate-400 dark:text-slate-500 ml-2">LLM 自主决策面试流程</span>
            </div>
          </label>

          <!-- Start Button -->
          <button onclick="App.startInterview()" id="btn-start" class="btn-primary w-full py-3 text-sm font-medium inline-flex items-center justify-center gap-2">
            ${ICONS.zap} 开始面试
          </button>
        </div>
      </div>`;
    App.loadSkills();
  },

  // ==================== 面试进行中 ====================
  renderInterview() {
    const q = State.currentQuestion;
    const ev = State.evaluation;
    const totalQ = State.questions?.length || 5;
    const progress = totalQ > 0 ? Math.round(((State.currentIndex + 1) / totalQ) * 100) : 0;

    // Build chat messages
    let messagesHtml = '';
    State.history.forEach((h, i) => {
      // User answer (right-aligned)
      messagesHtml += `<div class="flex items-start gap-3 justify-end fade-in">
        <div class="flex-1 max-w-[80%]"><div class="chat-bubble-user px-4 py-3 text-sm leading-relaxed">${escapeHtml(h.answer)}</div></div>
        <div class="w-8 h-8 bg-slate-200 dark:bg-slate-600 rounded-full flex items-center justify-center flex-shrink-0"><svg class="w-4 h-4 text-slate-600 dark:text-slate-300" viewBox="0 0 24 24" fill="none"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2"/></svg></div>
      </div>`;
      // Evaluation (left-aligned)
      if (h.evaluation) {
        messagesHtml += `<div class="flex items-start gap-3 fade-in">
          <div class="w-8 h-8 bg-primary-100 dark:bg-primary-900/50 rounded-full flex items-center justify-center flex-shrink-0"><svg class="w-4 h-4 text-primary-600 dark:text-primary-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/></svg></div>
          <div class="flex-1"><div class="flex items-center gap-2 mb-1"><span class="text-sm font-semibold text-slate-700 dark:text-slate-300">面试官</span><span class="text-xs text-slate-400 dark:text-slate-500">第${i + 1}题</span><span class="text-sm font-bold ${scoreColor(h.evaluation.score ?? 0)}">${h.evaluation.score ?? '-'}/10</span></div><div class="chat-bubble-assistant px-4 py-3 text-sm leading-relaxed">${escapeHtml(h.evaluation.feedback || '')}</div></div>
        </div>`;
      }
    });

    // Current question (left-aligned with avatar)
    if (q) {
      messagesHtml += `<div class="flex items-start gap-3 fade-in">
        <div class="w-8 h-8 bg-primary-100 dark:bg-primary-900/50 rounded-full flex items-center justify-center flex-shrink-0"><svg class="w-4 h-4 text-primary-600 dark:text-primary-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/></svg></div>
        <div class="flex-1">
          <div class="flex items-center gap-2 mb-1"><span class="text-sm font-semibold text-slate-700 dark:text-slate-300">面试官</span>${q.is_follow_up ? '<span class="px-2 py-0.5 bg-purple-50 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 text-xs rounded-full">追问</span>' : ''}${q.category ? `<span class="px-2 py-0.5 bg-primary-50 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 text-xs rounded-full">${escapeHtml(q.category)}</span>` : ''}</div>
          <div class="chat-bubble-assistant px-4 py-3 text-sm leading-relaxed">${escapeHtml(q.question)}</div>
        </div>
      </div>`;
    }

    // Evaluation result
    let evalHtml = '';
    if (ev) {
      const s = ev.score ?? 0;
      evalHtml = `<div class="px-6 py-3 fade-in"><div class="bg-white dark:bg-slate-800 rounded-xl p-4 border border-slate-100 dark:border-slate-700">
        <div class="flex items-center justify-between mb-3">
          <span class="text-sm font-semibold text-slate-700 dark:text-slate-300">评估结果</span>
          <div class="flex items-center gap-3">
            <div class="w-32 h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden"><div class="h-full ${scoreBgColor(s)} rounded-full transition-all duration-700" style="width:${s * 10}%"></div></div>
            <span class="text-lg font-bold ${scoreColor(s)}">${s}<span class="text-xs text-slate-400 dark:text-slate-500">/10</span></span>
          </div>
        </div>
        ${ev.feedback ? `<p class="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">${escapeHtml(ev.feedback)}</p>` : ''}
      </div></div>`;
    }

    // Hint
    let hintHtml = State.hint ? `<div class="px-6 py-2 fade-in"><div class="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800/40 rounded-xl px-4 py-3 text-sm text-amber-700 dark:text-amber-300 inline-flex items-start gap-2.5">${ICONS.lightbulb} <span class="leading-relaxed">${escapeHtml(State.hint)}</span></div></div>` : '';

    // Agent reasoning
    let reasoningHtml = '';
    if (State.agentReasoning?.thought) {
      reasoningHtml = `<div class="px-6 py-2 fade-in"><details class="bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800/40 rounded-xl overflow-hidden">
        <summary class="px-4 py-3 cursor-pointer text-sm text-purple-600 dark:text-purple-400 inline-flex items-center gap-2 hover:text-purple-700 dark:hover:text-purple-300 transition-colors">${ICONS.brain} Agent 推理过程</summary>
        <div class="px-4 pb-4"><p class="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">${escapeHtml(State.agentReasoning.thought)}</p>
        ${State.agentReasoning.action ? `<p class="text-xs text-slate-400 dark:text-slate-500 mt-2 font-mono">→ ${escapeHtml(State.agentReasoning.action)}</p>` : ''}</div>
      </details></div>`;
    }

    this.root().innerHTML = `
      <div class="flex flex-col h-full max-w-4xl mx-auto">
        <!-- Progress bar -->
        <div class="bg-white dark:bg-slate-800 rounded-xl p-5 mb-4 shadow-sm border border-slate-100 dark:border-slate-700">
          <div class="flex items-center justify-between mb-3">
            <span class="text-sm font-semibold text-slate-700 dark:text-slate-300">第 ${State.currentIndex + 1} / ${totalQ} 题</span>
            <span class="text-sm text-slate-500 dark:text-slate-400">${progress}%</span>
          </div>
          <div class="h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
            <div class="h-full bg-gradient-to-r from-primary-500 to-primary-600 rounded-full transition-all duration-300" style="width:${progress}%"></div>
          </div>
        </div>

        <!-- Chat area -->
        <div class="flex-1 bg-white dark:bg-slate-800 rounded-xl shadow-sm overflow-hidden flex flex-col min-h-0 border border-slate-100 dark:border-slate-700">
          <div class="flex-1 overflow-y-auto px-6 py-4 space-y-4" id="chat-history">
            ${messagesHtml}
            ${evalHtml}${hintHtml}${reasoningHtml}
          </div>

          <!-- Input area -->
          <div class="border-t border-slate-200 dark:border-slate-600 p-4 bg-slate-50 dark:bg-slate-700/50">
            <div class="flex gap-3">
              <textarea id="answer-input" placeholder="输入你的回答... (Ctrl + Enter 提交)" class="flex-1 px-4 py-3 border border-slate-300 dark:border-slate-500 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 text-sm" rows="3" onkeydown="if(event.ctrlKey&&event.key==='Enter'){App.submitAnswer()}"></textarea>
              <div class="flex flex-col gap-2">
                <button onclick="App.submitAnswer()" id="btn-submit" class="px-6 py-3 bg-primary-500 text-white rounded-xl font-medium hover:bg-primary-600 transition-colors flex items-center gap-2 text-sm">
                  ${ICONS.sparkles} 提交
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>`;
    const chat = document.getElementById('chat-history');
    if (chat) chat.scrollTop = chat.scrollHeight;
  },

  // ==================== 面试报告 ====================
  renderReport() {
    const r = State.report; if (!r) return;
    const scores = r.scores || r.question_scores || [];
    const strengths = r.strengths || r.strong_topics || [];
    const weaknesses = r.weaknesses || r.weak_topics || [];
    this.root().innerHTML = `
      <div class="max-w-3xl mx-auto fade-in">
        <!-- Header -->
        <div class="text-center mb-8">
          <div class="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-primary-500/20 to-primary-600/20 border border-primary-500/20 mb-4">
            ${ICONS.barChart}
          </div>
          <h2 class="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight" style="">面试报告</h2>
        </div>

        <!-- Total Score -->
        ${r.total_score != null ? `<div class="glass-card-lg p-8 mb-6 text-center">
          <div class="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br ${r.total_score >= 8 ? 'from-emerald-500/20 to-emerald-600/20 border-emerald-500/30' : r.total_score >= 6 ? 'from-amber-500/20 to-amber-600/20 border-amber-500/30' : 'from-orange-500/20 to-orange-600/20 border-orange-500/30'} border mb-4">
            <span class="text-3xl font-bold ${scoreColor(r.total_score)}" style="">${r.total_score}</span>
          </div>
          <p class="text-sm text-slate-500 dark:text-slate-400">综合评分 <span class="text-slate-400 dark:text-slate-500">/ 10</span></p>
        </div>` : ''}

        <!-- Summary -->
        ${r.summary ? `<div class="glass-card p-6 mb-6">
          <h3 class="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3" style="">总体评价</h3>
          <p class="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">${escapeHtml(r.summary)}</p>
        </div>` : ''}

        <!-- Scores -->
        ${scores.length ? `<div class="glass-card p-6 mb-6">
          <h3 class="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-4" style="">各题得分</h3>
          <div class="space-y-3">${scores.map((s, i) => { const sc = typeof s === 'object' ? (s.score ?? 0) : s; return `
            <div class="flex items-center gap-3">
              <span class="text-xs text-slate-400 dark:text-slate-500 w-24 truncate">${typeof s === 'object' ? (s.category || `第${i + 1}题`) : `第${i + 1}题`}</span>
              <div class="flex-1 h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden"><div class="h-full ${scoreBgColor(sc)} rounded-full transition-all duration-700" style="width:${sc * 10}%"></div></div>
              <span class="text-sm font-mono ${scoreColor(sc)} w-10 text-right">${sc}</span>
            </div>`; }).join('')}</div>
        </div>` : ''}

        <!-- Strengths & Weaknesses -->
        ${(strengths.length || weaknesses.length) ? `<div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
          <div class="glass-card p-6">
            <h3 class="text-sm font-semibold text-emerald-400 mb-3 inline-flex items-center gap-2" style="">${ICONS.check} 强项</h3>
            <ul class="space-y-2">${strengths.map(s => `<li class="text-sm text-slate-500 dark:text-slate-400 pl-4 border-l-2 border-emerald-500/30">${escapeHtml(typeof s === 'string' ? s : s.topic || JSON.stringify(s))}</li>`).join('')}</ul>
          </div>
          <div class="glass-card p-6">
            <h3 class="text-sm font-semibold text-amber-400 mb-3 inline-flex items-center gap-2" style="">${ICONS.warning} 弱项</h3>
            <ul class="space-y-2">${weaknesses.map(w => `<li class="text-sm text-slate-500 dark:text-slate-400 pl-4 border-l-2 border-amber-500/30">${escapeHtml(typeof w === 'string' ? w : w.topic || JSON.stringify(w))}</li>`).join('')}</ul>
          </div>
        </div>` : ''}

        <!-- Restart -->
        <button onclick="App.reset()" class="btn-secondary w-full py-3 text-sm font-medium">重新开始</button>
      </div>`;
  },

  // ==================== 简历列表 ====================
  renderResumeList() {
    const list = State.resumes;
    this.root().innerHTML = `
      <div class="max-w-4xl mx-auto fade-in">
        <!-- Header -->
        <div class="flex items-center justify-between mb-6">
          <div>
            <h2 class="text-xl font-bold text-slate-900 dark:text-slate-100 tracking-tight" style="">简历管理</h2>
            <p class="text-sm text-slate-400 dark:text-slate-500 mt-0.5">上传并分析你的简历</p>
          </div>
          <label class="btn-primary px-4 py-2 text-sm cursor-pointer inline-flex items-center gap-1.5">
            ${ICONS.upload} 上传简历<input type="file" class="hidden" accept=".pdf,.docx,.doc,.txt,.md" onchange="App.uploadResume(this.files[0])">
          </label>
        </div>

        ${list.length === 0 ? `
        <div class="glass-card-lg p-16 text-center">
          <div class="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-slate-100 dark:bg-slate-800/60 border border-slate-700/40 mb-4">
            ${ICONS.fileText}
          </div>
          <p class="text-slate-500 dark:text-slate-400 text-sm">暂无简历</p>
          <p class="text-slate-400 dark:text-slate-500 text-xs mt-1">点击右上角上传简历开始分析</p>
        </div>` : `
        <div class="space-y-3">
          ${list.map((r, i) => `
          <div class="glass-card p-4 flex items-center gap-4 hover:border-primary-500/30 transition-all cursor-pointer group" onclick="App.viewResume(${r.id})" style="animation-delay: ${i * 0.05}s">
            <div class="w-10 h-10 rounded-xl bg-primary-500/10 text-primary-500 flex items-center justify-center border border-primary-500/15">${ICONS.fileText}</div>
            <div class="flex-1 min-w-0">
              <div class="text-sm font-medium text-slate-900 dark:text-slate-100 truncate group-hover:text-primary-400 transition-colors">${escapeHtml(r.filename)}</div>
              <div class="text-xs text-slate-400 dark:text-slate-500 mt-1">${formatSize(r.file_size)} · ${formatTime(r.uploaded_at)}</div>
            </div>
            <div class="flex items-center gap-3">
              ${r.latest_score != null ? `<span class="text-lg font-bold ${scoreColor(r.latest_score / 10)}" style="">${r.latest_score}</span>` : ''}
              ${statusBadge(r.analyze_status)}
            </div>
            <button onclick="event.stopPropagation();App.deleteResume(${r.id})" class="text-slate-400 dark:text-slate-500 hover:text-red-400 transition p-1.5 rounded-lg hover:bg-red-500/10">${ICONS.trash}</button>
          </div>`).join('')}
        </div>`}
      </div>`;
  },

  // ==================== 简历详情 ====================
  renderResumeDetail() {
    const d = State.resumeDetail; if (!d) return;
    const latest = d.analyses?.[0];
    this.root().innerHTML = `
      <div class="max-w-4xl mx-auto fade-in">
        <button onclick="State.resumeDetail=null;UI.render()" class="text-sm text-slate-400 dark:text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 mb-6 inline-flex items-center gap-1.5 transition-colors">${ICONS.arrowLeft} 返回列表</button>

        <!-- Info Card -->
        <div class="glass-card-lg p-6 mb-6">
          <div class="flex items-center gap-4 mb-5">
            <div class="w-12 h-12 rounded-xl bg-primary-500/10 text-primary-500 flex items-center justify-center border border-primary-500/15">${ICONS.fileText}</div>
            <div>
              <h2 class="text-lg font-bold text-slate-900 dark:text-slate-100" style="">${escapeHtml(d.filename)}</h2>
              <p class="text-xs text-slate-400 dark:text-slate-500">${formatSize(d.file_size)} · ${d.content_type} · ${formatTime(d.uploaded_at)}</p>
            </div>
            <div class="ml-auto">${statusBadge(d.analyze_status)}</div>
          </div>
          ${latest ? `
          <!-- Score Grid -->
          <div class="grid grid-cols-5 gap-3 mb-5">
            ${[['总分', latest.overall_score], ['内容', latest.content_score], ['结构', latest.structure_score], ['技能', latest.skill_match_score], ['表达', latest.expression_score]].map(([l, s]) => `
              <div class="text-center glass-card p-3">
                <div class="text-2xl font-bold ${scoreColor(s / 10)}" style="">${s}</div>
                <div class="text-xs text-slate-400 dark:text-slate-500 mt-1">${l}</div>
              </div>
            `).join('')}
          </div>
          ${latest.summary ? `<p class="text-sm text-slate-500 dark:text-slate-400 mb-3 leading-relaxed">${escapeHtml(latest.summary)}</p>` : ''}
          ${latest.strengths?.length ? `<div class="mb-2"><span class="text-xs text-emerald-400 font-medium">强项：</span><span class="text-xs text-slate-500 dark:text-slate-400">${latest.strengths.join('、')}</span></div>` : ''}
          ${latest.suggestions?.length ? `<div><span class="text-xs text-amber-400 font-medium">建议：</span><span class="text-xs text-slate-500 dark:text-slate-400">${latest.suggestions.map(s => typeof s === 'string' ? s : s.recommendation || JSON.stringify(s)).join('、')}</span></div>` : ''}
          ` : '<p class="text-sm text-slate-400 dark:text-slate-500">暂无分析结果</p>'}
        </div>

        <!-- Resume Text -->
        ${d.resume_text ? `<details class="glass-card overflow-hidden">
          <summary class="px-6 py-4 cursor-pointer text-sm text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300 transition-colors">简历原文</summary>
          <div class="px-6 pb-4"><pre class="text-xs text-slate-500 dark:text-slate-400 whitespace-pre-wrap max-h-96 overflow-y-auto leading-relaxed">${escapeHtml(d.resume_text)}</pre></div>
        </details>` : ''}
      </div>`;
  },

  // ==================== 知识库列表 ====================
  renderKbList() {
    const list = State.kbList;
    const stats = State.kbStats;
    this.root().innerHTML = `
      <div class="max-w-5xl mx-auto fade-in">
        <!-- Header -->
        <div class="flex items-center justify-between mb-6">
          <div>
            <h2 class="text-xl font-bold text-slate-900 dark:text-slate-100 tracking-tight" style="">知识库管理</h2>
            <p class="text-sm text-slate-400 dark:text-slate-500 mt-0.5">管理 RAG 文档与检索</p>
          </div>
          <label class="btn-primary px-4 py-2 text-sm cursor-pointer inline-flex items-center gap-1.5">
            ${ICONS.upload} 上传文档 <input type="file" class="hidden" accept=".pdf,.docx,.doc,.txt,.md" onchange="App.uploadKb(this.files[0])">
          </label>
        </div>

        <!-- Stats -->
        ${stats ? `
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
          ${[['总文档', stats.total_count, ICONS.fileText, 'primary'], ['已完成', stats.completed_count, ICONS.check, 'emerald'], ['处理中', stats.processing_count, '<svg class="icon-sm text-amber-400 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>', 'amber'], ['总提问', stats.total_question_count, ICONS.search, 'blue']].map(([label, val, icon, color]) => `
            <div class="glass-card p-4 text-center hover:border-${color}-500/30 transition-colors">
              <div class="text-2xl font-bold text-slate-900 dark:text-slate-100" style="">${val ?? 0}</div>
              <div class="text-xs text-slate-400 dark:text-slate-500 mt-1 inline-flex items-center gap-1">${icon} ${label}</div>
            </div>`).join('')}
        </div>` : ''}

        ${list.length === 0 ? `
        <div class="glass-card-lg p-16 text-center">
          <div class="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-slate-100 dark:bg-slate-800/60 border border-slate-700/40 mb-4">
            ${ICONS.book}
          </div>
          <p class="text-slate-500 dark:text-slate-400 text-sm">暂无文档</p>
          <p class="text-slate-400 dark:text-slate-500 text-xs mt-1">点击右上角上传文档开始构建知识库</p>
        </div>` : `
        <div class="space-y-3">
          ${list.map((kb, i) => `
          <div class="glass-card p-4 flex items-center justify-between hover:border-primary-500/30 transition-all group" style="animation-delay: ${i * 0.05}s">
            <div class="flex items-center gap-4 flex-1 min-w-0 cursor-pointer" onclick="App.viewKb(${kb.id})">
              <div class="w-10 h-10 rounded-xl bg-purple-500/10 text-purple-400 flex items-center justify-center border border-purple-500/15">${ICONS.book}</div>
              <div class="flex-1 min-w-0">
                <div class="font-medium text-slate-900 dark:text-slate-100 truncate group-hover:text-primary-400 transition-colors">${escapeHtml(kb.name)}</div>
                <div class="text-xs text-slate-400 dark:text-slate-500 mt-1">${formatSize(kb.file_size)} · ${kb.chunk_count} 块 · ${formatTime(kb.uploaded_at)}</div>
                ${kb.vector_error ? `<div class="text-xs text-red-400 mt-1 truncate">⚠ ${escapeHtml(kb.vector_error)}</div>` : ''}
              </div>
            </div>
            <div class="flex items-center gap-2 ml-4">
              ${statusBadge(kb.vector_status)}
              <button onclick="App.revectorizeKb(${kb.id})" class="btn-secondary px-3 py-1.5 text-xs inline-flex items-center gap-1" title="重新向量化">${ICONS.refresh} 重新向量化</button>
              <button onclick="App.deleteKb(${kb.id})" class="text-slate-400 dark:text-slate-500 hover:text-red-400 transition p-1.5 rounded-lg hover:bg-red-500/10">${ICONS.trash}</button>
            </div>
          </div>`).join('')}
        </div>`}
      </div>`;
  },

  // ==================== 知识库详情 ====================
  renderKbDetail() {
    const kb = State.kbDetail; if (!kb) return;
    const stuck = kb.vector_status === 'PROCESSING' || kb.vector_status === 'PENDING';
    const failed = kb.vector_status === 'FAILED';
    const ready = kb.vector_status === 'COMPLETED';
    this.root().innerHTML = `
      <div class="max-w-5xl mx-auto fade-in">
        <button onclick="State.kbDetail=null;UI.render()" class="text-sm text-slate-400 dark:text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 mb-6 inline-flex items-center gap-1.5 transition-colors">${ICONS.arrowLeft} 返回列表</button>

        <!-- Info Card -->
        <div class="glass-card-lg p-6 mb-6">
          <div class="flex items-center justify-between mb-3">
            <h2 class="text-lg font-bold text-slate-900 dark:text-slate-100" style="">${escapeHtml(kb.name)}</h2>
            <button onclick="App.revectorizeKb(${kb.id})" class="btn-secondary px-3 py-1.5 text-sm inline-flex items-center gap-1.5">${ICONS.refresh} 重新向量化</button>
          </div>
          <div class="flex items-center gap-4 text-xs text-slate-400 dark:text-slate-500 mb-2">
            <span>${formatSize(kb.file_size)}</span><span>${kb.content_type}</span><span>${kb.chunk_count} 分块</span>${statusBadge(kb.vector_status)}
          </div>
          ${kb.vector_error ? `<div class="text-xs text-red-400 mt-1">⚠ 错误: ${escapeHtml(kb.vector_error)}</div>` : ''}
          ${stuck ? '<div class="text-xs text-amber-400 mt-1">⚠ 向量化可能未完成，点击「重新向量化」重试</div>' : ''}
        </div>

        ${ready ? `
        <!-- RAG Query -->
        <div class="glass-card-lg p-6">
          <h3 class="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-4 inline-flex items-center gap-2">${ICONS.search} RAG 检索测试</h3>
          <div class="flex gap-2 mb-4">
            <input id="kb-query" type="text" placeholder="输入问题测试检索效果..." class="input-field" onkeydown="if(event.key==='Enter'){App.queryKb()}">
            <button onclick="App.queryKb()" class="btn-primary px-4 py-2 text-sm shrink-0">检索</button>
          </div>
          <div id="kb-query-result"></div>
        </div>
        ` : '<div class="glass-card p-10 text-center text-slate-400 dark:text-slate-500 text-sm">向量化完成后可使用 RAG 检索</div>'}
      </div>`;
  },

  // ==================== 会话列表 ====================
  renderSessionList() {
    const list = State.sessions;
    this.root().innerHTML = `
      <div class="max-w-4xl mx-auto fade-in">
        <!-- Header -->
        <div class="mb-6">
          <h2 class="text-xl font-bold text-slate-900 dark:text-slate-100 tracking-tight" style="">会话记录</h2>
          <p class="text-sm text-slate-400 dark:text-slate-500 mt-0.5">查看历史面试会话</p>
        </div>

        ${list.length === 0 ? `
        <div class="glass-card-lg p-16 text-center">
          <div class="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-slate-100 dark:bg-slate-800/60 border border-slate-700/40 mb-4">
            ${ICONS.list}
          </div>
          <p class="text-slate-500 dark:text-slate-400 text-sm">暂无会话记录</p>
          <p class="text-slate-400 dark:text-slate-500 text-xs mt-1">完成一次面试后会自动记录</p>
        </div>` : `
        <div class="space-y-3">
          ${list.map((s, i) => `
          <div class="glass-card p-4 flex items-center gap-4 hover:border-primary-500/30 transition-all cursor-pointer group" onclick="App.viewSession('${s.session_id}')" style="animation-delay: ${i * 0.05}s">
            <div class="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center border border-emerald-500/15">${ICONS.mic}</div>
            <div class="flex-1 min-w-0">
              <div class="text-sm font-medium text-slate-900 dark:text-slate-100 group-hover:text-primary-400 transition-colors">${escapeHtml(s.skill_id)} · ${s.difficulty}</div>
              <div class="text-xs text-slate-400 dark:text-slate-500 mt-1">${s.total_questions} 题 · ${formatTime(s.created_at)}</div>
            </div>
            <div class="flex items-center gap-3">
              ${s.overall_score != null ? `<span class="text-lg font-bold ${scoreColor(s.overall_score / 10)}" style="">${s.overall_score}</span>` : ''}
              ${statusBadge(s.status)}
            </div>
            <button onclick="event.stopPropagation();App.deleteSession('${s.session_id}')" class="text-slate-400 dark:text-slate-500 hover:text-red-400 transition p-1.5 rounded-lg hover:bg-red-500/10">${ICONS.trash}</button>
          </div>`).join('')}
        </div>`}
      </div>`;
  },

  // ==================== 会话详情 ====================
  renderSessionDetail() {
    const d = State.sessionDetail; if (!d) return;
    this.root().innerHTML = `
      <div class="max-w-4xl mx-auto fade-in">
        <button onclick="State.sessionDetail=null;UI.render()" class="text-sm text-slate-400 dark:text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 mb-6 inline-flex items-center gap-1.5 transition-colors">${ICONS.arrowLeft} 返回列表</button>

        <!-- Header Card -->
        <div class="glass-card-lg p-6 mb-6">
          <h2 class="text-lg font-bold text-slate-900 dark:text-slate-100 mb-2" style="">${escapeHtml(d.skill_id)} · ${d.difficulty}</h2>
          <div class="flex items-center gap-4 text-xs text-slate-400 dark:text-slate-500">
            <span>${d.total_questions} 题</span><span>${d.status}</span><span>${formatTime(d.created_at)}</span>
            ${d.overall_score != null ? `<span class="text-lg font-bold ${scoreColor(d.overall_score / 10)}" style="">${d.overall_score}分</span>` : ''}
          </div>
        </div>

        <!-- Questions -->
        ${d.question_details?.length ? `<div class="space-y-3">${d.question_details.map((q, i) => `
          <div class="glass-card p-4" style="animation-delay: ${i * 0.05}s">
            <div class="flex items-center gap-2 mb-2">
              <span class="text-xs text-slate-400 dark:text-slate-500">#${i + 1}</span>
              <span class="text-xs bg-slate-100 dark:bg-slate-800/60 text-slate-400 dark:text-slate-500 px-2 py-0.5 rounded-full border border-slate-800">${escapeHtml(q.category)}</span>
              ${q.score != null ? `<span class="text-sm font-bold ${scoreColor(q.score)}">${q.score}/10</span>` : ''}
            </div>
            <p class="text-sm text-slate-800 dark:text-slate-200 mb-2 leading-relaxed">${escapeHtml(q.question)}</p>
            ${q.user_answer ? `<p class="text-sm text-slate-500 dark:text-slate-400 mb-2 inline-flex items-start gap-2">${ICONS.user} <span>${escapeHtml(q.user_answer)}</span></p>` : ''}
            ${q.feedback ? `<p class="text-xs text-slate-400 dark:text-slate-500 inline-flex items-start gap-2">${ICONS.lightbulb} <span>${escapeHtml(q.feedback)}</span></p>` : ''}
          </div>
        `).join('')}</div>` : ''}
      </div>`;
  },
};

// ========== 业务逻辑 ==========
const App = {
  // ---- 导航切换 ----
  async switchTab(tab) {
    State.tab = tab;
    State.resumeDetail = null;
    State.kbDetail = null;
    State.sessionDetail = null;
    UI.render();
    if (tab === 'resume') await this.loadResumes();
    if (tab === 'kb') await this.loadKbList();
    if (tab === 'sessions') await this.loadSessions();
  },

  // ---- 技能 ----
  async loadSkills() {
    try {
      const skills = await API.interview.listSkills();
      State.skills = skills;
      const sel = document.getElementById('cfg-skill');
      if (sel) {
        sel.innerHTML = skills.map(s => `<option value="${s.id}" ${s.id === State.skillId ? 'selected' : ''}>${s.name} – ${s.description}</option>`).join('');
      }
    } catch (e) {
      console.warn('加载技能失败', e);
    }
  },

  // ---- 面试 ----
  async startInterview() {
    const sessionId = document.getElementById('cfg-session')?.value?.trim();
    const skillId = document.getElementById('cfg-skill')?.value?.trim();
    const resumeText = document.getElementById('cfg-resume')?.value?.trim() || '';
    const agentMode = document.getElementById('cfg-agent')?.checked ?? true;
    const questionCount = parseInt(document.getElementById('cfg-count')?.value) || 5;

    if (!sessionId) return showToast('会话 ID 不能为空', 'error');
    if (!skillId) return showToast('请选择技能方向', 'error');

    const btn = document.getElementById('btn-start');
    if (btn) { btn.disabled = true; btn.innerHTML = `<div class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div> 启动中...`; }

    try {
      const data = await API.interview.start({
        session_id: sessionId, skill_id: skillId, difficulty: State.difficulty,
        question_count: questionCount, resume_text: resumeText, agent_mode: agentMode,
      });
      State.sessionId = sessionId; State.skillId = skillId; State.resumeText = resumeText;
      State.agentMode = agentMode; State.started = true; State.done = data.done || false;
      if (data.done) {
        State.report = data.report; State.candidateProfile = data.candidate_profile; State.topicPerformance = data.topic_performance;
      } else {
        State.currentQuestion = { question: data.question, question_index: data.question_index, category: data.category, is_follow_up: data.is_follow_up };
        State.currentIndex = data.question_index ?? 0; State.hint = data.hint || ''; State.interviewStrategy = data.interview_strategy || null;
      }
      UI.render(); showToast('面试已开始', 'success');
    } catch (e) { showToast('启动失败: ' + e.message, 'error'); }
    finally { if (btn) { btn.disabled = false; btn.innerHTML = `${ICONS.zap} 开始面试`; } }
  },

  async submitAnswer() {
    const input = document.getElementById('answer-input');
    const answer = input?.value?.trim();
    if (!answer) return showToast('请输入答案', 'error');
    const btn = document.getElementById('btn-submit');
    if (btn) { btn.disabled = true; btn.textContent = '提交中...'; }
    if (input) input.disabled = true;
    try {
      const data = await API.interview.submitAnswer(State.sessionId, answer, State.agentMode);
      State.history.push({ question: State.currentQuestion?.question || '', answer, evaluation: data.evaluation || null });
      State.done = data.done || false;
      if (data.done) {
        State.report = data.report; State.candidateProfile = data.candidate_profile; State.topicPerformance = data.topic_performance;
      } else {
        State.currentQuestion = { question: data.question, question_index: data.question_index, category: data.category, is_follow_up: data.is_follow_up };
        State.currentIndex = data.question_index ?? State.currentIndex + 1;
        State.evaluation = data.evaluation || null; State.agentReasoning = data.agent_reasoning || null; State.hint = data.hint || '';
      }
      UI.render();
    } catch (e) { showToast('提交失败: ' + e.message, 'error'); }
    finally { if (btn) { btn.disabled = false; btn.textContent = '提交答案'; } if (input) input.disabled = false; }
  },

  reset() {
    Object.assign(State, { sessionId: '', started: false, done: false, currentQuestion: null, currentIndex: 0, evaluation: null, agentReasoning: null, interviewStrategy: null, hint: '', report: null, candidateProfile: null, topicPerformance: null, history: [] });
    UI.render();
  },

  // ---- 简历 ----
  async loadResumes() {
    const tab = State.tab;
    UI.showLoading('加载简历列表...');
    try {
      const data = await API.resume.list();
      if (State.tab !== tab) return;
      State.resumes = data;
      UI.render();
    } catch (e) {
      if (State.tab !== tab) return;
      UI.showError('加载简历失败: ' + e.message, "App.loadResumes()");
    }
  },
  async uploadResume(file) {
    if (!file) return;
    showToast('上传并分析中...', 'info');
    try { await API.resume.upload(file); showToast('上传成功', 'success'); await this.loadResumes(); } catch (e) { showToast('上传失败: ' + e.message, 'error'); }
  },
  async viewResume(id) {
    UI.showLoading('加载简历详情...');
    try { State.resumeDetail = await API.resume.getDetail(id); UI.render(); } catch (e) { UI.showError('加载详情失败: ' + e.message); }
  },
  async deleteResume(id) {
    if (!confirm('确定删除此简历？')) return;
    try { await API.resume.delete(id); showToast('已删除', 'success'); await this.loadResumes(); } catch (e) { showToast('删除失败: ' + e.message, 'error'); }
  },

  // ---- 知识库 ----
  async loadKbList() {
    const tab = State.tab;
    UI.showLoading('加载知识库列表...');
    try {
      const [list, stats] = await Promise.all([API.kb.list(), API.kb.stats()]);
      if (State.tab !== tab) return;
      State.kbList = list;
      State.kbStats = stats;
      UI.render();
    } catch (e) {
      if (State.tab !== tab) return;
      UI.showError('加载知识库失败: ' + e.message, "App.loadKbList()");
    }
  },
  async uploadKb(file) {
    if (!file) return;
    const name = prompt('知识库名称（可选）', file.name.replace(/\.[^.]+$/, ''));
    showToast('上传并向量化中...', 'info');
    try { await API.kb.upload(file, name); showToast('上传成功', 'success'); await this.loadKbList(); } catch (e) { showToast('上传失败: ' + e.message, 'error'); }
  },
  async viewKb(id) {
    UI.showLoading('加载知识库详情...');
    try { State.kbDetail = await API.kb.getDetail(id); UI.render(); } catch (e) { UI.showError('加载详情失败: ' + e.message); }
  },
  async deleteKb(id) {
    if (!confirm('确定删除此知识库？')) return;
    try { await API.kb.delete(id); showToast('已删除', 'success'); await this.loadKbList(); } catch (e) { showToast('删除失败: ' + e.message, 'error'); }
  },
  async revectorizeKb(id) {
    showToast('重新向量化中...', 'info');
    try {
      await API.kb.revectorize(id);
      showToast('向量化完成', 'success');
      if (State.kbDetail?.id === id) {
        State.kbDetail = await API.kb.getDetail(id);
        UI.render();
      } else {
        await this.loadKbList();
      }
    } catch (e) { showToast('向量化失败: ' + e.message, 'error'); }
  },
  async queryKb() {
    const input = document.getElementById('kb-query');
    const q = input?.value?.trim();
    if (!q) return;
    const resultEl = document.getElementById('kb-query-result');
    if (resultEl) resultEl.innerHTML = '<p class="text-sm text-slate-400 dark:text-slate-500">检索并生成回答中...</p>';
    try {
      const data = await API.kb.query([State.kbDetail.id], q);
      if (resultEl) {
        let html = '';
        if (data.answer) {
          html += `<div class="mb-4 p-4 glass-card border-primary-500/20">
            <div class="text-xs text-primary-500 mb-2 inline-flex items-center gap-1">${ICONS.user} AI 回答</div>
            <div class="text-sm text-slate-800 dark:text-slate-200 markdown-body">${escapeHtml(data.answer)}</div>
          </div>`;
        }
        const sources = data.sources || [];
        if (sources.length) {
          html += `<details class="mt-2"><summary class="text-xs text-slate-400 dark:text-slate-500 cursor-pointer hover:text-slate-500 dark:hover:text-slate-400 mb-2 inline-flex items-center gap-1">${ICONS.search} 检索来源 (${sources.length} 条)</summary>
          <div class="space-y-2">${sources.map((r, i) => `<div class="glass-card p-3"><div class="flex items-center gap-2 mb-1"><span class="text-xs text-slate-400 dark:text-slate-500">来源${i + 1}</span><span class="text-xs text-primary-500">相关度: ${r.score?.toFixed(4)}</span></div><p class="text-xs text-slate-500 dark:text-slate-400 max-h-32 overflow-y-auto">${escapeHtml(r.content)}</p></div>`).join('')}</div></details>`;
        }
        resultEl.innerHTML = html || '<p class="text-sm text-slate-400 dark:text-slate-500">未找到相关内容</p>';
      }
    } catch (e) { if (resultEl) resultEl.innerHTML = `<p class="text-sm text-red-400">${escapeHtml(e.message)}</p>`; }
  },

  // ---- 会话 ----
  async loadSessions() {
    const tab = State.tab;
    UI.showLoading('加载会话记录...');
    try {
      const data = await API.interview.listSessions();
      if (State.tab !== tab) return;
      State.sessions = data;
      UI.render();
    } catch (e) {
      if (State.tab !== tab) return;
      UI.showError('加载会话失败: ' + e.message, "App.loadSessions()");
    }
  },
  async viewSession(id) {
    UI.showLoading('加载会话详情...');
    try { State.sessionDetail = await API.interview.getSession(id); UI.render(); } catch (e) { UI.showError('加载详情失败: ' + e.message); }
  },
  async deleteSession(id) {
    if (!confirm('确定删除此会话？')) return;
    try { await API.interview.deleteSession(id); showToast('已删除', 'success'); await this.loadSessions(); } catch (e) { showToast('删除失败: ' + e.message, 'error'); }
  },
};

// ========== 初始化 ==========
document.addEventListener('DOMContentLoaded', () => { UI.render(); });
