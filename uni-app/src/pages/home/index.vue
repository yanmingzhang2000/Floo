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
        <svg class="book-svg" viewBox="0 0 400 320" fill="none" xmlns="http://www.w3.org/2000/svg">
          <!-- 左页 -->
          <path d="M200 280 L200 100 Q160 80 80 90 L80 270 Q160 260 200 280Z" fill="#D0E8ED" stroke="#5B9AA8" stroke-width="2"/>
          <path d="M100 120 L180 112" stroke="#5B9AA8" stroke-width="1.5" opacity="0.5"/>
          <path d="M100 145 L175 138" stroke="#5B9AA8" stroke-width="1.5" opacity="0.4"/>
          <path d="M100 170 L170 164" stroke="#5B9AA8" stroke-width="1.5" opacity="0.3"/>
          <!-- 右页 -->
          <path d="M200 280 L200 100 Q240 80 320 90 L320 270 Q240 260 200 280Z" fill="#E4F0F3" stroke="#5B9AA8" stroke-width="2"/>
          <path d="M220 120 L300 128" stroke="#5B9AA8" stroke-width="1.5" opacity="0.5"/>
          <path d="M220 145 L295 152" stroke="#5B9AA8" stroke-width="1.5" opacity="0.4"/>
          <path d="M220 170 L290 176" stroke="#5B9AA8" stroke-width="1.5" opacity="0.3"/>
          <!-- 银河旋涡 -->
          <ellipse cx="200" cy="160" rx="55" ry="20" fill="none" stroke="#5B9AA8" stroke-width="1.5" transform="rotate(-20 200 160)" opacity="0.6"/>
          <ellipse cx="200" cy="160" rx="38" ry="14" fill="none" stroke="#7FB3BE" stroke-width="1.2" transform="rotate(-20 200 160)" opacity="0.5"/>
          <ellipse cx="200" cy="160" rx="20" ry="8" fill="#D0E8ED" stroke="#5B9AA8" stroke-width="1" transform="rotate(-20 200 160)"/>
          <!-- 地球 -->
          <circle cx="290" cy="130" r="28" fill="#D0E8ED" stroke="#5B9AA8" stroke-width="2"/>
          <path d="M270 130 Q280 115 295 120 Q310 125 305 140 Q295 150 280 145 Q272 138 270 130Z" fill="#5B9AA8" opacity="0.3"/>
          <!-- 星星 -->
          <path d="M150 105 L153 112 L160 112 L154 117 L156 124 L150 120 L144 124 L146 117 L140 112 L147 112Z" fill="#5B9AA8" opacity="0.7"/>
          <path d="M260 95 L262 100 L267 100 L263 103 L264 108 L260 105 L256 108 L257 103 L253 100 L258 100Z" fill="#5B9AA8" opacity="0.5"/>
          <path d="M130 140 L132 145 L137 145 L133 148 L134 153 L130 150 L126 153 L127 148 L123 145 L128 145Z" fill="#7FB3BE" opacity="0.6"/>
          <!-- 山川 -->
          <path d="M120 250 L155 195 L175 215 L200 180 L225 210 L245 195 L280 250Z" fill="none" stroke="#5B9AA8" stroke-width="2" opacity="0.6"/>
          <path d="M140 250 L170 205 L190 225 L210 200 L230 220 L260 250Z" fill="#D0E8ED" opacity="0.4"/>
          <!-- 波浪 -->
          <path d="M100 265 Q150 255 200 265 Q250 275 300 265" fill="none" stroke="#5B9AA8" stroke-width="2" opacity="0.5"/>
          <path d="M110 280 Q160 270 210 280 Q260 290 310 280" fill="none" stroke="#7FB3BE" stroke-width="1.5" opacity="0.4"/>
          <!-- 小蝴蝶 -->
          <path d="M310 160 Q318 150 325 158 Q318 155 310 160Z" fill="#5B9AA8" opacity="0.5"/>
          <path d="M310 160 Q318 170 325 162 Q318 165 310 160Z" fill="#7FB3BE" opacity="0.4"/>
        </svg>
      </view>

      <view class="bottom-card">
        <view class="cta-btn-group">
          <button class="cta-btn cta-btn-main" @tap="goLearning">
            <text class="cta-text cta-text-primary">开始学习</text>
          </button>
          <button class="cta-btn cta-btn-sub" @tap="goReviewLast" :disabled="!lastLearnedId">
            <text class="cta-text cta-text-muted">复习上次</text>
          </button>
        </view>
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
const lastLearnedId = ref<number | null>(null)

async function loadData() {
  loading.value = true
  const userId = auth.currentUserId
  const safe = (p: Promise<any>) => p.catch(() => null)

  const [contentRes, calendarRes, learnedRes] = await Promise.all([
    safe(dailyApi.getTodayList(userId)),
    safe(checkinApi.getCalendar(userId, new Date().getFullYear(), new Date().getMonth() + 1)),
    safe(dailyApi.getLearnedIds(userId)),
  ])

  if (contentRes?.data) contents.value = contentRes.data.contents || []
  if (calendarRes?.data) streakDays.value = calendarRes.data.current_streak_days || 0
  if (learnedRes?.data) {
    const ids = learnedRes.data.content_ids || []
    lastLearnedId.value = ids.length > 0 ? ids[0] : null
  }

  loading.value = false
}

function goLearning() {
  uni.switchTab({ url: '/pages/learning/index' })
}

function goReviewLast() {
  if (lastLearnedId.value) {
    navTo(`/pages/detail/index?id=${lastLearnedId.value}`)
  }
}

function goDetail(id: number) { navTo(`/pages/detail/index?id=${id}`) }
function goPreference() { navTo('/pages/preference/index') }
function goCheckin() { navTo('/pages/checkin/index') }
function goDictation() { uni.switchTab({ url: '/pages/review/index' }) }
function goCustom() {
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

.cta-btn-group {
  display: flex;
  gap: 16rpx;
}
.cta-btn {
  height: 96rpx;
  border: none;
  border-radius: 48rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.15s;
}
.cta-btn:active { transform: scale(0.97); }
.cta-btn-main {
  flex: 2;
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
  box-shadow: 0 8rpx 24rpx rgba(91,154,168,0.3);
}
.cta-btn-sub {
  flex: 1;
  background: var(--surface);
  border: 2rpx solid var(--outline-variant);
}
.cta-btn-sub[disabled] {
  opacity: 0.4;
}
.cta-text {
  font-size: 32rpx;
  font-weight: 700;
}
.cta-text-primary {
  color: #fff;
}
.cta-text-muted {
  color: var(--on-surface-variant);
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
