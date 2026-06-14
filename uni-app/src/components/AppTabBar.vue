<template>
  <view class="app-tabbar">
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
  { path: '/pages/learning/index',    icon: '📖', label: '学习' },
  { path: '/pages/dictionary/index',  icon: '📚', label: '单词书' },
  { path: '/pages/review/index',      icon: '✏️', label: '复习' },
  { path: '/pages/checkin/index',     icon: '📅', label: '打卡' },
]

// 当前路径，用于高亮激活项
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
  background: #fff;
  border-top: 1rpx solid var(--outline-variant);
  padding-bottom: env(safe-area-inset-bottom, 0);
  /* 与 page-container 同宽：不需要额外边距，组件放在容器内自动继承 */
}

.app-tabbar-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 16rpx 0 12rpx;
  gap: 6rpx;
  opacity: 0.45;
  transition: opacity 0.15s;
}
.app-tabbar-item.active {
  opacity: 1;
}
.app-tabbar-item:active { opacity: 0.7; }

.app-tabbar-icon {
  font-size: 44rpx;
  line-height: 1;
}
.app-tabbar-label {
  font-size: 20rpx;
  font-weight: 500;
  color: var(--on-surface-variant);
  .app-tabbar-item.active & {
    color: var(--primary);
    font-weight: 600;
  }
}
.app-tabbar-item.active .app-tabbar-label {
  color: var(--primary);
  font-weight: 600;
}
</style>
