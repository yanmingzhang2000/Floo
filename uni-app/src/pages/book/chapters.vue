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
      <!-- 使用说明 -->
      <view class="tip-card">
        <text class="tip-icon">💡</text>
        <text class="tip-text">点击章节进入阅读页。阅读时可对每段单独默写，也可查看整章译文。</text>
      </view>

      <view v-if="chapters.length === 0" class="empty-state">
        <text class="icon">📋</text>
        <text class="empty-text">暂无章节数据</text>
      </view>

      <view v-else class="chapter-list">
        <view
          v-for="c in chapters"
          :key="c.chapter_id"
          class="chapter-row"
          @tap="goDetail(c)"
        >
          <view class="chapter-index">
            <text>{{ c.order_no === 0 ? '序' : c.order_no }}</text>
          </view>
          <view class="chapter-info">
            <text class="chapter-title">{{ c.title }}</text>
            <text class="chapter-meta">{{ c.word_count }} 词 · {{ c.segment_count }} 段</text>
          </view>
          <text class="chapter-arrow">›</text>
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

const auth = useAuthStore()
const loading = ref(true)
const seriesId = ref(0)
const seriesName = ref('')
const chapters = ref<Chapter[]>([])

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
    const detail = e?.data?.detail || '加载失败'
    uni.showToast({ title: detail, icon: 'none' })
    chapters.value = []
  } finally {
    loading.value = false
  }
}

function goDetail(c: Chapter) {
  // 整章 content_id 走现有 detail 页；detail 页会自动识别为书籍章节
  navTo(`/pages/detail/index?id=${c.content_id}`)
}
</script>

<style scoped>
.tip-card {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 20rpx 24rpx;
  margin-bottom: 24rpx;
  background: #F0F9FF;
  border-radius: 16rpx;
  border-left: 6rpx solid var(--primary);
}
.tip-icon { font-size: 32rpx; }
.tip-text {
  flex: 1;
  font-size: 24rpx;
  color: var(--on-surface-variant);
  line-height: 1.5;
}

.chapter-list {
  padding-bottom: 32rpx;
}

.chapter-row {
  display: flex;
  align-items: center;
  padding: 28rpx 24rpx;
  gap: 20rpx;
  background: #fff;
  border-radius: 16rpx;
  margin-bottom: 12rpx;
  box-shadow: var(--shadow-sm);
}
.chapter-row:active { opacity: 0.85; }

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
