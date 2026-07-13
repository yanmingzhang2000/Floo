<template>
  <view class="page-container notes-page">
    <!-- 顶部通栏：主题青绿色块 + 白色标题 -->
    <view class="notes-header">
      <text class="notes-title">笔记</text>
    </view>

    <view v-if="loading" class="loading">
      <view class="spinner"></view>
    </view>

    <template v-else>
      <!-- ① 今日背词区 -->
      <view class="notes-section notes-vocab-section">
        <view class="notes-section-inner">
          <view class="vocab-row">
            <view class="vocab-info">
              <text class="vocab-label">今日生词</text>
              <view class="vocab-stat">
                <text class="vocab-num">{{ todayWordCount }}</text>
                <text class="vocab-unit">个</text>
              </view>
              <text class="vocab-hint">
                {{ todayWordCount > 0 ? '按遗忘曲线安排，开始复习' : '暂无待背单词，收藏更多词汇后再来' }}
              </text>
            </view>
            <view class="vocab-actions">
              <text
                class="vocab-action"
                :class="{ disabled: todayWordCount === 0 }"
                @tap="goVocabReview"
              >开始背词</text>
              <text class="vocab-action-secondary" @tap="goDictionary">单词书</text>
            </view>
          </view>
        </view>
      </view>

      <!-- ② 默写存档：摘要卡片 -->
      <view class="notes-section">
        <view class="notes-section-inner">
          <view v-if="historyError" class="empty-state" @tap="loadHistory">
            <text class="icon">⚠️</text>
            <text class="empty-text">加载失败</text>
            <text class="empty-hint">点此重试</text>
          </view>
          <view v-else-if="historyList.length === 0" class="empty-state">
            <text class="icon">📜</text>
            <text class="empty-text">暂无默写记录</text>
            <text class="empty-hint">在文章阅读页点「默写」即可开始</text>
          </view>
          <view v-else class="dictation-summary-card">
            <!-- 统计概览 -->
            <view class="summary-stats">
              <view class="summary-stat">
                <text class="summary-stat-num">{{ historyList.length }}</text>
                <text class="summary-stat-label">总次数</text>
              </view>
              <view class="summary-stat">
                <text class="summary-stat-num">{{ avgAccuracy }}%</text>
                <text class="summary-stat-label">平均准确率</text>
              </view>
            </view>

            <!-- AI 能力分析（来自最近默写的 AI 反馈） -->
            <view v-if="aiInsights.length > 0" class="summary-insights">
              <text class="summary-insights-title">AI 分析</text>
              <text v-for="(tip, i) in aiInsights" :key="i" class="summary-insight-item">{{ tip }}</text>
            </view>

            <!-- 查看详情入口 -->
            <text class="summary-detail-link" @tap="goReviewDictation">查看全部默写记录 ›</text>
          </view>
        </view>
      </view>
    </template>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { dictationApi, wordReviewApi, favoritesApi } from '@/api'
import { useAuthStore } from '@/stores'
import { navTo } from '@/utils/router'
import type { DictationHistory } from '@/types'

/**
 * 笔记页：复盘专区
 *   ① 今日背词：显示待复习词量，提供"开始背词"和"单词书"两个入口
 *   ② 默写存档：摘要卡片展示整体表现（总次数、平均准确率），
 *      AI 分析来自最近默写记录的 ai_feedback.suggestions，
 *      底部"查看全部"跳转复习页默写 tab。
 *
 * Why 用最近默写的 suggestions 而不是前端硬算：
 *   后端在每次默写批改时已经由 AI 生成了针对性的学习建议（如"词汇拼写薄弱"、
 *   "时态使用不稳定"），这些是真正的 AI 分析。前端只需展示即可，无需重复造轮子。
 */

const auth = useAuthStore()
const loading = ref(true)
const historyError = ref(false)
const historyList = ref<DictationHistory[]>([])
const todayWordCount = ref(0)
// 来自最近默写详情的 AI 建议
const aiInsights = ref<string[]>([])

// ---- 默写摘要计算 ----

const avgAccuracy = computed(() => {
  if (historyList.value.length === 0) return 0
  const sum = historyList.value.reduce((acc, r) => acc + r.accuracy_rate, 0)
  return Math.round(sum / historyList.value.length)
})

async function loadData() {
  loading.value = true
  await Promise.all([loadWordCount(), loadHistory()])
  loading.value = false
}

async function loadWordCount() {
  const userId = auth.currentUserId
  try {
    // 优先展示"今日到期"的量，这才是背词入口该显示的数字
    const { data } = await wordReviewApi.getDue(userId, 200)
    if (Array.isArray(data)) {
      todayWordCount.value = data.length
      console.debug('[Notes] 今日待背单词=%d', todayWordCount.value)
      return
    }
    // 后端可能包成 { words: [...] }，兜底两种结构
    if (data && Array.isArray((data as any).words)) {
      todayWordCount.value = (data as any).words.length
      return
    }
    todayWordCount.value = 0
  } catch (e) {
    // 复习接口挂了退化到收藏总数：至少显示一个非零值让用户能进入背词
    console.debug('[Notes] wordReviewApi.getDue 失败，降级到收藏总数 err=%o', e)
    try {
      const { data } = await favoritesApi.list(userId, 200)
      todayWordCount.value = Array.isArray(data) ? data.length : 0
    } catch {
      todayWordCount.value = 0
    }
  }
}

async function loadHistory() {
  const userId = auth.currentUserId
  historyError.value = false
  try {
    const { data } = await dictationApi.getHistory(userId, 200)
    historyList.value = Array.isArray(data) ? data : []
    console.debug('[Notes] 默写历史=%d 条', historyList.value.length)

    // 加载最近一条默写详情，提取 AI 建议作为能力分析
    if (historyList.value.length > 0) {
      const latestId = historyList.value[0].dictation_id
      try {
        const { data: detail } = await dictationApi.getHistoryDetail(latestId, userId)
        if (detail?.ai_feedback?.suggestions?.length) {
          // 最多展示 2 条，避免占太多空间
          aiInsights.value = detail.ai_feedback.suggestions.slice(0, 2)
          console.debug('[Notes] AI 分析建议=%o', aiInsights.value)
        } else {
          console.debug('[Notes] 最近默写无 AI 建议')
          aiInsights.value = []
        }
      } catch {
        console.debug('[Notes] 加载默写详情失败，跳过 AI 分析')
        aiInsights.value = []
      }
    }
  } catch (e) {
    console.debug('[Notes] 默写历史加载失败 err=%o', e)
    historyError.value = true
    historyList.value = []
  }
}

function goVocabReview() {
  if (todayWordCount.value === 0) {
    console.debug('[Notes] 无待背单词，拦截跳转')
    return
  }
  // autostart=1 让复习页数据加载完后自动进入背词练习，跳过中间的开始按钮
  navTo('/pages/review/index?tab=vocab&autostart=1')
}

function goDictionary() {
  navTo('/pages/dictionary/index')
}

function goReviewDictation() {
  navTo('/pages/review/index?tab=dictation')
}

function goDictationDetail(id: number) {
  navTo(`/pages/dictation-detail/index?id=${id}`)
}

// 格式化时间戳：显示 "MM.DD HH:mm" 或 "今天 HH:mm"
function formatDate(ts: string): string {
  if (!ts) return ''
  const d = new Date(ts)
  if (Number.isNaN(d.getTime())) return ts
  const now = new Date()
  const sameDay = d.getFullYear() === now.getFullYear() && d.getMonth() === now.getMonth() && d.getDate() === now.getDate()
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  const hh = String(d.getHours()).padStart(2, '0')
  const mi = String(d.getMinutes()).padStart(2, '0')
  if (sameDay) return `今天 ${hh}:${mi}`
  return `${mm}.${dd} ${hh}:${mi}`
}

onShow(loadData)
</script>

<style scoped>
.notes-page {
  padding-bottom: 40rpx;
}

/* 顶部通栏：主题青绿色 + 白色标题 */
.notes-header {
  padding: calc(env(safe-area-inset-top, 44px) + 16rpx) 32rpx 24rpx;
  background: var(--primary, #5B9AA8);
  margin: 0 -20rpx 0;
}
.notes-title {
  font-size: 36rpx;
  font-weight: 600;
  color: #fff;
  letter-spacing: 0.5rpx;
}

/* 分区容器 */
.notes-section { padding: 24rpx 0; }
.notes-section-inner { padding: 0 8rpx; }

/* ① 今日背词 */
.notes-vocab-section {
  padding-top: 32rpx;
  padding-bottom: 32rpx;
}
.vocab-row {
  display: flex;
  align-items: center;
  gap: 24rpx;
  padding: 32rpx 28rpx;
  background: #f6fbfc;
  border-radius: 24rpx;
  border: 1rpx solid #e4eff2;
  min-height: 200rpx;
  box-sizing: border-box;
}
.vocab-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}
.vocab-label {
  font-size: 24rpx;
  color: var(--on-surface-variant);
  letter-spacing: 1rpx;
}
.vocab-stat {
  display: flex;
  align-items: baseline;
  gap: 8rpx;
  margin-top: 4rpx;
}
.vocab-num {
  font-size: 56rpx;
  font-weight: 800;
  color: var(--primary);
  line-height: 1;
}
.vocab-unit {
  font-size: 26rpx;
  color: var(--on-surface-variant);
  font-weight: 500;
}
.vocab-hint {
  font-size: 22rpx;
  color: var(--on-surface-muted);
  margin-top: 8rpx;
}

/* 两个按钮竖排 */
.vocab-actions {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
  align-items: stretch;
  width: 180rpx;
}
.vocab-action {
  padding: 14rpx 0;
  border: 2rpx solid var(--primary);
  border-radius: 40rpx;
  font-size: 26rpx;
  font-weight: 600;
  color: var(--primary);
  white-space: nowrap;
  text-align: center;
  width: 100%;
  box-sizing: border-box;
}
.vocab-action.disabled {
  border-color: #d0d8dc;
  color: #b0b8c0;
  pointer-events: none;
}
.vocab-action-secondary {
  padding: 14rpx 0;
  border: 2rpx solid #c8e0e6;
  border-radius: 40rpx;
  font-size: 26rpx;
  font-weight: 500;
  color: var(--on-surface-variant);
  white-space: nowrap;
  text-align: center;
  width: 100%;
  box-sizing: border-box;
}

/* ② 默写存档摘要卡片 */
.dictation-summary-card {
  background: #f6fbfc;
  border: 1rpx solid #e4eff2;
  border-radius: 24rpx;
  padding: 32rpx 28rpx;
  display: flex;
  flex-direction: column;
  gap: 24rpx;
  min-height: 200rpx;
  box-sizing: border-box;
}

.summary-stats {
  display: flex;
  gap: 0;
}
.summary-stat {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6rpx;
}
.summary-stat + .summary-stat {
  border-left: 1rpx solid #e4eff2;
}
.summary-stat-num {
  font-size: 44rpx;
  font-weight: 800;
  color: var(--primary);
  line-height: 1;
}
.summary-stat-label {
  font-size: 22rpx;
  color: var(--on-surface-variant);
}

/* AI 分析区 */
.summary-insights {
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}
.summary-insights-title {
  font-size: 22rpx;
  color: var(--on-surface-variant);
  font-weight: 600;
  margin-bottom: 4rpx;
}
.summary-insight-item {
  font-size: 26rpx;
  color: var(--on-surface);
  line-height: 1.5;
  padding-left: 16rpx;
  border-left: 3rpx solid var(--primary);
}

.summary-detail-link {
  display: block;
  text-align: right;
  font-size: 26rpx;
  font-weight: 600;
  color: var(--primary);
  padding-top: 8rpx;
  border-top: 1rpx solid #eef4f6;
}
</style>
