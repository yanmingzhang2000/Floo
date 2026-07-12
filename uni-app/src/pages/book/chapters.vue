<template>
  <view class="page-container">
    <view class="nav-bar">
      <view class="nav-left">
        <view class="nav-back" @tap="navBackSafe"><text>‹</text></view>
      </view>
      <text class="nav-title">{{ seriesName || '章节目录' }}</text>
      <view class="nav-right"></view>
    </view>

    <view v-if="loading" class="loading">
      <view class="spinner"></view>
    </view>

    <template v-else>
      <!-- 阅读模式切换：整章 vs 分段 -->
      <view class="mode-tabs">
        <view
          class="mode-tab"
          :class="{ active: mode === 'whole' }"
          @tap="switchMode('whole')"
        >
          <text class="mode-tab-title">📖 整章模式</text>
          <text class="mode-tab-hint">完整章节，一次读完</text>
        </view>
        <view
          class="mode-tab"
          :class="{ active: mode === 'segmented' }"
          @tap="switchMode('segmented')"
        >
          <text class="mode-tab-title">📑 分段模式</text>
          <text class="mode-tab-hint">每段约 400 词</text>
        </view>
      </view>

      <view v-if="chapters.length === 0" class="empty-state">
        <text class="icon">📋</text>
        <text class="empty-text">暂无章节数据</text>
      </view>

      <view v-else class="chapter-list">
        <view
          v-for="c in chapters"
          :key="c.chapter_id"
          class="chapter-item"
        >
          <!-- 章节主行 -->
          <view class="chapter-row" @tap="onChapterTap(c)">
            <view class="chapter-index">
              <text>{{ c.order_no === 0 ? '序' : c.order_no }}</text>
            </view>
            <view class="chapter-info">
              <text class="chapter-title">{{ c.title }}</text>
              <text class="chapter-meta">
                {{ c.word_count }} 词
                <text v-if="mode === 'segmented' && c.segment_count > 0"> · {{ c.segment_count }} 段</text>
              </text>
            </view>
            <text class="chapter-arrow">›</text>
          </view>

          <!-- 分段模式：展开显示各段 -->
          <view
            v-if="mode === 'segmented' && expandedChapterId === c.chapter_id && loadedSegments[c.chapter_id]"
            class="segment-list"
          >
            <view
              v-for="(seg, idx) in loadedSegments[c.chapter_id]"
              :key="seg.segment_id"
              class="segment-item"
              @tap="goDetail(seg.content_id)"
            >
              <text class="segment-index">段 {{ idx + 1 }}</text>
              <text class="segment-meta">{{ seg.word_count }} 词</text>
              <text class="segment-arrow">›</text>
            </view>
          </view>
        </view>
      </view>
    </template>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { bookApi } from '@/api'
import { useAuthStore } from '@/stores'
import { navTo, navBackSafe } from '@/utils/router'

interface Chapter {
  chapter_id: number
  order_no: number
  title: string
  content_id: number
  word_count: number
  segment_count: number
}

interface Segment {
  segment_id: number
  order_no: number
  content_id: number
  word_count: number
}

const auth = useAuthStore()
const loading = ref(true)
const seriesId = ref(0)
const seriesName = ref('')
const chapters = ref<Chapter[]>([])
const mode = ref<'whole' | 'segmented'>('whole')
// 分段模式下当前展开的章节 chapter_id，一次只展开一个避免视觉混乱
const expandedChapterId = ref<number | null>(null)
// 已加载的分段缓存：{chapter_id: Segment[]}
const loadedSegments = ref<Record<number, Segment[]>>({})

onLoad((query) => {
  seriesId.value = Number(query?.series_id || 0)
  seriesName.value = decodeURIComponent((query?.name as string) || '')
  if (seriesId.value > 0) {
    loadChapters()
  } else {
    loading.value = false
  }
})

async function loadChapters() {
  loading.value = true
  try {
    const { data } = await bookApi.getChapters(seriesId.value, auth.currentUserId)
    chapters.value = data?.chapters || []
    if (!seriesName.value) {
      seriesName.value = data?.series_name || '章节目录'
    }
  } catch (e: any) {
    // 无权限 / 网络异常：给个 toast 让用户知道
    const detail = e?.data?.detail || '加载失败'
    uni.showToast({ title: detail, icon: 'none' })
    chapters.value = []
  } finally {
    loading.value = false
  }
}

function switchMode(m: 'whole' | 'segmented') {
  if (mode.value === m) return
  mode.value = m
  // 切换模式时收起所有展开项
  expandedChapterId.value = null
}

async function onChapterTap(c: Chapter) {
  if (mode.value === 'whole') {
    // 整章模式：直接进 detail 页
    goDetail(c.content_id)
    return
  }
  // 分段模式：切换展开/收起
  if (expandedChapterId.value === c.chapter_id) {
    expandedChapterId.value = null
    return
  }
  expandedChapterId.value = c.chapter_id
  // 首次展开该章节时懒加载分段列表
  if (!loadedSegments.value[c.chapter_id]) {
    try {
      const { data } = await bookApi.getSegments(c.chapter_id, auth.currentUserId)
      loadedSegments.value[c.chapter_id] = data?.segments || []
    } catch (e) {
      loadedSegments.value[c.chapter_id] = []
      uni.showToast({ title: '加载分段失败', icon: 'none' })
    }
  }
}

function goDetail(contentId: number) {
  // 复用现有的 detail 页，词典/朗读/默写全部自动继承
  navTo(`/pages/detail/index?id=${contentId}`)
}
</script>

<style scoped>
.mode-tabs {
  display: flex;
  gap: 16rpx;
  padding: 16rpx 0 24rpx;
}

.mode-tab {
  flex: 1;
  background: #fff;
  border-radius: 16rpx;
  padding: 20rpx 16rpx;
  border: 2rpx solid var(--outline-variant);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6rpx;
  transition: all 0.2s;
}

.mode-tab.active {
  border-color: var(--primary);
  background: #f0f9ff;
}

.mode-tab-title {
  font-size: 28rpx;
  font-weight: 700;
  color: var(--on-surface);
}

.mode-tab.active .mode-tab-title {
  color: var(--primary);
}

.mode-tab-hint {
  font-size: 22rpx;
  color: var(--on-surface-variant);
}

.chapter-list {
  padding-bottom: 32rpx;
}

.chapter-item {
  background: #fff;
  border-radius: 16rpx;
  margin-bottom: 12rpx;
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

.chapter-row {
  display: flex;
  align-items: center;
  padding: 24rpx;
  gap: 20rpx;
}

.chapter-row:active {
  opacity: 0.85;
}

.chapter-index {
  width: 60rpx;
  height: 60rpx;
  border-radius: 50%;
  background: var(--primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24rpx;
  font-weight: 700;
  flex-shrink: 0;
}

.chapter-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}

.chapter-title {
  font-size: 30rpx;
  font-weight: 600;
  color: var(--on-surface);
  line-height: 1.3;
}

.chapter-meta {
  font-size: 22rpx;
  color: var(--on-surface-variant);
}

.chapter-arrow {
  font-size: 40rpx;
  color: var(--on-surface-muted);
}

.segment-list {
  border-top: 2rpx solid var(--outline-variant);
  background: #fafcfd;
}

.segment-item {
  display: flex;
  align-items: center;
  padding: 20rpx 24rpx 20rpx 100rpx;
  gap: 16rpx;
  border-bottom: 2rpx solid var(--outline-variant);
}

.segment-item:last-child {
  border-bottom: none;
}

.segment-item:active {
  opacity: 0.85;
}

.segment-index {
  flex: 1;
  font-size: 26rpx;
  color: var(--on-surface);
  font-weight: 500;
}

.segment-meta {
  font-size: 22rpx;
  color: var(--on-surface-variant);
}

.segment-arrow {
  font-size: 32rpx;
  color: var(--on-surface-muted);
}

.empty-state {
  padding: 120rpx 0;
  text-align: center;
}

.empty-state .icon {
  font-size: 80rpx;
  display: block;
  margin-bottom: 20rpx;
}

.empty-text {
  font-size: 30rpx;
  color: var(--on-surface-variant);
  display: block;
}
</style>
