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
        <text>复述</text>
        <view v-if="dueTasks.length" class="tab-badge"><text>{{ dueTasks.length }}</text></view>
      </view>
      <view class="underline-tab" :class="{ active: activeTab === 'dictation' }" @tap="switchTab('dictation')">
        <text>默写</text>
      </view>
      <view class="underline-tab" :class="{ active: activeTab === 'wordChoice' }" @tap="switchTab('wordChoice')">
        <text>单词选义</text>
      </view>
      <view class="underline-tab" :class="{ active: activeTab === 'wordDictation' }" @tap="switchTab('wordDictation')">
        <text>单词默写</text>
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
        <view class="section">
          <text class="section-title">今日学习内容</text>
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

      <!-- ===== 单词选义 ===== -->
      <view v-show="activeTab === 'wordChoice'">
        <!-- 开始前 -->
        <view v-if="!wcActive" class="section">
          <text class="section-title">单词选义</text>
          <view v-if="wcDueWords.length === 0" class="empty-state">
            <text class="icon">🎯</text>
            <text class="empty-text">暂无待复习单词</text>
            <text class="empty-hint">收藏更多单词后再来复习</text>
          </view>
          <view v-else class="card vocab-start-card">
            <view class="vocab-info">
              <text class="vocab-info-icon">🎯</text>
              <view>
                <text class="vocab-info-label">待复习单词</text>
                <text class="vocab-info-count">{{ wcDueWords.length }}</text>
              </view>
            </view>
            <button class="btn btn-primary btn-sm" @tap="startWordChoice">
              <text>开始</text>
            </button>
          </view>
        </view>

        <!-- 进行中 -->
        <view v-else class="wc-active">
          <view class="vocab-progress-bar-bg">
            <view class="vocab-progress-bar-fill" :style="{ width: `${(wcIdx + 1) / wcWords.length * 100}%` }"></view>
          </view>
          <text class="vocab-progress-text">{{ wcIdx + 1 }} / {{ wcWords.length }}</text>

          <!-- 英文单词 -->
          <view class="card wc-word-card">
            <text class="wc-word-text">{{ wcCurrentWord?.word }}</text>
            <text v-if="wcCurrentWord?.phonetic" class="wc-word-phonetic">{{ wcCurrentWord.phonetic }}</text>
          </view>

          <!-- 四个选项 -->
          <view class="wc-options">
            <view
              v-for="(opt, i) in wcOptions"
              :key="i"
              class="card wc-option"
              :class="{
                correct: wcShowResult && opt === wcCurrentWord?.meaning,
                wrong: wcShowResult && wcSelectedIdx === i && opt !== wcCurrentWord?.meaning,
                selected: !wcShowResult && wcSelectedIdx === i,
              }"
              @tap="selectWcOption(i)"
            >
              <text class="wc-option-label">{{ ['A', 'B', 'C', 'D'][i] }}</text>
              <text class="wc-option-text">{{ opt }}</text>
            </view>
          </view>

          <!-- 结果提示 -->
          <view v-if="wcShowResult" class="card wc-result-card" :class="wcIsCorrect ? 'wc-result-correct' : 'wc-result-wrong'">
            <text>{{ wcIsCorrect ? '✅ 正确！' : '❌ 错误，正确答案：' + wcCurrentWord?.meaning }}</text>
          </view>

          <view class="wc-nav">
            <button v-if="!wcShowResult" class="btn btn-text" @tap="showWcAnswer">
              <text>不会，看答案</text>
            </button>
            <button v-if="wcShowResult" class="btn btn-primary btn-block btn-lg" @tap="nextWcWord">
              <text>{{ wcIdx < wcWords.length - 1 ? '下一个' : '查看结果' }}</text>
            </button>
          </view>

          <!-- 完成 -->
          <view v-if="wcDone" class="card vocab-done-card">
            <text class="vocab-done-title">🎉 选义完成</text>
            <view class="vocab-done-stats">
              <view class="vocab-done-stat">
                <text class="vocab-done-stat-num" style="color: var(--success)">{{ wcCorrectCount }}</text>
                <text class="vocab-done-stat-label">正确</text>
              </view>
              <view class="vocab-done-stat">
                <text class="vocab-done-stat-num" style="color: var(--error)">{{ wcWords.length - wcCorrectCount }}</text>
                <text class="vocab-done-stat-label">错误</text>
              </view>
            </view>
            <button class="btn btn-primary btn-block" @tap="resetWc">
              <text>返回</text>
            </button>
          </view>
        </view>
      </view>

      <!-- ===== 单词默写（接入后端） ===== -->
      <view v-show="activeTab === 'wordDictation'">
        <view v-if="!wdActive" class="section">
          <text class="section-title">单词默写</text>
          <view v-if="wdDueWords.length === 0" class="empty-state">
            <text class="icon">✏️</text>
            <text class="empty-text">暂无待复习单词</text>
            <text class="empty-hint">收藏更多单词后再来复习</text>
          </view>
          <view v-else class="card vocab-start-card">
            <view class="vocab-info">
              <text class="vocab-info-icon">✏️</text>
              <view>
                <text class="vocab-info-label">待复习单词</text>
                <text class="vocab-info-count">{{ wdDueWords.length }}</text>
              </view>
            </view>
            <button class="btn btn-primary btn-sm" @tap="startWordDictation">
              <text>开始</text>
            </button>
          </view>
        </view>

        <view v-else class="vocab-active">
          <view class="vocab-progress-bar-bg">
            <view class="vocab-progress-bar-fill" :style="{ width: `${(wdIdx + 1) / wdWords.length * 100}%` }"></view>
          </view>
          <text class="vocab-progress-text">{{ wdIdx + 1 }} / {{ wdWords.length }}</text>

          <view class="card vocab-hint-card">
            <text class="vocab-hint-label">中文释义</text>
            <text class="vocab-hint-meaning">{{ wdCurrentWord?.meaning || '' }}</text>
          </view>

          <view class="card vocab-input-card">
            <input v-model="wdInput" type="text" placeholder="输入英文单词..." class="vocab-input" @confirm="wdShowResult ? nextWdWord() : checkWdWord()" />
          </view>

          <view class="vocab-buttons">
            <button v-if="!wdShowResult" class="btn btn-primary btn-block btn-lg" :disabled="!wdInput.trim()" @tap="checkWdWord">
              <text>确认</text>
            </button>
            <button v-if="!wdShowResult" class="btn btn-text btn-block" @tap="showWdAnswer">
              <text>不会，看答案</text>
            </button>
            <button v-if="wdShowResult" class="btn btn-primary btn-block btn-lg" @tap="nextWdWord">
              <text>{{ wdIdx < wdWords.length - 1 ? '下一个' : '查看结果' }}</text>
            </button>
          </view>

          <view v-if="wdShowResult" class="card vocab-result-card">
            <text class="vocab-result-status" :class="wdIsCorrect ? 'correct' : 'wrong'">
              {{ wdIsCorrect ? '✅ 正确' : '❌ 错误' }}
            </text>
            <text v-if="!wdIsCorrect" class="vocab-result-answer">
              正确答案：{{ wdCurrentWord?.word }}
            </text>
          </view>

          <view v-if="wdDone" class="card vocab-done-card">
            <text class="vocab-done-title">🎉 默写完成</text>
            <view class="vocab-done-stats">
              <view class="vocab-done-stat">
                <text class="vocab-done-stat-num" style="color: var(--success)">{{ wdCorrectCount }}</text>
                <text class="vocab-done-stat-label">正确</text>
              </view>
              <view class="vocab-done-stat">
                <text class="vocab-done-stat-num" style="color: var(--error)">{{ wdWords.length - wdCorrectCount }}</text>
                <text class="vocab-done-stat-label">错误</text>
              </view>
            </view>
            <button class="btn btn-primary btn-block" @tap="resetWd">
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
          <view class="dictation-close" @tap="dictatingContent = null"><text>✕</text></view>
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
          <view class="dictation-score-area">
            <text class="dictation-score" :class="getScoreClass(dictResult.feedback.score)">{{ dictResult.feedback.score }}</text>
            <view class="dictation-score-meta">
              <text>准确率 {{ dictResult.accuracy_rate.toFixed(0) }}%</text>
              <text style="color: var(--success)">+{{ dictResult.earned_points }} 积分</text>
            </view>
          </view>
          <view v-if="dictResult.feedback.summary" class="dictation-feedback">
            <text class="dictation-feedback-label">AI 总评</text>
            <text class="dictation-feedback-text">{{ dictResult.feedback.summary }}</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { dailyApi, dictationApi, favoritesApi, wordReviewApi } from '@/api'
import { useAuthStore } from '@/stores'
import { navTo } from '@/utils/router'
import type { LearningContent, DictationResult, ReviewTask, MemoryProgress } from '@/types'

const auth = useAuthStore()
const loading = ref(true)
const activeTab = ref<'review' | 'dictation' | 'wordChoice' | 'wordDictation'>('review')
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

// 单词选义
const wcDueWords = ref<any[]>([])
const wcDistractors = ref<any[]>([])
const wcActive = ref(false)
const wcWords = ref<any[]>([])
const wcIdx = ref(0)
const wcOptions = ref<string[]>([])
const wcSelectedIdx = ref(-1)
const wcShowResult = ref(false)
const wcIsCorrect = ref(false)
const wcDone = ref(false)
const wcCorrectCount = ref(0)

// 单词默写
const wdDueWords = ref<any[]>([])
const wdActive = ref(false)
const wdWords = ref<any[]>([])
const wdIdx = ref(0)
const wdInput = ref('')
const wdShowResult = ref(false)
const wdIsCorrect = ref(false)
const wdDone = ref(false)
const wdCorrectCount = ref(0)

const wcCurrentWord = computed(() => wcWords.value[wcIdx.value] || null)
const wdCurrentWord = computed(() => wdWords.value[wdIdx.value] || null)
const usernameInitial = computed(() => (auth.username?.[0] || '?').toUpperCase())

const stageColors: Record<number, string> = {
  0: '#9E9E9E', 1: '#F44336', 2: '#FF9800',
  3: '#FFC107', 4: '#4CAF50', 5: '#2196F3',
}

function switchTab(tab: typeof activeTab.value) {
  activeTab.value = tab
  if ((tab === 'wordChoice' || tab === 'wordDictation') && wcDueWords.value.length === 0) {
    loadWordReview()
  }
}

function goDetail(contentId: number) { navTo(`/pages/detail/index?id=${contentId}`) }
function getScoreClass(score: number) {
  if (score >= 80) return 'score-green'
  if (score >= 60) return 'score-orange'
  return 'score-red'
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

// ===== 单词复习数据加载 =====
async function loadWordReview() {
  try {
    const { data } = await wordReviewApi.getDue(auth.currentUserId, 20)
    wcDueWords.value = data.words || []
    wcDistractors.value = data.distractors || []
    wdDueWords.value = data.words || []
  } catch {
    wcDueWords.value = []
    wcDistractors.value = []
    wdDueWords.value = []
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

// ===== 单词选义 =====
function startWordChoice() {
  if (wcDueWords.value.length === 0) return
  wcWords.value = shuffleArray(wcDueWords.value).slice(0, Math.min(15, wcDueWords.value.length))
  wcIdx.value = 0; wcSelectedIdx.value = -1; wcShowResult.value = false
  wcIsCorrect.value = false; wcDone.value = false; wcCorrectCount.value = 0
  wcActive.value = true
  generateWcOptions()
}

function generateWcOptions() {
  const current = wcWords.value[wcIdx.value]
  if (!current) return
  const correct = current.meaning || ''
  // 从干扰项中随机抽 3 个
  const pool = shuffleArray(wcDistractors.value.filter((d: any) => d.meaning && d.meaning !== correct))
  const distractorMeanings = pool.slice(0, 3).map((d: any) => d.meaning)
  // 不够就用占位
  while (distractorMeanings.length < 3) {
    distractorMeanings.push('暂无释义')
  }
  wcOptions.value = shuffleArray([correct, ...distractorMeanings])
}

function selectWcOption(idx: number) {
  if (wcShowResult.value) return
  wcSelectedIdx.value = idx
  const correct = wcWords.value[wcIdx.value]?.meaning
  wcIsCorrect.value = wcOptions.value[idx] === correct
  wcShowResult.value = true
  if (wcIsCorrect.value) wcCorrectCount.value++
  // 提交到后端
  wordReviewApi.submit(auth.currentUserId, wcWords.value[wcIdx.value].word, wcIsCorrect.value)
}

function showWcAnswer() {
  wcIsCorrect.value = false
  wcShowResult.value = true
  wordReviewApi.submit(auth.currentUserId, wcWords.value[wcIdx.value].word, false)
}

function nextWcWord() {
  if (wcIdx.value < wcWords.value.length - 1) {
    wcIdx.value++; wcSelectedIdx.value = -1; wcShowResult.value = false; wcIsCorrect.value = false
    generateWcOptions()
  } else {
    wcDone.value = true
  }
}

function resetWc() { wcActive.value = false }

// ===== 单词默写（后端版） =====
function startWordDictation() {
  if (wdDueWords.value.length === 0) return
  wdWords.value = shuffleArray(wdDueWords.value).slice(0, Math.min(15, wdDueWords.value.length))
  wdIdx.value = 0; wdInput.value = ''; wdShowResult.value = false
  wdIsCorrect.value = false; wdDone.value = false; wdCorrectCount.value = 0
  wdActive.value = true
}

function checkWdWord() {
  if (!wdCurrentWord.value || !wdInput.value.trim()) return
  wdIsCorrect.value = wdInput.value.trim().toLowerCase() === wdCurrentWord.value.word.toLowerCase()
  if (wdIsCorrect.value) wdCorrectCount.value++
  wdShowResult.value = true
  // 提交到后端
  const accuracy = wdIsCorrect.value ? 100 : 0
  wordReviewApi.submit(auth.currentUserId, wdCurrentWord.value.word, wdIsCorrect.value, accuracy)
}

function showWdAnswer() {
  wdIsCorrect.value = false
  wdShowResult.value = true
  wordReviewApi.submit(auth.currentUserId, wdWords.value[wdIdx.value].word, false, 0)
}

function nextWdWord() {
  if (wdIdx.value < wdWords.value.length - 1) {
    wdIdx.value++; wdInput.value = ''; wdShowResult.value = false; wdIsCorrect.value = false
  } else {
    wdDone.value = true
  }
}

function resetWd() { wdActive.value = false }

// ===== 数据加载 =====
async function loadData() {
  loading.value = true
  try {
    const { data } = await dailyApi.getReviewTasks(auth.currentUserId)
    dueTasks.value = data.tasks || []
  } catch {}
  try {
    const { data } = await dailyApi.getAllProgress(auth.currentUserId)
    progressList.value = data.items || []
    masteredCount.value = data.mastered_count || 0
  } catch {}
  try {
    const { data } = await dailyApi.getTodayList(auth.currentUserId)
    todayContents.value = data.contents || []
  } catch {}
  try {
    const { data } = await dailyApi.getList(30)
    if (Array.isArray(data)) {
      const ids = new Set(todayContents.value.map(c => c.id))
      for (const item of data) {
        if (!ids.has(item.id)) todayContents.value.push(item)
      }
    }
  } catch {}
  await loadWordReview()
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

/* 通用词汇卡片 */
.vocab-start-card { display: flex; align-items: center; justify-content: space-between; }
.vocab-info { display: flex; align-items: center; gap: 20rpx; }
.vocab-info-icon { font-size: 48rpx; }
.vocab-info-label { font-size: 26rpx; color: var(--on-surface-variant); display: block; }
.vocab-info-count { font-size: 32rpx; font-weight: 700; display: block; }
.vocab-progress-bar-bg { height: 8rpx; background: var(--surface-container); border-radius: 4rpx; margin: 32rpx 32rpx 0; overflow: hidden; }
.vocab-progress-bar-fill { height: 100%; background: var(--primary); border-radius: 4rpx; transition: width 0.3s; }
.vocab-progress-text { text-align: center; font-size: 24rpx; color: var(--on-surface-variant); margin-top: 12rpx; display: block; }
.vocab-hint-card { text-align: center; padding: 40rpx; }
.vocab-hint-label { font-size: 22rpx; color: var(--on-surface-variant); margin-bottom: 16rpx; display: block; }
.vocab-hint-meaning { font-size: 40rpx; font-weight: 600; display: block; }
.vocab-input-card { margin: 0 32rpx 24rpx; }
.vocab-input { width: 100%; border: none; border-bottom: 3rpx solid var(--outline); padding: 20rpx 0; font-size: 36rpx; text-align: center; outline: none; }
.vocab-input:focus { border-bottom-color: var(--primary); }
.vocab-buttons { padding: 0 32rpx 24rpx; display: flex; flex-direction: column; gap: 12rpx; align-items: center; }
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

/* 单词选义 */
.wc-word-card { text-align: center; padding: 48rpx 32rpx; margin: 16rpx 32rpx; }
.wc-word-text { font-size: 52rpx; font-weight: 800; display: block; }
.wc-word-phonetic { font-size: 26rpx; color: var(--on-surface-variant); display: block; margin-top: 12rpx; }
.wc-options { padding: 0 32rpx; display: flex; flex-direction: column; gap: 16rpx; }
.wc-option {
  display: flex; align-items: center; gap: 20rpx; padding: 28rpx 24rpx;
  border: 3rpx solid var(--outline-variant); border-radius: 16rpx; transition: all 0.15s;
}
.wc-option.selected { border-color: var(--primary); background: var(--primary-container); }
.wc-option.correct { border-color: var(--success); background: var(--success-container); }
.wc-option.wrong { border-color: var(--error); background: var(--error-container); }
.wc-option-label { font-size: 28rpx; font-weight: 700; color: var(--on-surface-variant); width: 48rpx; text-align: center; }
.wc-option-text { font-size: 28rpx; flex: 1; }
.wc-result-card { margin: 24rpx 32rpx; padding: 24rpx; text-align: center; font-size: 28rpx; font-weight: 600; }
.wc-result-correct { background: var(--success-container); color: var(--success); }
.wc-result-wrong { background: var(--error-container); color: var(--error); }
.wc-nav { padding: 16rpx 32rpx 32rpx; text-align: center; }

/* 默写弹窗 */
.dictation-sheet { width: 100%; max-width: 600px; max-height: 90vh; background: white; border-radius: 32rpx 32rpx 0 0; overflow-y: auto; padding-bottom: env(safe-area-inset-bottom, 32rpx); }
.dictation-sheet-top { display: flex; justify-content: space-between; align-items: center; padding: 32rpx 32rpx 0; }
.dictation-close { width: 56rpx; height: 56rpx; background: var(--surface-container); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 28rpx; }
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
</style>
