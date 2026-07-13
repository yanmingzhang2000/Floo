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

// 备用自定义 tabBar：目前项目使用 pages.json 原生 tabBar，此处保持与之同步以备后用
const tabs = [
  { path: '/pages/learning/index', icon: '📖', label: '图书馆' },
  { path: '/pages/notes/index',    icon: '📝', label: '笔记' },
  { path: '/pages/reading/index',  icon: '📚', label: '在读' },
  { path: '/pages/floo/index',     icon: '🎁', label: 'Floo' },
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
  background: rgba(255,255,255,0.95);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-top: 1rpx solid #f0f0f0;
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
  transition: opacity 0.15s;
}

.app-tabbar-icon {
  font-size: 40rpx;
  line-height: 1;
  opacity: 0.4;
}
.app-tabbar-item.active .app-tabbar-icon {
  opacity: 1;
}

.app-tabbar-label {
  font-size: 20rpx;
  font-weight: 500;
  color: #b0b8c0;
}
.app-tabbar-item.active .app-tabbar-label {
  color: var(--primary);
  font-weight: 700;
}
</style>
