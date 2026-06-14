<template>
  <view class="page-container">
    <view class="nav-bar">
      <view class="nav-left">
        <view class="nav-back" @tap="uni.navigateBack()"><text>‹</text></view>
      </view>
      <text class="nav-title">历史内容</text>
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
      <text class="empty-text">暂无历史内容</text>
    </view>

    <view v-else class="list-view">
      <view v-for="item in list" :key="item.id" class="card list-item" @tap="goDetail(item.id)">
        <view class="list-item-icon">
          <text>📄</text>
        </view>
        <view class="list-item-info">
          <text class="list-item-title">{{ item.title }}</text>
          <view class="list-item-meta">
            <text>{{ item.content_date }}</text>
            <text class="tag tag-primary" style="margin-left: 12rpx">{{ item.difficulty_level }}</text>
          </view>
        </view>
        <text class="list-item-arrow">›</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { dailyApi } from '@/api'
import { useAuthStore } from '@/stores'
import { navTo } from '@/utils/router'
import type { LearningContent } from '@/types'

const auth = useAuthStore()
const loading = ref(true)
const list = ref<LearningContent[]>([])

const usernameInitial = computed(() => (auth.username?.[0] || '?').toUpperCase())

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
.list-view { padding: 16rpx 0; }
.list-item {
  display: flex; align-items: center; gap: 20rpx; padding: 28rpx;
}
.list-item-icon { font-size: 48rpx; flex-shrink: 0; }
.list-item-info { flex: 1; min-width: 0; }
.list-item-title { font-weight: 600; font-size: 28rpx; display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.list-item-meta { font-size: 24rpx; color: var(--on-surface-variant); margin-top: 8rpx; display: flex; align-items: center; }
.list-item-arrow { font-size: 36rpx; color: var(--on-surface-muted); flex-shrink: 0; }
</style>
