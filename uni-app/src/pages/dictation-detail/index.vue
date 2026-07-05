<template>
  <view class="page-container">
    <view class="nav-bar">
      <view class="nav-left">
        <view class="nav-back" @tap="navBackSafe"><text>‹</text></view>
      </view>
      <text class="nav-title">默写详情</text>
      <view class="nav-right"></view>
    </view>

    <view v-if="loading" class="loading">
      <view class="spinner"></view>
    </view>

    <view v-else-if="detail" class="detail-wrap">
      <!-- 分数卡 -->
      <view class="card score-card">
        <view class="score-row">
          <text class="score-num" :class="getScoreClass(detail.accuracy_rate)">{{ detail.accuracy_rate.toFixed(0) }}</text>
          <view class="score-meta">
            <text class="score-label">准确率</text>
            <text class="score-points">+{{ detail.earned_points }} 积分</text>
          </view>
        </view>
        <text class="score-date">{{ formatDate(detail.created_at) }}{{ detail.content_title ? ' · ' + detail.content_title : '' }}</text>
      </view>

      <!-- AI 总评 -->
      <view v-if="detail.ai_feedback?.summary" class="card">
        <text class="section-label">AI 总评</text>
        <text class="feedback-text">{{ detail.ai_feedback.summary }}</text>
      </view>

      <!-- 错误明细 -->
      <view v-if="detail.ai_feedback?.diffs?.length" class="card">
        <text class="section-label">错误明细</text>
        <view v-for="(d, i) in detail.ai_feedback.diffs" :key="i" class="diff-item">
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
      <view v-if="detail.error_words && detail.error_words.length" class="card">
        <text class="section-label">错词本（点击收藏到单词本）</text>
        <view class="error-words-row">
          <view
            v-for="(w, i) in detail.error_words"
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
      <view v-if="detail.ai_feedback?.suggestions?.length" class="card">
        <text class="section-label">学习建议</text>
        <view v-for="(s, i) in detail.ai_feedback.suggestions" :key="i" class="suggestion-item">
          <text class="suggestion-text">• {{ s }}</text>
        </view>
      </view>

      <!-- 原文 -->
      <view class="card">
        <text class="section-label">原文</text>
        <text class="text-block">{{ detail.original_text }}</text>
      </view>

      <!-- 我的默写 -->
      <view class="card">
        <text class="section-label">我的默写</text>
        <text class="text-block user-text">{{ detail.user_input }}</text>
      </view>
    </view>

    <view v-else class="empty-state">
      <text class="icon">⚠️</text>
      <text class="empty-text">记录不存在</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { dictationApi, favoritesApi } from '@/api'
import { useAuthStore } from '@/stores'
import { navBackSafe } from '@/utils/router'
import type { DictationHistoryDetail } from '@/types'

const auth = useAuthStore()
const loading = ref(true)
const detail = ref<DictationHistoryDetail | null>(null)
const favoritedWords = ref<Set<string>>(new Set())

onLoad((options) => {
  const id = Number(options?.id)
  if (!id) { loading.value = false; return }
  loadDetail(id)
})

async function loadDetail(id: number) {
  loading.value = true
  try {
    const { data } = await dictationApi.getHistoryDetail(id, auth.currentUserId)
    detail.value = data
  } catch {
    detail.value = null
  }
  loading.value = false
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
      await favoritesApi.add(auth.currentUserId, word, undefined, undefined, 'dictation', detail.value?.content_id)
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

function formatDate(dateStr: string) {
  const d = new Date(dateStr)
  return `${d.getFullYear()}/${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
</script>

<style scoped>
.detail-wrap { padding: 0 32rpx 48rpx; }

.score-card { padding: 32rpx; }
.score-row { display: flex; align-items: center; gap: 24rpx; }
.score-num { font-size: 80rpx; font-weight: 800; }
.score-green { color: var(--success); }
.score-orange { color: var(--warning); }
.score-red { color: var(--error); }
.score-meta { display: flex; flex-direction: column; gap: 4rpx; }
.score-label { font-size: 26rpx; color: var(--on-surface-variant); }
.score-points { font-size: 28rpx; color: var(--success); font-weight: 600; }
.score-date { font-size: 24rpx; color: var(--on-surface-variant); margin-top: 16rpx; display: block; }

.section-label { font-size: 24rpx; color: var(--on-surface-variant); margin-bottom: 16rpx; display: block; font-weight: 600; }
.feedback-text { font-size: 28rpx; line-height: 1.7; display: block; }

.diff-item { display: flex; gap: 12rpx; margin-bottom: 12rpx; padding: 16rpx; background: var(--surface-container); border-radius: 12rpx; }
.diff-type { font-size: 22rpx; font-weight: 600; padding: 4rpx 12rpx; border-radius: 12rpx; flex-shrink: 0; }
.diff-missing { background: #FFF3E0; color: #E65100; }
.diff-wrong { background: #FFEBEE; color: #C62828; }
.diff-extra { background: #E3F2FD; color: #1565C0; }
.diff-detail { flex: 1; display: flex; flex-direction: column; gap: 4rpx; }
.diff-expected { font-size: 26rpx; color: var(--success); }
.diff-actual { font-size: 26rpx; color: var(--error); text-decoration: line-through; }
.diff-sentence { font-size: 24rpx; color: var(--on-surface-variant); margin-top: 6rpx; font-style: italic; }
.diff-reason { font-size: 24rpx; color: var(--primary); margin-top: 6rpx; }

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
.suggestion-text { font-size: 26rpx; color: var(--on-surface); line-height: 1.6; }

.text-block { font-size: 28rpx; line-height: 1.8; display: block; white-space: pre-wrap; }
.user-text { color: var(--on-surface); }
</style>
