<template>
  <view class="page-container">
    <!-- 顶栏统一青绿 -->
    <view class="nav-bar-themed">
      <view class="nav-back" @tap="navBackSafe"><text class="nav-back-icon">‹</text></view>
      <text class="nav-bar-title">默写详情</text>
      <view class="nav-placeholder"></view>
    </view>

    <view v-if="loading" class="loading">
      <view class="spinner"></view>
    </view>

    <view v-else-if="detail" class="detail-wrap">
      <!-- 分数卡：统一青绿色 -->
      <view class="score-card">
        <view class="score-row">
          <text class="score-num">{{ detail.accuracy_rate.toFixed(0) }}</text>
          <view class="score-meta">
            <text class="score-label">准确率</text>
            <text class="score-sub">{{ formatDate(detail.created_at) }}</text>
          </view>
        </view>
        <text v-if="detail.content_title" class="score-title">{{ detail.content_title }}</text>
      </view>

      <!-- AI 总评 -->
      <view v-if="detail.ai_feedback?.summary" class="detail-card">
        <text class="section-label">AI 总评</text>
        <text class="feedback-text">{{ detail.ai_feedback.summary }}</text>
      </view>

      <!-- 错误明细：去彩色，用深灰 + 青色区分 -->
      <view v-if="detail.ai_feedback?.diffs?.length" class="detail-card">
        <text class="section-label">错误明细</text>
        <view v-for="(d, i) in detail.ai_feedback.diffs" :key="i" class="diff-item">
          <text class="diff-type">{{ { missing: '漏写', wrong: '写错', extra: '多写' }[d.type] || d.type }}</text>
          <view class="diff-detail">
            <text v-if="d.expected" class="diff-expected">{{ d.expected }}</text>
            <text v-if="d.actual && d.type !== 'missing'" class="diff-actual">{{ d.actual }}</text>
            <text v-if="d.sentence" class="diff-sentence">{{ d.sentence }}</text>
            <text v-if="d.reason" class="diff-reason">{{ d.reason }}</text>
          </view>
        </view>
      </view>

      <!-- 错词本 -->
      <view v-if="detail.error_words && detail.error_words.length" class="detail-card">
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
      <view v-if="detail.ai_feedback?.suggestions?.length" class="detail-card">
        <text class="section-label">学习建议</text>
        <view v-for="(s, i) in detail.ai_feedback.suggestions" :key="i" class="suggestion-item">
          <text class="suggestion-text">• {{ s }}</text>
        </view>
      </view>

      <!-- 原文与默写对比 -->
      <view class="detail-card">
        <text class="section-label">原文与默写对比</text>
        <view class="compare-container">
          <view class="compare-row">
            <text class="compare-label">原文</text>
            <text class="compare-text original-text">{{ detail.original_text }}</text>
          </view>
          <view class="compare-divider"></view>
          <view class="compare-row">
            <text class="compare-label">我的默写</text>
            <text class="compare-text user-text">{{ detail.user_input }}</text>
          </view>
        </view>
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

function formatDate(dateStr: string) {
  const d = new Date(dateStr)
  return `${d.getFullYear()}/${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
</script>

<style scoped>
/* ---- 顶栏统一青绿 ---- */
.nav-bar-themed {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  padding: calc(env(safe-area-inset-top, 44px) + 16rpx) 32rpx 24rpx;
  background: var(--primary, #5B9AA8);
}
.nav-back {
  width: 48rpx;
  height: 48rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}
.nav-back-icon { font-size: 40rpx; color: #fff; font-weight: 300; }
.nav-bar-title { font-size: 36rpx; font-weight: 600; color: #fff; letter-spacing: 0.5rpx; }
.nav-placeholder { width: 48rpx; }

/* ---- 内容区 ---- */
.detail-wrap { padding: 24rpx 24rpx 48rpx; display: flex; flex-direction: column; gap: 24rpx; }

/* ---- 通用卡片 ---- */
.detail-card {
  background: #ffffff;
  box-shadow: 0 2rpx 12rpx rgba(91, 154, 168, 0.10);
  border-radius: 20rpx;
  padding: 28rpx;
}

/* ---- 分数卡 ---- */
.score-card {
  background: #ffffff;
  box-shadow: 0 2rpx 12rpx rgba(91, 154, 168, 0.10);
  border-radius: 20rpx;
  padding: 32rpx 28rpx;
}
.score-row { display: flex; align-items: center; gap: 24rpx; }
.score-num { font-size: 72rpx; font-weight: 800; color: var(--primary); }
.score-meta { display: flex; flex-direction: column; gap: 4rpx; }
.score-label { font-size: 26rpx; color: var(--on-surface-variant); }
.score-sub { font-size: 22rpx; color: #b0b8c0; }
.score-title { font-size: 26rpx; color: var(--on-surface-variant); margin-top: 16rpx; display: block; }

/* ---- 标签 ---- */
.section-label { font-size: 24rpx; color: var(--on-surface-variant); margin-bottom: 16rpx; display: block; font-weight: 600; }
.feedback-text { font-size: 28rpx; line-height: 1.7; display: block; color: var(--on-surface); }

/* ---- 错误明细：统一灰 + 青色 ---- */
.diff-item {
  display: flex;
  gap: 16rpx;
  margin-bottom: 16rpx;
  padding: 20rpx;
  background: #fff;
  border-radius: 12rpx;
  border: 1rpx solid #eef4f6;
}
.diff-type {
  font-size: 22rpx;
  font-weight: 600;
  padding: 4rpx 14rpx;
  border-radius: 12rpx;
  flex-shrink: 0;
  background: #eef4f6;
  color: #5a6a72;
}
.diff-detail { flex: 1; display: flex; flex-direction: column; gap: 6rpx; }
.diff-expected { font-size: 26rpx; color: var(--primary); font-weight: 600; }
.diff-actual { font-size: 26rpx; color: #888; text-decoration: line-through; }
.diff-sentence { font-size: 24rpx; color: var(--on-surface-variant); margin-top: 6rpx; font-style: italic; }
.diff-reason { font-size: 24rpx; color: var(--on-surface-variant); margin-top: 6rpx; }

/* ---- 错词本 ---- */
.error-words-row { display: flex; flex-wrap: wrap; gap: 16rpx; }
.error-word-chip {
  display: flex; align-items: center; gap: 8rpx;
  padding: 12rpx 20rpx; border-radius: 24rpx;
  background: #fff; border: 1rpx solid #e4eff2;
}
.error-word-chip.word-favorited {
  background: rgba(91,154,168,0.08); border-color: var(--primary);
}
.error-word-text { font-size: 26rpx; color: var(--on-surface); }
.error-word-star { font-size: 28rpx; color: var(--primary); }

/* ---- 建议 ---- */
.suggestion-item { margin-bottom: 8rpx; }
.suggestion-text { font-size: 26rpx; color: var(--on-surface); line-height: 1.6; }

/* ---- 对比视图 ---- */
.compare-container { display: flex; flex-direction: column; gap: 16rpx; }
.compare-row { display: flex; flex-direction: column; gap: 8rpx; }
.compare-label { font-size: 22rpx; color: var(--on-surface-variant); font-weight: 600; }
.compare-text { font-size: 28rpx; line-height: 1.8; display: block; white-space: pre-wrap; padding: 16rpx; border-radius: 12rpx; }
.original-text { background: #fff; }
.user-text { color: var(--on-surface); }
.compare-divider { height: 1rpx; background: #e4eff2; }
</style>
