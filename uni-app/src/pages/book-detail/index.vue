<template>
  <view class="page-container">
    <view class="nav-bar">
      <view class="nav-left" @tap="navBackSafe">
        <text class="nav-back-icon">‹</text>
      </view>
      <text class="nav-title">书本详情</text>
      <view class="nav-right"></view>
    </view>

    <view v-if="loading" class="loading">
      <view class="spinner"></view>
    </view>

    <template v-else>
      <!-- 书籍信息 -->
      <view class="book-header">
        <image
          v-if="bookInfo?.formats?.['image/jpeg']"
          :src="bookInfo.formats['image/jpeg']"
          class="book-cover-lg"
          mode="aspectFill"
        />
        <view v-else class="book-cover-lg book-cover-lg-placeholder">
          <text>📖</text>
        </view>
        <view class="book-info-text">
          <text class="book-title-lg">{{ bookInfo?.cn_title || bookInfo?.title || '未知书名' }}</text>
          <text class="book-author-lg">{{ bookInfo?.authors?.[0]?.name || '未知作者' }}</text>
          <text class="book-lang">{{ bookInfo?.languages?.[0] || 'English' }}</text>
        </view>
      </view>

      <!-- 章节列表 -->
      <text class="section-title">章节目录</text>
      <view v-if="chapters.length === 0" class="empty-state">
        <text class="icon">📄</text>
        <text class="empty-text">暂无章节数据</text>
        <text class="empty-hint">该书可能为单篇完整文本</text>
        <button class="btn btn-primary" style="margin-top: 24rpx;" @tap="readChapter(-1)">
          <text>阅读全文</text>
        </button>
      </view>
      <view v-else class="chapter-list">
        <view
          v-for="(ch, idx) in chapters"
          :key="idx"
          class="chapter-item"
          :class="{ read: readChapters.includes(idx) }"
          @tap="readChapter(idx)"
        >
          <view class="chapter-left">
            <text class="chapter-idx">{{ idx + 1 }}</text>
            <view>
              <text class="chapter-title">{{ ch.title || `第 ${idx + 1} 章` }}</text>
              <text class="chapter-status">{{ readChapters.includes(idx) ? '✅已读' : '未读' }}</text>
            </view>
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
import { booksApi } from '@/api'
import { useAuthStore } from '@/stores'
import { navTo, navBackSafe } from '@/utils/router'

const auth = useAuthStore()
const loading = ref(true)
const gutenbergId = ref(0)
const bookInfo = ref<any>(null)
const chapters = ref<any[]>([])
const readChapters = ref<number[]>([])

onLoad((query: any) => {
  gutenbergId.value = Number(query?.id)
  loadBook()
})

async function loadBook() {
  loading.value = true
  const safe = (p: Promise<any>) => p.catch(() => null)
  const [detailRes, chaptersRes] = await Promise.all([
    safe(booksApi.getDetail(gutenbergId.value)),
    safe(booksApi.getChapters(gutenbergId.value)),
  ])
  if (detailRes?.data) bookInfo.value = detailRes.data
  if (chaptersRes?.data) chapters.value = chaptersRes.data.chapters || []
  loading.value = false
}

function readChapter(idx: number) {
  navTo(`/pages/chapter/index?id=${gutenbergId.value}&chapter=${idx}`)
}
</script>

<style scoped>
.book-header {
  display: flex;
  gap: 24rpx;
  padding: 20rpx 0 32rpx;
}
.book-cover-lg {
  width: 180rpx;
  height: 260rpx;
  border-radius: 16rpx;
  flex-shrink: 0;
  background: var(--surface-container);
}
.book-cover-lg-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 64rpx;
}
.book-info-text { flex: 1; display: flex; flex-direction: column; gap: 8rpx; }
.book-title-lg {
  font-size: 34rpx;
  font-weight: 700;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.book-author-lg { font-size: 28rpx; color: var(--on-surface-variant); }
.book-lang { font-size: 24rpx; color: var(--on-surface-muted); }

.section-title {
  font-size: 30rpx;
  font-weight: 700;
  display: block;
  padding: 12rpx 0 16rpx;
}

.chapter-list { padding-bottom: 32rpx; }
.chapter-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 28rpx 24rpx;
  background: #fff;
  border-radius: 16rpx;
  margin-bottom: 12rpx;
  box-shadow: var(--shadow-sm);
}
.chapter-item:active { opacity: 0.8; }
.chapter-item.read { opacity: 0.7; }
.chapter-left { display: flex; align-items: center; gap: 20rpx; }
.chapter-idx {
  width: 56rpx;
  height: 56rpx;
  border-radius: 50%;
  background: var(--primary-container);
  color: var(--primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26rpx;
  font-weight: 700;
}
.chapter-title { font-size: 28rpx; font-weight: 600; display: block; }
.chapter-status { font-size: 22rpx; color: var(--on-surface-muted); display: block; margin-top: 4rpx; }
.chapter-arrow { font-size: 32rpx; color: var(--on-surface-muted); }

.empty-state { padding: 40rpx 0; text-align: center; }
.empty-state .icon { font-size: 56rpx; display: block; margin-bottom: 12rpx; }
.empty-text { font-size: 28rpx; color: var(--on-surface-variant); display: block; }
.empty-hint { font-size: 24rpx; color: var(--on-surface-muted); display: block; margin-top: 8rpx; }
</style>
