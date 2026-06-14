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
      <view class="underline-tab" :class="{ active: activeTab === 'review' }" @tap="activeTab = 'review'">
        <text>复述</text>
        <view v-if="dueTasks.length" class="tab-badge"><text>{{ dueTasks.length }}</text></view>
      </view>
      <view class="underline-tab" :class="{ active: activeTab === 'dictation' }" @tap="activeTab = 'dictation'">
        <text>默写</text>
      </view>
      <view class="underline-tab" :class="{ active: activeTab === 'vocab' }" @tap="activeTab = 'vocab'">
        <text>词汇默写</text>
      </view>
    </view>

    <view v-if="loading" class="loading">
      <view class="spinner"></view>
    </view>

    <template v-else>
      <!-- 复述 -->
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

      <!-- 默写 -->
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

      <!-- 词汇默写 -->
      <view v-show="activeTab === 'vocab'">
        <view v-if="!vocabActive" class="section">
          <text class="section-title">收藏词汇默写</text>
          <view v-if="favoriteWords.length === 0" class="empty-state">
            <text class="icon">📝</text>
            <text class="empty-text">暂无收藏词汇</text>
            <text class="empty-hint">在阅读页点击单词可收藏</text>
          </view>
          <view v-else>
            <view class="card vocab-start-card">
              <view class="vocab-info">
                <text class="vocab-info-icon">📚</text>
                <view>
                  <text class="vocab-info-label">收藏词汇</text>
                  <text class="vocab-info-count">{{ favoriteWords.length }}</text>
                </view>
              </view>
              <button class="btn btn-primary btn-sm" @tap="startVocabDictation">
                <text>开始</text>
              </button>
            </view>
          </view>
        </view>

        <view v-else class="vocab-active">
          <!-- 进度条 -->
          <view class="vocab-progress-bar-bg">
            <view class="vocab-progress-bar-fill" :style="{ width: `${(vocabIdx + 1) / vocabWords.length * 100}%` }"></view>
          </view>
          <text class="vocab-progress-text">{{ vocabIdx + 1 }} / {{ vocabWords.length }}</text>

          <!-- 提示卡 -->
          <view class="card vocab-hint-card">
            <text class="vocab-hint-label">中文释义</text>
            <text class="vocab-hint-meaning">{{ vocabCurrentWord?.meaning || '' }}</text>
          </view>

          <view class="card vocab-input-card">
            <input v-model="vocabInput" type="text" placeholder="输入英文单词..." class="vocab-input" @confirm="vocabShowResult ? nextVocabWord() : checkVocabWord()" />
          </view>

          <view class="vocab-buttons">
            <button v-if="!vocabShowResult" class="btn btn-primary btn-block btn-lg" :disabled="!vocabInput.trim()" @tap="checkVocabWord">
              <text>确认</text>
            </button>
            <button v-if="!vocabShowResult" class="btn btn-text btn-block" @tap="showVocabAnswer">
              <text>不会，看答案</text>
            </button>
            <button v-if="vocabShowResult" class="btn btn-primary btn-block btn-lg" @tap="nextVocabWord">
              <text>{{ vocabIdx < vocabWords.length - 1 ? '下一个' : '查看结果' }}</text>
            </button>
          </view>

          <view v-if="vocabShowResult" class="card vocab-result-card">
            <text class="vocab-result-status" :class="vocabIsCorrect ? 'correct' : 'wrong'">
              {{ vocabIsCorrect ? '✅ 正确' : '❌ 错误' }}
            </text>
            <text v-if="!vocabIsCorrect" class="vocab-result-answer">
              正确答案：{{ vocabCurrentWord?.word }}
            </text>
          </view>

          <view v-if="vocabDone" class="card vocab-done-card">
            <text class="vocab-done-title">🎉 默写完成</text>
            <view class="vocab-done-stats">
              <view class="vocab-done-stat">
                <text class="vocab-done-stat-num" style="color: var(--success)">{{ vocabCorrectCount }}</text>
                <text class="vocab-done-stat-label">正确</text>
              </view>
              <view class="vocab-done-stat">
                <text class="vocab-done-stat-num" style="color: var(--error)">{{ vocabWords.length - vocabCorrectCount }}</text>
                <text class="vocab-done-stat-label">错误</text>
              </view>
            </view>
            <button class="btn btn-primary btn-block" @tap="resetVocab">
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

        <view v-if="result" class="card dictation-result-card">
          <view class="dictation-score-area">
            <text class="dictation-score" :class="getScoreClass(result.feedback.score)">{{ result.feedback.score }}</text>
            <view class="dictation-score-meta">
              <text>准确率 {{ result.accuracy_rate.toFixed(0) }}%</text>
              <text style="color: var(--success)">+{{ result.earned_points }} 积分</text>
            </view>
          </view>
          <view v-if="result.feedback.summary" class="dictation-feedback">
            <text class="dictation-feedback-label">AI 总评</text>
            <text class="dictation-feedback-text">{{ result.feedback.summary }}</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { dailyApi, dictationApi, favoritesApi } from '@/api'
import { useAuthStore } from '@/stores'
import { navTo } from '@/utils/router'
import type { LearningContent, DictationResult, ReviewTask, MemoryProgress } from '@/types'

const auth = useAuthStore()
const loading = ref(true)
const activeTab = ref<'review' | 'dictation' | 'vocab'>('review')

// 复习
const dueTasks = ref<ReviewTask[]>([])
const progressList = ref<MemoryProgress[]>([])
const masteredCount = ref(0)

// 默写
const todayContents = ref<LearningContent[]>([])
const dictatingContent = ref<LearningContent | null>(null)
const showOriginal = ref(false)
const userInput = ref('')
const submitting = ref(false)
const result = ref<DictationResult | null>(null)

// 词汇默写
const favoriteWords = ref<{ word: string; meaning?: string }[]>([])
const vocabActive = ref(false)
const vocabWords = ref<{ word: string; meaning?: string }[]>([])
const vocabIdx = ref(0)
const vocabInput = ref('')
const vocabShowResult = ref(false)
const vocabIsCorrect = ref(false)
const vocabDone = ref(false)
const vocabCorrectCount = ref(0)

const vocabCurrentWord = computed(() => vocabWords.value[vocabIdx.value] || null)

const usernameInitial = computed(() => (auth.username?.[0] || '?').toUpperCase())

const stageColors: Record<number, string> = {
  0: '#9E9E9E', 1: '#F44336', 2: '#FF9800',
  3: '#FFC107', 4: '#4CAF50', 5: '#2196F3',
}

function goDetail(contentId: number) { navTo(`/pages/detail/index?id=${contentId}`) }
function getScoreClass(score: number) {
  if (score >= 80) return 'score-green'
  if (score >= 60) return 'score-orange'
  return 'score-red'
}

function startDictation(item: LearningContent) {
  dictatingContent.value = item
  showOriginal.value = false
  userInput.value = ''
  result.value = null
}

async function handleSubmit() {
  if (!dictatingContent.value || !userInput.value.trim()) return
  submitting.value = true
  try {
    const { data } = await dictationApi.submit(auth.currentUserId, dictatingContent.value.id, userInput.value)
    result.value = data
  } catch { uni.showToast({ title: '提交失败', icon: 'none' }) }
  submitting.value = false
}

async function loadFavorites() {
  try {
    const { data } = await favoritesApi.list(auth.currentUserId, 200)
    favoriteWords.value = (data || []).map((f: any) => ({ word: f.word, meaning: f.meaning || '' }))
  } catch { favoriteWords.value = [] }
}

function shuffleArray<T>(array: T[]): T[] {
  const shuffled = [...array]
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
  }
  return shuffled
}

function startVocabDictation() {
  if (favoriteWords.value.length === 0) return
  const shuffled = shuffleArray(favoriteWords.value)
  vocabWords.value = shuffled.slice(0, Math.min(10, shuffled.length))
  vocabIdx.value = 0; vocabInput.value = ''; vocabShowResult.value = false
  vocabIsCorrect.value = false; vocabDone.value = false; vocabCorrectCount.value = 0
  vocabActive.value = true
}

function checkVocabWord() {
  if (!vocabCurrentWord.value || !vocabInput.value.trim()) return
  vocabIsCorrect.value = vocabInput.value.trim().toLowerCase() === vocabCurrentWord.value.word.toLowerCase()
  if (vocabIsCorrect.value) vocabCorrectCount.value++
  vocabShowResult.value = true
}

function showVocabAnswer() { vocabIsCorrect.value = false; vocabShowResult.value = true }
function nextVocabWord() {
  if (vocabIdx.value < vocabWords.value.length - 1) {
    vocabIdx.value++; vocabInput.value = ''; vocabShowResult.value = false; vocabIsCorrect.value = false
  } else { vocabDone.value = true }
}
function resetVocab() { vocabActive.value = false }

async function loadData() {
  loading.value = true
  try {
    const [reviewRes, progressRes, todayRes] = await Promise.all([
      dailyApi.getReviewTasks(auth.currentUserId),
      dailyApi.getAllProgress(auth.currentUserId),
      dailyApi.getTodayList(auth.currentUserId),
    ])
    dueTasks.value = reviewRes.data.tasks || []
    progressList.value = progressRes.data.items || []
    masteredCount.value = progressRes.data.mastered_count || 0
    todayContents.value = todayRes.data.contents || []
    await loadFavorites()
  } catch {}
  loading.value = false
}

onShow(loadData)
</script>

<style scoped>
.tab-badge {
  display: inline-block;
  background: var(--error);
  color: white;
  font-size: 20rpx;
  font-weight: 700;
  min-width: 32rpx;
  height: 32rpx;
  line-height: 32rpx;
  border-radius: 16rpx;
  padding: 0 8rpx;
  margin-left: 8rpx;
  vertical-align: middle;
  text-align: center;
}

.section { padding: 24rpx 24rpx; }
.section-title { font-size: 28rpx; font-weight: 700; margin-bottom: 20rpx; display: block; }

.task-list { display: flex; flex-direction: column; gap: 16rpx; }
.task-item { display: flex; align-items: center; gap: 20rpx; padding: 24rpx 28rpx; }
.task-avatar {
  width: 72rpx; height: 72rpx; border-radius: 20rpx;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.task-stage { color: white; font-weight: 700; font-size: 24rpx; }
.task-info { flex: 1; min-width: 0; }
.task-title { font-weight: 600; font-size: 28rpx; display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.task-meta { font-size: 22rpx; color: var(--on-surface-variant); margin-top: 4rpx; display: block; }

.content-list { display: flex; flex-direction: column; gap: 16rpx; }
.content-item { display: flex; align-items: center; gap: 20rpx; }
.content-left { flex: 1; }
.content-title { font-weight: 600; font-size: 28rpx; display: block; }
.content-meta { font-size: 24rpx; color: var(--on-surface-variant); margin-top: 4rpx; display: block; }

/* 词汇默写 - 开始卡片 */
.vocab-start-card {
  display: flex; align-items: center; justify-content: space-between;
}
.vocab-info { display: flex; align-items: center; gap: 20rpx; }
.vocab-info-icon { font-size: 48rpx; }
.vocab-info-label { font-size: 26rpx; color: var(--on-surface-variant); display: block; }
.vocab-info-count { font-size: 32rpx; font-weight: 700; display: block; }

/* 词汇默写 - 进行中 */
.vocab-progress-bar-bg {
  height: 8rpx; background: var(--surface-container); border-radius: 4rpx;
  margin: 32rpx 32rpx 0; overflow: hidden;
}
.vocab-progress-bar-fill { height: 100%; background: var(--primary); border-radius: 4rpx; transition: width 0.3s; }
.vocab-progress-text { text-align: center; font-size: 24rpx; color: var(--on-surface-variant); margin-top: 12rpx; display: block; }
.vocab-hint-card { text-align: center; padding: 40rpx; }
.vocab-hint-label { font-size: 22rpx; color: var(--on-surface-variant); margin-bottom: 16rpx; display: block; }
.vocab-hint-meaning { font-size: 40rpx; font-weight: 600; display: block; }
.vocab-input-card { margin: 0 32rpx 24rpx; }
.vocab-input {
  width: 100%; border: none; border-bottom: 3rpx solid var(--outline);
  padding: 20rpx 0; font-size: 36rpx; text-align: center; outline: none;
}
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

/* 默写弹窗 */
.dictation-sheet {
  width: 100%; max-width: 600px; max-height: 90vh;
  background: white; border-radius: 32rpx 32rpx 0 0;
  overflow-y: auto;
  padding-bottom: env(safe-area-inset-bottom, 32rpx);
}
.dictation-sheet-top {
  display: flex; justify-content: space-between; align-items: center;
  padding: 32rpx 32rpx 0;
}
.dictation-close {
  width: 56rpx; height: 56rpx;
  background: var(--surface-container); border-radius: 50%;
  display: flex; align-items: center; justify-content: center; font-size: 28rpx;
}
.dictation-hint-card {
  margin: 24rpx 32rpx; padding: 28rpx;
  background: var(--primary-container); border-radius: 16rpx;
}
.dictation-hint-label { font-size: 22rpx; color: var(--on-primary-container); margin-bottom: 12rpx; display: block; }
.dictation-hint-text { font-size: 28rpx; line-height: 1.6; display: block; color: var(--on-primary-container); }
.dictation-original-card {
  margin: 16rpx 32rpx; padding: 28rpx;
  background: var(--surface-container); border-radius: 16rpx;
}
.dictation-original-text { font-size: 28rpx; line-height: 1.6; display: block; }
.dictation-input-card { padding: 16rpx 32rpx; }
.dictation-textarea {
  width: 100%; height: 280rpx;
  border: 3rpx solid var(--outline); border-radius: 16rpx;
  padding: 24rpx; font-size: 28rpx; line-height: 1.6;
}
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
