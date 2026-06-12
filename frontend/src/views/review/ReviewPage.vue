<template>
  <div class="page-container">
    <div class="page-header">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <h1>复习</h1>
        <button class="btn btn-sm" style="background:rgba(255,255,255,0.2);color:white" @click="loadData">🔄 刷新</button>
      </div>
    </div>

    <!-- 功能入口 -->
    <div class="feature-tabs">
      <div class="feature-tab" :class="{ active: activeTab === 'review' }" @click="activeTab = 'review'">
        <span class="feature-icon">🔄</span>
        <span class="feature-name">记忆复习</span>
        <span class="feature-badge" v-if="dueTasks.length">{{ visibleDueTasks.length }}/{{ dueTasks.length }}</span>
      </div>
      <div class="feature-tab" :class="{ active: activeTab === 'dictation' }" @click="activeTab = 'dictation'">
        <span class="feature-icon">✏️</span>
        <span class="feature-name">默写练习</span>
      </div>
      <div class="feature-tab" :class="{ active: activeTab === 'vocab' }" @click="activeTab = 'vocab'">
        <span class="feature-icon">📚</span>
        <span class="feature-name">词汇默写</span>
      </div>
    </div>

    <div v-if="loading" class="loading"><div class="spinner"></div></div>

    <!-- ========== 复习 tab ========== -->
    <template v-else-if="activeTab === 'review'">
      <!-- 记忆概览卡片 -->
      <div class="stats-row">
        <div class="stat-card">
          <div class="stat-num">{{ progressList.length }}</div>
          <div class="stat-label">总内容</div>
        </div>
        <div class="stat-card">
          <div class="stat-num" style="color:var(--success)">{{ masteredCount }}</div>
          <div class="stat-label">已掌握</div>
        </div>
        <div class="stat-card">
          <div class="stat-num" style="color:var(--warning)">{{ visibleDueTasks.length }}</div>
          <div class="stat-label">今日待复习</div>
        </div>
      </div>

      <!-- 待复习队列 -->
      <div class="section" v-if="visibleDueTasks.length">
        <h3 class="section-title">📋 今日复习 <span class="section-hint">（{{ visibleDueTasks.length }}/{{ dueTasks.length }} 条，按记忆曲线排序）</span></h3>
        <div class="task-list">
          <div v-for="task in visibleDueTasks" :key="task.content_id" class="card task-item">
            <div class="task-avatar" :style="{ background: stageColors[task.review_stage] || 'var(--primary)' }">
              S{{ task.review_stage }}
            </div>
            <div class="task-info">
              <div class="task-title">{{ task.title }}</div>
              <div class="task-meta">
                上次准确率 {{ task.last_accuracy.toFixed(0) }}%
                <span v-if="task.next_review_at"> · {{ formatDue(task.next_review_at) }}</span>
              </div>
            </div>
            <router-link :to="`/learning/content/${task.content_id}`" class="btn btn-sm btn-primary">去复习</router-link>
          </div>
        </div>
      </div>

      <div v-else class="empty-state" style="padding-top:20px">
        <div class="icon" style="color:var(--success)">✅</div>
        <p v-if="dueTasks.length">今日复习已完成，还有 {{ dueTasks.length }} 条待复习</p>
        <p v-else>暂无待复习内容，继续学习吧！</p>
      </div>

      <!-- 全部内容进度 -->
      <div class="section" v-if="progressList.length">
        <h3 class="section-title">📊 全部内容进度</h3>
        <div class="progress-list">
          <div v-for="item in sortedProgress" :key="item.content_id" class="card progress-item">
            <div class="progress-left">
              <div class="progress-title">{{ item.title }}</div>
              <div class="progress-meta">
                <span class="stage-badge" :style="{ background: stageColors[item.review_stage] || 'var(--primary)' }">
                  {{ item.review_stage === 0 ? '新' : `S${item.review_stage}` }}
                </span>
                <span v-if="item.is_mastered" class="mastered-badge">已掌握</span>
                <span v-else-if="item.review_stage === 0" class="due-text">未默写</span>
                <span v-else-if="item.next_review_at" class="due-text">{{ formatDue(item.next_review_at) }}</span>
              </div>
            </div>
            <div class="progress-accuracy" :style="{ color: getAccuracyColor(item.last_accuracy) }">
              {{ item.review_stage === 0 ? '-' : `${item.last_accuracy.toFixed(0)}%` }}
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- ========== 默写 tab ========== -->
    <template v-else-if="activeTab === 'dictation'">
      <!-- 默写历史 -->
      <div class="section" v-if="history.length">
        <h3 class="section-title">📝 近期默写记录</h3>
        <div class="card history-card">
          <div v-for="h in history" :key="h.dictation_id" class="history-item" @click="startDictationById(h.content_id)">
            <div class="history-left">
              <span class="history-date">{{ h.created_at?.slice(5, 10) }}</span>
              <span class="history-title" v-if="getContentTitle(h.content_id)">{{ getContentTitle(h.content_id) }}</span>
            </div>
            <div class="history-right">
              <span :style="{ color: getAccuracyColor(h.accuracy_rate) }">{{ h.accuracy_rate.toFixed(0) }}%</span>
              <span style="color:var(--success)">+{{ h.earned_points }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 今日学习内容 -->
      <div class="section">
        <div class="section-header-row">
          <h3 class="section-title">📚 今日学习 <span class="section-hint">（{{ visibleContents.length }} 条）</span></h3>
          <button class="filter-btn" :class="{ active: learnedOnly }" @click="learnedOnly = !learnedOnly">
            {{ learnedOnly ? '✅ 已学' : '☑️ 已学筛选' }}
          </button>
        </div>
        <div v-if="todayContents.length === 0" class="empty-state">
          <div class="icon">📝</div>
          <p>暂无学习内容</p>
        </div>
        <div v-else class="content-list">
          <div v-for="item in visibleContents" :key="item.id" class="card content-item">
            <div class="content-left">
              <div class="content-title">{{ item.title }}</div>
              <div class="content-meta">
                <span>{{ item.content_date }}</span>
                <span class="tag tag-primary" style="margin-left:8px;font-size:11px">{{ item.difficulty_level }}</span>
                <span v-if="item.words?.length" style="margin-left:8px;font-size:11px;color:var(--primary)">重点词汇 {{ item.words.length }} 个</span>
              </div>
            </div>
            <div class="content-actions">
              <button class="btn btn-sm btn-outline" @click="startDictation(item)">默写全文</button>
              <button v-if="item.words?.length" class="btn btn-sm btn-primary" @click="startWordDictation(item)">默写词汇</button>
            </div>
          </div>
        </div>
      </div>

      <!-- 默写练习区 -->
      <Teleport to="body">
        <Transition name="fade">
          <div v-if="dictatingContent" class="modal-overlay" @click.self="dictatingContent = null">
            <div class="dictation-sheet">
              <div class="sheet-header">
                <span class="tag tag-primary">默写练习</span>
                <button class="close-btn" @click="dictatingContent = null">✕</button>
              </div>

              <div class="card" style="margin:12px 16px">
                <h4 style="margin-bottom:8px;color:var(--on-surface-variant)">中文翻译提示</h4>
                <p style="line-height:1.6">{{ dictatingContent.translation || '暂无翻译' }}</p>
              </div>

              <Transition name="slide-up">
                <div v-if="showOriginal" class="card" style="margin:0 16px;background:var(--primary-container)">
                  <h4 style="margin-bottom:8px;color:var(--on-primary-container)">英文原文</h4>
                  <p style="line-height:1.8;font-size:15px">{{ dictatingContent.article }}</p>
                </div>
              </Transition>

              <div style="padding:8px 16px">
                <button class="btn btn-sm btn-outline" @click="showOriginal = !showOriginal" style="margin-bottom:8px">
                  {{ showOriginal ? '🙈 隐藏原文' : '👁️ 显示原文' }}
                </button>
              </div>

              <div class="card" style="margin:0 16px">
                <textarea v-model="userInput" rows="8" placeholder="在这里输入你默写的英文内容..." class="dictation-input"></textarea>
              </div>

              <div style="padding:12px 16px;display:flex;gap:10px">
                <button class="btn btn-primary btn-block" @click="handleSubmit" :disabled="submitting || !userInput.trim()">
                  {{ submitting ? 'AI 批改中...' : '提交批改' }}
                </button>
                <button class="btn btn-outline" @click="userInput = ''">清空</button>
              </div>

              <!-- 批改结果 -->
              <div v-if="result" class="card result-card" style="margin:0 16px 16px">
                <div class="score-area">
                  <div class="score" :class="{ green: result.feedback.score >= 80, orange: result.feedback.score >= 60, red: result.feedback.score < 60 }">
                    {{ result.feedback.score }}
                  </div>
                  <div class="score-meta">
                    <div>准确率 {{ result.accuracy_rate.toFixed(0) }}%</div>
                    <div style="color:var(--success)">+{{ result.earned_points }} 积分</div>
                    <div style="color:var(--primary)">S{{ result.review_stage }} · {{ result.next_review_at?.slice(5, 10) || '-' }}</div>
                  </div>
                </div>

                <div class="feedback-section" v-if="result.feedback.summary">
                  <h4>AI 总评</h4>
                  <p>{{ result.feedback.summary }}</p>
                </div>

                <div v-if="result.feedback.diffs?.length" class="feedback-section">
                  <h4>差异分析</h4>
                  <div v-for="(d, i) in result.feedback.diffs" :key="i" class="diff-item" :class="d.type">
                    <span class="diff-type">{{ d.type === 'missing' ? '遗漏' : d.type === 'wrong' ? '错误' : '多余' }}</span>
                    <span>应为 <strong>{{ d.expected }}</strong></span>
                    <span v-if="d.type !== 'missing'">你写 <strong>{{ d.actual }}</strong></span>
                  </div>
                </div>

                <div v-if="result.feedback.suggestions?.length" class="feedback-section">
                  <h4>改进建议</h4>
                  <ul>
                    <li v-for="(s, i) in result.feedback.suggestions" :key="i">{{ s }}</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </Transition>
      </Teleport>

      <!-- 词汇默写弹窗 -->
      <Teleport to="body">
        <Transition name="fade">
          <div v-if="wordDictationContent" class="modal-overlay" @click.self="wordDictationContent = null">
            <div class="dictation-sheet">
              <div class="sheet-header">
                <span class="tag tag-primary">词汇默写</span>
                <span class="word-progress">{{ wordDictationIdx + 1 }} / {{ wordDictationWords.length }}</span>
                <button class="close-btn" @click="wordDictationContent = null">✕</button>
              </div>

              <!-- 中文提示 -->
              <div class="card" style="margin:12px 16px">
                <div class="word-hint-label">中文释义</div>
                <div class="word-hint-meaning">{{ currentWordMeaning }}</div>
                <!-- 音标不显示，避免暴露单词 -->
              </div>

              <!-- 输入框 -->
              <div class="card" style="margin:0 16px">
                <input v-model="wordInput" type="text" placeholder="输入英文单词..." class="word-input"
                  @keyup.enter="showWordResult ? nextWord() : handleSubmitWord()" />
              </div>

              <!-- 操作按钮 -->
              <div style="padding:12px 16px;display:flex;gap:10px">
                <button v-if="!showWordResult" class="btn btn-primary btn-block" @click="handleSubmitWord"
                  :disabled="!wordInput.trim()">
                  确认
                </button>
                <button v-if="!showWordResult" class="btn btn-outline" @click="showWordResult = true; wordResultCorrect = false">
                  不会，看答案
                </button>
                <button v-if="showWordResult" class="btn btn-primary btn-block" @click="nextWord">
                  {{ wordDictationIdx < wordDictationWords.length - 1 ? '下一个' : '完成' }}
                </button>
              </div>

              <!-- 结果展示 -->
              <Transition name="slide-up">
                <div v-if="showWordResult" class="card word-result-card" style="margin:0 16px 16px">
                  <div class="word-result-status" :class="{ correct: wordResultCorrect, wrong: !wordResultCorrect }">
                    {{ wordResultCorrect ? '✅ 正确' : '❌ 错误' }}
                  </div>
                  <div v-if="!wordResultCorrect" class="word-result-correct">
                    正确答案：<strong>{{ currentWord }}</strong>
                  </div>
                  <div class="word-result-usage" v-if="currentWordUsage">
                    用法：{{ currentWordUsage }}
                  </div>
                </div>
              </Transition>

              <!-- 完成统计 -->
              <div v-if="wordDictationDone" class="card word-done-card" style="margin:0 16px 16px">
                <div class="word-done-title">🎉 默写完成</div>
                <div class="word-done-stats">
                  <div class="word-stat">
                    <span class="word-stat-num" style="color:var(--success)">{{ wordCorrectCount }}</span>
                    <span class="word-stat-label">正确</span>
                  </div>
                  <div class="word-stat">
                    <span class="word-stat-num" style="color:var(--error)">{{ wordDictationWords.length - wordCorrectCount }}</span>
                    <span class="word-stat-label">错误</span>
                  </div>
                  <div class="word-stat">
                    <span class="word-stat-num" style="color:var(--primary)">{{ Math.round(wordCorrectCount / wordDictationWords.length * 100) }}%</span>
                    <span class="word-stat-label">正确率</span>
                  </div>
                </div>
                <button class="btn btn-primary btn-block" @click="wordDictationContent = null">返回</button>
              </div>
            </div>
          </div>
        </Transition>
      </Teleport>
    </template>

    <!-- ========== 词汇默写 tab（收藏词汇） ========== -->
    <template v-else-if="activeTab === 'vocab'">
      <!-- 未开始默写时显示的界面 -->
      <div v-if="!vocabDictationActive">
        <div class="section">
          <h3 class="section-title">📚 收藏词汇默写</h3>
          <p style="color:var(--on-surface-variant);font-size:14px;margin-bottom:16px">
            从你的收藏词汇中随机抽取，背单词咯！
          </p>
          
          <div v-if="favoriteWords.length === 0" class="empty-state">
            <div class="icon">📝</div>
            <p>暂无收藏词汇</p>
            <p style="font-size:13px;color:var(--on-surface-variant)">在学习页面点击单词即可收藏</p>
          </div>
          
          <div v-else>
            <div class="vocab-info-card card">
              <div class="vocab-info-row">
                <span class="vocab-info-label">收藏词汇数</span>
                <span class="vocab-info-value">{{ favoriteWords.length }}</span>
              </div>
              <div class="vocab-info-row">
                <span class="vocab-info-label">每次默写</span>
                <span class="vocab-info-value">
                  <select v-model="vocabCount" class="vocab-select">
                    <option :value="5">5个</option>
                    <option :value="10">10个</option>
                    <option :value="20">20个</option>
                    <option :value="favoriteWords.length">全部</option>
                  </select>
                </span>
              </div>
            </div>
            <button class="btn btn-primary btn-block" @click="startVocabDictation" style="margin-top:16px">
              开始默写
            </button>
          </div>
        </div>
      </div>

      <!-- 默写进行中 -->
      <div v-else>
        <!-- 进度条 -->
        <div class="vocab-progress">
          <div class="vocab-progress-bar" :style="{ width: `${(vocabIdx + 1) / vocabWords.length * 100}%` }"></div>
        </div>
        <div class="vocab-progress-text">{{ vocabIdx + 1 }} / {{ vocabWords.length }}</div>

        <!-- 中文提示 -->
        <div class="card vocab-hint-card">
          <div class="vocab-hint-label">中文释义</div>
          <div class="vocab-hint-meaning">{{ vocabCurrentWord?.meaning || '' }}</div>
          <!-- 音标不显示，避免暴露单词 -->
        </div>

        <!-- 输入框 -->
        <div class="card vocab-input-card">
          <input 
            v-model="vocabInput" 
            type="text" 
            placeholder="输入英文单词..." 
            class="vocab-input"
            @keyup.enter="vocabShowResult ? nextVocabWord() : checkVocabWord()" 
            autofocus
          />
        </div>

        <!-- 操作按钮 -->
        <div class="vocab-actions">
          <button v-if="!vocabShowResult" class="btn btn-primary btn-block" @click="checkVocabWord" :disabled="!vocabInput.trim()">
            确认
          </button>
          <button v-if="!vocabShowResult" class="btn btn-outline" @click="showVocabAnswer">
            不会，看答案
          </button>
          <button v-if="vocabShowResult" class="btn btn-primary btn-block" @click="nextVocabWord">
            {{ vocabIdx < vocabWords.length - 1 ? '下一个' : '查看结果' }}
          </button>
        </div>

        <!-- 结果展示 -->
        <Transition name="slide-up">
          <div v-if="vocabShowResult" class="card vocab-result-card">
            <div class="vocab-result-status" :class="{ correct: vocabIsCorrect, wrong: !vocabIsCorrect }">
              {{ vocabIsCorrect ? '✅ 正确' : '❌ 错误' }}
            </div>
            <div v-if="!vocabIsCorrect" class="vocab-result-correct">
              正确答案：<strong>{{ vocabCurrentWord?.word }}</strong>
            </div>
          </div>
        </Transition>

        <!-- 完成统计 -->
        <div v-if="vocabDone" class="card vocab-done-card">
          <div class="vocab-done-title">🎉 默写完成</div>
          <div class="vocab-done-stats">
            <div class="vocab-stat">
              <span class="vocab-stat-num" style="color:var(--success)">{{ vocabCorrectCount }}</span>
              <span class="vocab-stat-label">正确</span>
            </div>
            <div class="vocab-stat">
              <span class="vocab-stat-num" style="color:var(--error)">{{ vocabWords.length - vocabCorrectCount }}</span>
              <span class="vocab-stat-label">错误</span>
            </div>
            <div class="vocab-stat">
              <span class="vocab-stat-num" style="color:var(--primary)">{{ Math.round(vocabCorrectCount / vocabWords.length * 100) }}%</span>
              <span class="vocab-stat-label">正确率</span>
            </div>
          </div>
          <button class="btn btn-primary btn-block" @click="resetVocabDictation">返回</button>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { dailyApi, dictationApi, favoritesApi } from '@/api'
import { useAuthStore } from '@/stores'
import type { LearningContent, DictationResult, ReviewTask, MemoryProgress, DictationHistory } from '@/types'

const auth = useAuthStore()
const loading = ref(true)
const activeTab = ref<'review' | 'dictation' | 'vocab'>('review')

// 复习
const dueTasks = ref<ReviewTask[]>([])
const progressList = ref<MemoryProgress[]>([])
const masteredCount = ref(0)

// 默写
const todayContents = ref<LearningContent[]>([])
const allContents = ref<LearningContent[]>([])
const history = ref<DictationHistory[]>([])
const dictatingContent = ref<LearningContent | null>(null)
const showOriginal = ref(false)
const userInput = ref('')
const submitting = ref(false)
const result = ref<DictationResult | null>(null)

// 已学筛选
const learnedOnly = ref(false)
const learnedIds = ref(new Set<number>())

// 词汇默写
const wordDictationContent = ref<LearningContent | null>(null)
const wordDictationIdx = ref(0)
const wordInput = ref('')
const showWordResult = ref(false)
const wordResultCorrect = ref(false)
const wordDictationDone = ref(false)
const wordCorrectCount = ref(0)

// 收藏词汇默写
const favoriteWords = ref<{word: string; phonetic?: string; meaning?: string}[]>([])
const vocabDictationActive = ref(false)
const vocabWords = ref<{word: string; phonetic?: string; meaning?: string}[]>([])
const vocabIdx = ref(0)
const vocabInput = ref('')
const vocabShowResult = ref(false)
const vocabIsCorrect = ref(false)
const vocabDone = ref(false)
const vocabCorrectCount = ref(0)
const vocabCount = ref(10)

// 词汇默写相关计算
const wordDictationWords = computed(() => wordDictationContent.value?.words || [])
const currentWord = computed(() => wordDictationWords.value[wordDictationIdx.value]?.word || '')
const currentWordMeaning = computed(() => wordDictationWords.value[wordDictationIdx.value]?.meaning || '')
const currentWordPhonetic = computed(() => wordDictationWords.value[wordDictationIdx.value]?.phonetic || '')
const currentWordUsage = computed(() => wordDictationWords.value[wordDictationIdx.value]?.usage || '')

// 收藏词汇默写相关计算
const vocabCurrentWord = computed(() => vocabWords.value[vocabIdx.value] || null)

const stageColors: Record<number, string> = {
  0: '#9E9E9E', 1: '#F44336', 2: '#FF9800',
  3: '#FFC107', 4: '#4CAF50', 5: '#2196F3',
  6: '#9C27B0', 7: '#00BCD4',
}

// 按阶段排序：已掌握 > 复习中 > 新内容
const sortedProgress = computed(() => {
  return [...progressList.value].sort((a, b) => {
    if (a.is_mastered !== b.is_mastered) return a.is_mastered ? -1 : 1
    if (a.review_stage !== b.review_stage) return b.review_stage - a.review_stage
    return 0
  })
})

// 根据每日学习时长计算展示上限
const dailyLimit = computed(() => {
  const goal = auth.preference?.daily_goal_minutes || 15
  return goal <= 15 ? 1 : goal <= 30 ? 2 : goal <= 45 ? 3 : 4
})

// 复习 tab：只显示 dailyLimit 条待复习
const visibleDueTasks = computed(() => dueTasks.value.slice(0, dailyLimit.value))

// 默写 tab：显示今日学习内容（可按已学筛选）
const visibleContents = computed(() => {
  if (!learnedOnly.value) return todayContents.value
  return todayContents.value.filter(c => learnedIds.value.has(c.id))
})

onMounted(loadData)

async function loadData() {
  loading.value = true
  try {
    const [reviewRes, progressRes, todayRes, histRes, allRes, learnedRes] = await Promise.all([
      dailyApi.getReviewTasks(auth.currentUserId),
      dailyApi.getAllProgress(auth.currentUserId),
      dailyApi.getTodayList(auth.currentUserId),
      dictationApi.getHistory(auth.currentUserId).catch(() => ({ data: [] })),
      dailyApi.getList(100).catch(() => ({ data: [] })),
      dailyApi.getLearnedIds(auth.currentUserId).catch(() => ({ data: { content_ids: [] } })),
    ])
    dueTasks.value = reviewRes.data.tasks || []
    progressList.value = progressRes.data.items || []
    masteredCount.value = progressRes.data.mastered_count || 0
    todayContents.value = todayRes.data.contents || []
    allContents.value = allRes.data || []
    history.value = histRes.data?.slice(0, 20) || []
    learnedIds.value = new Set(learnedRes.data.content_ids || [])
    // 加载收藏词汇
    await loadFavorites()
  } catch { /* ignore */ }
  loading.value = false
}

function getContentTitle(contentId?: number | null): string {
  if (!contentId) return ''
  // 先在今日内容中找
  const todayItem = todayContents.value.find(c => c.id === contentId)
  if (todayItem) return todayItem.title
  // 再在所有内容中找
  const allItem = allContents.value.find(c => c.id === contentId)
  return allItem?.title || ''
}

function formatDue(dateStr: string): string {
  const d = new Date(dateStr)
  const now = new Date()
  const diffMs = d.getTime() - now.getTime()
  const diffH = Math.round(diffMs / 3600000)
  if (diffH <= 0) return '已到期'
  if (diffH < 24) return `${diffH}小时后`
  return `${Math.round(diffH / 24)}天后`
}

function getAccuracyColor(acc: number): string {
  if (acc >= 80) return 'var(--success)'
  if (acc >= 60) return 'var(--warning)'
  return 'var(--error)'
}

function startDictation(item: LearningContent) {
  dictatingContent.value = item
  showOriginal.value = false
  userInput.value = ''
  result.value = null
}

function startDictationById(contentId?: number | null) {
  if (!contentId) return
  // 先在今日内容中找
  let item = todayContents.value.find(c => c.id === contentId)
  // 再在所有内容中找
  if (!item) {
    item = allContents.value.find(c => c.id === contentId)
  }
  if (item) startDictation(item)
}

async function handleSubmit() {
  if (!dictatingContent.value || !userInput.value.trim()) return
  submitting.value = true
  result.value = null
  try {
    const { data } = await dictationApi.submit(auth.currentUserId, dictatingContent.value.id, userInput.value)
    result.value = data
    // 刷新历史
    const histRes = await dictationApi.getHistory(auth.currentUserId)
    history.value = histRes.data?.slice(0, 20) || []
  } catch { /* ignore */ }
  submitting.value = false
}

function startWordDictation(item: LearningContent) {
  wordDictationContent.value = item
  wordDictationIdx.value = 0
  wordInput.value = ''
  showWordResult.value = false
  wordResultCorrect.value = false
  wordDictationDone.value = false
  wordCorrectCount.value = 0
}

function handleSubmitWord() {
  if (!wordInput.value.trim()) return
  const input = wordInput.value.trim().toLowerCase()
  const correct = currentWord.value.toLowerCase()
  wordResultCorrect.value = input === correct
  if (wordResultCorrect.value) wordCorrectCount.value++
  showWordResult.value = true
}

function nextWord() {
  if (wordDictationIdx.value < wordDictationWords.value.length - 1) {
    wordDictationIdx.value++
    wordInput.value = ''
    showWordResult.value = false
    wordResultCorrect.value = false
  } else {
    wordDictationDone.value = true
  }
}

// ===== 收藏词汇默写功能 =====
function shuffleArray<T>(array: T[]): T[] {
  const shuffled = [...array]
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
  }
  return shuffled
}

// 判断是否为单词变形（-ing, -ed, -s, -es, -ly, -tion等）
function isInflectedForm(word: string): boolean {
  const lower = word.toLowerCase()
  // 常见变形后缀
  const inflectionPatterns = [
    /ing$/i,    // running, going
    /ed$/i,     // walked, played
    /s$/i,      // plays, runs（但要注意像 bus, class 这种本身以s结尾的词）
    /es$/i,     // watches, boxes
    /ly$/i,     // quickly, slowly
    /tion$/i,   // education
    /sion$/i,   // decision
    /ment$/i,   // development
    /ness$/i,   // happiness
    /ful$/i,    // beautiful
    /less$/i,   // endless
    /er$/i,     // teacher（但要注意像 teacher 这种是完整词）
    /est$/i,    // biggest
    /able$/i,   // comfortable
    /ible$/i,   // possible
  ]
  
  // 如果单词长度<=3，不做过滤（避免误过滤短词）
  if (lower.length <= 3) return false
  
  // 检查是否匹配变形模式
  for (const pattern of inflectionPatterns) {
    if (pattern.test(lower)) {
      // 进一步检查：去掉后缀后是否还有合理的词根
      const root = lower.replace(/(?:ing|ed|s|es|ly|tion|sion|ment|ness|ful|less|er|est|able|ible)$/, '')
      // 如果词根长度>=2，认为可能是变形词
      if (root.length >= 2) {
        return true
      }
    }
  }
  return false
}

// 过滤词汇，只保留原型和单数形式
function filterToBaseForms(words: {word: string; phonetic?: string; meaning?: string}[]): {word: string; phonetic?: string; meaning?: string}[] {
  // 按单词分组，每组只保留第一个（通常是原型）
  const seen = new Set<string>()
  const result: {word: string; phonetic?: string; meaning?: string}[] = []
  
  for (const w of words) {
    const lower = w.word.toLowerCase().trim()
    // 跳过空词
    if (!lower) continue
    // 跳过明显是变形的词
    if (isInflectedForm(lower)) {
      // 如果这个词是变形的，但原型还没出现，可以添加原型版本
      const baseForm = lower
        .replace(/ing$/, '')    // 去掉 -ing
        .replace(/ed$/, '')     // 去掉 -ed
        .replace(/s$/, '')      // 去掉 -s
        .replace(/es$/, '')     // 去掉 -es
        .replace(/ly$/, '')     // 去掉 -ly
        .replace(/tion$/, '')   // 去掉 -tion
        .replace(/ment$/, '')   // 去掉 -ment
        .replace(/ness$/, '')   // 去掉 -ness
        .replace(/ful$/, '')    // 去掉 -ful
        .replace(/less$/, '')   // 去掉 -less
        .replace(/er$/, '')     // 去掉 -er
        .replace(/est$/, '')    // 去掉 -est
        .replace(/able$/, '')   // 去掉 -able
        .replace(/ible$/, '')   // 去掉 -ible
      
      // 如果原型还没添加，添加原型
      if (baseForm && !seen.has(baseForm) && baseForm.length >= 2) {
        seen.add(baseForm)
        result.push({ ...w, word: baseForm })
      }
      continue
    }
    // 正常词，直接添加
    if (!seen.has(lower)) {
      seen.add(lower)
      result.push(w)
    }
  }
  
  return result
}

async function loadFavorites() {
  try {
    const { data } = await favoritesApi.list(auth.currentUserId, 200)
    const allWords = (data || []).map((f: any) => ({
      word: f.word,
      phonetic: f.phonetic || '',
      meaning: f.meaning || '',
    }))
    // 过滤掉变形词，只保留原型和单数形式
    favoriteWords.value = filterToBaseForms(allWords)
  } catch { favoriteWords.value = [] }
}

function startVocabDictation() {
  if (favoriteWords.value.length === 0) return
  const shuffled = shuffleArray(favoriteWords.value)
  vocabWords.value = shuffled.slice(0, Math.min(vocabCount.value, shuffled.length))
  vocabIdx.value = 0
  vocabInput.value = ''
  vocabShowResult.value = false
  vocabIsCorrect.value = false
  vocabDone.value = false
  vocabCorrectCount.value = 0
  vocabDictationActive.value = true
}

function checkVocabWord() {
  if (!vocabCurrentWord.value || !vocabInput.value.trim()) return
  const input = vocabInput.value.trim().toLowerCase()
  const correct = vocabCurrentWord.value.word.toLowerCase()
  vocabIsCorrect.value = input === correct
  if (vocabIsCorrect.value) vocabCorrectCount.value++
  vocabShowResult.value = true
}

function showVocabAnswer() {
  vocabIsCorrect.value = false
  vocabShowResult.value = true
}

function nextVocabWord() {
  if (vocabIdx.value < vocabWords.value.length - 1) {
    vocabIdx.value++
    vocabInput.value = ''
    vocabShowResult.value = false
    vocabIsCorrect.value = false
  } else {
    vocabDone.value = true
  }
}

function resetVocabDictation() {
  vocabDictationActive.value = false
  vocabWords.value = []
  vocabIdx.value = 0
  vocabInput.value = ''
  vocabShowResult.value = false
  vocabIsCorrect.value = false
  vocabDone.value = false
  vocabCorrectCount.value = 0
}
</script>

<style scoped>
.feature-tabs {
  display: flex;
  gap: 12px;
  padding: 12px 16px;
}

.feature-tab {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 16px 12px;
  background: var(--surface-container);
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.feature-tab.active {
  background: var(--primary);
  color: white;
}

.feature-icon { font-size: 24px; }
.feature-name { font-size: 13px; font-weight: 500; }

.feature-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  background: var(--error);
  color: white;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 10px;
}

.stats-row {
  display: flex;
  gap: 10px;
  padding: 0 16px 12px;
}

.stat-card {
  flex: 1;
  text-align: center;
  padding: 14px 8px;
  background: var(--surface-container);
  border-radius: 14px;
}

.stat-num { font-size: 24px; font-weight: 800; }
.stat-label { font-size: 12px; color: var(--on-surface-variant); margin-top: 2px; }

.section { padding: 0 16px; margin-bottom: 16px; }
.section-title { font-size: 15px; font-weight: 700; margin-bottom: 10px; }
.section-header-row { display: flex; justify-content: space-between; align-items: center; }
.filter-btn {
  padding: 4px 12px; border-radius: 16px; font-size: 12px;
  border: 1.5px solid var(--outline-variant); background: var(--surface);
  color: var(--on-surface-variant); cursor: pointer; transition: all 0.2s;
}
.filter-btn.active { background: var(--primary); color: white; border-color: var(--primary); }
.section-hint { font-size: 12px; font-weight: 400; color: var(--on-surface-variant); }

.task-list { display: flex; flex-direction: column; gap: 8px; }
.task-item { display: flex; align-items: center; gap: 12px; }
.task-avatar {
  width: 44px; height: 44px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  color: white; font-weight: 700; font-size: 14px; flex-shrink: 0;
}
.task-info { flex: 1; }
.task-title { font-weight: 600; font-size: 15px; }
.task-meta { font-size: 13px; color: var(--on-surface-variant); margin-top: 2px; }

.progress-list { display: flex; flex-direction: column; gap: 6px; }
.progress-item { display: flex; align-items: center; gap: 12px; padding: 12px 14px; }
.progress-left { flex: 1; }
.progress-title { font-weight: 600; font-size: 14px; }
.progress-meta { display: flex; align-items: center; gap: 6px; margin-top: 4px; }
.stage-badge {
  font-size: 11px; font-weight: 700; color: white;
  padding: 2px 8px; border-radius: 8px;
}
.mastered-badge { font-size: 11px; color: var(--success); font-weight: 600; }
.due-text { font-size: 12px; color: var(--on-surface-variant); }
.progress-accuracy { font-size: 18px; font-weight: 700; }

.content-list { display: flex; flex-direction: column; gap: 6px; }
.content-item {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 14px; transition: background 0.15s;
}
.content-left { flex: 1; }
.content-title { font-weight: 600; font-size: 15px; }
.content-meta { font-size: 13px; color: var(--on-surface-variant); margin-top: 3px; }
.content-actions { display: flex; gap: 6px; flex-shrink: 0; }
.arrow { font-size: 20px; color: var(--on-surface-variant); }

.history-card { padding: 0 14px; }
.history-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 10px 0; border-bottom: 1px solid var(--surface-container);
  cursor: pointer; transition: background 0.15s;
}
.history-item:last-child { border-bottom: none; }
.history-item:hover { background: var(--surface-container); margin: 0 -14px; padding: 10px 14px; }
.history-left { display: flex; flex-direction: column; gap: 2px; }
.history-date { font-size: 13px; color: var(--on-surface-variant); }
.history-title { font-size: 14px; font-weight: 600; }
.history-right { display: flex; gap: 10px; font-size: 14px; font-weight: 600; }

/* 默写弹窗 */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.4);
  z-index: 500; display: flex; align-items: flex-end; justify-content: center;
}

.dictation-sheet {
  width: 100%; max-width: 480px; max-height: 90vh;
  background: white; border-radius: 20px 20px 0 0;
  overflow-y: auto; padding-bottom: env(safe-area-inset-bottom, 16px);
}

.sheet-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 16px 0;
}

.close-btn {
  width: 32px; height: 32px; border: none; background: var(--surface-container);
  border-radius: 50%; font-size: 16px; cursor: pointer; display: flex;
  align-items: center; justify-content: center;
}

.dictation-input {
  width: 100%; border: 1.5px solid var(--outline); border-radius: var(--radius-sm);
  padding: 12px; font-size: 15px; line-height: 1.6; resize: vertical;
  outline: none; font-family: inherit;
}
.dictation-input:focus { border-color: var(--primary); }

/* 词汇默写 */
.word-progress { font-size: 13px; color: var(--on-surface-variant); }
.word-hint-label { font-size: 12px; color: var(--on-surface-variant); margin-bottom: 6px; }
.word-hint-meaning { font-size: 18px; font-weight: 600; line-height: 1.4; }
.word-hint-phonetic { font-size: 13px; color: var(--on-surface-variant); margin-top: 4px; }
.word-input {
  width: 100%; border: 1.5px solid var(--outline); border-radius: var(--radius-sm);
  padding: 14px; font-size: 18px; outline: none; font-family: inherit;
  text-align: center; letter-spacing: 1px;
}
.word-input:focus { border-color: var(--primary); }
.word-input:disabled { background: var(--surface-container); }
.word-result-card { text-align: center; padding: 16px; }
.word-result-status { font-size: 18px; font-weight: 700; margin-bottom: 8px; }
.word-result-status.correct { color: var(--success); }
.word-result-status.wrong { color: var(--error); }
.word-result-correct { font-size: 15px; margin-bottom: 8px; }
.word-result-usage { font-size: 13px; color: var(--on-surface-variant); margin-top: 8px; line-height: 1.5; }
.word-done-card { text-align: center; padding: 20px 16px; }
.word-done-title { font-size: 20px; font-weight: 700; margin-bottom: 16px; }
.word-done-stats { display: flex; justify-content: center; gap: 24px; margin-bottom: 16px; }
.word-stat { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.word-stat-num { font-size: 28px; font-weight: 800; }
.word-stat-label { font-size: 12px; color: var(--on-surface-variant); }

.result-card { border-left: 4px solid var(--primary); }
.score-area { display: flex; align-items: center; gap: 16px; margin-bottom: 16px; }
.score { font-size: 48px; font-weight: 800; }
.score.green { color: var(--success); }
.score.orange { color: var(--warning); }
.score.red { color: var(--error); }
.score-meta { font-size: 14px; line-height: 1.6; }

.feedback-section { margin-top: 16px; padding-top: 12px; border-top: 1px solid var(--surface-container-high); }
.feedback-section h4 { font-size: 14px; color: var(--on-surface-variant); margin-bottom: 8px; }

.diff-item { padding: 6px 0; font-size: 14px; display: flex; gap: 8px; align-items: center; }
.diff-type { font-size: 12px; padding: 2px 8px; border-radius: 4px; font-weight: 600; }
.diff-item.missing .diff-type { background: #FFEBEE; color: var(--error); }
.diff-item.wrong .diff-type { background: #FFF3E0; color: var(--warning); }
.diff-item.extra .diff-type { background: #E3F2FD; color: #1976D2; }

.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.slide-up-enter-active, .slide-up-leave-active { transition: all 0.3s ease; }
.slide-up-enter-from, .slide-up-leave-to { opacity: 0; transform: translateY(10px); }

/* 收藏词汇默写 */
.vocab-info-card { padding: 16px; }
.vocab-info-row { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; }
.vocab-info-row + .vocab-info-row { border-top: 1px solid var(--surface-container); }
.vocab-info-label { font-size: 14px; color: var(--on-surface-variant); }
.vocab-info-value { font-size: 16px; font-weight: 600; }
.vocab-select {
  padding: 6px 12px; border: 1px solid var(--outline); border-radius: var(--radius-sm);
  font-size: 14px; background: white; cursor: pointer;
}
.vocab-progress {
  height: 6px; background: var(--surface-container); border-radius: 3px;
  margin: 16px 16px 0; overflow: hidden;
}
.vocab-progress-bar {
  height: 100%; background: var(--primary); border-radius: 3px;
  transition: width 0.3s ease;
}
.vocab-progress-text {
  text-align: center; font-size: 13px; color: var(--on-surface-variant);
  margin-top: 8px;
}
.vocab-hint-card { margin: 16px; text-align: center; }
.vocab-hint-label { font-size: 12px; color: var(--on-surface-variant); margin-bottom: 8px; }
.vocab-hint-meaning { font-size: 22px; font-weight: 600; line-height: 1.4; }
.vocab-hint-phonetic { font-size: 14px; color: var(--on-surface-variant); margin-top: 6px; }
.vocab-input-card { margin: 0 16px; }
.vocab-input {
  width: 100%; border: 1.5px solid var(--outline); border-radius: var(--radius-sm);
  padding: 14px; font-size: 18px; outline: none; font-family: inherit;
  text-align: center; letter-spacing: 1px;
}
.vocab-input:focus { border-color: var(--primary); }
.vocab-input:disabled { background: var(--surface-container); }
.vocab-actions { padding: 12px 16px; display: flex; flex-direction: column; gap: 10px; }
.vocab-result-card { margin: 0 16px 16px; text-align: center; padding: 16px; }
.vocab-result-status { font-size: 18px; font-weight: 700; margin-bottom: 8px; }
.vocab-result-status.correct { color: var(--success); }
.vocab-result-status.wrong { color: var(--error); }
.vocab-result-correct { font-size: 15px; }
.vocab-done-card { margin: 0 16px 16px; text-align: center; padding: 20px; }
.vocab-done-title { font-size: 20px; font-weight: 700; margin-bottom: 16px; }
.vocab-done-stats { display: flex; justify-content: center; gap: 24px; margin-bottom: 16px; }
.vocab-stat { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.vocab-stat-num { font-size: 28px; font-weight: 800; }
.vocab-stat-label { font-size: 12px; color: var(--on-surface-variant); }
</style>
