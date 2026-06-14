<template>
  <view class="page-container">
    <view class="page-header">
      <text class="title">打卡日历</text>
    </view>

    <view v-if="loading" class="loading">
      <view class="spinner"></view>
    </view>

    <view v-else>
      <view class="stats-banner">
        <view class="stat-item">
          <text class="stat-icon">🔥</text>
          <text class="stat-value">{{ calendar?.current_streak_days || 0 }}</text>
          <text class="stat-label">连续打卡</text>
        </view>
        <view class="stat-item">
          <text class="stat-icon">📅</text>
          <text class="stat-value">{{ checkedDays }}</text>
          <text class="stat-label">本月打卡</text>
        </view>
        <view class="stat-item">
          <text class="stat-icon">⭐</text>
          <text class="stat-value">{{ calendar?.available_points || 0 }}</text>
          <text class="stat-label">可用积分</text>
        </view>
      </view>

      <view class="card calendar-card">
        <view class="calendar-header">
          <view class="month-btn" @tap="changeMonth(-1)"><text>‹</text></view>
          <text class="month-title">{{ currentYear }}年{{ currentMonth }}月</text>
          <view class="month-btn" @tap="changeMonth(1)"><text>›</text></view>
        </view>
        <view class="calendar-grid">
          <text v-for="d in ['日','一','二','三','四','五','六']" :key="d" class="weekday">{{ d }}</text>
          <view
            v-for="(day, idx) in calendarDays"
            :key="idx"
            class="day-cell"
            :class="getDayClass(day)"
          >
            <text v-if="day" class="day-num">{{ day }}</text>
            <text v-if="day && isChecked(day)" class="check-mark">✓</text>
          </view>
        </view>
      </view>

      <view class="checkin-btn-wrap">
        <button
          class="btn btn-primary btn-block btn-lg"
          :disabled="checking || todayChecked"
          @tap="handleCheckin"
        >
          <text>{{ checking ? '打卡中...' : (todayChecked ? '今日已打卡 ✓' : '今日打卡') }}</text>
        </button>
      </view>

      <view v-if="showSuccess && checkinResult" class="checkin-success">
        <text class="success-title">🎉 打卡成功！</text>
        <text class="success-message">
          你今天学习了 {{ checkinResult.completed_count }} 个内容，获得了 +{{ checkinResult.earned_points }} 积分
        </text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
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
  const now = new Date()
  const today = `${now.getUTCFullYear()}-${String(now.getUTCMonth() + 1).padStart(2, '0')}-${String(now.getUTCDate()).padStart(2, '0')}`
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
  const now = new Date()
  return day === now.getUTCDate() && currentMonth.value === now.getUTCMonth() + 1 && currentYear.value === now.getUTCFullYear()
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

async function loadData() {
  loading.value = true
  await loadCalendar()
  loading.value = false
}

async function loadCalendar() {
  try {
    const { data } = await checkinApi.getCalendar(auth.currentUserId, currentYear.value, currentMonth.value)
    calendar.value = data
  } catch {
    calendar.value = null
  }
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
  } catch {
    uni.showToast({ title: '打卡失败', icon: 'none' })
  }
  checking.value = false
}

onShow(loadData)
</script>

<style scoped>
.page-header .title {
  font-size: 40rpx;
  font-weight: 700;
  color: white;
  display: block;
}

.stats-banner {
  display: flex;
  justify-content: space-around;
  padding: 40rpx 32rpx;
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
  color: white;
  margin-bottom: 24rpx;
}
.stat-item { text-align: center; }
.stat-icon { font-size: 48rpx; display: block; }
.stat-value { font-size: 48rpx; font-weight: 800; margin-top: 8rpx; display: block; }
.stat-label { font-size: 24rpx; opacity: 0.85; display: block; }

.calendar-card { margin: 0 24rpx 24rpx; padding: 28rpx; }
.calendar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24rpx;
}
.month-btn {
  width: 72rpx; height: 72rpx;
  background: var(--surface-container);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36rpx;
}
.month-title { font-size: 32rpx; font-weight: 700; }

.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 12rpx;
  text-align: center;
}
.weekday {
  font-size: 24rpx;
  color: var(--on-surface-variant);
  padding: 16rpx 0;
  font-weight: 600;
}

.day-cell {
  aspect-ratio: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 24rpx;
  font-size: 28rpx;
  position: relative;
}
.day-cell.empty { visibility: hidden; }
.day-cell.is-today {
  background: #F5E6C8;
  color: #8B7355;
  font-weight: 700;
}
.day-cell.is-checked {
  background: linear-gradient(135deg, #D0E8ED 0%, #B9D7DD 100%);
  color: #4A8A98;
  font-weight: 700;
}
.day-num { position: relative; z-index: 2; }
.check-mark {
  position: absolute;
  bottom: 8rpx;
  right: 8rpx;
  font-size: 20rpx;
  opacity: 0.6;
}

.checkin-btn-wrap { padding: 0 32rpx 24rpx; }
.checkin-success {
  margin: 0 32rpx 32rpx;
  padding: 32rpx;
  background: var(--surface-container);
  border-radius: 24rpx;
  text-align: center;
}
.success-title { font-size: 32rpx; font-weight: 700; margin-bottom: 16rpx; display: block; }
.success-message { font-size: 28rpx; color: var(--on-surface-variant); line-height: 1.6; display: block; }
</style>