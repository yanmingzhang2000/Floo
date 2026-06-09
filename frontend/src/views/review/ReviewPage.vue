<template>
  <div class="page-container">
    <div class="page-header">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <h1>复习</h1>
        <button class="btn btn-sm" style="background:rgba(255,255,255,0.2);color:white" @click="loadData">🔄 刷新</button>
      </div>
    </div>

    <!-- 功能入口 -->
    <div class="feature-tabs">
      <div class="feature-tab" :class="{ active: activeTab === 'review' }" @click="activeTab = 'review'">
        <span class="feature-icon">🔄</span>
        <span class="feature-name">复习任务</span>
        <span class="feature-badge" v-if="tasks.length">{{ tasks.length }}</span>
      </div>
      <div class="feature-tab" :class="{ active: activeTab === 'dictation' }" @click="activeTab = 'dictation'">
        <span class="feature-icon">✏️</span>
        <span class="feature-name">默写练习</span>
      </div>
    </div>

    <div v-if="loading" class="loading"><div class="spinner"></div></div>

    <!-- 复习任务 -->
    <template v-else-if="activeTab === 'review'">
      <div v-if="tasks.length === 0" class="empty-state">
        <div class="icon" style="color:var(--success)">✅</div>
        <p>今日无待复习内容</p>
      </div>

      <div v-else class="task-list">
        <div v-for="task in tasks" :key="task.content_id" class="card task-item">
          <div class="task-avatar" :style="{ background: stageColors[task.review_stage] || 'var(--primary)' }">
            S{{ task.review_stage }}
          </div>
          <div class="task-info">
            <div class="task-title">{{ task.title }}</div>
            <div class="task-meta">
              上次准确率 {{ (task.last_accuracy * 100).toFixed(0) }}%
            </div>
          </div>
          <router-link :to="`/daily/content/${task.content_id}`" class="btn btn-sm btn-primary">去复习</router-link>
        </div>
      </div>
    </template>

    <!-- 默写练习 -->
    <template v-else-if="activeTab === 'dictation'">
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
        <router-link to="/daily" class="btn btn-primary" style="margin-top:16px">去生成</router-link>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { dailyApi, dictationApi } from '@/api'
import { useAuthStore } from '@/stores'
import type { LearningContent, DictationResult, ReviewTask } from '@/types'

const auth = useAuthStore()
const loading = ref(true)
const activeTab = ref<'review' | 'dictation'>('review')

// 复习
const tasks = ref<ReviewTask[]>([])
const stageColors: Record<number, string> = {
  0: '#9E9E9E', 1: '#F44336', 2: '#FF9800',
  3: '#FFC107', 4: '#4CAF50', 5: '#2196F3',
}

// 默写
const loadingContent = ref(true)
const currentContent = ref<LearningContent | null>(null)
const showOriginal = ref(false)
const userInput = ref('')
const submitting = ref(false)
const result = ref<DictationResult | null>(null)

onMounted(loadData)

async function loadData() {
  loading.value = true
  loadingContent.value = true
  try {
    const [reviewRes, contentRes] = await Promise.all([
      dailyApi.getReviewTasks(auth.currentUserId),
      dailyApi.getToday(auth.currentUserId).catch(() => ({ data: null })),
    ])
    tasks.value = reviewRes.data.tasks || []
    currentContent.value = contentRes.data
  } catch { /* ignore */ }
  loading.value = false
  loadingContent.value = false
}

async function handleSubmit() {
  if (!currentContent.value || !userInput.value.trim()) return
  submitting.value = true
  result.value = null
  try {
    const { data } = await dictationApi.submit(auth.currentUserId, currentContent.value.id, userInput.value)
    result.value = data
  } catch { /* ignore */ }
  submitting.value = false
}
</script>

<style scoped>
.feature-tabs {
  display: flex;
  gap: 12px;
  padding: 12px 16px;
}

.feature-tab {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 16px 12px;
  background: var(--surface-container);
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.feature-tab.active {
  background: var(--primary);
  color: white;
}

.feature-icon { font-size: 24px; }
.feature-name { font-size: 13px; font-weight: 500; }

.feature-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  background: var(--error);
  color: white;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 10px;
}

.task-list { padding: 0 16px; }
.task-item { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
.task-avatar {
  width: 44px; height: 44px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  color: white; font-weight: 700; font-size: 14px; flex-shrink: 0;
}
.task-info { flex: 1; }
.task-title { font-weight: 600; font-size: 15px; }
.task-meta { font-size: 13px; color: var(--on-surface-variant); margin-top: 2px; }

.dictation-area { padding-bottom: 20px; }
.title-hint { display: flex; align-items: center; margin: 16px; }
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

.result-card { margin: 0 16px; border-left: 4px solid var(--primary); }
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
</style>
