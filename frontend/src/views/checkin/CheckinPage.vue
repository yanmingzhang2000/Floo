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
            <span v-if="day" class="day-num">{{ day }}</span>
            <span v-if="day && isChecked(day)" class="check-pattern" :class="getPatternClass(day)"></span>
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

// 莫兰迪色系 - 7种颜色用于连续打卡
const morandiColors = [
  { bg: '#E8C4C4', accent: '#B5838D' },  // 豆沙粉
  { bg: '#D4C5B9', accent: '#A39285' },  // 奶茶色
  { bg: '#C9D6DF', accent: '#7E9AAF' },  // 雾霾蓝
  { bg: '#D5C9D1', accent: '#9E8EA0' },  // 藤紫
  { bg: '#C8D5BB', accent: '#8FA87A' },  // 抹茶绿
  { bg: '#E2D1C3', accent: '#B5A48D' },  // 杏仁色
  { bg: '#D1C4D9', accent: '#9575CD' },  // 淡紫
]

// 暗纹图案
const patterns = ['candy', 'star', 'flower', 'heart', 'dot', 'grid']

// 为每个日期生成固定的随机种子（基于日期字符串）
function getDaySeed(day: number): number {
  const dateStr = `${currentYear.value}-${currentMonth.value}-${day}`
  let hash = 0
  for (let i = 0; i < dateStr.length; i++) {
    hash = ((hash << 5) - hash) + dateStr.charCodeAt(i)
    hash |= 0
  }
  return Math.abs(hash)
}

// 获取打卡的连续天数（用于颜色分配）
function getCheckedStreak(day: number): number {
  if (!calendar.value?.checked_dates) return 0
  const today = new Date()
  const todayDate = today.getDate()
  const currentMonthNum = today.getMonth() + 1
  const currentYearNum = today.getFullYear()
  
  // 如果不是当月，返回0
  if (currentMonth.value !== currentMonthNum || currentYear.value !== currentYearNum) {
    return calendar.value.checked_dates.includes(
      `${currentYear.value}-${String(currentMonth.value).padStart(2, '0')}-${String(day).padStart(2, '0')}`
    ) ? 1 : 0
  }
  
  // 计算从今天往前的连续打卡天数
  let streak = 0
  for (let d = todayDate; d >= 1; d--) {
    const dateStr = `${currentYear.value}-${String(currentMonth.value).padStart(2, '0')}-${String(d).padStart(2, '0')}`
    if (calendar.value.checked_dates.includes(dateStr)) {
      streak++
    } else {
      break
    }
  }
  
  // 如果点击的日期在连续区间内，返回对应的颜色索引
  if (day <= todayDate && day > todayDate - streak) {
    return todayDate - day + 1
  }
  return 0
}

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
  
  // 获取连续打卡的颜色索引
  const streak = getCheckedStreak(day)
  const colorIndex = streak > 0 ? (streak - 1) % morandiColors.length : -1
  
  return {
    'is-today': isTodayFlag,
    'is-checked': isChecked(day),
    'is-future': isFuture,
    [`color-${colorIndex}`]: colorIndex >= 0,
  }
}

function getPatternClass(day: number): string {
  const seed = getDaySeed(day)
  return `pattern-${patterns[seed % patterns.length]}`
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
  gap: 6px;
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
  border-radius: 14px;
  font-size: 14px;
  position: relative;
  transition: all 0.2s ease;
  overflow: hidden;
}
.day-cell.empty { visibility: hidden; }

.day-num {
  position: relative;
  z-index: 2;
}

/* 今天 */
.day-cell.is-today {
  background: #F5E6C8;
  color: #8B7355;
  font-weight: 700;
  box-shadow: inset 0 0 0 2px #D4C4A8;
}

/* 已打卡 - 莫兰迪渐变色 */
.day-cell.is-checked {
  box-shadow: inset 0 0 0 2px rgba(255,255,255,0.5);
}

/* 7种莫兰迪打卡颜色 */
.day-cell.color-0 { background: linear-gradient(135deg, #E8C4C4 0%, #D4A5A5 100%); color: #8B6F6F; }
.day-cell.color-1 { background: linear-gradient(135deg, #D4C5B9 0%, #C4B5A9 100%); color: #7A6E62; }
.day-cell.color-2 { background: linear-gradient(135deg, #C9D6DF 0%, #B9C6CF 100%); color: #5E7A8A; }
.day-cell.color-3 { background: linear-gradient(135deg, #D5C9D1 0%, #C5B9C1 100%); color: #7A6E78; }
.day-cell.color-4 { background: linear-gradient(135deg, #C8D5BB 0%, #B8C5AB 100%); color: #6A7A5A; }
.day-cell.color-5 { background: linear-gradient(135deg, #E2D1C3 0%, #D2C1B3 100%); color: #8A7A6A; }
.day-cell.color-6 { background: linear-gradient(135deg, #D1C4D9 0%, #C1B4C9 100%); color: #7A6A8A; }

/* 暗纹图案 */
.check-pattern {
  position: absolute;
  inset: 0;
  opacity: 0.3;
  pointer-events: none;
}

/* 小糖果 */
.pattern-candy::before {
  content: '🍬';
  position: absolute;
  font-size: 14px;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

/* 小星星 */
.pattern-star::before {
  content: '✦';
  position: absolute;
  font-size: 18px;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: inherit;
}

/* 小花朵 */
.pattern-flower::before {
  content: '✿';
  position: absolute;
  font-size: 16px;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: inherit;
}

/* 小爱心 */
.pattern-heart::before {
  content: '♡';
  position: absolute;
  font-size: 16px;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: inherit;
}

/* 小圆点 */
.pattern-dot::before {
  content: '';
  position: absolute;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: currentColor;
  opacity: 0.4;
}

/* 格子纹 */
.pattern-grid::before {
  content: '';
  position: absolute;
  inset: 4px;
  border: 1.5px dashed currentColor;
  border-radius: 8px;
  opacity: 0.3;
}

/* 未来日期 */
.day-cell.is-future { color: var(--outline); opacity: 0.5; }

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
