<template>
  <view class="page-container">
    <view class="nav-bar">
      <view class="nav-left"></view>
      <text class="nav-title">复习</text>
      <view class="nav-right">
        <view class="nav-avatar" @tap="showProfile = true">
          <text>{{ usernameInitial }}</text>
        </view>
      </view>
    </view>

    <view class="underline-tabs">
      <view class="underline-tab" :class="{ active: activeTab === 'review' }" @tap="switchTab('review')">
        <text>复习</text>
        <view v-if="dueTasks.length" class="tab-badge"><text>{{ dueTasks.length }}</text></view>
      </view>
      <view class="underline-tab" :class="{ active: activeTab === 'dictation' }" @tap="switchTab('dictation')">
        <text>默写</text>
      </view>
      <view class="underline-tab" :class="{ active: activeTab === 'vocab' }" @tap="switchTab('vocab')">
        <text>背单词</text>
      </view>
    </view>

    <view v-if="loading" class="loading">
      <view class="spinner"></view>
    </view>

    <template v-else>
      <!-- ===== 复述 ===== -->
      <view v-show="activeTab === 'review'">
        <view class="stats-banner">
          <view class="stat-item">
            <text class="stat-icon">📚</text>
            <text class="stat-value">{{ progressList.length }}</text>
            <text class="stat-label">总内容</text>
          </view>
          <view class="stat-item">
            <text class="stat-icon">✅</text>
            <text class="stat-value" style="color: var(--success)">{{ masteredCount }}</text>
            <text class="stat-label">已掌握</text>
          </view>
          <view class="stat-item">
            <text class="stat-icon">⏰</text>
            <text class="stat-value" style="color: var(--warning)">{{ dueTasks.length }}</text>
            <text class="stat-label">待复习</text>
          </view>
        </view>
        <view v-if="dueTasks.length" class="section">
          <text class="section-title">今日待复习</text>
          <view class="task-list">
            <view v-for="task in dueTasks" :key="task.content_id" class="card task-item">
              <view class="task-avatar" :style="{ background: stageColors[task.review_stage] || '#5B9AA8' }">
                <text class="task-stage">S{{ task.review_stage }}</text>
              </view>
              <view class="task-info">
                <text class="task-title">{{ task.title }}</text>
                <text class="task-meta">准确率 {{ task.last_accuracy.toFixed(0) }}% · 下次 {{ task.next_review_date }}</text>
              </view>
              <button class="btn btn-sm btn-primary" @tap="goDetail(task.content_id)">
                <text>去复述</text>
              </button>
            </view>
          </view>
        </view>
        <view v-else class="empty-state">
          <text class="icon" style="color: var(--success)">✅</text>
          <text class="empty-text">暂无待复习内容</text>
          <text class="empty-hint">继续学习新内容吧</text>
        </view>
      </view>

      <!-- ===== 默写 ===== -->
      <view v-show="activeTab === 'dictation'">
        <!-- 历史记录优先展示，因为默写入口在文章详情页 -->
        <view class="section">
          <text class="section-title">默写记录</text>
          <view v-if="historyLoadError" class="empty-state" style="cursor: pointer" @tap="loadData">
            <text class="icon">⚠️</text>
            <text class="empty-text">加载失败</text>
            <text class="empty-hint">点此重试</text>
          </view>
          <view v-else-if="historyList.length === 0" class="empty-state">
            <text class="icon">📜</text>
            <text class="empty-text">暂无默写记录</text>
            <text class="empty-hint">在文章阅读页点击「默写」开始练习</text>
          </view>
          <view v-else class="history-list">
            <view v-for="rec in historyList" :key="rec.dictation_id" class="card history-item" @tap="goDictationDetail(rec.dictation_id)">
              <view class="history-left">
                <text class="history-date">{{ formatDate(rec.created_at) }}</text>
                <text class="history-title ellipsis">{{ rec.content_title || '默写练习' }}</text>
              </view>
              <view class="history-right">
                <text class="history-accuracy" :class="getScoreClass(rec.accuracy_rate)">{{ rec.accuracy_rate.toFixed(0) }}%</text>
                <text class="history-points">+{{ rec.earned_points }}</text>
              </view>
            </view>
          </view>
        </view>

        <view class="section">
          <view class="section-title-row" @tap="showTodayContent = !showTodayContent">
            <text class="section-title">今日学习内容</text>
            <text class="section-toggle">{{ showTodayContent ? '收起 ▲' : '展开 ▼' }}</text>
          </view>
          <view v-if="showTodayContent">
            <view v-if="todayContents.length === 0" class="empty-state">
              <text class="icon">📝</text>
              <text class="empty-text">暂无内容</text>
            </view>
            <view v-else class="content-list">
              <view v-for="item in todayContents" :key="item.id" class="card content-item" @tap="startDictation(item)">
                <view class="content-left">
                  <text class="content-title">{{ item.title }}</text>
                  <text class="content-meta">{{ item.content_date }} · {{ item.difficulty_level }}</text>
                </view>
                <button class="btn btn-sm btn-outline" @tap.stop="startDictation(item)">
                  <text>默写</text>
                </button>
              </view>
            </view>
          </view>
        </view>
      </view>

      <!-- ===== 背单词（选义 + 默写随机出题） ===== -->
      <view v-show="activeTab === 'vocab'">
        <!-- 开始前 -->
        <view v-if="!vbActive" class="section">
          <text class="section-title">背单词</text>
          <view v-if="vbDueWords.length === 0" class="empty-state">
            <text class="icon">📖</text>
            <text class="empty-text">暂无待复习单词</text>
            <text class="empty-hint">收藏更多单词后再来复习</text>
          </view>
          <view v-else>
            <view class="card vocab-start-card">
              <view class="vocab-info">
                <text class="vocab-info-icon">📖</text>
                <view>
                  <text class="vocab-info-label">待复习单词</text>
                  <text class="vocab-info-count">{{ vbDueWords.length }}</text>
                </view>
              </view>
              <button class="btn btn-primary btn-sm" @tap="startVocab">
                <text>复习</text>
              </button>
            </view>
            <view class="vb-mode-hints">
              <view class="vb-mode-hint">
                <text class="vb-mode-icon">🎯</text>
                <text class="vb-mode-text">选义：看英文选中文释义</text>
              </view>
              <view class="vb-mode-hint">
                <text class="vb-mode-icon">✏️</text>
                <text class="vb-mode-text">默写：看中文拼写英文单词</text>
              </view>
            </view>
          </view>
        </view>

        <!-- 进行中 -->
        <view v-else class="vb-active">
          <view class="vocab-progress-bar-bg">
            <view class="vocab-progress-bar-fill" :style="{ width: ((vbIdx + 1) / vbWords.length * 100) + '%' }"></view>
          </view>
          <view class="vb-progress-row">
            <text class="vocab-progress-text">{{ vbIdx + 1 }} / {{ vbWords.length }}</text>
            <text class="vb-mode-tag">{{ vbCurrentMode === 'choice' ? '🎯 选义' : '✏️ 默写' }}</text>
          </view>

          <!-- ====== 选义模式 ====== -->
          <template v-if="vbCurrentMode === 'choice'">
            <view class="card wc-word-card">
              <text class="wc-word-text">{{ vbCurrentWord?.word }}</text>
              <text v-if="vbCurrentWord?.phonetic" class="wc-word-phonetic">{{ vbCurrentWord.phonetic }}</text>
            </view>
            <view class="wc-options">
              <view
                v-for="(opt, i) in vbChoiceOptions"
                :key="i"
                class="card wc-option"
                :class="{
                  correct: vbShowResult && opt === vbCurrentWord?.meaning,
                  wrong: vbShowResult && vbSelectedIdx === i && opt !== vbCurrentWord?.meaning,
                  selected: !vbShowResult && vbSelectedIdx === i,
                }"
                @tap="selectVbChoice(i)"
              >
                <text class="wc-option-label">{{ ['A', 'B', 'C', 'D'][i] }}</text>
                <text class="wc-option-text">{{ opt }}</text>
              </view>
            </view>
          </template>

          <!-- ====== 默写模式 ====== -->
          <template v-else>
            <view class="card vocab-hint-card">
              <text class="vocab-hint-label">中文释义</text>
              <text class="vocab-hint-meaning">{{ vbCurrentWord?.meaning || '' }}</text>
            </view>
            <view class="card vocab-input-card">
              <input v-model="vbDictInput" type="text" placeholder="输入英文单词..." class="vocab-input" @confirm="vbShowResult ? nextVbWord() : checkVbDict()" />
            </view>
          </template>

          <!-- 操作按钮 -->
          <view class="vb-actions">
            <template v-if="vbCurrentMode === 'choice'">
              <view v-if="vbShowResult" class="vb-result-line" :class="vbIsCorrect ? 'vb-correct' : 'vb-wrong'">
                <text>{{ vbIsCorrect ? '✅ 正确！' : '❌ 错误，正确答案：' + vbCurrentWord?.meaning }}</text>
              </view>
              <button v-if="!vbShowResult" class="btn btn-text" @tap="showVbAnswer">
                <text>不会，看答案</text>
              </button>
              <button v-if="vbShowResult" class="btn btn-primary btn-block btn-lg" @tap="nextVbWord">
                <text>{{ vbIdx < vbWords.length - 1 ? '下一个' : '查看结果' }}</text>
              </button>
            </template>
            <template v-else>
              <button v-if="!vbShowResult" class="btn btn-primary btn-block btn-lg" :disabled="!vbDictInput.trim()" @tap="checkVbDict">
                <text>确认</text>
              </button>
              <button v-if="!vbShowResult" class="btn btn-text" @tap="showVbAnswer">
                <text>不会，看答案</text>
              </button>
              <view v-if="vbShowResult" class="vb-result-line" :class="vbIsCorrect ? 'vb-correct' : 'vb-wrong'">
                <text>{{ vbIsCorrect ? '✅ 正确！' : '❌ 错误，正确答案：' + vbCurrentWord?.word }}</text>
              </view>
              <button v-if="vbShowResult" class="btn btn-primary btn-block btn-lg" @tap="nextVbWord">
                <text>{{ vbIdx < vbWords.length - 1 ? '下一个' : '查看结果' }}</text>
              </button>
            </template>
          </view>

          <!-- 完成 -->
          <view v-if="vbDone" class="card vocab-done-card">
            <text class="vocab-done-title">🎉 背单词完成</text>
            <view class="vocab-done-stats">
              <view class="vocab-done-stat">
                <text class="vocab-done-stat-num" style="color: var(--success)">{{ vbCorrectCount }}</text>
                <text class="vocab-done-stat-label">正确</text>
              </view>
              <view class="vocab-done-stat">
                <text class="vocab-done-stat-num" style="color: var(--error)">{{ vbWords.length - vbCorrectCount }}</text>
                <text class="vocab-done-stat-label">错误</text>
              </view>
            </view>
            <button class="btn btn-primary btn-block" @tap="resetVb">
              <text>返回</text>
            </button>
          </view>
        </view>
      </view>
    </template>

    <!-- 默写弹窗 -->
    <view v-if="dictatingContent" class="modal-overlay" @tap="dictatingContent = null">
      <view class="dictation-sheet" @tap.stop>
        <view class="dictation-sheet-top">
          <text class="tag tag-primary">默写练习</text>
          <view class="btn-icon dictation-close" @tap="dictatingContent = null"><text>✕</text></view>
        </view>
        <view class="dictation-hint-card">
          <text class="dictation-hint-label">中文翻译提示</text>
          <text class="dictation-hint-text">{{ dictatingContent.translation || '暂无翻译' }}</text>
        </view>
        <view style="padding: 0 32rpx">
          <button class="btn btn-sm btn-text" @tap="showOriginal = !showOriginal">
            <text>{{ showOriginal ? '🙈 隐藏原文' : '👁️ 显示原文' }}</text>
          </button>
        </view>
        <view v-if="showOriginal" class="dictation-original-card">
          <text class="dictation-original-text">{{ dictatingContent.article }}</text>
        </view>
        <view class="dictation-input-card">
          <textarea v-model="userInput" :maxlength="-1" placeholder="在这里输入默写的英文内容..." class="dictation-textarea" />
        </view>
        <view class="dictation-submit">
          <button class="btn btn-primary btn-block btn-lg" :disabled="submitting || !userInput.trim()" @tap="handleSubmit">
            <text>{{ submitting ? 'AI 批改中...' : '提交批改' }}</text>
          </button>
        </view>
        <view v-if="dictResult" class="card dictation-result-card">
          <!-- 分数行 -->
          <view class="dictation-score-area">
            <text class="dictation-score" :class="getScoreClass(dictResult.feedback.score)">{{ dictResult.feedback.score }}</text>
            <view class="dictation-score-meta">
              <text>准确率 {{ dictResult.accuracy_rate.toFixed(0) }}%</text>
              <text style="color: var(--success)">+{{ dictResult.earned_points }} 积分</text>
            </view>
          </view>
          <!-- AI 总评 -->
          <view v-if="dictResult.feedback.summary" class="dictation-feedback">
            <text class="dictation-feedback-label">AI 总评</text>
            <text class="dictation-feedback-text">{{ dictResult.feedback.summary }}</text>
          </view>
          <!-- 错误明细 -->
          <view v-if="dictResult.feedback.diffs && dictResult.feedback.diffs.length" class="dictation-diffs">
            <text class="dictation-feedback-label">错误明细</text>
            <view v-for="(d, i) in dictResult.feedback.diffs" :key="i" class="diff-item">
              <text class="diff-type" :class="'diff-' + d.type">{{ { missing: '漏写', wrong: '写错', extra: '多写' }[d.type] || d.type }}</text>
              <view class="diff-detail">
                <text v-if="d.expected" class="diff-expected">✓ {{ d.expected }}</text>
                <text v-if="d.actual && d.type !== 'missing'" class="diff-actual">✗ {{ d.actual }}</text>
              </view>
            </view>
          </view>
          <!-- 学习建议 -->
          <view v-if="dictResult.feedback.suggestions && dictResult.feedback.suggestions.length" class="dictation-suggestions">
            <text class="dictation-feedback-label">建议</text>
            <view v-for="(s, i) in dictResult.feedback.suggestions" :key="i" class="suggestion-item">
              <text class="suggestion-text">• {{ s }}</text>
            </view>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { dailyApi, dictationApi, wordReviewApi } from '@/api'
import { useAuthStore } from '@/stores'
import { navTo } from '@/utils/router'
import type { LearningContent, DictationResult, DictationHistory, ReviewTask, MemoryProgress } from '@/types'

const auth = useAuthStore()
const loading = ref(true)
const activeTab = ref<'review' | 'dictation' | 'vocab'>('review')
const showProfile = ref(false)

// 复述
const dueTasks = ref<ReviewTask[]>([])
const progressList = ref<MemoryProgress[]>([])
const masteredCount = ref(0)

// 默写
const todayContents = ref<LearningContent[]>([])
const dictatingContent = ref<LearningContent | null>(null)
const showOriginal = ref(false)
const userInput = ref('')
const submitting = ref(false)
const dictResult = ref<DictationResult | null>(null)
const historyList = ref<DictationHistory[]>([])
const historyLoadError = ref(false)
const showTodayContent = ref(false)

// 背单词
const vbDueWords = ref<any[]>([])
const vbDistractors = ref<any[]>([])
const vbActive = ref(false)
const vbWords = ref<any[]>([])
const vbIdx = ref(0)
const vbCurrentMode = ref<'choice' | 'dictation'>('choice')
const vbChoiceOptions = ref<string[]>([])
const vbSelectedIdx = ref(-1)
const vbDictInput = ref('')
const vbShowResult = ref(false)
const vbIsCorrect = ref(false)
const vbDone = ref(false)
const vbCorrectCount = ref(0)

const vbCurrentWord = computed(() => vbWords.value[vbIdx.value] || null)
const usernameInitial = computed(() => (auth.username?.[0] || '?').toUpperCase())

const stageColors: Record<number, string> = {
  0: '#9E9E9E', 1: '#F44336', 2: '#FF9800',
  3: '#FFC107', 4: '#4CAF50', 5: '#2196F3',
}

onLoad((options) => {
  if (options?.tab === 'dictation') activeTab.value = 'dictation'
  if (options?.tab === 'vocab') activeTab.value = 'vocab'
})

function switchTab(tab: typeof activeTab.value) {
  activeTab.value = tab
}

function goDetail(contentId: number) { navTo(`/pages/detail/index?id=${contentId}`) }
function goDictationDetail(dictationId: number) { navTo(`/pages/dictation-detail/index?id=${dictationId}`) }
function getScoreClass(score: number) {
  if (score >= 80) return 'score-green'
  if (score >= 60) return 'score-orange'
  return 'score-red'
}

function formatDate(dateStr: string) {
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

// ===== 默写 =====
function startDictation(item: LearningContent) {
  dictatingContent.value = item
  showOriginal.value = false
  userInput.value = ''
  dictResult.value = null
}

async function handleSubmit() {
  if (!dictatingContent.value || !userInput.value.trim()) return
  submitting.value = true
  try {
    const { data } = await dictationApi.submit(auth.currentUserId, dictatingContent.value.id, userInput.value)
    dictResult.value = data
  } catch { uni.showToast({ title: '提交失败', icon: 'none' }) }
  submitting.value = false
}

// ===== 背单词 =====
async function loadVocabReview() {
  try {
    const { data } = await wordReviewApi.getDue(auth.currentUserId, 20)
    vbDueWords.value = data.words || []
    vbDistractors.value = data.distractors || []
  } catch {
    vbDueWords.value = []
    vbDistractors.value = []
  }
}

function shuffleArray<T>(array: T[]): T[] {
  const shuffled = [...array]
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
  }
  return shuffled
}

function pickMode(): 'choice' | 'dictation' {
  return Math.random() < 0.5 ? 'choice' : 'dictation'
}

function startVocab() {
  if (vbDueWords.value.length === 0) return
  const pool = shuffleArray(vbDueWords.value).slice(0, Math.min(15, vbDueWords.value.length))
  // 随机为每个词分配模式
  vbWords.value = pool.map(w => ({ ...w, _mode: pickMode() }))
  vbIdx.value = 0
  vbCurrentMode.value = vbWords.value[0]._mode
  vbSelectedIdx.value = -1
  vbDictInput.value = ''
  vbShowResult.value = false
  vbIsCorrect.value = false
  vbDone.value = false
  vbCorrectCount.value = 0
  vbActive.value = true
  generateVbOptions()
}

// 兜底干扰词：当用户自己的词库不够时补充，保证始终 4 个选项
const FALLBACK_DISTRACTORS = [
  'n. 城市', 'v. 走路', 'n. 太阳', 'v. 喜爱', 'adj. 大的',
  'n. 书本', 'v. 学习', 'n. 家庭', 'adj. 漂亮的', 'v. 运动',
  'n. 时间', 'v. 写作', 'n. 水果', 'adj. 快乐的', 'n. 动物',
  'v. 阅读', 'n. 音乐', 'adj. 聪明的', 'v. 思考', 'n. 食物',
  'n. 道路', 'v. 跑步', 'n. 花朵', 'adj. 温暖的', 'n. 故事',
  'v. 唱歌', 'n. 图片', 'adj. 重要的', 'v. 帮助', 'n. 电影',
  'n. 早晨', 'v. 休息', 'n. 眼睛', 'adj. 安静的', 'n. 椅子',
  'v. 等待', 'n. 月亮', 'adj. 新的', 'v. 站立', 'n. 电话',
  'n. 礼物', 'v. 微笑', 'n. 雨伞', 'adj. 高的', 'n. 窗户',
]

function generateVbOptions() {
  const current = vbCurrentWord.value
  if (!current) return
  const correct = current.meaning || ''

  // 1. 从用户自己的干扰项池取有效释义
  const pool = shuffleArray(vbDistractors.value.filter((d: any) => d.meaning && d.meaning.trim() && d.meaning.trim() !== correct))
  const distractorMeanings = pool.slice(0, 3).map((d: any) => d.meaning)

  // 2. 不够 3 个则从兜底词库补（排除与正确答案重复的）
  if (distractorMeanings.length < 3) {
    const fallbackPool = shuffleArray(FALLBACK_DISTRACTORS.filter(m => m !== correct && !distractorMeanings.includes(m)))
    while (distractorMeanings.length < 3 && fallbackPool.length > 0) {
      distractorMeanings.push(fallbackPool.pop()!)
    }
  }

  vbChoiceOptions.value = shuffleArray([correct, ...distractorMeanings])
}

// 选义
function selectVbChoice(idx: number) {
  if (vbShowResult.value) return
  vbSelectedIdx.value = idx
  const correct = vbCurrentWord.value?.meaning
  vbIsCorrect.value = vbChoiceOptions.value[idx] === correct
  vbShowResult.value = true
  if (vbIsCorrect.value) vbCorrectCount.value++
  wordReviewApi.submit(auth.currentUserId, vbCurrentWord.value.word, vbIsCorrect.value)
}

// 默写
function checkVbDict() {
  if (!vbCurrentWord.value || !vbDictInput.value.trim()) return
  vbIsCorrect.value = vbDictInput.value.trim().toLowerCase() === vbCurrentWord.value.word.toLowerCase()
  if (vbIsCorrect.value) vbCorrectCount.value++
  vbShowResult.value = true
  wordReviewApi.submit(auth.currentUserId, vbCurrentWord.value.word, vbIsCorrect.value, vbIsCorrect.value ? 100 : 0)
}

function showVbAnswer() {
  vbIsCorrect.value = false
  vbShowResult.value = true
  wordReviewApi.submit(auth.currentUserId, vbCurrentWord.value.word, false, 0)
}

function nextVbWord() {
  if (vbIdx.value < vbWords.value.length - 1) {
    vbIdx.value++
    vbCurrentMode.value = vbWords.value[vbIdx.value]._mode
    vbSelectedIdx.value = -1
    vbDictInput.value = ''
    vbShowResult.value = false
    vbIsCorrect.value = false
    if (vbCurrentMode.value === 'choice') generateVbOptions()
  } else {
    vbDone.value = true
  }
}

function resetVb() { vbActive.value = false }

// ===== 数据加载 =====
async function loadData() {
  loading.value = true

  // 并行加载所有独立的 API 请求
  const [
    reviewTasksRes,
    allProgressRes,
    todayListRes,
    listRes,
    historyRes,
    vocabRes
  ] = await Promise.allSettled([
    dailyApi.getReviewTasks(auth.currentUserId),
    dailyApi.getAllProgress(auth.currentUserId),
    dailyApi.getTodayList(auth.currentUserId),
    dailyApi.getList(30),
    dictationApi.getHistory(auth.currentUserId, 50),
    wordReviewApi.getDue(auth.currentUserId, 20)
  ])

  // 处理复习任务
  if (reviewTasksRes.status === 'fulfilled') {
    dueTasks.value = reviewTasksRes.value.data.tasks || []
  }

  // 处理进度
  if (allProgressRes.status === 'fulfilled') {
    progressList.value = allProgressRes.value.data.items || []
    masteredCount.value = allProgressRes.value.data.mastered_count || 0
  }

  // 处理今日内容
  if (todayListRes.status === 'fulfilled') {
    todayContents.value = todayListRes.value.data.contents || []
  }

  // 补充更多内容
  if (listRes.status === 'fulfilled') {
    const items = listRes.value.data
    if (Array.isArray(items)) {
      const ids = new Set(todayContents.value.map(c => c.id))
      for (const item of items) {
        if (!ids.has(item.id)) todayContents.value.push(item)
      }
    }
  }

  // 处理默写历史
  if (historyRes.status === 'fulfilled') {
    const res = historyRes.value
    if (res.statusCode >= 400) {
      historyLoadError.value = true
    } else if (Array.isArray(res.data)) {
      historyList.value = res.data
      historyLoadError.value = false
    }
  } else {
    historyLoadError.value = true
  }

  // 处理背单词数据
  if (vocabRes.status === 'fulfilled') {
    vbDueWords.value = vocabRes.value.data.words || []
    vbDistractors.value = vocabRes.value.data.distractors || []
  }

  loading.value = false
}

onShow(loadData)
</script>

<style scoped>
.tab-badge {
  display: inline-block; background: var(--error); color: white;
  font-size: 20rpx; font-weight: 700; min-width: 32rpx; height: 32rpx;
  line-height: 32rpx; border-radius: 16rpx; padding: 0 8rpx;
  margin-left: 8rpx; text-align: center;
}
.section { padding: 24rpx 0; }
.section-title { font-size: 28rpx; font-weight: 700; margin-bottom: 20rpx; display: block; }

/* 复述 */
.task-list { display: flex; flex-direction: column; gap: 16rpx; }
.task-item { display: flex; align-items: center; gap: 20rpx; padding: 24rpx 28rpx; }
.task-avatar { width: 72rpx; height: 72rpx; border-radius: 20rpx; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.task-stage { color: white; font-weight: 700; font-size: 24rpx; }
.task-info { flex: 1; min-width: 0; }
.task-title { font-weight: 600; font-size: 28rpx; display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.task-meta { font-size: 22rpx; color: var(--on-surface-variant); margin-top: 4rpx; display: block; }

/* 默写 */
.content-list { display: flex; flex-direction: column; gap: 16rpx; }
.content-item { display: flex; align-items: center; gap: 20rpx; }
.content-left { flex: 1; }
.content-title { font-weight: 600; font-size: 28rpx; display: block; }
.content-meta { font-size: 24rpx; color: var(--on-surface-variant); margin-top: 4rpx; display: block; }
.section-title-row { display: flex; justify-content: space-between; align-items: center; cursor: pointer; }
.section-toggle { font-size: 24rpx; color: var(--primary); }
.history-list { display: flex; flex-direction: column; gap: 12rpx; }
.history-item { display: flex; align-items: center; padding: 20rpx 28rpx; cursor: pointer; }
.history-left { flex: 1; display: flex; flex-direction: column; gap: 4rpx; min-width: 0; }
.history-right { display: flex; align-items: center; gap: 16rpx; flex-shrink: 0; }
.history-title { font-size: 26rpx; font-weight: 500; }
.history-date { font-size: 22rpx; color: var(--on-surface-variant); }
.history-accuracy { font-size: 32rpx; font-weight: 700; min-width: 72rpx; text-align: right; }
.history-points { font-size: 24rpx; color: var(--success); font-weight: 700; }

/* 通用词汇 */
.vocab-start-card { display: flex; align-items: center; justify-content: space-between; }
.vocab-info { display: flex; align-items: center; gap: 20rpx; flex: 1; }
.vocab-info-icon { font-size: 48rpx; }
.vocab-info-label { font-size: 26rpx; color: var(--on-surface-variant); display: block; }
.vocab-info-count { font-size: 32rpx; font-weight: 700; display: block; }
.vocab-progress-bar-bg { height: 8rpx; background: var(--surface-container); border-radius: 4rpx; margin: 32rpx 32rpx 0; overflow: hidden; }
.vocab-progress-bar-fill { height: 100%; background: var(--primary); border-radius: 4rpx; transition: width 0.3s; }
.vocab-progress-text { font-size: 24rpx; color: var(--on-surface-variant); }
.vocab-hint-card { text-align: center; padding: 40rpx; }
.vocab-hint-label { font-size: 22rpx; color: var(--on-surface-variant); margin-bottom: 16rpx; display: block; }
.vocab-hint-meaning { font-size: 40rpx; font-weight: 600; display: block; }
.vocab-input-card { margin: 0 32rpx 24rpx; padding: 0; }
.vocab-input { width: 100%; border: none; border-bottom: 3rpx solid var(--outline); padding: 28rpx 16rpx; min-height: 88rpx; font-size: 36rpx; text-align: center; outline: none; color: var(--on-surface); background: transparent; line-height: 1.4; box-sizing: border-box; }
.vocab-input:focus { border-bottom-color: var(--primary); }
.vocab-result-card { text-align: center; padding: 32rpx; margin: 0 32rpx 24rpx; }
.vocab-result-status { font-size: 32rpx; font-weight: 700; display: block; margin-bottom: 12rpx; }
.vocab-result-status.correct { color: var(--success); }
.vocab-result-status.wrong { color: var(--error); }
.vocab-result-answer { font-size: 28rpx; display: block; color: var(--on-surface-variant); }
.vocab-done-card { text-align: center; padding: 40rpx; margin: 0 32rpx 32rpx; }
.vocab-done-title { font-size: 36rpx; font-weight: 700; margin-bottom: 32rpx; display: block; }
.vocab-done-stats { display: flex; justify-content: center; gap: 64rpx; margin-bottom: 32rpx; }
.vocab-done-stat { display: flex; flex-direction: column; align-items: center; gap: 8rpx; }
.vocab-done-stat-num { font-size: 48rpx; font-weight: 800; }
.vocab-done-stat-label { font-size: 22rpx; color: var(--on-surface-variant); }

/* 背单词专属 */
.vb-mode-hints { margin-top: 24rpx; display: flex; flex-direction: column; gap: 16rpx; }
.vb-mode-hint { display: flex; align-items: center; gap: 16rpx; padding: 20rpx 24rpx; background: var(--surface-container); border-radius: 12rpx; }
.vb-mode-icon { font-size: 32rpx; }
.vb-mode-text { font-size: 26rpx; color: var(--on-surface-variant); }
.vb-progress-row { display: flex; justify-content: space-between; align-items: center; padding: 12rpx 32rpx 0; }
.vb-mode-tag { font-size: 24rpx; color: var(--primary); font-weight: 600; }
.vb-actions { padding: 16rpx 32rpx 32rpx; display: flex; flex-direction: column; gap: 12rpx; align-items: center; }
.vb-result-line { text-align: center; font-size: 28rpx; font-weight: 600; padding: 16rpx 0; }
.vb-correct { color: var(--success); }
.vb-wrong { color: var(--error); }

/* 选义卡片 */
.wc-word-card { text-align: center; padding: 48rpx 32rpx; margin: 16rpx 32rpx; }
.wc-word-text { font-size: 52rpx; font-weight: 800; display: block; }
.wc-word-phonetic { font-size: 26rpx; color: var(--on-surface-variant); display: block; margin-top: 12rpx; }
.wc-options { padding: 0 32rpx; display: flex; flex-direction: column; gap: 16rpx; }
.wc-option { display: flex; align-items: center; gap: 20rpx; padding: 28rpx 24rpx; border: 3rpx solid var(--outline-variant); border-radius: 16rpx; transition: all 0.15s; }
.wc-option.selected { border-color: var(--primary); background: var(--primary-container); }
.wc-option.correct { border-color: var(--success); background: var(--success-container); }
.wc-option.wrong { border-color: var(--error); background: var(--error-container); }
.wc-option-label { font-size: 28rpx; font-weight: 700; color: var(--on-surface-variant); width: 48rpx; text-align: center; }
.wc-option-text { font-size: 28rpx; flex: 1; }

/* 默写弹窗 */
.dictation-sheet { width: 100%; max-width: 600px; max-height: 90vh; background: white; border-radius: 32rpx 32rpx 0 0; overflow-y: auto; padding-bottom: env(safe-area-inset-bottom, 32rpx); }
.dictation-sheet-top { display: flex; justify-content: space-between; align-items: center; padding: 32rpx 32rpx 0; }
.dictation-close { background: var(--surface-container); }
.dictation-hint-card { margin: 24rpx 32rpx; padding: 28rpx; background: var(--primary-container); border-radius: 16rpx; }
.dictation-hint-label { font-size: 22rpx; color: var(--on-primary-container); margin-bottom: 12rpx; display: block; }
.dictation-hint-text { font-size: 28rpx; line-height: 1.6; display: block; color: var(--on-primary-container); }
.dictation-original-card { margin: 16rpx 32rpx; padding: 28rpx; background: var(--surface-container); border-radius: 16rpx; }
.dictation-original-text { font-size: 28rpx; line-height: 1.6; display: block; }
.dictation-input-card { padding: 16rpx 32rpx; }
.dictation-textarea { width: 100%; height: 280rpx; border: 3rpx solid var(--outline); border-radius: 16rpx; padding: 24rpx; font-size: 28rpx; line-height: 1.6; }
.dictation-submit { padding: 0 32rpx 24rpx; }
.dictation-result-card { border-left: 8rpx solid var(--primary); margin: 0 32rpx 32rpx; }
.dictation-score-area { display: flex; align-items: center; gap: 28rpx; }
.dictation-score { font-size: 80rpx; font-weight: 800; }
.score-green { color: var(--success); }
.score-orange { color: var(--warning); }
.score-red { color: var(--error); }
.dictation-score-meta { font-size: 26rpx; line-height: 1.6; }
.dictation-feedback { margin-top: 24rpx; padding-top: 20rpx; border-top: 2rpx solid var(--surface-container-high); }
.dictation-feedback-label { font-size: 24rpx; color: var(--on-surface-variant); margin-bottom: 12rpx; display: block; }
.dictation-feedback-text { font-size: 26rpx; line-height: 1.6; display: block; }

.dictation-diffs { margin-top: 20rpx; padding-top: 16rpx; border-top: 2rpx solid var(--surface-container-high); }
.diff-item { display: flex; gap: 12rpx; margin-bottom: 12rpx; padding: 12rpx; background: var(--surface-container); border-radius: 8rpx; }
.diff-type { font-size: 22rpx; font-weight: 600; padding: 4rpx 12rpx; border-radius: 12rpx; flex-shrink: 0; }
.diff-type.diff-missing { background: #FFF3E0; color: #E65100; }
.diff-type.diff-wrong { background: #FFEBEE; color: #C62828; }
.diff-type.diff-extra { background: #E3F2FD; color: #1565C0; }
.diff-detail { flex: 1; display: flex; flex-direction: column; gap: 4rpx; }
.diff-expected { font-size: 24rpx; color: var(--success); }
.diff-actual { font-size: 24rpx; color: var(--error); text-decoration: line-through; }

.dictation-suggestions { margin-top: 20rpx; padding-top: 16rpx; border-top: 2rpx solid var(--surface-container-high); }
.suggestion-item { margin-bottom: 8rpx; }
.suggestion-text { font-size: 24rpx; color: var(--on-surface); line-height: 1.6; }
</style>
