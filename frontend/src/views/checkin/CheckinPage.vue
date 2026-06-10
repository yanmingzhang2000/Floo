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
          <div class="success-title">🎉 打卡成功！</div>
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

function isToday(day: number) {
  const today = new Date()
  return day === today.getDate() && currentMonth.value === today.getMonth() + 1 && currentYear.value === today.getFullYear()
}

function getDayClass(day: number | null) {
  if (!day) return 'empty'
  const isTodayFlag = isToday(day)
  const today = new Date()
  const isFuture = new Date(currentYear.value, currentMonth.value - 1, day) > today
  return {
    'is-today': isTodayFlag,
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
    checkinResult.value = {
      completed_count: data.checkin.completed_count,
      earned_points: data.checkin.earned_points,
    }
    showSuccess.value = true
    setTimeout(() => { showSuccess.value = false }, 3000)
  } catch { /* ignore */ }
  checking.value = false
}
</script>

<style scoped>
/* 统计横幅 */
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

/* 日历卡片 */
.calendar-card {
  margin: 0 16px 16px;
}
.calendar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.month-btn {
  width: 36px; height: 36px;
  border: none;
  background: var(--surface-container);
  border-radius: 50%;
  font-size: 18px;
  cursor: pointer;
}
.month-btn:hover { background: var(--primary-container); }
.month-title { font-size: 16px; font-weight: 700; }

.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
  text-align: center;
}
.weekday {
  font-size: 12px;
  color: var(--on-surface-variant);
  padding: 8px 0;
  font-weight: 600;
}

.day-cell {
  aspect-ratio: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  font-size: 14px;
  position: relative;
  transition: all 0.2s ease;
}
.day-cell.empty { visibility: hidden; }

/* 今天 - 莫兰迪鹅黄 */
.day-cell.is-today {
  background: #F5E6C8;
  color: #8B7355;
  font-weight: 700;
}

/* 已打卡 - 莫兰迪豆沙粉 */
.day-cell.is-checked {
  background: #E8C4C4;
  color: #8B6F6F;
}
.check-mark {
  font-size: 10px;
  position: absolute;
  bottom: 2px;
  color: #B5838D;
}

/* 未来日期 */
.day-cell.is-future { color: var(--outline); }

/* 打卡成功提示 */
.checkin-success {
  margin: 0 16px 16px;
  padding: 16px;
  background: #F5F5F5;
  border-radius: 12px;
  text-align: center;
}
.success-title { font-size: 16px; font-weight: 700; margin-bottom: 8px; }
.success-message { font-size: 14px; color: var(--on-surface-variant); line-height: 1.6; }
.success-encourage { font-size: 14px; font-weight: 600; color: var(--primary); margin-top: 8px; }

.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.weekly-link {
  display: block;
  text-align: center;
  color: var(--primary);
  text-decoration: none;
  font-weight: 600;
  padding: 8px 0;
}
</style>
