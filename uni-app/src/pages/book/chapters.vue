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
      <!-- 继续阅读横幅：上次读过本书才显示 -->
      <view v-if="lastChapter" class="resume-banner" @tap="goDetail(lastChapter)">
        <view class="resume-banner-left">
          <text class="resume-banner-label">继续阅读</text>
          <text class="resume-banner-title">{{ lastChapter.title }}</text>
        </view>
        <text class="resume-banner-arrow">→</text>
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
          :class="{ 'chapter-row-last': c.content_id === lastChapter?.content_id }"
          @tap="goDetail(c)"
        >
          <view class="chapter-index">
            <text>{{ c.order_no === 0 ? '序' : c.order_no }}</text>
          </view>
          <view class="chapter-info">
            <text class="chapter-title">{{ c.title }}</text>
            <text class="chapter-meta">{{ c.word_count }} 词 · {{ c.segment_count }} 段</text>
          </view>
          <text v-if="c.content_id === lastChapter?.content_id" class="chapter-last-tag">上次</text>
          <text v-else class="chapter-arrow">›</text>
        </view>
      </view>
    </template>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { bookApi, dailyApi } from '@/api'
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
// 本书上次阅读的章节，null 表示从未读过
const lastChapter = ref<Chapter | null>(null)

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
    // 并行拉章节列表和已打开记录，减少等待时间
    const [chaptersRes, learnedRes] = await Promise.all([
      bookApi.getChapters(seriesId.value, auth.currentUserId),
      dailyApi.getLearnedIds(auth.currentUserId).catch(() => null),
    ])

    const chapterList: Chapter[] = chaptersRes.data?.chapters || []
    chapters.value = chapterList

    if (!seriesName.value) {
      seriesName.value = chaptersRes.data?.series_name || '章节目录'
    }

    // 找本书上次阅读的章节：
    // opened_ids 已按 opened_at DESC 排序，第一个匹配本书章节的即为上次阅读
    const openedIds: number[] = learnedRes?.data?.opened_ids || []
    const chapterContentIds = new Set(chapterList.map(c => c.content_id))
    const lastOpenedId = openedIds.find(id => chapterContentIds.has(id))
    lastChapter.value = lastOpenedId
      ? chapterList.find(c => c.content_id === lastOpenedId) ?? null
      : null

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
/* 继续阅读横幅 */
.resume-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 28rpx 32rpx;
  margin-bottom: 24rpx;
  background: var(--primary);
  border-radius: 20rpx;
  box-shadow: 0 4rpx 16rpx rgba(91,154,168,0.25);
  transition: transform 0.15s;
}
.resume-banner:active { transform: scale(0.98); }
.resume-banner-left { flex: 1; overflow: hidden; }
.resume-banner-label {
  font-size: 22rpx;
  color: rgba(255,255,255,0.75);
  display: block;
  margin-bottom: 6rpx;
}
.resume-banner-title {
  font-size: 30rpx;
  font-weight: 700;
  color: #fff;
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.resume-banner-arrow {
  font-size: 36rpx;
  color: rgba(255,255,255,0.9);
  margin-left: 20rpx;
  flex-shrink: 0;
}

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

/* 上次阅读的章节行，左侧加主题色边框 */
.chapter-row-last {
  border-left: 6rpx solid var(--primary);
  padding-left: 18rpx;
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

/* 上次标签，替换右侧箭头 */
.chapter-last-tag {
  font-size: 20rpx;
  font-weight: 600;
  color: var(--primary);
  background: var(--primary-container);
  padding: 4rpx 14rpx;
  border-radius: 20rpx;
  flex-shrink: 0;
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
