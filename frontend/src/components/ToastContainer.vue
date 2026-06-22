/**
 * 全局 Toast 容器
 *
 * 放在 App.vue 顶层，所有页面共享同一套 Toast 通知。
 * 支持 success / error / info / warning 四种类型，自动消失。
 */
<script setup lang="ts">
import { useToast } from '../composables/useToast'

const { toasts, remove } = useToast()

function toastClass(type: string) {
  return `toast-item toast-${type}`
}
</script>

<template>
  <div class="toast-container">
    <TransitionGroup name="toast-fade">
      <div
        v-for="toast in toasts"
        :key="toast.id"
        :class="toastClass(toast.type)"
        @click="remove(toast.id)"
      >
        <span class="toast-icon">
          <template v-if="toast.type === 'success'">✓</template>
          <template v-else-if="toast.type === 'error'">✕</template>
          <template v-else-if="toast.type === 'warning'">!</template>
          <template v-else>i</template>
        </span>
        <span class="toast-msg">{{ toast.message }}</span>
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
.toast-container {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10000;
  display: flex;
  flex-direction: column;
  gap: 8px;
  pointer-events: none;
}

.toast-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 500;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  pointer-events: auto;
  cursor: pointer;
  max-width: 90vw;
  min-width: 120px;
  justify-content: center;
}

.toast-icon {
  font-size: 14px;
  font-weight: bold;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.toast-success {
  background: rgba(16, 185, 129, 0.9);
  color: white;
}
.toast-success .toast-icon {
  background: rgba(255, 255, 255, 0.2);
}

.toast-error {
  background: rgba(239, 68, 68, 0.9);
  color: white;
}
.toast-error .toast-icon {
  background: rgba(255, 255, 255, 0.2);
}

.toast-warning {
  background: rgba(245, 158, 11, 0.9);
  color: white;
}
.toast-warning .toast-icon {
  background: rgba(255, 255, 255, 0.2);
}

.toast-info {
  background: rgba(59, 130, 246, 0.9);
  color: white;
}
.toast-info .toast-icon {
  background: rgba(255, 255, 255, 0.2);
}

/* TransitionGroup 动画 */
.toast-fade-enter-active {
  transition: all 0.3s ease-out;
}
.toast-fade-leave-active {
  transition: all 0.25s ease-in;
}
.toast-fade-enter-from {
  opacity: 0;
  transform: translateY(-16px) scale(0.95);
}
.toast-fade-leave-to {
  opacity: 0;
  transform: translateY(-8px) scale(0.95);
}
</style>
