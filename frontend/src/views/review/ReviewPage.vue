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
                上次准确率 {{ (task.last_accuracy * 100).toFixed(0) }}%
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
              {{ item.review_stage === 0 ? '-' : `${(item.last_accuracy * 100).toFixed(0)}%` }}
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
              <span :style="{ color: getAccuracyColor(h.accuracy_rate) }">{{ (h.accuracy_rate * 100).toFixed(0) }}%</span>
              <span style="color:var(--success)">+{{ h.earned_points }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 今日学习内容 -->
      <div class="section">
        <h3 class="section-title">📚 今日学习 <span class="section-hint">（{{ visibleContents.length }} 条）</span></h3>
        <div v-if="todayContents.length === 0" class="empty-state">
          <div class="icon">📝</div>
          <p>暂无学习内容</p>
        </div>
        <div v-else class="content-list">
          <div v-for="item in visibleContents" :key="item.id" class="card content-item" @click="startDictation(item)">
            <div class="content-left">
              <div class="content-title">{{ item.title }}</div>
              <div class="content-meta">
                <span>{{ item.content_date }}</span>
                <span class="tag tag-primary" style="margin-left:8px;font-size:11px">{{ item.difficulty_level }}</span>
                <span v-if="item.lexicon?.length" class="tag tag-success" style="margin-left:4px;font-size:11px">{{ item.lexicon.length }}词</span>
              </div>
            </div>
            <span class="arrow">›</span>
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

              <!-- 模式切换 -->
              <div class="mode-switch" v-if="dictatingContent.lexicon?.length">
                <button :class="['mode-btn', { active: dictationMode === 'full' }]" @click="dictationMode = 'full'">
                  📝 全文默写
                </button>
                <button :class="['mode-btn', { active: dictationMode === 'vocab' }]" @click="dictationMode = 'vocab'">
                  📚 词汇默写
                </button>
              </div>

              <!-- 全文默写模式 -->
              <template v-if="dictationMode === 'full'">
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
              </template>

              <!-- 词汇默写模式 -->
              <template v-else>
                <div class="card vocab-hint-card" style="margin:12px 16px">
                  <h4 style="margin-bottom:8px;color:var(--on-surface-variant)">中文词汇提示</h4>
                  <div class="vocab-hint-list">
                    <span v-for="(word, idx) in vocabHintList" :key="idx" class="vocab-hint-item">{{ word }}</span>
                  </div>
                </div>

                <Transition name="slide-up">
                  <div v-if="showOriginal" class="card" style="margin:0 16px;background:var(--primary-container)">
                    <h4 style="margin-bottom:8px;color:var(--on-primary-container)">英文词汇</h4>
                    <div class="vocab-answer-list">
                      <span v-for="(word, idx) in vocabAnswerList" :key="idx" class="vocab-answer-item">{{ word }}</span>
                    </div>
                  </div>
                </Transition>

                <div style="padding:8px 16px">
                  <button class="btn btn-sm btn-outline" @click="showOriginal = !showOriginal" style="margin-bottom:8px">
                    {{ showOriginal ? '🙈 隐藏答案' : '👁️ 显示答案' }}
                  </button>
                </div>

                <div class="card" style="margin:0 16px">
                  <textarea v-model="userInput" rows="6" placeholder="请按顺序输入对应的英文词汇，用空格或逗号分隔..." class="dictation-input"></textarea>
                </div>
              </template>

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
                    <div>准确率 {{ (result.accuracy_rate * 100).toFixed(0) }}%</div>
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
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { dailyApi, dictationApi } from '@/api'
import { useAuthStore } from '@/stores'
import type { LearningContent, DictationResult, ReviewTask, MemoryProgress, DictationHistory } from '@/types'

const auth = useAuthStore()
const loading = ref(true)
const activeTab = ref<'review' | 'dictation'>('review')

// 复习
const dueTasks = ref<ReviewTask[]>([])
const progressList = ref<MemoryProgress[]>([])
const masteredCount = ref(0)

// 默写
const todayContents = ref<LearningContent[]>([])
const history = ref<DictationHistory[]>([])
const dictatingContent = ref<LearningContent | null>(null)
const dictationMode = ref<'full' | 'vocab'>('full')
const showOriginal = ref(false)
const userInput = ref('')
const submitting = ref(false)
const result = ref<DictationResult | null>(null)

// 词汇默写的中文提示列表
const vocabHintList = computed(() => {
  if (!dictatingContent.value?.lexicon) return []
  return dictatingContent.value.lexicon.map((w: any) => w.meaning || w.word)
})

// 词汇默写的英文答案列表
const vocabAnswerList = computed(() => {
  if (!dictatingContent.value?.lexicon) return []
  return dictatingContent.value.lexicon.map((w: any) => w.word)
})

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

// 默写 tab：显示今日学习内容（已在getTodayList中按dailyGoal过滤）
const visibleContents = computed(() => todayContents.value)

onMounted(loadData)

async function loadData() {
  loading.value = true
  try {
    const [reviewRes, progressRes, todayRes, histRes] = await Promise.all([
      dailyApi.getReviewTasks(auth.currentUserId),
      dailyApi.getAllProgress(auth.currentUserId),
      dailyApi.getTodayList(auth.currentUserId),
      dictationApi.getHistory(auth.currentUserId).catch(() => ({ data: [] })),
    ])
    dueTasks.value = reviewRes.data.tasks || []
    progressList.value = progressRes.data.items || []
    masteredCount.value = progressRes.data.mastered_count || 0
    todayContents.value = todayRes.data.contents || []
    history.value = histRes.data?.slice(0, 20) || []
  } catch { /* ignore */ }
  loading.value = false
}

function getContentTitle(contentId?: number | null): string {
  if (!contentId) return ''
  const item = todayContents.value.find(c => c.id === contentId)
  return item?.title || ''
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
  if (acc >= 0.8) return 'var(--success)'
  if (acc >= 0.6) return 'var(--warning)'
  return 'var(--error)'
}

function startDictation(item: LearningContent) {
  dictatingContent.value = item
  dictationMode.value = 'full'
  showOriginal.value = false
  userInput.value = ''
  result.value = null
}

function startDictationById(contentId?: number | null) {
  if (!contentId) return
  const item = todayContents.value.find(c => c.id === contentId)
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
  padding: 12px 14px; cursor: pointer; transition: background 0.15s;
}
.content-item:hover { background: var(--surface-container); }
.content-left { flex: 1; }
.content-title { font-weight: 600; font-size: 15px; }
.content-meta { font-size: 13px; color: var(--on-surface-variant); margin-top: 3px; }
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

.mode-switch {
  display: flex; gap: 8px; padding: 12px 16px 0;
}

.mode-btn {
  flex: 1; padding: 10px; border: 1.5px solid var(--outline);
  background: white; border-radius: 10px; font-size: 13px;
  font-weight: 500; cursor: pointer; transition: all 0.2s;
}

.mode-btn.active {
  border-color: var(--primary); background: var(--primary-container);
  color: var(--primary); font-weight: 600;
}

.vocab-hint-card {
  background: linear-gradient(135deg, #FFF8E1 0%, #FFFFFF 100%);
  border: 1px solid #FFE082;
}

.vocab-hint-list {
  display: flex; flex-wrap: wrap; gap: 8px;
}

.vocab-hint-item {
  padding: 6px 12px; background: #FFECB3; border-radius: 8px;
  font-size: 14px; color: #F57F17; font-weight: 500;
}

.vocab-answer-list {
  display: flex; flex-wrap: wrap; gap: 8px;
}

.vocab-answer-item {
  padding: 6px 12px; background: var(--primary-container); border-radius: 8px;
  font-size: 14px; color: var(--primary); font-weight: 600;
}

.dictation-input {
  width: 100%; border: 1.5px solid var(--outline); border-radius: var(--radius-sm);
  padding: 12px; font-size: 15px; line-height: 1.6; resize: vertical;
  outline: none; font-family: inherit;
}
.dictation-input:focus { border-color: var(--primary); }

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
</style>
