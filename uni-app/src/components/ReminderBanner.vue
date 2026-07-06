<template>
  <view v-if="visible" class="reminder-banner" @tap="handleTap">
    <view class="reminder-icon">⏰</view>
    <view class="reminder-text">
      <text class="reminder-title">{{ title }}</text>
      <text class="reminder-sub">点击去打卡</text>
    </view>
    <view class="reminder-close" @tap.stop="dismiss">✕</view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { navTo } from '@/utils/router'

const props = defineProps<{
  visible: boolean
  daysSinceLast: number
}>()

const emit = defineEmits<{
  (e: 'dismiss'): void
}>()

const title = computed(() => {
  if (props.daysSinceLast < 0) return '还没有开始背单词，今天开始吧！'
  return `你已经 ${props.daysSinceLast} 天没有背单词了`
})

function handleTap() {
  emit('dismiss')
  navTo('/pages/checkin/index')
}

function dismiss() {
  emit('dismiss')
}
</script>

<style scoped>
.reminder-banner {
  display: flex;
  flex-direction: row;
  align-items: center;
  background: #FFF8E1;
  border: 1rpx solid #FFD54F;
  border-radius: 16rpx;
  padding: 20rpx 24rpx;
  margin: 16rpx 32rpx 0;
  gap: 16rpx;
}

.reminder-icon {
  font-size: 36rpx;
  flex-shrink: 0;
}

.reminder-text {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.reminder-title {
  font-size: 26rpx;
  font-weight: 600;
  color: #5D4037;
  line-height: 1.4;
}

.reminder-sub {
  font-size: 22rpx;
  color: #8D6E63;
}

.reminder-close {
  font-size: 24rpx;
  color: #BCAAA4;
  padding: 4rpx 8rpx;
  flex-shrink: 0;
}
</style>
