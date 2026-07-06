import axios from 'axios'

const API_BASE = 'https://floo-production.up.railway.app'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const userId = localStorage.getItem('user_id')
  if (userId) {
    config.params = { ...config.params, user_id: userId }
  }
  return config
})

// 全局错误拦截：网络异常、500 等不再静默吞掉
api.interceptors.response.use(
  (res) => res,
  (err) => {
    // 组件内部如果有 catch 并想自定义处理，可设 skipToast 跳过
    const skipToast = err.config?.skipToast
    if (!skipToast) {
      // 动态 import 避免循环依赖，仅在需要时加载
      import('../composables/useToast').then(({ useToast }) => {
        const toast = useToast()
        const status = err.response?.status
        const msg = err.response?.data?.detail || err.message || '网络异常'
        if (status === 401) {
          toast.error('登录已过期，请重新登录')
        } else if (status === 403) {
          toast.error('没有权限执行此操作')
        } else if (status === 404) {
          toast.warning('请求的资源不存在')
        } else if (status === 429) {
          toast.warning('请求太频繁，请稍后再试')
        } else if (status >= 500) {
          toast.error('服务器繁忙，请稍后再试')
        } else {
          toast.error(msg)
        }
      })
    }
    return Promise.reject(err)
  }
)

// ===== 用户 =====
export const userApi = {
  login: (data: { username: string; password: string }) =>
    api.post('/api/user/login', data),
  register: (data: { username: string; password: string }) =>
    api.post('/api/user/register', data),
  getPreference: (userId: number) =>
    api.get(`/api/user/${userId}/preference`),
  updatePreference: (userId: number, data: { difficulty_level?: string; theme_type?: string; daily_goal_minutes?: number }) =>
    api.put(`/api/user/${userId}/preference`, data),
  getPoints: (userId: number) =>
    api.get(`/api/user/${userId}/points`),
}

// ===== 每日学习 =====
export const dailyApi = {
  getTodayList: (userId: number) =>
    api.get('/api/daily/today-list', { params: { user_id: userId } }),
  getToday: (userId: number) =>
    api.get('/api/daily/today', { params: { user_id: userId } }),
  generate: (userId: number, themeOverride?: string, force = false) =>
    api.post('/api/daily/generate', { user_id: userId, theme_override: themeOverride, force }),
  getList: (limit = 20) =>
    api.get('/api/daily/list', { params: { limit } }),
  getContent: (contentId: number) =>
    api.get(`/api/daily/content/${contentId}`),
  getReviewTasks: (userId: number) =>
    api.get('/api/daily/review', { params: { user_id: userId } }),
  getAllProgress: (userId: number) =>
    api.get('/api/daily/progress', { params: { user_id: userId } }),
  cleanup: () =>
    api.post('/api/daily/cleanup'),
  // 已学内容
  markLearned: (userId: number, contentId: number) =>
    api.post('/api/daily/learned/mark', null, { params: { user_id: userId, content_id: contentId } }),
  toggleLearned: (userId: number, contentId: number) =>
    api.post('/api/daily/learned/toggle', null, { params: { user_id: userId, content_id: contentId } }),
  checkLearned: (userId: number, contentId: number) =>
    api.get('/api/daily/learned/check', { params: { user_id: userId, content_id: contentId } }),
  getLearnedIds: (userId: number) =>
    api.get('/api/daily/learned/list', { params: { user_id: userId } }),
  getLearnedReviewTasks: (userId: number) =>
    api.get('/api/daily/review/learned', { params: { user_id: userId } }),
  // 自定义内容
  createCustomContent: (userId: number, text: string) =>
    api.post('/api/daily/custom-content', { user_id: userId, text }),
  getCustomContents: (userId: number) =>
    api.get('/api/daily/custom-content', { params: { user_id: userId } }),
  deleteCustomContent: (contentId: number, userId: number) =>
    api.delete(`/api/daily/custom-content/${contentId}`, { params: { user_id: userId } }),
  regenerateCustomContent: (contentId: number, userId: number) =>
    api.post(`/api/daily/custom-content/${contentId}/regenerate`, null, { params: { user_id: userId }, timeout: 120000 }),
}

// ===== 默写 =====
export const dictationApi = {
  submit: (userId: number, contentId: number, userInput: string) =>
    api.post('/api/dictation/submit', { user_id: userId, content_id: contentId, user_input: userInput }),
  getHistory: (userId: number, limit = 1000) =>
    api.get('/api/dictation/history', { params: { user_id: userId, limit } }),
}

// ===== 打卡 =====
export const checkinApi = {
  getCalendar: (userId: number, year: number, month: number) =>
    api.get('/api/checkin/calendar', { params: { user_id: userId, year, month } }),
  doCheckin: (userId: number) =>
    api.post('/api/checkin', { user_id: userId }),
  getWeekly: (userId: number) =>
    api.get('/api/checkin/weekly', { params: { user_id: userId } }),
}

// ===== 词典查询（通过后端代理） =====
export const dictionaryApi = {
  lookup: (word: string) =>
    api.get('/api/dictionary/lookup', { params: { word } }),
}

// ===== 生成次数限制 =====
export const generationLimitApi = {
  getLimit: (userId: number) =>
    api.get('/api/daily/generation-limit', { params: { user_id: userId } }),
}

// ===== 词汇收藏夹 =====
export const favoritesApi = {
  add: (userId: number, word: string, phonetic?: string, meaning?: string, source?: string, contentId?: number) =>
    api.post('/api/favorites/add', { user_id: userId, word, phonetic, meaning, source, source_content_id: contentId }),
  remove: (userId: number, word: string) =>
    api.delete('/api/favorites/remove', { params: { user_id: userId, word } }),
  list: (userId: number, limit = 100) =>
    api.get('/api/favorites/list', { params: { user_id: userId, limit } }),
  check: (userId: number, word: string) =>
    api.get('/api/favorites/check', { params: { user_id: userId, word } }),
}

// ===== 积分商城 =====
export const shopApi = {
  getCharacters: (userId: number) =>
    api.get('/api/shop/characters', { params: { user_id: userId } }),
  getBalance: (userId: number) =>
    api.get('/api/shop/balance', { params: { user_id: userId } }),
  openBox: (userId: number, count: number) =>
    api.post('/api/shop/open-box', { user_id: userId, count }),
  getCollection: (userId: number) =>
    api.get('/api/shop/collection', { params: { user_id: userId } }),
}

// ===== 语音评测 =====
export const speechApi = {
  evaluate: (audio: string, text: string, langType = 'en') =>
    api.post('/api/speech/evaluate', { audio, text, lang_type: langType, format: 'wav' }),
}

export default api
