<template>
  <view v-if="visible" class="modal-overlay" @tap.self="handleClose">
    <view class="modal-sheet" @tap.stop>
      <view class="sheet-header">
        <text class="sheet-title">📝 粘贴文章</text>
        <view class="close-btn" @tap="handleClose">
          <text>✕</text>
        </view>
      </view>
      <view class="sheet-body">
        <text class="hint">粘贴英文文本，AI 自动生成翻译和生词</text>
        <textarea
          v-model="inputText"
          class="content-input"
          placeholder="在此粘贴英文段落..."
          placeholder-style="color: #999;"
          :maxlength="-1"
          :disabled="loading"
        />
        <text class="char-count">{{ inputText.length }} 字</text>
        <view v-if="errorMsg" class="error-msg">
          <text>{{ errorMsg }}</text>
        </view>
        <view v-if="successMsg" class="success-msg">
          <text>{{ successMsg }}</text>
        </view>
        <button
          class="submit-btn"
          :disabled="!inputText.trim() || loading"
          @tap="handleSubmit"
        >
          <text>{{ loading ? 'AI 处理中...' : '开始处理' }}</text>
        </button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { dailyApi } from '@/api'
import { useAuthStore } from '@/stores'

const props = defineProps<{ visible: boolean }>()
const emit = defineEmits<{ close: []; created: [] }>()

const auth = useAuthStore()
const inputText = ref('')
const loading = ref(false)
const errorMsg = ref('')
const successMsg = ref('')

watch(() => props.visible, (v) => {
  if (v) {
    inputText.value = ''
    errorMsg.value = ''
    successMsg.value = ''
  }
})

function handleClose() {
  if (!loading.value) emit('close')
}

async function handleSubmit() {
  const text = inputText.value.trim()
  if (!text) return

  loading.value = true
  errorMsg.value = ''
  successMsg.value = ''

  try {
    const userId = Number(auth.userId || 1)
    const res = await dailyApi.createCustomContent(userId, text)
    successMsg.value = `✅ ${res.data.title}，已加入复习计划`
    emit('created')
    setTimeout(() => emit('close'), 1200)
  } catch (e: any) {
    const detail = e.response?.data?.detail || e.data?.detail
    errorMsg.value = detail || '处理失败，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 200;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.modal-sheet {
  width: calc(100% - 40rpx);   /* 左右各 20rpx，和 page-container 等宽 */
  background: white;
  border-radius: 32rpx 32rpx 0 0;
  padding: 36rpx 32rpx;
  padding-bottom: calc(36rpx + env(safe-area-inset-bottom, 0px));
  max-height: 80vh;
  overflow-y: auto;
}

.sheet-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32rpx;
}

.sheet-title {
  font-size: 36rpx;
  font-weight: 700;
  color: #2C3E50;
}

.close-btn {
  width: 64rpx;
  height: 64rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40rpx;
  color: #999;
}

.hint {
  font-size: 26rpx;
  color: #999;
  margin-bottom: 24rpx;
  display: block;
}

.content-input {
  width: 100%;
  padding: 28rpx;
  border: 2rpx solid #E0E0E0;
  border-radius: 24rpx;
  font-size: 30rpx;
  line-height: 1.6;
  background: #FAFAFA;
  color: #333;
  height: 320rpx;
}

.char-count {
  text-align: right;
  font-size: 24rpx;
  color: #bbb;
  margin: 12rpx 0 0;
  display: block;
}

.error-msg {
  margin-top: 20rpx;
  padding: 20rpx 28rpx;
  background: #FFF0F0;
  color: #D32F2F;
  border-radius: 16rpx;
  font-size: 26rpx;
}

.success-msg {
  margin-top: 20rpx;
  padding: 20rpx 28rpx;
  background: #F0FFF4;
  color: #2E7D32;
  border-radius: 16rpx;
  font-size: 26rpx;
}

.submit-btn {
  width: 100%;
  margin-top: 32rpx;
  padding: 28rpx;
  background: var(--primary);
  color: white;
  border: none;
  border-radius: 24rpx;
  font-size: 32rpx;
  font-weight: 600;
}

.submit-btn[disabled] {
  opacity: 0.5;
}
</style>
