<template>
  <view class="page-container">
    <view class="nav-bar">
      <view class="nav-left">
        <view class="nav-back" @tap="navBackSafe"><text>‹</text></view>
      </view>
      <text class="nav-title">默写练习</text>
      <view class="nav-right"></view>
    </view>

    <view v-if="loading" class="loading">
      <view class="spinner"></view>
    </view>

    <view v-else class="dictation-page">
      <!-- 中文提示卡片 -->
      <view class="card hint-card">
        <text class="hint-label">中文翻译提示</text>
        <text class="hint-text">{{ content?.translation || '暂无翻译' }}</text>
      </view>

      <!-- 输入区 -->
      <view class="card input-card">
        <textarea
          v-model="userInput"
          :maxlength="-1"
          placeholder="在这里输入默写的英文内容..."
          class="dictation-textarea"
        />
      </view>

      <!-- 提交按钮 -->
      <view class="submit-area">
        <button
          class="btn btn-primary btn-block btn-lg"
          :disabled="submitting || !userInput.trim()"
          @tap="handleSubmit"
        >
          <text>{{ submitting ? 'AI 批改中...' : '提交批改' }}</text>
        </button>
      </view>

      <!-- 批改结果 -->
      <view v-if="result" class="card result-card">
        <!-- 分数行 -->
        <view class="score-area">
          <text class="score-num" :class="getScoreClass(result.feedback.score)">{{ result.feedback.score }}</text>
          <view class="score-meta">
            <text>准确率 {{ result.accuracy_rate.toFixed(0) }}%</text>
            <text style="color: var(--success)">+{{ result.earned_points }} 积分</text>
          </view>
        </view>
        <!-- AI 总评 -->
        <view v-if="result.feedback.summary" class="feedback-section">
          <text class="feedback-label">AI 总评</text>
          <text class="feedback-text">{{ result.feedback.summary }}</text>
        </view>
        <!-- 错误明细 -->
        <view v-if="result.feedback.diffs && result.feedback.diffs.length" class="feedback-section">
          <text class="feedback-label">错误明细</text>
          <view v-for="(d, i) in result.feedback.diffs" :key="i" class="diff-item">
            <text class="diff-type" :class="'diff-' + d.type">{{ { missing: '漏写', wrong: '写错', extra: '多写' }[d.type] || d.type }}</text>
            <view class="diff-detail">
              <text v-if="d.expected" class="diff-expected">✓ {{ d.expected }}</text>
              <text v-if="d.actual && d.type !== 'missing'" class="diff-actual">✗ {{ d.actual }}</text>
              <text v-if="d.sentence" class="diff-sentence">{{ d.sentence }}</text>
              <text v-if="d.reason" class="diff-reason">{{ d.reason }}</text>
            </view>
          </view>
        </view>
        <!-- 错词本 -->
        <view v-if="result.feedback.error_words && result.feedback.error_words.length" class="feedback-section">
          <text class="feedback-label">错词本（点击收藏到单词本）</text>
          <view class="error-words-row">
            <view
              v-for="(w, i) in result.feedback.error_words"
              :key="i"
              class="error-word-chip"
              :class="{ 'word-favorited': favoritedWords.has(w) }"
              @tap="toggleErrorWord(w)"
            >
              <text class="error-word-text">{{ w }}</text>
              <text class="error-word-star">{{ favoritedWords.has(w) ? '★' : '☆' }}</text>
            </view>
          </view>
        </view>
        <!-- 建议 -->
        <view v-if="result.feedback.suggestions && result.feedback.suggestions.length" class="feedback-section">
          <text class="feedback-label">建议</text>
          <view v-for="(s, i) in result.feedback.suggestions" :key="i" class="suggestion-item">
            <text class="suggestion-text">• {{ s }}</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { dailyApi, dictationApi, favoritesApi } from '@/api'
import { useAuthStore } from '@/stores'
import { navBackSafe } from '@/utils/router'
import type { LearningContent, DictationResult } from '@/types'

const auth = useAuthStore()
const loading = ref(true)
const content = ref<LearningContent | null>(null)
const userInput = ref('')
const submitting = ref(false)
const result = ref<DictationResult | null>(null)
const favoritedWords = ref<Set<string>>(new Set())
let contentId = 0

onLoad((query) => {
  contentId = Number(query?.id || 0)
  loadContent()
})

async function loadContent() {
  if (!contentId) { loading.value = false; return }
  loading.value = true
  try {
    const { data } = await dailyApi.getContent(contentId)
    content.value = data
  } catch { content.value = null }
  loading.value = false
}

async function handleSubmit() {
  if (!content.value || !userInput.value.trim()) return
  submitting.value = true
  try {
    const { data } = await dictationApi.submit(auth.currentUserId, contentId, userInput.value)
    result.value = data
  } catch { uni.showToast({ title: '提交失败', icon: 'none' }) }
  submitting.value = false
}

async function toggleErrorWord(word: string) {
  if (favoritedWords.value.has(word)) {
    try {
      await favoritesApi.remove(auth.currentUserId, word)
      favoritedWords.value.delete(word)
      favoritedWords.value = new Set(favoritedWords.value)
      uni.showToast({ title: '已取消收藏', icon: 'none' })
    } catch { uni.showToast({ title: '操作失败', icon: 'none' }) }
  } else {
    try {
      await favoritesApi.add(auth.currentUserId, word, undefined, undefined, 'dictation', contentId)
      favoritedWords.value.add(word)
      favoritedWords.value = new Set(favoritedWords.value)
      uni.showToast({ title: '已收藏到单词本', icon: 'none' })
    } catch { uni.showToast({ title: '收藏失败', icon: 'none' }) }
  }
}

function getScoreClass(score: number) {
  if (score >= 80) return 'score-green'
  if (score >= 60) return 'score-orange'
  return 'score-red'
}

function navBack() { navBackSafe() }
</script>

<style scoped>
.dictation-page { padding: 0 32rpx 48rpx; }

/* 提示卡片 */
.hint-card { padding: 28rpx; background: var(--primary-container); border-radius: 16rpx; }
.hint-label { font-size: 22rpx; color: var(--on-primary-container); margin-bottom: 12rpx; display: block; }
.hint-text { font-size: 28rpx; line-height: 1.6; display: block; color: var(--on-primary-container); }

/* 输入区 */
.input-card { padding: 24rpx; }
.dictation-textarea {
  width: 100%; height: 360rpx;
  border: 3rpx solid var(--outline); border-radius: 16rpx;
  padding: 24rpx; font-size: 28rpx; line-height: 1.6;
}

/* 提交 */
.submit-area { margin-bottom: 24rpx; }

/* 结果 */
.result-card { border-left: 8rpx solid var(--primary); }
.score-area { display: flex; align-items: center; gap: 28rpx; margin-bottom: 24rpx; }
.score-num { font-size: 80rpx; font-weight: 800; }
.score-green { color: var(--success); }
.score-orange { color: var(--warning); }
.score-red { color: var(--error); }
.score-meta { font-size: 26rpx; line-height: 1.6; }

.feedback-section { padding-top: 20rpx; border-top: 2rpx solid var(--surface-container-high); margin-top: 20rpx; }
.feedback-label { font-size: 24rpx; color: var(--on-surface-variant); margin-bottom: 12rpx; display: block; }
.feedback-text { font-size: 26rpx; line-height: 1.6; display: block; }

.diff-item { display: flex; gap: 12rpx; margin-bottom: 12rpx; padding: 12rpx; background: var(--surface-container); border-radius: 8rpx; }
.diff-type { font-size: 22rpx; font-weight: 600; padding: 4rpx 12rpx; border-radius: 12rpx; flex-shrink: 0; }
.diff-missing { background: #FFF3E0; color: #E65100; }
.diff-wrong { background: #FFEBEE; color: #C62828; }
.diff-extra { background: #E3F2FD; color: #1565C0; }
.diff-detail { flex: 1; display: flex; flex-direction: column; gap: 4rpx; }
.diff-expected { font-size: 24rpx; color: var(--success); }
.diff-actual { font-size: 24rpx; color: var(--error); text-decoration: line-through; }
.diff-sentence { font-size: 22rpx; color: var(--on-surface-variant); margin-top: 4rpx; font-style: italic; }
.diff-reason { font-size: 22rpx; color: var(--primary); margin-top: 4rpx; }

.error-words-row { display: flex; flex-wrap: wrap; gap: 16rpx; }
.error-word-chip {
  display: flex; align-items: center; gap: 8rpx;
  padding: 12rpx 20rpx; border-radius: 24rpx;
  background: var(--surface-container); border: 2rpx solid var(--outline-variant);
}
.error-word-chip.word-favorited {
  background: var(--primary-container); border-color: var(--primary);
}
.error-word-text { font-size: 26rpx; }
.error-word-star { font-size: 28rpx; color: var(--warning); }

.suggestion-item { margin-bottom: 8rpx; }
.suggestion-text { font-size: 24rpx; color: var(--on-surface); line-height: 1.6; }
</style>
