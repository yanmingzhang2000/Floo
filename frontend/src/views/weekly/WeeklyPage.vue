<template>
  <div class="page-container">
    <div class="page-header">
      <button class="btn-back" @click="router.back()">← 返回</button>
      <h1>每周学习报告</h1>
    </div>

    <div v-if="loading" class="loading"><div class="spinner"></div></div>

    <div v-else-if="summary" class="weekly-content">
      <div class="card week-title">
        <span style="font-size:18px;font-weight:700">{{ summary.year_week }}周</span>
      </div>

      <div class="card points-card">
        <span style="font-size:24px">⭐</span>
        <span style="font-size:28px;font-weight:800;color:var(--primary)">{{ summary.total_earned_points }}</span>
        <span style="font-size:14px;color:var(--on-surface-variant)">本周获得积分</span>
      </div>

      <div class="stats-grid">
        <div class="card stat-card">
          <div class="stat-value">{{ summary.total_checkin_days }}/7</div>
          <div class="stat-label">打卡天数</div>
        </div>
        <div class="card stat-card">
          <div class="stat-value">{{ summary.total_learned_count }}</div>
          <div class="stat-label">学习篇数</div>
        </div>
        <div class="card stat-card">
          <div class="stat-value" :class="{ green: summary.avg_accuracy_rate >= 0.8, orange: summary.avg_accuracy_rate < 0.8 }">
            {{ (summary.avg_accuracy_rate * 100).toFixed(0) }}%
          </div>
          <div class="stat-label">平均准确率</div>
        </div>
      </div>

      <div class="card motivation-card">
        <p>{{ motivationText }}</p>
      </div>
    </div>

    <div v-else class="empty-state">
      <div class="icon">📊</div>
      <p>本周暂无学习数据</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { checkinApi } from '@/api'
import { useAuthStore } from '@/stores'
import type { WeeklySummary } from '@/types'

const router = useRouter()
const auth = useAuthStore()
const loading = ref(true)
const summary = ref<WeeklySummary | null>(null)

const motivationText = computed(() => {
  const days = summary.value?.total_checkin_days || 0
  if (days >= 7) return '完美！本周全勤打卡，继续保持！'
  if (days >= 5) return '很棒！坚持得不错，继续加油！'
  if (days >= 3) return '还不错，还有提升空间，下周再努力！'
  return '学习不太稳定，建议每天抽出一点时间哦~'
})

onMounted(async () => {
  try {
    const { data } = await checkinApi.getWeekly(auth.currentUserId)
    summary.value = data
  } catch { summary.value = null }
  loading.value = false
})
</script>

<style scoped>
.weekly-content { padding: 8px 0; }
.week-title { text-align: center; }

.points-card {
  display: flex;
  align-items: center;
  gap: 10px;
  justify-content: center;
  flex-direction: column;
  padding: 20px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  padding: 0 16px;
}

.stat-card { text-align: center; padding: 16px 8px; }
.stat-value { font-size: 22px; font-weight: 800; }
.stat-value.green { color: var(--success); }
.stat-value.orange { color: var(--warning); }
.stat-label { font-size: 12px; color: var(--on-surface-variant); margin-top: 4px; }

.motivation-card {
  margin: 16px;
  text-align: center;
  background: var(--primary-container);
  color: var(--on-primary-container);
}
.motivation-card p { font-size: 15px; font-weight: 500; }
</style>
