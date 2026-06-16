<template>
  <view class="page-container">
    <view class="nav-bar">
      <view class="nav-left"></view>
      <text class="nav-title">打卡</text>
      <view class="nav-right">
        <view class="nav-avatar" @tap="navTo('/pages/preference/index')">
          <text>{{ usernameInitial }}</text>
        </view>
      </view>
    </view>

    <view v-if="loading" class="loading">
      <view class="spinner"></view>
    </view>

    <view v-else>
      <!-- 核心打卡区 -->
      <view class="checkin-hero">
        <view class="checkin-streak">
          <text class="checkin-streak-num">{{ calendar?.current_streak_days || 0 }}</text>
          <text class="checkin-streak-label">连续打卡天数</text>
        </view>
        <button
          class="btn btn-lg checkin-btn"
          :class="todayChecked ? 'btn-success' : 'btn-primary'"
          :disabled="checking || todayChecked"
          @tap="handleCheckin"
        >
          <text>{{ checking ? '打卡中...' : (todayChecked ? '今日已完成 ✓' : '今日打卡') }}</text>
        </button>
        <text class="checkin-points">打卡奖励 +10 积分</text>
      </view>

      <!-- 统计 -->
      <view class="stats-banner">
        <view class="stat-item">
          <text class="stat-icon">📅</text>
          <text class="stat-value">{{ checkedDays }}</text>
          <text class="stat-label">本月打卡</text>
        </view>
        <view class="stat-item">
          <text class="stat-icon">⭐</text>
          <text class="stat-value">{{ calendar?.available_points || 0 }}</text>
          <text class="stat-label">积分余额</text>
        </view>
      </view>

      <!-- 日历热力图 -->
      <view class="card calendar-card">
        <view class="calendar-header">
          <view class="btn-icon month-btn" @tap="changeMonth(-1)"><text>‹</text></view>
          <text class="month-title">{{ currentYear }}年{{ currentMonth }}月</text>
          <view class="btn-icon month-btn" @tap="changeMonth(1)"><text>›</text></view>
        </view>
        <view class="calendar-grid">
          <text v-for="d in ['日','一','二','三','四','五','六']" :key="d" class="weekday">{{ d }}</text>
          <view v-for="(day, idx) in calendarDays" :key="idx" class="day-cell" :class="getDayClass(day)">
            <text v-if="day" class="day-num">{{ day }}</text>
            <text v-if="day && isChecked(day)" class="check-mark">✓</text>
          </view>
        </view>
      </view>

      <!-- 打卡成功提示 -->
      <view v-if="showSuccess && checkinResult" class="checkin-success">
        <text class="checkin-success-title">🎉 打卡成功！</text>
        <text class="checkin-success-msg">获得 +{{ checkinResult.earned_points }} 积分</text>
      </view>

      <!-- 入口 -->
      <view class="checkin-links">
        <button class="btn btn-outline" @tap="goWeekly">
          <text>📊 查看本周周报</text>
        </button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { checkinApi } from '@/api'
import { useAuthStore } from '@/stores'
import { navTo } from '@/utils/router'
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
  const now = new Date()
  const today = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
  return calendar.value?.checked_dates?.includes(today) || false
})

const usernameInitial = computed(() => (auth.username?.[0] || '?').toUpperCase())

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
  const now = new Date()
  return day === now.getDate() && currentMonth.value === now.getMonth() + 1 && currentYear.value === now.getFullYear()
}
function getDayClass(day: number | null) {
  if (!day) return 'empty'
  const classes: string[] = []
  if (isToday(day)) classes.push('is-today')
  if (isChecked(day)) classes.push('is-checked')
  return classes.join(' ')
}
function changeMonth(delta: number) {
  currentMonth.value += delta
  if (currentMonth.value > 12) { currentMonth.value = 1; currentYear.value++ }
  if (currentMonth.value < 1) { currentMonth.value = 12; currentYear.value-- }
  loadCalendar()
}

async function loadData() { loading.value = true; await loadCalendar(); loading.value = false }
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
    checkinResult.value = { completed_count: data.checkin.completed_count, earned_points: data.checkin.earned_points }
    showSuccess.value = true
    setTimeout(() => { showSuccess.value = false }, 3000)
  } catch { uni.showToast({ title: '打卡失败', icon: 'none' }) }
  checking.value = false
}

function goWeekly() { navTo('/pages/weekly/index') }
onShow(loadData)
</script>

<style scoped>
.checkin-hero {
  text-align: center;
  padding: 48rpx 32rpx 32rpx;
  background: linear-gradient(180deg, var(--primary-container) 0%, transparent 100%);
  margin-bottom: 8rpx;
}
.checkin-streak-num {
  font-size: 72rpx; font-weight: 800; color: var(--primary); display: block;
}
.checkin-streak-label {
  font-size: 26rpx; color: var(--on-surface-variant); margin-top: 8rpx; display: block;
}
.checkin-btn {
  margin-top: 32rpx; min-width: 400rpx;
}
.checkin-points {
  display: block; font-size: 24rpx; color: var(--on-surface-variant); margin-top: 16rpx;
}

.calendar-card { margin: 0 0 24rpx; padding: 28rpx; }
.calendar-header {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 24rpx;
}
.month-title { font-size: 30rpx; font-weight: 700; }

.calendar-grid {
  display: grid; grid-template-columns: repeat(7, 1fr);
  gap: 8rpx; text-align: center;
}
.weekday { font-size: 22rpx; color: var(--on-surface-variant); padding: 12rpx 0; font-weight: 600; }
.day-cell {
  aspect-ratio: 1; display: flex; align-items: center; justify-content: center;
  border-radius: 24rpx; font-size: 26rpx; position: relative;
}
.day-cell.empty { visibility: hidden; }
.day-cell.is-today {
  background: #F5E6C8; color: #8B7355; font-weight: 700;
}
.day-cell.is-checked {
  background: linear-gradient(135deg, #D0E8ED 0%, #B9D7DD 100%);
  color: #4A8A98; font-weight: 700;
}
.day-num { position: relative; z-index: 2; }
.check-mark {
  position: absolute; bottom: 4rpx; right: 8rpx;
  font-size: 18rpx; opacity: 0.7; color: var(--primary);
}

.checkin-success {
  margin: 0 0 24rpx; padding: 32rpx;
  background: var(--success-container); border-radius: 20rpx; text-align: center;
}
.checkin-success-title { font-size: 32rpx; font-weight: 700; margin-bottom: 8rpx; display: block; color: var(--success); }
.checkin-success-msg { font-size: 26rpx; display: block; color: var(--success); }

.checkin-links { padding: 0 0 48rpx; }
</style>
