/**
 * API 客户端 - Agent Meet
 */
const API = {
  BASE: window.location.origin,

  async request(method, path, body = null) {
    const opts = { method, headers: {} };
    if (body) {
      opts.headers['Content-Type'] = 'application/json';
      opts.body = JSON.stringify(body);
    }
    const res = await fetch(this.BASE + path, opts);
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    const data = await res.json();
    if (data.code != null && data.code !== 0) throw new Error(data.message || `请求失败 (code=${data.code})`);
    return data.data;
  },

  async upload(path, file, params = {}) {
    const form = new FormData();
    form.append('file', file);
    for (const [k, v] of Object.entries(params)) {
      if (v != null) form.append(k, v);
    }
    const res = await fetch(this.BASE + path, { method: 'POST', body: form });
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    const data = await res.json();
    if (data.code != null && data.code !== 0) throw new Error(data.message || `上传失败 (code=${data.code})`);
    return data.data;
  },

  post(path, body) { return this.request('POST', path, body); },
  get(path) { return this.request('GET', path); },
  del(path) { return this.request('DELETE', path); },

  // ---- 面试 ----
  interview: {
    start: (data) => API.post('/api/interview/start', data),
    submitAnswer: (sessionId, answer, agentMode = true) =>
      API.post(`/api/interview/sessions/${sessionId}/answer?agent_mode=${agentMode}`, { answer }),
    listSessions: () => API.get('/api/interview/sessions'),
    getSession: (id) => API.get(`/api/interview/sessions/${id}`),
    getReport: (id) => API.get(`/api/interview/sessions/${id}/report`),
    deleteSession: (id) => API.del(`/api/interview/sessions/${id}`),
    listSkills: () => API.get('/api/interview/skills'),
  },

  // ---- 简历 ----
  resume: {
    upload: (file) => API.upload('/api/resumes/upload', file),
    list: () => API.get('/api/resumes'),
    getDetail: (id) => API.get(`/api/resumes/${id}/detail`),
    delete: (id) => API.del(`/api/resumes/${id}`),
    reanalyze: (id) => API.post(`/api/resumes/${id}/reanalyze`),
  },

  // ---- 知识库 ----
  kb: {
    upload: (file, name, category) => API.upload('/api/knowledgebase/upload', file, { name, category }),
    list: () => API.get('/api/knowledgebase/list'),
    getDetail: (id) => API.get(`/api/knowledgebase/${id}`),
    delete: (id) => API.del(`/api/knowledgebase/${id}`),
    revectorize: (id) => API.post(`/api/knowledgebase/${id}/revectorize`),
    stats: () => API.get('/api/knowledgebase/stats'),
    query: (kbIds, question) => API.post('/api/knowledgebase/query', { knowledge_base_ids: kbIds, question }),
  },
};
