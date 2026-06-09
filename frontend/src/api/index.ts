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
}

// ===== 默写 =====
export const dictationApi = {
  submit: (userId: number, contentId: number, userInput: string) =>
    api.post('/api/dictation/submit', { user_id: userId, content_id: contentId, user_input: userInput }),
  getHistory: (userId: number) =>
    api.get('/api/dictation/history', { params: { user_id: userId } }),
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

export default api
