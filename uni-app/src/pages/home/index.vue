<template>
  <view class="page-container">
    <view class="nav-bar">
      <view class="nav-left">
        <text class="nav-logo">Floo!</text>
      </view>
      <view class="nav-right nav-right-row">
        <view class="nav-icon-btn" @tap="goPreference">
          <text>⚙️</text>
        </view>
        <view class="nav-user" v-if="auth.username">
          <text class="nav-username">{{ auth.username }}</text>
        </view>
      </view>
    </view>

    <view v-if="loading" class="loading">
      <view class="spinner"></view>
    </view>

    <scroll-view v-else class="home-scroll" scroll-y>
      <view class="hero-section">
        <text class="hero-label">ENGLISH FOR DAILY LIFE</text>
        <text class="hero-title-en">Read the world,</text>
        <text class="hero-title-en">one page at a time</text>
        <text class="hero-title-cn">用英语慢慢理解世界</text>
        <text class="hero-desc">通勤、午休、夜晚，把学习放进生活缝隙</text>
        <view class="hero-streak" v-if="streakDays > 0">
          <text class="streak-tag">🔥 已连续 {{ streakDays }} 天</text>
        </view>
      </view>

      <view class="illustration-area">
        <image
          src="/static/images/hero-book.png"
          mode="widthFix"
          class="hero-illustration"
        />
      </view>

      <view class="bottom-card">
        <button class="cta-btn" @tap="handleMainAction">
          <text class="cta-text">{{ contents.length > 0 ? '继续今日学习' : '开始今日学习' }}</text>
        </button>
        <view class="quick-grid" :class="{ expanded: showQuick }">
          <view class="quick-card" @tap="goDictation">
            <view class="quick-icon-wrap" style="background: #FFF3E0;">
              <text class="quick-icon" style="color: #E65100;">✍️</text>
            </view>
            <text class="quick-title">默写</text>
          </view>
          <view class="quick-card" @tap="goCustom">
            <view class="quick-icon-wrap" style="background: #E3F2FD;">
              <text class="quick-icon" style="color: #1565C0;">📝</text>
            </view>
            <text class="quick-title">自定义</text>
          </view>
          <view class="quick-card" @tap="goCheckin">
            <view class="quick-icon-wrap" style="background: #F3E5F5;">
              <text class="quick-icon" style="color: #7B1FA2;">📅</text>
            </view>
            <text class="quick-title">打卡</text>
          </view>
        </view>
      </view>

      <view style="height: 40rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { dailyApi, checkinApi } from '@/api'
import { useAuthStore } from '@/stores'
import { navTo } from '@/utils/router'
import { storage } from '@/utils/storage'
import type { LearningContent } from '@/types'

const auth = useAuthStore()
const loading = ref(true)
const contents = ref<LearningContent[]>([])
const streakDays = ref(0)
const showQuick = ref(false)

async function loadData() {
  loading.value = true
  const userId = auth.currentUserId
  const safe = (p: Promise<any>) => p.catch(() => null)

  const [contentRes, calendarRes] = await Promise.all([
    safe(dailyApi.getTodayList(userId)),
    safe(checkinApi.getCalendar(userId, new Date().getFullYear(), new Date().getMonth() + 1)),
  ])

  if (contentRes?.data) contents.value = contentRes.data.contents || []
  if (calendarRes?.data) streakDays.value = calendarRes.data.current_streak_days || 0

  loading.value = false
}

function handleMainAction() {
  if (contents.value.length > 0) {
    goDetail(contents.value[0].id)
  } else {
    showQuick.value = !showQuick.value
  }
}

function goDetail(id: number) { navTo(`/pages/detail/index?id=${id}`) }
function goPreference() { navTo('/pages/preference/index') }
function goCheckin() { navTo('/pages/checkin/index') }
// review 不再是 tab，用 navigateTo 打开
function goDictation() { uni.navigateTo({ url: '/pages/review/index' }) }
function goCustom() {
  // 图书馆是 tab；带上 storage 里的偏好 tab，让图书馆落地到"自定义文稿"分区
  storage.set('learning_active_tab', 'custom')
  uni.switchTab({ url: '/pages/learning/index' })
}

onShow(() => {
  loadData()
  showQuick.value = false
})
</script>

<style scoped>
.nav-logo {
  font-size: 38rpx;
  font-weight: 800;
  color: #fff;
  letter-spacing: -1rpx;
}

.nav-right-row {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.nav-icon-btn {
  width: 56rpx;
  height: 56rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32rpx;
  border-radius: 50%;
  background: rgba(255,255,255,0.15);
}
.nav-icon-btn:active { background: rgba(255,255,255,0.3); }

.nav-user {
  padding: 8rpx 20rpx;
  background: rgba(255,255,255,0.2);
  border-radius: 30rpx;
}
.nav-username {
  font-size: 26rpx;
  font-weight: 600;
  color: #fff;
}

.home-scroll { flex: 1; }

.hero-section {
  padding: 40rpx 40rpx 0;
}
.hero-label {
  font-size: 22rpx;
  letter-spacing: 4rpx;
  color: var(--on-surface-muted);
  font-weight: 500;
  display: block;
  margin-bottom: 32rpx;
}
.hero-title-en {
  font-size: 48rpx;
  font-weight: 700;
  color: var(--on-surface);
  line-height: 1.25;
  display: block;
}
.hero-title-cn {
  font-size: 40rpx;
  font-weight: 700;
  color: var(--on-surface);
  margin-top: 16rpx;
  display: block;
}
.hero-desc {
  font-size: 28rpx;
  color: var(--on-surface-variant);
  margin-top: 16rpx;
  line-height: 1.6;
  display: block;
}
.hero-streak {
  margin-top: 20rpx;
}
.streak-tag {
  font-size: 24rpx;
  font-weight: 600;
  color: var(--primary);
  background: var(--primary-container);
  padding: 8rpx 24rpx;
  border-radius: 30rpx;
  display: inline-block;
}

.illustration-area {
  display: flex;
  justify-content: center;
  padding: 20rpx 40rpx 0;
}
.book-svg {
  width: 100%;
  max-width: 600rpx;
  height: auto;
}

.bottom-card {
  margin: 24rpx 32rpx 0;
  background: #fff;
  border-radius: 28rpx;
  padding: 32rpx;
  box-shadow: 0 2rpx 16rpx rgba(91,154,168,0.1);
}

.cta-btn {
  width: 100%;
  height: 96rpx;
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
  border: none;
  border-radius: 48rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 24rpx rgba(91,154,168,0.3);
  transition: transform 0.15s;
}
.cta-btn:active { transform: scale(0.97); }
.cta-text {
  font-size: 32rpx;
  font-weight: 700;
  color: #fff;
}

.quick-grid {
  display: flex;
  gap: 16rpx;
  margin-top: 0;
  max-height: 0;
  overflow: hidden;
  opacity: 0;
  transition: max-height 0.35s ease, opacity 0.3s ease, margin-top 0.3s ease;
}
.quick-grid.expanded {
  max-height: 300rpx;
  opacity: 1;
  margin-top: 24rpx;
}

.quick-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12rpx;
  padding: 24rpx 0;
  background: var(--surface);
  border-radius: 20rpx;
  transition: transform 0.15s;
}
.quick-card:active { transform: scale(0.96); }
.quick-icon-wrap {
  width: 72rpx;
  height: 72rpx;
  border-radius: 18rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}
.quick-icon { font-size: 32rpx; }
.quick-title {
  font-size: 24rpx;
  font-weight: 600;
  color: var(--on-surface);
}
</style>
