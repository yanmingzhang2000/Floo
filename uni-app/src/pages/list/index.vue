<template>
  <view class="page-container">
    <view class="nav-bar">
      <view class="nav-left">
        <view class="nav-back" @tap="navBackSafe"><text>‹</text></view>
      </view>
      <text class="nav-title">往期内容</text>
      <view class="nav-right">
        <view class="nav-avatar">
          <text>{{ usernameInitial }}</text>
        </view>
      </view>
    </view>

    <view v-if="loading" class="loading">
      <view class="spinner"></view>
    </view>

    <view v-else-if="list.length === 0" class="empty-state">
      <text class="icon">📚</text>
      <text class="empty-text">暂无往期内容</text>
    </view>

    <view v-else class="list-view">
      <view
        v-for="item in list"
        :key="item.id"
        class="list-item"
        @tap="goDetail(item.id)"
      >
        <!-- 主信息 -->
        <view class="list-item-info">
          <text class="list-item-title">{{ item.title }}</text>
          <view class="list-item-meta">
            <text class="tag tag-success">{{ themeLabels[item.theme_type] || item.theme_type }}</text>
            <text class="list-item-date">{{ item.content_date }}</text>
          </view>
        </view>
        <!-- 箭头 -->
        <text class="list-item-arrow">›</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { dailyApi } from '@/api'
import { useAuthStore } from '@/stores'
import { navTo, navBackSafe } from '@/utils/router'
import type { LearningContent } from '@/types'

const auth = useAuthStore()
const loading = ref(true)
const list = ref<LearningContent[]>([])

const usernameInitial = computed(() => (auth.username?.[0] || '?').toUpperCase())

const themeLabels: Record<string, string> = {
  ai_tech: 'AI科技', product_tech: '产品技术', business: '财经商业',
  daily_news: '日常新闻', self_growth: '个人成长', all_random: '随机', custom: '自定义',
}

function goDetail(id: number) { navTo(`/pages/detail/index?id=${id}`) }

onMounted(async () => {
  loading.value = true
  try {
    const { data } = await dailyApi.getList(50)
    list.value = data || []
  } catch { list.value = [] }
  loading.value = false
})
</script>

<style scoped>
.list-view {
  padding: 8rpx 0 40rpx;
}

.list-item {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 24rpx 0;
  border-bottom: 1rpx solid var(--outline-variant);
}
.list-item:last-child { border-bottom: none; }

.list-item-info {
  flex: 1;
  min-width: 0;  /* 让 flex 子项可以收缩，触发 overflow 截断 */
}
.list-item-title {
  font-size: 28rpx;
  font-weight: 600;
  color: var(--on-surface);
  display: block;
  /* 最多两行，超出省略 */
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.5;
  margin-bottom: 10rpx;
}
.list-item-meta {
  display: flex;
  align-items: center;
  gap: 16rpx;
}
.list-item-date {
  font-size: 22rpx;
  color: var(--on-surface-muted);
}

.list-item-arrow {
  font-size: 40rpx;
  color: var(--on-surface-muted);
  flex-shrink: 0;
  margin-left: 8rpx;
}
</style>
