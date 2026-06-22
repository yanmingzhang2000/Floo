/**
 * LoadingButton 组件
 *
 * 统一所有按钮的 loading 状态：显示小 spinner + 禁用。
 * 之前各页面用不同文字变化实现（"生成中..." / "保存中..."），样式不一致。
 */
<script setup lang="ts">
defineProps<{
  loading?: boolean
  disabled?: boolean
  variant?: 'primary' | 'outline' | 'header' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  block?: boolean
}>()
</script>

<template>
  <button
    class="btn"
    :class="[
      variant && `btn-${variant}`,
      size && `btn-${size}`,
      block && 'btn-block',
    ]"
    :disabled="loading || disabled"
  >
    <span v-if="loading" class="loading-btn-spinner"></span>
    <slot />
  </button>
</template>

<style scoped>
.loading-btn-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: btn-spin 0.6s linear infinite;
  flex-shrink: 0;
}

@keyframes btn-spin {
  to { transform: rotate(360deg); }
}
</style>
