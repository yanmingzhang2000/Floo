import { api } from '@/utils/request'

// ===== 用户 =====
export const userApi = {
  login: (data: { username: string; password: string }) =>
    api.post('/api/user/login', data),
  register: (data: { username: string; password: string }) =>
    api.post('/api/user/register', data),
  wechatLogin: (code: string) =>
    api.post('/api/user/wechat-login', { code }),
  bindWechat: (userId: number, code: string) =>
    api.post(`/api/user/bind-wechat?user_id=${userId}`, { code }),
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
    api.post('/api/daily/generate', { user_id: userId, theme_override: themeOverride, force }, { timeout: 120000 }),
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
  markLearned: (userId: number, contentId: number) =>
    api.post('/api/daily/learned/mark', null, { params: { user_id: userId, content_id: contentId } }),
  toggleLearned: (userId: number, contentId: number) =>
    api.post('/api/daily/learned/toggle', null, { params: { user_id: userId, content_id: contentId } }),
  checkLearned: (userId: number, contentId: number) =>
    api.get('/api/daily/learned/check', { params: { user_id: userId, content_id: contentId } }),
  getLearnedIds: (userId: number) =>
    api.get('/api/daily/learned/list', { params: { user_id: userId } }),
  getFilteredLearnedContents: (userId: number, startDate?: string, endDate?: string) =>
    api.get('/api/daily/learned/filtered', { 
      params: { user_id: userId, start_date: startDate, end_date: endDate } 
    }),
  getLearnedReviewTasks: (userId: number) =>
    api.get('/api/daily/review/learned', { params: { user_id: userId } }),
  createCustomContent: (userId: number, text: string) =>
    api.post('/api/daily/custom-content', { user_id: userId, text }),
  getCustomContents: (userId: number) =>
    api.get('/api/daily/custom-content', { params: { user_id: userId } }),
  deleteCustomContent: (contentId: number, userId: number) =>
    api.delete(`/api/daily/custom-content/${contentId}`, { params: { user_id: userId } }),
}

// ===== 默写 =====
export const dictationApi = {
  submit: (userId: number, contentId: number, userInput: string) =>
    api.post('/api/dictation/submit', { user_id: userId, content_id: contentId, user_input: userInput }),
  getHistory: (userId: number, limit = 1000) =>
    api.get('/api/dictation/history', { params: { user_id: userId, limit } }),
  getHistoryDetail: (dictationId: number, userId: number) =>
    api.get(`/api/dictation/history/${dictationId}`, { params: { user_id: userId } }),
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

// ===== 词典查询 =====
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
  toggleMastered: (userId: number, word: string) =>
    api.patch('/api/favorites/mastered', null, { params: { user_id: userId, word } }),
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
  givePointsToAll: (amount: number = 50) =>
    api.post(`/api/shop/admin/give-points?amount=${amount}`),
}

// ===== 单词复习 =====
export const wordReviewApi = {
  getDue: (userId: number, limit = 15) =>
    api.get('/api/word-review/due', { params: { user_id: userId, limit } }),
  submit: (userId: number, word: string, correct: boolean, accuracy = 100) =>
    api.post('/api/word-review/submit', { user_id: userId, word, correct, accuracy }),
}

// ===== 语音评测 =====
export const speechApi = {
  evaluate: (audio: string, text: string, langType = 'en') =>
    api.post('/api/speech/evaluate', { audio, text, lang_type: langType, format: 'wav' }),
}

// ===== TTS 语音合成 =====
export const ttsApi = {
  synthesize: (text: string, langType = '0') =>
    api.post('/api/tts/synthesize', { text, lang_type: langType }),
}

// ===== AI陪练 =====
export const aiCoachApi = {
  // 语音转文字 + 语言检测
  transcribe: (audio: string, format: string = 'mp3') =>
    api.post('/api/ai-coach/transcribe', { audio, format }),
  
  // 聊天接口（中英翻译 / 英语问答）
  chat: (text: string, lang: string, history: Array<{role: string, content: string}> = []) =>
    api.post('/api/ai-coach/chat', { text, lang, history }),
  
  // 文字转语音
  tts: (text: string, lang: string = 'en') =>
    api.post('/api/ai-coach/tts', { text, lang }),
  
  // 获取学习报告
  getReport: (userId: number, sessionId: string) =>
    api.get(`/api/ai-coach/report/${sessionId}`, { params: { user_id: userId } }),
}

export default api
