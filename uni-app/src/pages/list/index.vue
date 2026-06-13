<template>
  <view class="page-container">
    <view v-if="loading" class="loading">
      <view class="spinner"></view>
    </view>

    <view v-else-if="list.length === 0" class="empty-state">
      <text class="icon">📚</text>
      <text class="empty-text">暂无历史内容</text>
    </view>

    <view v-else class="list-view">
      <view
        v-for="item in list"
        :key="item.id"
        class="list-item card"
        @tap="goDetail(item.id)"
      >
        <text class="item-icon">📄</text>
        <view class="item-info">
          <text class="item-title">{{ item.title }}</text>
          <view class="item-meta">
            <text>{{ item.content_date }}</text>
            <text class="tag tag-primary" style="margin-left: 16rpx">{{ item.difficulty_level }}</text>
          </view>
        </view>
        <text class="arrow">›</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { dailyApi } from '@/api'
import { navTo } from '@/utils/router'
import type { LearningContent } from '@/types'

const loading = ref(true)
const list = ref<LearningContent[]>([])

function goDetail(id: number) {
  navTo(`/pages/detail/index?id=${id}`)
}

onMounted(async () => {
  loading.value = true
  try {
    const { data } = await dailyApi.getList(50)
    list.value = data || []
  } catch {
    list.value = []
  }
  loading.value = false
})
</script>

<style scoped>
.empty-text { font-size: 30rpx; display: block; }

.list-view { padding: 16rpx 0; }
.list-item {
  display: flex;
  align-items: center;
  gap: 24rpx;
}
.item-icon { font-size: 56rpx; }
.item-info { flex: 1; }
.item-title { font-weight: 600; font-size: 30rpx; display: block; }
.item-meta { font-size: 26rpx; color: var(--on-surface-variant); margin-top: 8rpx; display: flex; align-items: center; }
.arrow { font-size: 40rpx; color: var(--on-surface-variant); }
</style>