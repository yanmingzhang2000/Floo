<template>
  <view class="page-container">
    <view class="nav-bar">
      <view class="nav-left">
        <view class="nav-back" @tap="navBackSafe"><text>‹</text></view>
      </view>
      <text class="nav-title">书籍精读</text>
      <view class="nav-right"></view>
    </view>

    <view v-if="loading" class="loading">
      <view class="spinner"></view>
    </view>

    <template v-else>
      <view v-if="books.length === 0" class="empty-state">
        <text class="icon">📚</text>
        <text class="empty-text">暂无可访问书籍</text>
        <text class="empty-hint">书籍需管理员授权后才能阅读</text>
      </view>

      <view v-else class="book-list">
        <view
          v-for="b in books"
          :key="b.series_id"
          class="book-card"
          @tap="openBook(b)"
        >
          <view class="book-cover">
            <text class="book-cover-icon">📖</text>
          </view>
          <view class="book-info">
            <text class="book-title">{{ b.name_cn || b.name }}</text>
            <text v-if="b.name_cn && b.name" class="book-title-en">{{ b.name }}</text>
            <text v-if="b.author" class="book-author">{{ b.author }}</text>
            <text class="book-meta">共 {{ b.total_chapters }} 章</text>
            <text v-if="b.description" class="book-desc">{{ b.description.slice(0, 80) }}...</text>
          </view>
        </view>
      </view>
    </template>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { bookApi } from '@/api'
import { useAuthStore } from '@/stores'
import { navTo, navBackSafe } from '@/utils/router'

interface BookSeries {
  series_id: number
  name: string
  name_cn?: string
  author?: string
  cover_url?: string
  description?: string
  total_chapters: number
}

const auth = useAuthStore()
const loading = ref(true)
const books = ref<BookSeries[]>([])

async function loadBooks() {
  loading.value = true
  try {
    const { data } = await bookApi.listMine(auth.currentUserId)
    books.value = data?.books || []
  } catch (e) {
    // 网络异常：给个空列表兜底，不弹错，避免打扰用户
    books.value = []
  } finally {
    loading.value = false
  }
}

function openBook(book: BookSeries) {
  // 跳章节页，把 series 名字一起带过去做标题回显
  const name = encodeURIComponent(book.name_cn || book.name)
  navTo(`/pages/book/chapters?series_id=${book.series_id}&name=${name}`)
}

onShow(loadBooks)
</script>

<style scoped>
.book-list {
  padding: 16rpx 0;
}

.book-card {
  display: flex;
  gap: 24rpx;
  background: #fff;
  border-radius: 20rpx;
  padding: 24rpx;
  margin-bottom: 16rpx;
  box-shadow: var(--shadow-sm);
}

.book-card:active {
  opacity: 0.85;
}

.book-cover {
  width: 120rpx;
  height: 160rpx;
  background: linear-gradient(135deg, #5B9AA8 0%, #7FB3C1 100%);
  border-radius: 12rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.book-cover-icon {
  font-size: 60rpx;
}

.book-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}

.book-title {
  font-size: 32rpx;
  font-weight: 700;
  color: var(--on-surface);
  line-height: 1.3;
}

.book-title-en {
  font-size: 24rpx;
  color: var(--on-surface-variant);
  line-height: 1.3;
}

.book-author {
  font-size: 24rpx;
  color: var(--on-surface-variant);
  margin-top: 4rpx;
}

.book-meta {
  font-size: 22rpx;
  color: var(--primary);
  font-weight: 600;
  margin-top: 4rpx;
}

.book-desc {
  font-size: 24rpx;
  color: var(--on-surface-variant);
  line-height: 1.5;
  margin-top: 8rpx;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
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

.empty-hint {
  font-size: 24rpx;
  color: var(--on-surface-muted);
  display: block;
  margin-top: 12rpx;
}
</style>
