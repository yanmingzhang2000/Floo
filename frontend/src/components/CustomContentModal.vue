<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="visible" class="modal-overlay" @click.self="handleClose">
        <div class="modal-sheet">
          <div class="sheet-header">
            <h3>📝 自定义学习内容</h3>
            <button class="close-btn" @click="handleClose">✕</button>
          </div>
          <div class="sheet-body">
            <p class="hint">粘贴英文文本，AI 自动生成翻译和生词</p>
            <textarea
              v-model="inputText"
              class="content-input"
              placeholder="在此粘贴英文段落..."
              rows="8"
              :disabled="loading"
            ></textarea>
            <p class="char-count">{{ inputText.length }} 字</p>
            <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>
            <div v-if="successMsg" class="success-msg">{{ successMsg }}</div>
            <LoadingButton
              variant="primary"
              size="lg"
              block
              :loading="loading"
              :disabled="!inputText.trim()"
              class="submit-btn"
              @click="handleSubmit"
            >
              开始处理
            </LoadingButton>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { dailyApi } from '@/api'
import { useAuthStore } from '@/stores'
import LoadingButton from '@/components/LoadingButton.vue'

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
    const detail = e.response?.data?.detail
    errorMsg.value = detail || '处理失败，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.4);
  z-index: 200;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.modal-sheet {
  width: 100%;
  max-width: 480px;
  background: white;
  border-radius: 20px 20px 0 0;
  padding: 20px;
  max-height: 85vh;
  overflow-y: auto;
}

.sheet-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.sheet-header h3 {
  font-size: 18px;
  font-weight: 700;
  color: var(--on-surface);
}

.close-btn {
  background: none;
  border: none;
  font-size: 20px;
  color: var(--on-surface-variant);
  cursor: pointer;
  padding: 4px;
}

.hint {
  font-size: 13px;
  color: var(--on-surface-variant);
  margin-bottom: 12px;
}

.content-input {
  width: 100%;
  padding: 14px;
  border: 1px solid var(--outline);
  border-radius: 12px;
  font-size: 15px;
  line-height: 1.6;
  resize: vertical;
  font-family: inherit;
  background: var(--surface-container);
  color: var(--on-surface);
}

.content-input:focus {
  outline: none;
  border-color: var(--primary);
  background: white;
}

.content-input:disabled {
  opacity: 0.6;
}

.char-count {
  text-align: right;
  font-size: 12px;
  color: var(--on-surface-variant);
  margin: 6px 0 0;
}

.error-msg {
  margin-top: 10px;
  padding: 10px 14px;
  background: #FFEBEE;
  color: var(--error);
  border-radius: 8px;
  font-size: 13px;
}

.success-msg {
  margin-top: 10px;
  padding: 10px 14px;
  background: #E8F5E9;
  color: var(--success);
  border-radius: 8px;
  font-size: 13px;
}

.submit-btn {
  margin-top: 16px;
}

.fade-enter-active, .fade-leave-active { transition: opacity 0.25s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
