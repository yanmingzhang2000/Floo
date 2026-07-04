<template>
  <view class="page-container">
    <view class="nav-bar">
      <view class="nav-left">
        <view class="nav-back" @tap="navBackSafe"><text>‹</text></view>
      </view>
      <text class="nav-title">学习周报</text>
      <view class="nav-right">
        <view class="nav-avatar">
          <text>{{ usernameInitial }}</text>
        </view>
      </view>
    </view>

    <view v-if="loading" class="loading">
      <view class="spinner"></view>
    </view>

    <view v-else-if="!weekly" class="empty-state">
      <text class="icon">⚠️</text>
      <text class="empty-text">加载失败</text>
    </view>

    <view v-else class="weekly-wrap">
      <view class="weekly-header-card">
        <text class="weekly-header-title">📊 本周学习报告</text>
        <text class="weekly-header-week">{{ weekly.year_week }}</text>
      </view>

      <view class="stats-grid">
        <view class="stat-item">
          <text class="stat-icon">📅</text>
          <text class="stat-value">{{ weekly.total_checkin_days }}</text>
          <text class="stat-label">打卡天数</text>
        </view>
        <view class="stat-item">
          <text class="stat-icon">📖</text>
          <text class="stat-value">{{ weekly.total_learned_count }}</text>
          <text class="stat-label">学习篇数</text>
        </view>
        <view class="stat-item">
          <text class="stat-icon">🎯</text>
          <text class="stat-value">{{ weekly.avg_accuracy_rate.toFixed(0) }}%</text>
          <text class="stat-label">平均准确率</text>
        </view>
        <view class="stat-item">
          <text class="stat-icon">⭐</text>
          <text class="stat-value">{{ weekly.total_earned_points }}</text>
          <text class="stat-label">获得积分</text>
        </view>
      </view>

      <view class="weekly-footer">
        <button class="btn btn-outline" @tap="navBackSafe">
          <text>返回打卡页</text>
        </button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { checkinApi } from '@/api'
import { useAuthStore } from '@/stores'
import { navBackSafe } from '@/utils/router'
import type { WeeklySummary } from '@/types'

const auth = useAuthStore()
const loading = ref(true)
const weekly = ref<WeeklySummary | null>(null)

const usernameInitial = computed(() => (auth.username?.[0] || '?').toUpperCase())

onMounted(async () => {
  loading.value = true
  try {
    const { data } = await checkinApi.getWeekly(auth.currentUserId)
    weekly.value = data
  } catch (e) { console.error('周报加载失败', e); weekly.value = null }
  loading.value = false
})
</script>

<style scoped>
.weekly-wrap { padding-bottom: 48rpx; }
.weekly-header-card {
  text-align: center; padding: 48rpx 32rpx;
  background: linear-gradient(180deg, var(--primary-container) 0%, transparent 100%);
}
.weekly-header-title { font-size: 36rpx; font-weight: 700; display: block; }
.weekly-header-week { font-size: 26rpx; color: var(--on-surface-variant); margin-top: 8rpx; display: block; }

.stats-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 16rpx;
  padding: 0;
}
.stat-item {
  text-align: center; padding: 32rpx 16rpx;
  background: #fff; border-radius: 20rpx; box-shadow: var(--shadow-sm);
}
.stat-icon { font-size: 40rpx; display: block; margin-bottom: 8rpx; }
.stat-value { font-size: 48rpx; font-weight: 800; color: var(--primary); display: block; }
.stat-label { font-size: 24rpx; color: var(--on-surface-variant); margin-top: 4rpx; display: block; }

.weekly-footer { padding: 32rpx 0; }
</style>
