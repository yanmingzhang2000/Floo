/**
 * 全局 Confirm 弹窗组件
 *
 * 放在 App.vue 顶层，配合 useConfirm composable 使用。
 * 替代原生 confirm()，支持自定义样式和动画。
 */
<script setup lang="ts">
import { useConfirm } from '../composables/useConfirm'

const { state, handleConfirm, handleCancel } = useConfirm()
</script>

<template>
  <Teleport to="body">
    <Transition name="confirm-fade">
      <div v-if="state.visible" class="confirm-overlay" @click.self="handleCancel">
        <div class="confirm-dialog">
          <h3 class="confirm-title">{{ state.title }}</h3>
          <p class="confirm-message">{{ state.message }}</p>
          <div class="confirm-actions">
            <button class="btn btn-sm confirm-cancel-btn" @click="handleCancel">
              {{ state.cancelText }}
            </button>
            <button
              class="btn btn-sm"
              :class="state.confirmClass"
              @click="handleConfirm"
            >
              {{ state.confirmText }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.confirm-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  backdrop-filter: blur(2px);
  -webkit-backdrop-filter: blur(2px);
}

.confirm-dialog {
  background: white;
  border-radius: var(--radius);
  padding: 24px;
  width: 85%;
  max-width: 320px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
}

.confirm-title {
  font-size: 17px;
  font-weight: 700;
  color: var(--on-surface);
  margin-bottom: 8px;
}

.confirm-message {
  font-size: 14px;
  color: var(--on-surface-variant);
  line-height: 1.5;
  margin-bottom: 20px;
}

.confirm-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.confirm-cancel-btn {
  background: var(--surface-container);
  color: var(--on-surface);
}

/* Transition */
.confirm-fade-enter-active { transition: all 0.2s ease-out; }
.confirm-fade-leave-active { transition: all 0.15s ease-in; }
.confirm-fade-enter-from { opacity: 0; }
.confirm-fade-leave-to { opacity: 0; }
.confirm-fade-enter-from .confirm-dialog { transform: scale(0.95); }
.confirm-fade-leave-to .confirm-dialog { transform: scale(0.95); }
</style>
