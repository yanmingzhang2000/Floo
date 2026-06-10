<template>
  <div class="page-container checkin-page">
    <div class="page-header" style="background: linear-gradient(135deg, #FFB6C1 0%, #FFC0CB 50%, #FFD1DC 100%);">
      <h1 style="color:#D81B60">打卡日历</h1>
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
            <div class="day-inner">
              <span class="day-num" v-if="day">{{ day }}</span>
              <span v-if="day && isChecked(day)" class="check-candy">🍬</span>
              <span v-else-if="day && isToday(day)" class="today-dot"></span>
            </div>
          </div>
        </div>
      </div>

      <!-- 打卡按钮 -->
      <div style="padding:16px">
        <button class="btn-checkin" @click="handleCheckin" :disabled="checking || todayChecked">
          <span class="btn-checkin-inner" :class="{ 'btn-done': todayChecked }">
            {{ checking ? '打卡中...' : todayChecked ? '✓ 今日已打卡' : '✨ 今日打卡' }}
          </span>
        </button>
      </div>

      <!-- 打卡成功弹窗 -->
      <Teleport to="body">
        <Transition name="pop">
          <div v-if="showSuccess" class="success-overlay" @click.self="showSuccess = false">
            <div class="success-popup">
              <div class="success-candy">🎉</div>
              <div class="success-title">打卡成功！</div>
              <div class="success-stats">
                <div class="success-stat">
                  <span class="stat-num" style="color:#FF6B9D">{{ checkinResult?.completed_count || 0 }}</span>
                  <span class="stat-text">个内容</span>
                </div>
                <div class="success-divider">·</div>
                <div class="success-stat">
                  <span class="stat-num" style="color:#7C4DFF">+{{ checkinResult?.earned_points || 0 }}</span>
                  <span class="stat-text">积分</span>
                </div>
              </div>
              <div class="success-msg">你今天学习了 {{ checkinResult?.completed_count || 0 }} 个内容</div>
              <div class="success-encourage">你真棒！继续加油哦～ 💪</div>
              <button class="btn-close-popup" @click="showSuccess = false">好的</button>
            </div>
          </div>
        </Transition>
      </Teleport>

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
  const today = new Date()
  const isTodayFlag = isToday(day)
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
  } catch { /* ignore */ }
  checking.value = false
}
</script>

<style scoped>
.checkin-page {
  background: linear-gradient(180deg, #FFF5F7 0%, #FFF 100%);
  min-height: 100vh;
}

/* 统计横幅 */
.stats-banner {
  display: flex;
  justify-content: space-around;
  padding: 24px 16px;
  margin: 0 16px 16px;
  background: linear-gradient(135deg, #FFB6C1 0%, #FFC0CB 50%, #FFD1DC 100%);
  border-radius: 20px;
  box-shadow: 0 8px 24px rgba(255, 182, 193, 0.4);
}
.stat-item { text-align: center; }
.stat-icon { font-size: 28px; }
.stat-value { font-size: 28px; font-weight: 800; color: #D81B60; margin-top: 4px; }
.stat-label { font-size: 12px; color: #AD1457; font-weight: 500; }

/* 日历卡片 */
.calendar-card {
  margin: 0 16px 16px;
  border-radius: 20px;
  overflow: hidden;
  background: white;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}
.calendar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: linear-gradient(135deg, #E1BEE7 0%, #CE93D8 100%);
}
.month-btn {
  width: 36px; height: 36px;
  border: none;
  background: rgba(255,255,255,0.9);
  border-radius: 50%;
  font-size: 20px;
  cursor: pointer;
  color: #7B1FA2;
  font-weight: bold;
  transition: all 0.2s;
}
.month-btn:hover { background: white; transform: scale(1.1); }
.month-title { font-size: 16px; font-weight: 700; color: #7B1FA2; }

.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
  padding: 8px;
  text-align: center;
}
.weekday {
  font-size: 12px;
  color: #9E9E9E;
  padding: 8px 0;
  font-weight: 600;
}
.day-cell {
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  font-size: 14px;
  position: relative;
  transition: all 0.3s ease;
}
.day-cell.empty { visibility: hidden; }

.day-inner {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  position: relative;
}

/* 今天 - 糖果色高亮 */
.day-cell.is-today .day-inner {
  background: linear-gradient(135deg, #FFD54F 0%, #FFC107 100%);
  box-shadow: 0 4px 12px rgba(255, 193, 7, 0.4);
  animation: pulse 2s infinite;
}
.day-cell.is-today .day-num { color: #F57F17; font-weight: 700; }
.today-dot {
  width: 6px;
  height: 6px;
  background: #F57F17;
  border-radius: 50%;
  margin-top: 2px;
}

/* 已打卡 - 糖果翻开效果 */
.day-cell.is-checked .day-inner {
  background: linear-gradient(135deg, #A5D6A7 0%, #81C784 50%, #66BB6A 100%);
  box-shadow: 0 4px 12px rgba(102, 187, 106, 0.4);
  animation: flip-in 0.5s ease;
}
.day-cell.is-checked .day-num { color: white; font-weight: 700; }
.check-candy {
  font-size: 16px;
  animation: candy-bounce 1s ease infinite;
}

/* 未来日期 */
.day-cell.is-future { opacity: 0.4; }

/* 打卡按钮 */
.btn-checkin {
  width: 100%;
  padding: 0;
  border: none;
  background: none;
  cursor: pointer;
}
.btn-checkin-inner {
  display: block;
  width: 100%;
  padding: 18px 24px;
  background: linear-gradient(135deg, #FF8A80 0%, #FF5252 50%, #FF1744 100%);
  color: white;
  font-size: 18px;
  font-weight: 700;
  border-radius: 20px;
  box-shadow: 0 8px 24px rgba(255, 23, 68, 0.4);
  transition: all 0.3s ease;
}
.btn-checkin:not(:disabled) .btn-checkin-inner:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 28px rgba(255, 23, 68, 0.5);
}
.btn-checkin:not(:disabled) .btn-checkin-inner:active {
  transform: scale(0.98);
}
.btn-checkin:disabled .btn-checkin-inner {
  background: linear-gradient(135deg, #E0E0E0 0%, #BDBDBD 100%);
  box-shadow: none;
  color: #9E9E9E;
}
.btn-done {
  background: linear-gradient(135deg, #81C784 0%, #66BB6A 100%) !important;
  box-shadow: 0 8px 24px rgba(102, 187, 106, 0.4) !important;
}

/* 打卡成功弹窗 */
.success-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}
.success-popup {
  width: 100%;
  max-width: 320px;
  background: white;
  border-radius: 24px;
  padding: 32px 24px;
  text-align: center;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}
.success-candy { font-size: 64px; margin-bottom: 12px; }
.success-title {
  font-size: 24px;
  font-weight: 800;
  background: linear-gradient(135deg, #FF6B9D 0%, #7C4DFF 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 16px;
}
.success-stats {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-bottom: 16px;
  padding: 16px;
  background: linear-gradient(135deg, #FFF5F7 0%, #F3E5F5 100%);
  border-radius: 16px;
}
.success-stat { text-align: center; }
.stat-num { font-size: 28px; font-weight: 800; }
.stat-text { font-size: 12px; color: #757575; display: block; }
.success-divider { font-size: 24px; color: #E0E0E0; }
.success-msg { font-size: 14px; color: #616161; margin-bottom: 8px; }
.success-encourage {
  font-size: 16px;
  font-weight: 600;
  color: #FF6B9D;
  margin-bottom: 20px;
}
.btn-close-popup {
  width: 100%;
  padding: 14px;
  background: linear-gradient(135deg, #FF80AB 0%, #FF4081 100%);
  color: white;
  border: none;
  border-radius: 16px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-close-popup:hover { transform: scale(1.02); }

.weekly-link {
  display: block;
  text-align: center;
  color: #7C4DFF;
  text-decoration: none;
  font-weight: 600;
  padding: 12px 0;
}

/* 动画 */
@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.02); }
}

@keyframes flip-in {
  0% { transform: scale(0.8) rotateY(90deg); opacity: 0; }
  50% { transform: scale(1.1) rotateY(0deg); }
  100% { transform: scale(1) rotateY(0deg); opacity: 1; }
}

@keyframes candy-bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-3px); }
}

.pop-enter-active { animation: pop-in 0.4s ease; }
.pop-leave-active { animation: pop-in 0.3s ease reverse; }
@keyframes pop-in {
  0% { opacity: 0; transform: scale(0.8); }
  100% { opacity: 1; transform: scale(1); }
}
</style>
