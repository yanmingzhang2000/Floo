/**
 * 全局 Toast 通知工具
 *
 * 为什么需要：之前所有错误都被静默吞掉（/* ignore *​/），用户完全不知道发生了什么。
 * Toast 提供轻量级的操作反馈，替代 alert() 和静默 catch。
 */
import { ref } from 'vue'

export interface ToastItem {
  id: number
  message: string
  type: 'success' | 'error' | 'info' | 'warning'
  duration: number
}

const toasts = ref<ToastItem[]>([])
let nextId = 0

function addToast(message: string, type: ToastItem['type'] = 'info', duration = 3000) {
  const id = nextId++
  const toast: ToastItem = { id, message, type, duration }
  toasts.value.push(toast)

  if (duration > 0) {
    setTimeout(() => {
      removeToast(id)
    }, duration)
  }

  return id
}

function removeToast(id: number) {
  const idx = toasts.value.findIndex(t => t.id === id)
  if (idx !== -1) {
    toasts.value.splice(idx, 1)
  }
}

export function useToast() {
  return {
    toasts,

    success(message: string, duration = 3000) {
      return addToast(message, 'success', duration)
    },

    error(message: string, duration = 4000) {
      return addToast(message, 'error', duration)
    },

    info(message: string, duration = 3000) {
      return addToast(message, 'info', duration)
    },

    warning(message: string, duration = 3500) {
      return addToast(message, 'warning', duration)
    },

    remove: removeToast,
  }
}
