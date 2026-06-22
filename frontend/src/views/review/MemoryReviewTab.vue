<template>
  <div>
    <!-- 记忆概览卡片 -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-num">{{ progressList.length }}</div>
        <div class="stat-label">总内容</div>
      </div>
      <div class="stat-card">
        <div class="stat-num" style="color:var(--success)">{{ masteredCount }}</div>
        <div class="stat-label">已掌握</div>
      </div>
      <div class="stat-card">
        <div class="stat-num" style="color:var(--warning)">{{ visibleDueTasks.length }}</div>
        <div class="stat-label">今日待复习</div>
      </div>
    </div>

    <!-- 待复习队列 -->
    <div class="section" v-if="visibleDueTasks.length">
      <h3 class="section-title">📋 今日复习 <span class="section-hint">（{{ visibleDueTasks.length }}/{{ dueTasks.length }} 条，按记忆曲线排序）</span></h3>
      <div class="task-list">
        <div v-for="task in visibleDueTasks" :key="task.content_id" class="card task-item">
          <div class="task-avatar" :style="{ background: stageColors[task.review_stage] || 'var(--primary)' }">
            S{{ task.review_stage }}
          </div>
          <div class="task-info">
            <div class="task-title">{{ task.title }}</div>
            <div class="task-meta">
              上次准确率 {{ task.last_accuracy.toFixed(0) }}%
              <span v-if="task.next_review_at"> · {{ formatDue(task.next_review_at) }}</span>
            </div>
          </div>
          <router-link :to="`/learning/content/${task.content_id}`" class="btn btn-sm btn-primary">去复习</router-link>
        </div>
      </div>
    </div>

    <div v-else class="empty-state" style="padding-top:20px">
      <div class="icon" style="color:var(--success)">✅</div>
      <p v-if="dueTasks.length">今日复习已完成，还有 {{ dueTasks.length }} 条待复习</p>
      <p v-else>暂无待复习内容，继续学习吧！</p>
    </div>

    <!-- 全部内容进度 -->
    <div class="section" v-if="progressList.length">
      <h3 class="section-title">📊 全部内容进度</h3>
      <div class="progress-list">
        <div v-for="item in sortedProgress" :key="item.content_id" class="card progress-item">
          <div class="progress-left">
            <div class="progress-title">{{ item.title }}</div>
            <div class="progress-meta">
              <span class="stage-badge" :style="{ background: stageColors[item.review_stage] || 'var(--primary)' }">
                {{ item.review_stage === 0 ? '新' : `S${item.review_stage}` }}
              </span>
              <span v-if="item.is_mastered" class="mastered-badge">已掌握</span>
              <span v-else-if="item.review_stage === 0" class="due-text">未默写</span>
              <span v-else-if="item.next_review_at" class="due-text">{{ formatDue(item.next_review_at) }}</span>
            </div>
          </div>
          <div class="progress-accuracy" :style="{ color: getAccuracyColor(item.last_accuracy) }">
            {{ item.review_stage === 0 ? '-' : `${item.last_accuracy.toFixed(0)}%` }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { dailyApi } from '@/api'
import { useAuthStore } from '@/stores'
import type { ReviewTask, MemoryProgress } from '@/types'

const auth = useAuthStore()

const dueTasks = ref<ReviewTask[]>([])
const progressList = ref<MemoryProgress[]>([])
const masteredCount = ref(0)

const stageColors: Record<number, string> = {
  0: '#9E9E9E', 1: '#F44336', 2: '#FF9800',
  3: '#FFC107', 4: '#4CAF50', 5: '#2196F3',
  6: '#9C27B0', 7: '#00BCD4',
}

const sortedProgress = computed(() => {
  return [...progressList.value].sort((a, b) => {
    if (a.is_mastered !== b.is_mastered) return a.is_mastered ? -1 : 1
    if (a.review_stage !== b.review_stage) return b.review_stage - a.review_stage
    return 0
  })
})

const dailyLimit = computed(() => {
  const goal = auth.preference?.daily_goal_minutes || 15
  return goal <= 15 ? 1 : goal <= 30 ? 2 : goal <= 45 ? 3 : 4
})

const visibleDueTasks = computed(() => dueTasks.value.slice(0, dailyLimit.value))

function formatDue(dateStr: string): string {
  const d = new Date(dateStr)
  const now = new Date()
  const diffMs = d.getTime() - now.getTime()
  const diffH = Math.round(diffMs / 3600000)
  if (diffH <= 0) return '已到期'
  if (diffH < 24) return `${diffH}小时后`
  return `${Math.round(diffH / 24)}天后`
}

function getAccuracyColor(acc: number): string {
  if (acc >= 80) return 'var(--success)'
  if (acc >= 60) return 'var(--warning)'
  return 'var(--error)'
}

onMounted(async () => {
  try {
    const [reviewRes, progressRes] = await Promise.all([
      dailyApi.getReviewTasks(auth.currentUserId),
      dailyApi.getAllProgress(auth.currentUserId),
    ])
    dueTasks.value = reviewRes.data.tasks || []
    progressList.value = progressRes.data.items || []
    masteredCount.value = progressRes.data.mastered_count || 0
  } catch { /* ignore */ }
})
</script>

<style scoped>
.stats-row {
  display: flex;
  gap: 10px;
  padding: 0 16px 12px;
}

.stat-card {
  flex: 1;
  text-align: center;
  padding: 14px 8px;
  background: var(--surface-container);
  border-radius: 14px;
}

.stat-num { font-size: 24px; font-weight: 800; }
.stat-label { font-size: 12px; color: var(--on-surface-variant); margin-top: 2px; }

.section { padding: 0 16px; margin-bottom: 16px; }
.section-title { font-size: 15px; font-weight: 700; margin-bottom: 10px; }
.section-hint { font-size: 12px; font-weight: 400; color: var(--on-surface-variant); }

.task-list { display: flex; flex-direction: column; gap: 8px; }
.task-item { display: flex; align-items: center; gap: 12px; }
.task-avatar {
  width: 44px; height: 44px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  color: white; font-weight: 700; font-size: 14px; flex-shrink: 0;
}
.task-info { flex: 1; }
.task-title { font-weight: 600; font-size: 15px; }
.task-meta { font-size: 13px; color: var(--on-surface-variant); margin-top: 2px; }

.progress-list { display: flex; flex-direction: column; gap: 6px; }
.progress-item { display: flex; align-items: center; gap: 12px; padding: 12px 14px; }
.progress-left { flex: 1; }
.progress-title { font-weight: 600; font-size: 14px; }
.progress-meta { display: flex; align-items: center; gap: 6px; margin-top: 4px; }
.stage-badge {
  font-size: 11px; font-weight: 700; color: white;
  padding: 2px 8px; border-radius: 8px;
}
.mastered-badge { font-size: 11px; color: var(--success); font-weight: 600; }
.due-text { font-size: 12px; color: var(--on-surface-variant); }
.progress-accuracy { font-size: 18px; font-weight: 700; }
</style>
