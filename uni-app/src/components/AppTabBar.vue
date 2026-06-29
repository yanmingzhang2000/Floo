<template>
  <view class="app-tabbar glass">
    <view
      v-for="tab in tabs"
      :key="tab.path"
      class="app-tabbar-item"
      :class="{ active: currentPath === tab.path }"
      @tap="onTap(tab.path)"
    >
      <text class="app-tabbar-icon">{{ tab.icon }}</text>
      <text class="app-tabbar-label">{{ tab.label }}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { navTo } from '@/utils/router'

const tabs = [
  { path: '/pages/home/index',      icon: '🏠', label: '首页' },
  { path: '/pages/learning/index',  icon: '📖', label: '学习' },
  { path: '/pages/dictionary/index', icon: '📚', label: '单词' },
  { path: '/pages/review/index',    icon: '✏️', label: '复习' },
  { path: '/pages/checkin/index',   icon: '📅', label: '打卡' },
]

const currentPath = computed(() => {
  const pages = getCurrentPages()
  const cur = pages[pages.length - 1] as any
  const route = cur?.route || cur?.$page?.route || ''
  return route ? `/${route}` : ''
})

function onTap(path: string) {
  navTo(path)
}
</script>

<style scoped>
.app-tabbar {
  display: flex;
  align-items: center;
  background: rgba(255,255,255,0.88);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-top: 1rpx solid rgba(255,255,255,0.5);
  padding-bottom: env(safe-area-inset-bottom, 0);
}

.app-tabbar-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 14rpx 0 10rpx;
  gap: 4rpx;
  opacity: 0.45;
  transition: opacity 0.15s, transform 0.15s;
}
.app-tabbar-item.active {
  opacity: 1;
  transform: scale(1.05);
}
.app-tabbar-item:active {
  opacity: 0.7;
  transform: scale(0.95);
}

.app-tabbar-icon {
  font-size: 40rpx;
  line-height: 1;
}
.app-tabbar-label {
  font-size: 20rpx;
  font-weight: 500;
  color: var(--on-surface-variant);
}
.app-tabbar-item.active .app-tabbar-label {
  color: var(--primary);
  font-weight: 600;
}
</style>
