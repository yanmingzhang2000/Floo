<template>
  <div class="page-container">
    <div class="page-header">
      <h1>打卡日历</h1>
    </div>

    <div v-if="loading" class="loading"><div class="spinner"></div></div>

    <div v-else>
      <!-- 统计横幅 -->
      <div class="stats-banner">
        <div class="stat-item">
          <div class="stat-icon">🔥</div>
          <div class="stat-value">{{ calendar?.current_streak_days || 0 }}</div>
          <div class="stat-label">连续打卡</div>
        </div>
        <div class="stat-item">
          <div class="stat-icon">📅</div>
          <div class="stat-value">{{ checkedDays }}</div>
          <div class="stat-label">本月打卡</div>
        </div>
        <div class="stat-item">
          <div class="stat-icon">⭐</div>
          <div class="stat-value">{{ calendar?.available_points || 0 }}</div>
          <div class="stat-label">可用积分</div>
        </div>
      </div>

      <!-- 日历 -->
      <div class="card calendar-card">
        <div class="calendar-header">
          <button @click="changeMonth(-1)" class="month-btn">‹</button>
          <span class="month-title">{{ currentYear }}年{{ currentMonth }}月</span>
          <button @click="changeMonth(1)" class="month-btn">›</button>
        </div>
        <div class="calendar-grid">
          <div v-for="d in ['日','一','二','三','四','五','六']" :key="d" class="weekday">{{ d }}</div>
          <div v-for="(day, idx) in calendarDays" :key="idx" class="day-cell" :class="getDayClass(day)">
            <span v-if="day">{{ day }}</span>
            <span v-if="day && isChecked(day)" class="check-mark">✓</span>
          </div>
        </div>
      </div>

      <!-- 打卡按钮 -->
      <div style="padding:16px">
        <button class="btn btn-primary btn-block btn-lg" @click="handleCheckin" :disabled="checking || todayChecked">
          {{ checking ? '打卡中...' : todayChecked ? '今日已打卡 ✓' : '今日打卡' }}
        </button>
      </div>

      <!-- 打卡成功提示 -->
      <Transition name="fade">
        <div v-if="showSuccess && checkinResult" class="checkin-success">
          <div class="success-icon">🎉</div>
          <div class="success-title">打卡成功！</div>
          <div class="success-message">
            你今天学习了 <strong>{{ checkinResult.completed_count }}</strong> 个内容，获得了 <strong>+{{ checkinResult.earned_points }}</strong> 积分
          </div>
          <div class="success-encourage">你真棒！继续加油哦～</div>
        </div>
      </Transition>

      <div class="card" style="margin:0 16px 16px">
        <router-link to="/weekly" class="weekly-link">
          📊 查看每周学习报告 →
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { checkinApi } from '@/api'
import { useAuthStore } from '@/stores'
import type { CheckinCalendar } from '@/types'

const auth = useAuthStore()
const loading = ref(true)
const checking = ref(false)
const calendar = ref<CheckinCalendar | null>(null)
const currentYear = ref(new Date().getFullYear())
const currentMonth = ref(new Date().getMonth() + 1)
const checkinResult = ref<{ completed_count: number; earned_points: number } | null>(null)
const showSuccess = ref(false)

const checkedDays = computed(() => calendar.value?.checked_dates?.length || 0)
const todayChecked = computed(() => {
  const today = new Date().toISOString().slice(0, 10)
  return calendar.value?.checked_dates?.includes(today) || false
})

const calendarDays = computed(() => {
  const first = new Date(currentYear.value, currentMonth.value - 1, 1).getDay()
  const total = new Date(currentYear.value, currentMonth.value, 0).getDate()
  const days: (number | null)[] = []
  for (let i = 0; i < first; i++) days.push(null)
  for (let i = 1; i <= total; i++) days.push(i)
  return days
})

function isChecked(day: number) {
  const dateStr = `${currentYear.value}-${String(currentMonth.value).padStart(2, '0')}-${String(day).padStart(2, '0')}`
  return calendar.value?.checked_dates?.includes(dateStr)
}

function getDayClass(day: number | null) {
  if (!day) return 'empty'
  const today = new Date()
  const isToday = day === today.getDate() && currentMonth.value === today.getMonth() + 1 && currentYear.value === today.getFullYear()
  const isFuture = new Date(currentYear.value, currentMonth.value - 1, day) > today
  return {
    'is-today': isToday,
    'is-checked': isChecked(day),
    'is-future': isFuture,
  }
}

function changeMonth(delta: number) {
  currentMonth.value += delta
  if (currentMonth.value > 12) { currentMonth.value = 1; currentYear.value++ }
  if (currentMonth.value < 1) { currentMonth.value = 12; currentYear.value-- }
  loadCalendar()
}

onMounted(loadData)

async function loadData() {
  loading.value = true
  await loadCalendar()
  loading.value = false
}

async function loadCalendar() {
  try {
    const { data } = await checkinApi.getCalendar(auth.currentUserId, currentYear.value, currentMonth.value)
    calendar.value = data
  } catch { calendar.value = null }
}

async function handleCheckin() {
  checking.value = true
  try {
    const { data } = await checkinApi.doCheckin(auth.currentUserId)
    await loadCalendar()
    // 显示成功提示
    checkinResult.value = {
      completed_count: data.checkin.completed_count,
      earned_points: data.checkin.earned_points,
    }
    showSuccess.value = true
    // 3秒后自动关闭
    setTimeout(() => { showSuccess.value = false }, 3000)
  } catch { /* ignore */ }
  checking.value = false
}
</script>

<style scoped>
.stats-banner {
  display: flex;
  justify-content: space-around;
  padding: 20px 16px;
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
  color: white;
}
.stat-item { text-align: center; }
.stat-icon { font-size: 24px; }
.stat-value { font-size: 24px; font-weight: 800; margin-top: 4px; }
.stat-label { font-size: 12px; opacity: 0.85; }

.calendar-card { margin: 16px; }
.calendar-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.month-btn {
  width: 36px; height: 36px; border: none; background: var(--surface-container);
  border-radius: 50%; font-size: 18px; cursor: pointer; display: flex; align-items: center; justify-content: center;
}
.month-btn:hover { background: var(--primary-container); }
.month-title { font-size: 16px; font-weight: 700; }

.calendar-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px; text-align: center; }
.weekday { font-size: 12px; color: var(--on-surface-variant); padding: 8px 0; font-weight: 600; }
.day-cell {
  aspect-ratio: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: 14px;
  position: relative;
}
.day-cell.empty { visibility: hidden; }
.day-cell.is-today { background: var(--primary-container); color: var(--primary); font-weight: 700; }
.day-cell.is-checked { background: var(--primary); color: white; }
.day-cell.is-future { color: var(--outline); }
.check-mark { font-size: 10px; position: absolute; bottom: 2px; }

.weekly-link {
  display: block;
  text-align: center;
  color: var(--primary);
  text-decoration: none;
  font-weight: 600;
  padding: 8px 0;
}

/* 打卡成功提示 */
.checkin-success {
  margin: 0 16px 16px;
  padding: 20px;
  background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
  border-radius: 16px;
  text-align: center;
  animation: bounce-in 0.5s ease;
}
.success-icon { font-size: 48px; margin-bottom: 8px; }
.success-title { font-size: 20px; font-weight: 700; color: var(--success); margin-bottom: 8px; }
.success-message { font-size: 15px; color: #2E7D32; line-height: 1.6; }
.success-encourage { font-size: 16px; font-weight: 600; color: var(--success); margin-top: 12px; }

.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

@keyframes bounce-in {
  0% { transform: scale(0.8); opacity: 0; }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); opacity: 1; }
}
</style>
