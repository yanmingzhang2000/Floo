<template>
  <div class="page-container">
    <div class="page-header">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <h1>复习任务</h1>
        <button class="btn btn-sm" style="background:rgba(255,255,255,0.2);color:white" @click="loadData">🔄 刷新</button>
      </div>
      <p class="subtitle" v-if="tasks.length">今日待复习 {{ tasks.length }} 篇</p>
    </div>

    <div v-if="loading" class="loading"><div class="spinner"></div></div>

    <div v-else-if="tasks.length === 0" class="empty-state">
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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { dailyApi } from '@/api'
import { useAuthStore } from '@/stores'
import type { ReviewTask } from '@/types'

const auth = useAuthStore()
const loading = ref(true)
const tasks = ref<ReviewTask[]>([])

const stageColors: Record<number, string> = {
  0: '#9E9E9E', 1: '#F44336', 2: '#FF9800',
  3: '#FFC107', 4: '#4CAF50', 5: '#2196F3',
}

onMounted(loadData)

async function loadData() {
  loading.value = true
  try {
    const { data } = await dailyApi.getReviewTasks(auth.currentUserId)
    tasks.value = data.tasks || []
  } catch { tasks.value = [] }
  loading.value = false
}
</script>

<style scoped>
.task-list { padding: 8px 16px; }
.task-item { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
.task-avatar {
  width: 44px; height: 44px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  color: white; font-weight: 700; font-size: 14px; flex-shrink: 0;
}
.task-info { flex: 1; }
.task-title { font-weight: 600; font-size: 15px; }
.task-meta { font-size: 13px; color: var(--on-surface-variant); margin-top: 2px; }
</style>
