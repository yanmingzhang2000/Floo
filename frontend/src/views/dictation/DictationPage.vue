<template>
  <div class="page-container">
    <div class="page-header">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <h1>默写练习</h1>
        <button class="btn btn-sm" style="background:rgba(255,255,255,0.2);color:white" @click="showOriginal = !showOriginal">
          {{ showOriginal ? '🙈 隐藏原文' : '👁️ 显示原文' }}
        </button>
      </div>
    </div>

    <div v-if="loadingContent" class="loading"><div class="spinner"></div></div>

    <div v-else-if="currentContent" class="dictation-area">
      <div class="card title-hint">
        <span class="tag tag-primary">当前内容</span>
        <span style="margin-left:8px;font-weight:600">{{ currentContent.title }}</span>
      </div>

      <div class="card">
        <h4 style="margin-bottom:8px;color:var(--on-surface-variant)">中文翻译提示</h4>
        <p style="line-height:1.6">{{ currentContent.translation || '暂无翻译' }}</p>
      </div>

      <Transition name="slide-up">
        <div v-if="showOriginal" class="card" style="background:var(--primary-container)">
          <h4 style="margin-bottom:8px;color:var(--on-primary-container)">英文原文</h4>
          <p style="line-height:1.8;font-size:15px">{{ currentContent.article }}</p>
        </div>
      </Transition>

      <div class="card">
        <textarea v-model="userInput" rows="10" placeholder="在这里输入你默写的英文内容..." class="dictation-input"></textarea>
      </div>

      <div style="padding:0 16px 16px;display:flex;gap:10px">
        <button class="btn btn-primary btn-block" @click="handleSubmit" :disabled="submitting || !userInput.trim()">
          {{ submitting ? 'AI 批改中...' : '提交批改' }}
        </button>
        <button class="btn btn-outline" @click="userInput = ''">清空</button>
      </div>

      <!-- 批改结果 -->
      <div v-if="result" class="card result-card">
        <div class="score-area">
          <div class="score" :class="{ green: result.feedback.score >= 80, orange: result.feedback.score >= 60, red: result.feedback.score < 60 }">
            {{ result.feedback.score }}
          </div>
          <div class="score-meta">
            <div>准确率 {{ (result.accuracy_rate * 100).toFixed(0) }}%</div>
            <div style="color:var(--success)">+{{ result.earned_points }} 积分</div>
            <div style="color:var(--primary)">S{{ result.review_stage }} · {{ result.next_review_at?.slice(5, 10) || '-' }}</div>
          </div>
        </div>

        <div class="feedback-section" v-if="result.feedback.summary">
          <h4>AI 总评</h4>
          <p>{{ result.feedback.summary }}</p>
        </div>

        <div v-if="result.feedback.diffs?.length" class="feedback-section">
          <h4>差异分析</h4>
          <div v-for="(d, i) in result.feedback.diffs" :key="i" class="diff-item" :class="d.type">
            <span class="diff-type">{{ d.type === 'missing' ? '遗漏' : d.type === 'wrong' ? '错误' : '多余' }}</span>
            <span>应为 <strong>{{ d.expected }}</strong></span>
            <span v-if="d.type !== 'missing'">你写 <strong>{{ d.actual }}</strong></span>
          </div>
        </div>

        <div v-if="result.feedback.suggestions?.length" class="feedback-section">
          <h4>改进建议</h4>
          <ul>
            <li v-for="(s, i) in result.feedback.suggestions" :key="i">{{ s }}</li>
          </ul>
        </div>
      </div>
    </div>

    <div v-else class="empty-state">
      <div class="icon">✏️</div>
      <p>今日暂无学习内容，请先生成</p>
      <router-link to="/learning" class="btn btn-primary" style="margin-top:16px">去生成</router-link>
    </div>

    <!-- 历史记录 -->
    <div class="card history-section" v-if="history.length">
      <h4 style="margin-bottom:10px">历史记录</h4>
      <div v-for="h in history" :key="h.dictation_id" class="history-item">
        <span>{{ h.created_at?.slice(5, 10) }}</span>
        <span :style="{ color: h.accuracy_rate >= 0.8 ? 'var(--success)' : h.accuracy_rate >= 0.6 ? 'var(--warning)' : 'var(--error)' }">
          {{ (h.accuracy_rate * 100).toFixed(0) }}%
        </span>
        <span style="color:var(--success)">+{{ h.earned_points }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { dailyApi, dictationApi } from '@/api'
import { useAuthStore } from '@/stores'
import type { LearningContent, DictationResult, DictationHistory } from '@/types'

const auth = useAuthStore()
const loadingContent = ref(true)
const currentContent = ref<LearningContent | null>(null)
const showOriginal = ref(false)
const userInput = ref('')
const submitting = ref(false)
const result = ref<DictationResult | null>(null)
const history = ref<DictationHistory[]>([])

onMounted(async () => {
  try {
    const [todayRes, histRes] = await Promise.all([
      dailyApi.getToday(auth.currentUserId),
      dictationApi.getHistory(auth.currentUserId),
    ])
    currentContent.value = todayRes.data
    history.value = histRes.data?.slice(0, 10) || []
  } catch { /* ignore */ }
  loadingContent.value = false
})

async function handleSubmit() {
  if (!currentContent.value || !userInput.value.trim()) return
  submitting.value = true
  result.value = null
  try {
    const { data } = await dictationApi.submit(auth.currentUserId, currentContent.value.id, userInput.value)
    result.value = data
    const histRes = await dictationApi.getHistory(auth.currentUserId)
    history.value = histRes.data?.slice(0, 10) || []
  } catch { /* ignore */ }
  submitting.value = false
}
</script>

<style scoped>
.title-hint { display: flex; align-items: center; }
.dictation-input {
  width: 100%;
  border: 1.5px solid var(--outline);
  border-radius: var(--radius-sm);
  padding: 12px;
  font-size: 15px;
  line-height: 1.6;
  resize: vertical;
  outline: none;
  font-family: inherit;
}
.dictation-input:focus { border-color: var(--primary); }

.result-card { border-left: 4px solid var(--primary); }
.score-area { display: flex; align-items: center; gap: 16px; margin-bottom: 16px; }
.score { font-size: 48px; font-weight: 800; }
.score.green { color: var(--success); }
.score.orange { color: var(--warning); }
.score.red { color: var(--error); }
.score-meta { font-size: 14px; line-height: 1.6; }

.feedback-section { margin-top: 16px; padding-top: 12px; border-top: 1px solid var(--surface-container-high); }
.feedback-section h4 { font-size: 14px; color: var(--on-surface-variant); margin-bottom: 8px; }

.diff-item { padding: 6px 0; font-size: 14px; display: flex; gap: 8px; align-items: center; }
.diff-type { font-size: 12px; padding: 2px 8px; border-radius: 4px; font-weight: 600; }
.diff-item.missing .diff-type { background: #FFEBEE; color: var(--error); }
.diff-item.wrong .diff-type { background: #FFF3E0; color: var(--warning); }
.diff-item.extra .diff-type { background: #E3F2FD; color: #1976D2; }

.history-section { margin: 0 16px 16px; }
.history-item { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid var(--surface-container); font-size: 14px; }
</style>
