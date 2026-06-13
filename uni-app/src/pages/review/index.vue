<template>
  <view class="page-container">
    <view class="page-header">
      <text class="title">复习</text>
    </view>

    <!-- 功能入口 -->
    <view class="feature-tabs">
      <view class="feature-tab" :class="{ active: activeTab === 'review' }" @tap="activeTab = 'review'">
        <text class="feature-icon">🔄</text>
        <text class="feature-name">记忆复习</text>
        <view v-if="dueTasks.length" class="feature-badge">
          <text>{{ dueTasks.length }}</text>
        </view>
      </view>
      <view class="feature-tab" :class="{ active: activeTab === 'dictation' }" @tap="activeTab = 'dictation'">
        <text class="feature-icon">✏️</text>
        <text class="feature-name">默写练习</text>
      </view>
      <view class="feature-tab" :class="{ active: activeTab === 'vocab' }" @tap="activeTab = 'vocab'">
        <text class="feature-icon">📚</text>
        <text class="feature-name">词汇默写</text>
      </view>
    </view>

    <view v-if="loading" class="loading">
      <view class="spinner"></view>
    </view>

    <!-- 复习 tab -->
    <view v-else-if="activeTab === 'review'">
      <view class="stats-row">
        <view class="stat-card">
          <text class="stat-num">{{ progressList.length }}</text>
          <text class="stat-label">总内容</text>
        </view>
        <view class="stat-card">
          <text class="stat-num stat-success">{{ masteredCount }}</text>
          <text class="stat-label">已掌握</text>
        </view>
        <view class="stat-card">
          <text class="stat-num stat-warning">{{ dueTasks.length }}</text>
          <text class="stat-label">待复习</text>
        </view>
      </view>

      <view v-if="dueTasks.length" class="section">
        <text class="section-title">📋 今日复习</text>
        <view class="task-list">
          <view v-for="task in dueTasks" :key="task.content_id" class="card task-item">
            <view class="task-avatar" :style="{ background: stageColors[task.review_stage] || '#5B9AA8' }">
              <text class="task-stage">S{{ task.review_stage }}</text>
            </view>
            <view class="task-info">
              <text class="task-title">{{ task.title }}</text>
              <text class="task-meta">准确率 {{ task.last_accuracy.toFixed(0) }}%</text>
            </view>
            <button class="btn btn-sm btn-primary" @tap="goDetail(task.content_id)">
              <text>去复习</text>
            </button>
          </view>
        </view>
      </view>

      <view v-else class="empty-state" style="padding-top: 40rpx">
        <text class="icon" style="color: var(--success)">✅</text>
        <text class="empty-text">暂无待复习内容，继续学习吧！</text>
      </view>
    </view>

    <!-- 默写 tab -->
    <view v-else-if="activeTab === 'dictation'">
      <view class="section">
        <text class="section-title">📚 今日学习内容</text>
        <view v-if="todayContents.length === 0" class="empty-state">
          <text class="icon">📝</text>
          <text class="empty-text">暂无学习内容</text>
        </view>
        <view v-else class="content-list">
          <view v-for="item in todayContents" :key="item.id" class="card content-item">
            <view class="content-left">
              <text class="content-title">{{ item.title }}</text>
              <text class="content-meta">{{ item.content_date }} · {{ item.difficulty_level }}</text>
            </view>
            <view class="content-actions">
              <button class="btn btn-sm btn-outline" @tap="startDictation(item)">
                <text>默写</text>
              </button>
            </view>
          </view>
        </view>
      </view>

      <!-- 默写弹窗 -->
      <view v-if="dictatingContent" class="modal-overlay" @tap="dictatingContent = null">
        <view class="dictation-sheet" @tap.stop>
          <view class="sheet-top">
            <text class="tag tag-primary">默写练习</text>
            <view class="close-btn" @tap="dictatingContent = null"><text>✕</text></view>
          </view>

          <view class="card" style="margin: 24rpx 32rpx">
            <text class="hint-label">中文翻译提示</text>
            <text class="hint-text">{{ dictatingContent.translation || '暂无翻译' }}</text>
          </view>

          <view v-if="showOriginal" class="card" style="margin: 0 32rpx; background: var(--primary-container)">
            <text class="hint-label" style="color: var(--on-primary-container)">英文原文</text>
            <text class="original-text">{{ dictatingContent.article }}</text>
          </view>

          <view style="padding: 16rpx 32rpx">
            <button class="btn btn-sm btn-outline" @tap="showOriginal = !showOriginal">
              <text>{{ showOriginal ? '🙈 隐藏原文' : '👁️ 显示原文' }}</text>
            </button>
          </view>

          <view class="card" style="margin: 0 32rpx">
            <textarea
              v-model="userInput"
              :maxlength="-1"
              placeholder="在这里输入你默写的英文内容..."
              placeholder-style="color: #999"
              class="dictation-textarea"
            />
          </view>

          <view style="padding: 24rpx 32rpx; display: flex; gap: 20rpx">
            <button
              class="btn btn-primary btn-block"
              :disabled="submitting || !userInput.trim()"
              @tap="handleSubmit"
            >
              <text>{{ submitting ? 'AI 批改中...' : '提交批改' }}</text>
            </button>
          </view>

          <view v-if="result" class="card result-card" style="margin: 0 32rpx 32rpx">
            <view class="score-area">
              <text class="score" :class="getScoreClass(result.feedback.score)">{{ result.feedback.score }}</text>
              <view class="score-meta">
                <text>准确率 {{ result.accuracy_rate.toFixed(0) }}%</text>
                <text style="color: var(--success)">+{{ result.earned_points }} 积分</text>
              </view>
            </view>
            <view v-if="result.feedback.summary" class="feedback-section">
              <text class="feedback-label">AI 总评</text>
              <text class="feedback-text">{{ result.feedback.summary }}</text>
            </view>
          </view>
        </view>
      </view>
    </view>

    <!-- 词汇默写 tab -->
    <view v-else-if="activeTab === 'vocab'">
      <view v-if="!vocabActive">
        <view class="section">
          <text class="section-title">📚 收藏词汇默写</text>
          <view v-if="favoriteWords.length === 0" class="empty-state">
            <text class="icon">📝</text>
            <text class="empty-text">暂无收藏词汇</text>
          </view>
          <view v-else>
            <view class="card">
              <view class="vocab-info-row">
                <text>收藏词汇数</text>
                <text class="vocab-info-val">{{ favoriteWords.length }}</text>
              </view>
            </view>
            <button class="btn btn-primary btn-block" style="margin-top: 32rpx" @tap="startVocabDictation">
              <text>开始默写</text>
            </button>
          </view>
        </view>
      </view>

      <!-- 词汇默写进行中 -->
      <view v-else>
        <view class="vocab-progress">
          <view class="vocab-progress-bar" :style="{ width: `${(vocabIdx + 1) / vocabWords.length * 100}%` }"></view>
        </view>
        <text class="vocab-progress-text">{{ vocabIdx + 1 }} / {{ vocabWords.length }}</text>

        <view class="card vocab-hint-card">
          <text class="vocab-hint-label">中文释义</text>
          <text class="vocab-hint-meaning">{{ vocabCurrentWord?.meaning || '' }}</text>
        </view>

        <view class="card" style="margin: 0 32rpx">
          <input
            v-model="vocabInput"
            type="text"
            placeholder="输入英文单词..."
            class="vocab-input"
            @confirm="vocabShowResult ? nextVocabWord() : checkVocabWord()"
          />
        </view>

        <view class="vocab-actions">
          <button v-if="!vocabShowResult" class="btn btn-primary btn-block" :disabled="!vocabInput.trim()" @tap="checkVocabWord">
            <text>确认</text>
          </button>
          <button v-if="!vocabShowResult" class="btn btn-outline btn-block" @tap="showVocabAnswer">
            <text>不会，看答案</text>
          </button>
          <button v-if="vocabShowResult" class="btn btn-primary btn-block" @tap="nextVocabWord">
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
            <view class="vocab-stat">
              <text class="vocab-stat-num stat-success">{{ vocabCorrectCount }}</text>
              <text class="vocab-stat-label">正确</text>
            </view>
            <view class="vocab-stat">
              <text class="vocab-stat-num stat-error">{{ vocabWords.length - vocabCorrectCount }}</text>
              <text class="vocab-stat-label">错误</text>
            </view>
          </view>
          <button class="btn btn-primary btn-block" @tap="resetVocab">
            <text>返回</text>
          </button>
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

const stageColors: Record<number, string> = {
  0: '#9E9E9E', 1: '#F44336', 2: '#FF9800',
  3: '#FFC107', 4: '#4CAF50', 5: '#2196F3',
}

function goDetail(contentId: number) {
  navTo(`/pages/detail/index?id=${contentId}`)
}

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
  } catch {
    uni.showToast({ title: '提交失败', icon: 'none' })
  }
  submitting.value = false
}

// 词汇默写
async function loadFavorites() {
  try {
    const { data } = await favoritesApi.list(auth.currentUserId, 200)
    favoriteWords.value = (data || []).map((f: any) => ({
      word: f.word,
      meaning: f.meaning || '',
    }))
  } catch {
    favoriteWords.value = []
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

function startVocabDictation() {
  if (favoriteWords.value.length === 0) return
  const shuffled = shuffleArray(favoriteWords.value)
  vocabWords.value = shuffled.slice(0, Math.min(10, shuffled.length))
  vocabIdx.value = 0
  vocabInput.value = ''
  vocabShowResult.value = false
  vocabIsCorrect.value = false
  vocabDone.value = false
  vocabCorrectCount.value = 0
  vocabActive.value = true
}

function checkVocabWord() {
  if (!vocabCurrentWord.value || !vocabInput.value.trim()) return
  vocabIsCorrect.value = vocabInput.value.trim().toLowerCase() === vocabCurrentWord.value.word.toLowerCase()
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

function resetVocab() {
  vocabActive.value = false
}

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
.page-header .title {
  font-size: 40rpx;
  font-weight: 700;
  color: white;
  display: block;
}

.feature-tabs {
  display: flex;
  gap: 24rpx;
  padding: 24rpx 32rpx;
}
.feature-tab {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
  padding: 32rpx 24rpx;
  background: var(--surface-container);
  border-radius: 24rpx;
  position: relative;
}
.feature-tab.active {
  background: var(--primary);
  color: white;
}
.feature-icon { font-size: 48rpx; }
.feature-name { font-size: 26rpx; font-weight: 500; }
.feature-badge {
  position: absolute;
  top: 16rpx;
  right: 16rpx;
  background: var(--error);
  color: white;
  font-size: 22rpx;
  padding: 4rpx 12rpx;
  border-radius: 20rpx;
}

.stats-row {
  display: flex;
  gap: 20rpx;
  padding: 0 32rpx 24rpx;
}
.stat-card {
  flex: 1;
  text-align: center;
  padding: 28rpx 16rpx;
  background: var(--surface-container);
  border-radius: 24rpx;
}
.stat-num { font-size: 48rpx; font-weight: 800; display: block; }
.stat-success { color: var(--success); }
.stat-warning { color: var(--warning); }
.stat-error { color: var(--error); }
.stat-label { font-size: 24rpx; color: var(--on-surface-variant); display: block; margin-top: 4rpx; }

.section { padding: 0 32rpx; margin-bottom: 32rpx; }
.section-title { font-size: 30rpx; font-weight: 700; margin-bottom: 20rpx; display: block; }
.empty-text { font-size: 30rpx; display: block; }

.task-list { display: flex; flex-direction: column; gap: 16rpx; }
.task-item { display: flex; align-items: center; gap: 24rpx; }
.task-avatar {
  width: 88rpx; height: 88rpx; border-radius: 24rpx;
  display: flex; align-items: center; justify-content: center;
}
.task-stage { color: white; font-weight: 700; font-size: 28rpx; }
.task-info { flex: 1; }
.task-title { font-weight: 600; font-size: 30rpx; display: block; }
.task-meta { font-size: 26rpx; color: var(--on-surface-variant); margin-top: 4rpx; display: block; }

.content-list { display: flex; flex-direction: column; gap: 12rpx; }
.content-item { display: flex; align-items: center; gap: 24rpx; }
.content-left { flex: 1; }
.content-title { font-weight: 600; font-size: 30rpx; display: block; }
.content-meta { font-size: 26rpx; color: var(--on-surface-variant); margin-top: 4rpx; display: block; }
.content-actions { flex-shrink: 0; }

/* 默写弹窗 */
.modal-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.4); z-index: 999;
  display: flex; align-items: flex-end;
}
.dictation-sheet {
  width: 100%; max-height: 90vh;
  background: white; border-radius: 32rpx 32rpx 0 0;
  overflow-y: scroll;
  padding-bottom: env(safe-area-inset-bottom, 32rpx);
}
.sheet-top {
  display: flex; justify-content: space-between; align-items: center;
  padding: 32rpx 32rpx 0;
}
.close-btn {
  width: 64rpx; height: 64rpx;
  background: var(--surface-container); border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 32rpx;
}
.hint-label { font-size: 24rpx; color: var(--on-surface-variant); margin-bottom: 12rpx; display: block; }
.hint-text { font-size: 30rpx; line-height: 1.6; display: block; }
.original-text { font-size: 30rpx; line-height: 1.8; display: block; }
.dictation-textarea {
  width: 100%; height: 320rpx;
  border: 3rpx solid var(--outline); border-radius: 16rpx;
  padding: 24rpx; font-size: 30rpx; line-height: 1.6;
}
.result-card { border-left: 8rpx solid var(--primary); }
.score-area { display: flex; align-items: center; gap: 32rpx; }
.score { font-size: 96rpx; font-weight: 800; }
.score-green { color: var(--success); }
.score-orange { color: var(--warning); }
.score-red { color: var(--error); }
.score-meta { font-size: 28rpx; line-height: 1.6; }
.feedback-section { margin-top: 32rpx; padding-top: 24rpx; border-top: 2rpx solid var(--surface-container-high); }
.feedback-label { font-size: 28rpx; color: var(--on-surface-variant); margin-bottom: 16rpx; display: block; }
.feedback-text { font-size: 28rpx; line-height: 1.6; display: block; }

/* 词汇默写 */
.vocab-info-row { display: flex; justify-content: space-between; padding: 16rpx 0; }
.vocab-info-val { font-weight: 600; }
.vocab-progress { height: 12rpx; background: var(--surface-container); border-radius: 6rpx; margin: 32rpx 32rpx 0; overflow: hidden; }
.vocab-progress-bar { height: 100%; background: var(--primary); border-radius: 6rpx; transition: width 0.3s; }
.vocab-progress-text { text-align: center; font-size: 26rpx; color: var(--on-surface-variant); margin-top: 16rpx; display: block; }
.vocab-hint-card { margin: 32rpx; text-align: center; }
.vocab-hint-label { font-size: 24rpx; color: var(--on-surface-variant); margin-bottom: 16rpx; display: block; }
.vocab-hint-meaning { font-size: 44rpx; font-weight: 600; display: block; }
.vocab-input {
  width: 100%; border: 3rpx solid var(--outline); border-radius: 16rpx;
  padding: 28rpx; font-size: 36rpx; text-align: center;
}
.vocab-actions { padding: 24rpx 32rpx; display: flex; flex-direction: column; gap: 20rpx; }
.vocab-result-card { margin: 0 32rpx 32rpx; text-align: center; padding: 32rpx; }
.vocab-result-status { font-size: 36rpx; font-weight: 700; display: block; margin-bottom: 16rpx; }
.vocab-result-status.correct { color: var(--success); }
.vocab-result-status.wrong { color: var(--error); }
.vocab-result-answer { font-size: 30rpx; display: block; }
.vocab-done-card { margin: 0 32rpx 32rpx; text-align: center; padding: 40rpx; }
.vocab-done-title { font-size: 40rpx; font-weight: 700; margin-bottom: 32rpx; display: block; }
.vocab-done-stats { display: flex; justify-content: center; gap: 48rpx; margin-bottom: 32rpx; }
.vocab-stat { display: flex; flex-direction: column; align-items: center; gap: 8rpx; }
.vocab-stat-num { font-size: 56rpx; font-weight: 800; }
.vocab-stat-label { font-size: 24rpx; color: var(--on-surface-variant); }
</style>