<template>
  <view class="page-container notes-page">
    <!-- 顶部通栏：主题青绿色块 + 白色标题，与图书馆一致 -->
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
            <text
              class="vocab-action"
              :class="{ disabled: todayWordCount === 0 }"
              @tap="goVocabReview"
            >开始背词</text>
          </view>
        </view>
      </view>

      <!-- 细线分割 -->
      <view class="notes-divider"></view>

      <!-- ② 默写存档区（按文章分组折叠） -->
      <view class="notes-section">
        <view class="notes-section-inner">
          <text class="notes-section-title">默写存档</text>
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
          <view v-else class="history-list">
            <view
              v-for="group in groupedHistory"
              :key="group.title"
              class="history-group"
            >
              <view class="history-group-header" @tap="toggleGroup(group.title)">
                <text class="history-group-title">{{ group.title }}</text>
                <text class="history-group-meta">{{ group.items.length }} 次 · 最高 {{ group.bestAccuracy }}%</text>
                <text class="history-group-toggle">{{ expandedGroups.has(group.title) ? '▲' : '▼' }}</text>
              </view>
              <view v-if="expandedGroups.has(group.title)" class="history-group-list">
                <view
                  v-for="rec in group.items"
                  :key="rec.dictation_id"
                  class="history-card"
                  @tap="goDictationDetail(rec.dictation_id)"
                >
                  <text class="history-meta">{{ formatDate(rec.created_at) }}</text>
                  <text class="history-accuracy">{{ rec.accuracy_rate.toFixed(0) }}%</text>
                  <text class="history-view">查看 ›</text>
                </view>
              </view>
            </view>
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
 * 笔记页：复盘专区，两大分区上下排布
 *   ① 今日背词：显示待复习词量 → 跳复习页
 *   ② 默写存档：按文章分组折叠 → 跳默写详情
 *
 * Why 数量取"待复习"而不是"收藏总数"：
 *   收藏总数会一直涨，用户看不出"今日要背几个"。用 wordReviewApi.getDue 拿
 *   艾宾浩斯当天到期的量，才是真正的"今日生词"。空数组降级为收藏总数，避免
 *   接口出错时用户看到"0"以为没词可背。
 */

const auth = useAuthStore()
const loading = ref(true)
const historyError = ref(false)
const historyList = ref<DictationHistory[]>([])
const todayWordCount = ref(0)
const expandedGroups = ref<Set<string>>(new Set())

// 按文章标题分组，同一篇文章多次默写折叠在一起
interface HistoryGroup {
  title: string
  bestAccuracy: number
  items: DictationHistory[]
}
const groupedHistory = computed<HistoryGroup[]>(() => {
  const map = new Map<string, DictationHistory[]>()
  for (const rec of historyList.value) {
    const title = rec.content_title || '默写练习'
    if (!map.has(title)) map.set(title, [])
    map.get(title)!.push(rec)
  }
  const groups: HistoryGroup[] = []
  for (const [title, items] of map) {
    const bestAccuracy = Math.max(...items.map(i => i.accuracy_rate))
    groups.push({ title, bestAccuracy: Math.round(bestAccuracy), items })
  }
  return groups
})

function toggleGroup(title: string) {
  if (expandedGroups.value.has(title)) {
    expandedGroups.value.delete(title)
  } else {
    expandedGroups.value.add(title)
  }
  // 触发响应式更新
  expandedGroups.value = new Set(expandedGroups.value)
}

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
    // 默认展开第一组
    if (groupedHistory.value.length > 0) {
      expandedGroups.value = new Set([groupedHistory.value[0].title])
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
  // review 页支持 ?tab=vocab 直接落地到"背单词"分区
  navTo('/pages/review/index?tab=vocab')
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
.notes-section {
  padding: 24rpx 0;
}
.notes-section-inner {
  padding: 0 8rpx;
}
.notes-section-title {
  display: block;
  font-size: 28rpx;
  font-weight: 700;
  color: var(--on-surface);
  margin-bottom: 20rpx;
  letter-spacing: 0.5rpx;
}

/* 分割线 */
.notes-divider {
  height: 1rpx;
  background: #e4eff2;
  margin: 0 8rpx;
}

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
/* 背词按钮：细青描边 */
.vocab-action {
  flex-shrink: 0;
  padding: 16rpx 32rpx;
  border: 2rpx solid var(--primary);
  border-radius: 40rpx;
  font-size: 26rpx;
  font-weight: 600;
  color: var(--primary);
  background: transparent;
}
.vocab-action.disabled {
  border-color: #d0d8dc;
  color: #b0b8c0;
  pointer-events: none;
}

/* ② 默写存档 - 分组折叠 */
.history-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}
.history-group {
  background: #f6fbfc;
  border: 1rpx solid #e4eff2;
  border-radius: 20rpx;
  overflow: hidden;
}
.history-group-header {
  display: flex;
  align-items: center;
  padding: 24rpx 28rpx;
  gap: 12rpx;
}
.history-group-title {
  flex: 1;
  font-size: 28rpx;
  font-weight: 700;
  color: var(--on-surface);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.history-group-meta {
  font-size: 22rpx;
  color: var(--on-surface-variant);
  flex-shrink: 0;
}
.history-group-toggle {
  font-size: 20rpx;
  color: #b0b8c0;
  flex-shrink: 0;
}
.history-group-list {
  border-top: 1rpx solid #e4eff2;
}
.history-card {
  display: flex;
  align-items: center;
  padding: 20rpx 28rpx;
  gap: 16rpx;
}
.history-card + .history-card {
  border-top: 1rpx solid #eef4f6;
}
.history-meta {
  font-size: 24rpx;
  color: var(--on-surface-variant);
  flex: 1;
}
.history-accuracy {
  font-size: 28rpx;
  font-weight: 700;
  color: var(--primary);
}
.history-view {
  font-size: 24rpx;
  color: var(--primary);
  font-weight: 600;
}
</style>
