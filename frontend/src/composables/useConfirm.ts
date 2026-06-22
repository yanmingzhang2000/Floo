/**
 * 全局 Confirm 弹窗（替代原生 confirm()）
 *
 * 原生 confirm 会阻塞主线程，无法自定义样式，移动端体验差。
 * 这个 composable 返回 Promise，支持 async/await 调用。
 */
import { ref } from 'vue'

interface ConfirmState {
  visible: boolean
  title: string
  message: string
  confirmText: string
  cancelText: string
  confirmClass: string
  resolve: ((value: boolean) => void) | null
}

const state = ref<ConfirmState>({
  visible: false,
  title: '确认',
  message: '',
  confirmText: '确定',
  cancelText: '取消',
  confirmClass: 'btn-primary',
  resolve: null,
})

export function useConfirm() {
  function show(options: {
    title?: string
    message: string
    confirmText?: string
    cancelText?: string
    confirmClass?: string
  }): Promise<boolean> {
    return new Promise((resolve) => {
      state.value = {
        visible: true,
        title: options.title || '确认',
        message: options.message,
        confirmText: options.confirmText || '确定',
        cancelText: options.cancelText || '取消',
        confirmClass: options.confirmClass || 'btn-primary',
        resolve,
      }
    })
  }

  function confirm(options: Parameters<typeof show>[0]) {
    return show(options)
  }

  function handleConfirm() {
    state.value.resolve?.(true)
    state.value.visible = false
  }

  function handleCancel() {
    state.value.resolve?.(false)
    state.value.visible = false
  }

  return {
    state,
    show,
    confirm,
    handleConfirm,
    handleCancel,
  }
}
