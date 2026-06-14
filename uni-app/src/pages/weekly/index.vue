<template>
  <view class="page-container">
    <view v-if="loading" class="loading">
      <view class="spinner"></view>
    </view>

    <view v-else-if="!weekly" class="empty-state">
      <text class="icon">📊</text>
      <text class="empty-text">暂无周报数据</text>
    </view>

    <view v-else>
      <view class="card">
        <text class="report-title">📊 本周学习报告</text>
        <text class="report-week">{{ weekly.year_week }}</text>
      </view>

      <view class="stats-grid">
        <view class="stat-card">
          <text class="stat-icon">📅</text>
          <text class="stat-num">{{ weekly.total_checkin_days }}</text>
          <text class="stat-label">打卡天数</text>
        </view>
        <view class="stat-card">
          <text class="stat-icon">📖</text>
          <text class="stat-num">{{ weekly.total_learned_count }}</text>
          <text class="stat-label">学习篇数</text>
        </view>
        <view class="stat-card">
          <text class="stat-icon">🎯</text>
          <text class="stat-num">{{ weekly.avg_accuracy_rate.toFixed(0) }}%</text>
          <text class="stat-label">平均准确率</text>
        </view>
        <view class="stat-card">
          <text class="stat-icon">⭐</text>
          <text class="stat-num">{{ weekly.total_earned_points }}</text>
          <text class="stat-label">获得积分</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { checkinApi } from '@/api'
import { useAuthStore } from '@/stores'
import type { WeeklySummary } from '@/types'

const auth = useAuthStore()
const loading = ref(true)
const weekly = ref<WeeklySummary | null>(null)

onMounted(async () => {
  loading.value = true
  try {
    const { data } = await checkinApi.getWeekly(auth.currentUserId)
    weekly.value = data
  } catch {
    weekly.value = null
  }
  loading.value = false
})
</script>

<style scoped>
.report-title { font-size: 36rpx; font-weight: 700; display: block; margin-bottom: 8rpx; }
.report-week { font-size: 28rpx; color: var(--on-surface-variant); display: block; }
.empty-text { font-size: 30rpx; display: block; }

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16rpx;
  padding: 0 24rpx;
}

.stat-card {
  text-align: center;
  padding: 32rpx 16rpx;
  background: #fff;
  border-radius: 20rpx;
  box-shadow: var(--shadow-sm);
}

.stat-icon { font-size: 40rpx; display: block; margin-bottom: 8rpx; }
.stat-num {
  font-size: 48rpx;
  font-weight: 800;
  color: var(--primary);
  display: block;
}
.stat-label {
  font-size: 24rpx;
  color: var(--on-surface-variant);
  margin-top: 4rpx;
  display: block;
}
</style>