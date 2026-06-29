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
        <view class="points-badge" @tap="goShop">
          <text class="points-icon">⭐</text>
          <text class="points-num">{{ pointBalance }}</text>
        </view>
      </view>
    </view>

    <view v-if="loading" class="loading">
      <view class="spinner"></view>
    </view>

    <scroll-view v-else class="home-scroll" scroll-y>
      <!-- 激励横幅 -->
      <view class="hero-banner">
        <view class="hero-greeting">
          <text class="hero-hi">Hi{{ auth.username ? ', ' + auth.username : '' }} 👋</text>
        </view>
        <view class="hero-streak" v-if="streakDays > 0">
          <text class="streak-num">{{ streakDays }}</text>
          <view class="streak-text">
            <text class="streak-label">连续学习天数</text>
            <text class="streak-motivation">{{ streakMessage }}</text>
          </view>
        </view>
        <view class="hero-streak" v-else>
          <text class="streak-zero">开始你的第一天学习吧</text>
        </view>
      </view>

      <!-- 主行动按钮 -->
      <view class="cta-section">
        <button class="cta-btn" @tap="handleMainAction">
          <view class="cta-content">
            <text class="cta-icon">{{ contents.length > 0 ? '📖' : '✨' }}</text>
            <view class="cta-text-wrap">
              <text class="cta-title">{{ contents.length > 0 ? '继续今日学习' : 'AI 生成今日内容' }}</text>
              <text class="cta-sub" v-if="contents.length > 0">你有 {{ contents.length }} 篇文章待学习</text>
              <text class="cta-sub" v-else-if="remainingCount > 0">还能生成 {{ remainingCount }} 次</text>
              <text class="cta-sub" v-else>今日次数已用完</text>
            </view>
            <text class="cta-arrow">›</text>
          </view>
        </button>
      </view>

      <!-- 快捷入口 -->
      <view class="quick-grid">
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
        <view class="quick-card" @tap="goBooks">
          <view class="quick-icon-wrap" style="background: #E8F5E9;">
            <text class="quick-icon" style="color: #2E7D32;">📚</text>
          </view>
          <text class="quick-title">名著</text>
        </view>
        <view class="quick-card" @tap="goCheckin">
          <view class="quick-icon-wrap" style="background: #F3E5F5;">
            <text class="quick-icon" style="color: #7B1FA2;">📅</text>
          </view>
          <text class="quick-title">打卡</text>
        </view>
      </view>

      <!-- 最近学习 -->
      <view class="section" v-if="contents.length > 0">
        <view class="section-header">
          <text class="section-title">最近学习</text>
          <text class="section-more" @tap="goLearningList">查看全部 ›</text>
        </view>
        <view class="recent-list">
          <view
            v-for="item in recentContents"
            :key="item.id"
            class="recent-card"
            @tap="goDetail(item.id)"
          >
            <view class="recent-left">
              <view class="recent-tag-row">
                <text class="recent-tag">{{ themeLabels[item.theme_type] || item.theme_type }}</text>
                <text class="recent-status" :class="learnedIds.includes(item.id) ? 'done' : 'todo'">
                  {{ learnedIds.includes(item.id) ? '✅已学' : '未学' }}
                </text>
              </view>
              <text class="recent-title">{{ item.title }}</text>
              <text class="recent-desc">{{ item.article?.slice(0, 50) }}...</text>
            </view>
            <text class="recent-arrow">›</text>
          </view>
        </view>
      </view>

      <!-- 空状态 -->
      <view v-if="contents.length === 0 && !loading" class="empty-hint">
        <text class="empty-hint-text">点击上方按钮开始今天的学习</text>
      </view>

      <view style="height: 40rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { dailyApi, checkinApi, shopApi, generationLimitApi } from '@/api'
import { useAuthStore } from '@/stores'
import { navTo } from '@/utils/router'
import { storage } from '@/utils/storage'
import type { LearningContent } from '@/types'

const auth = useAuthStore()
const loading = ref(true)
const contents = ref<LearningContent[]>([])
const learnedIds = ref<number[]>([])
const streakDays = ref(0)
const pointBalance = ref(0)
const remainingCount = ref(3)

const themeLabels: Record<string, string> = {
  ai_tech: 'AI科技', product_tech: '产品技术', business: '财经商业',
  daily_news: '日常新闻', self_growth: '个人成长', all_random: '随机',
}

const recentContents = computed(() => contents.value.slice(0, 5))

const streakMessage = computed(() => {
  const d = streakDays.value
  if (d >= 30) return '太厉害了，坚持一个月！'
  if (d >= 14) return '两周不断，你很棒！'
  if (d >= 7) return '一周达成，继续加油！'
  if (d >= 3) return '三天了，习惯正在养成'
  if (d >= 1) return '保持住，别断了'
  return '开始第一天'
})

async function loadData() {
  loading.value = true
  const userId = auth.currentUserId
  const safe = (p: Promise<any>) => p.catch(() => null)

  const [contentRes, limitRes, learnedRes, calendarRes, balanceRes] = await Promise.all([
    safe(dailyApi.getTodayList(userId)),
    safe(generationLimitApi.getLimit(userId)),
    safe(dailyApi.getLearnedIds(userId)),
    safe(checkinApi.getCalendar(userId, new Date().getFullYear(), new Date().getMonth() + 1)),
    safe(shopApi.getBalance(userId)),
  ])

  if (contentRes?.data) contents.value = contentRes.data.contents || []
  if (learnedRes?.data) learnedIds.value = learnedRes.data.content_ids || []
  if (limitRes?.data) remainingCount.value = limitRes.data.remaining_count ?? 3
  if (calendarRes?.data) streakDays.value = calendarRes.data.current_streak_days || 0
  if (balanceRes?.data) pointBalance.value = balanceRes.data.available_points || 0

  loading.value = false
}

function handleMainAction() {
  if (contents.value.length > 0) {
    goDetail(contents.value[0].id)
  } else {
    uni.switchTab({ url: '/pages/learning/index' })
  }
}

function goDetail(id: number) { navTo(`/pages/detail/index?id=${id}`) }
function goLearningList() { navTo('/pages/list/index') }
function goPreference() { navTo('/pages/preference/index') }
function goShop() { navTo('/pages/shop/index') }
function goCheckin() { navTo('/pages/checkin/index') }
function goDictation() { uni.switchTab({ url: '/pages/review/index' }) }
function goCustom() {
  storage.set('learning_active_tab', 'custom')
  uni.switchTab({ url: '/pages/learning/index' })
}
function goBooks() {
  storage.set('learning_active_tab', 'books')
  uni.switchTab({ url: '/pages/learning/index' })
}

onShow(loadData)
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

.points-badge {
  display: flex;
  align-items: center;
  gap: 6rpx;
  padding: 10rpx 20rpx;
  background: rgba(255,255,255,0.2);
  border-radius: 40rpx;
  backdrop-filter: blur(10px);
}
.points-badge:active { background: rgba(255,255,255,0.35); }
.points-icon { font-size: 24rpx; }
.points-num { font-size: 26rpx; font-weight: 700; color: #fff; }

.home-scroll { flex: 1; }

/* 激励横幅 */
.hero-banner {
  padding: 32rpx 32rpx 24rpx;
}
.hero-hi {
  font-size: 32rpx;
  color: var(--on-surface-variant);
  display: block;
}
.hero-streak {
  display: flex;
  align-items: center;
  gap: 20rpx;
  margin-top: 16rpx;
}
.streak-num {
  font-size: 64rpx;
  font-weight: 800;
  color: var(--primary);
  line-height: 1;
}
.streak-text { flex: 1; }
.streak-label {
  font-size: 26rpx;
  color: var(--on-surface-variant);
  display: block;
}
.streak-motivation {
  font-size: 28rpx;
  font-weight: 600;
  color: var(--on-surface);
  margin-top: 4rpx;
  display: block;
}
.streak-zero {
  font-size: 30rpx;
  font-weight: 600;
  color: var(--primary);
}

/* 主行动按钮 */
.cta-section {
  padding: 0 24rpx 20rpx;
}
.cta-btn {
  width: 100%;
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
  border: none;
  border-radius: 24rpx;
  padding: 0;
  box-shadow: 0 8rpx 24rpx rgba(91,154,168,0.3);
  transition: transform 0.15s, box-shadow 0.15s;
}
.cta-btn:active {
  transform: scale(0.98);
  box-shadow: 0 4rpx 12rpx rgba(91,154,168,0.2);
}
.cta-content {
  display: flex;
  align-items: center;
  padding: 32rpx;
  gap: 20rpx;
}
.cta-icon { font-size: 48rpx; }
.cta-text-wrap { flex: 1; text-align: left; }
.cta-title {
  font-size: 32rpx;
  font-weight: 700;
  color: #fff;
  display: block;
}
.cta-sub {
  font-size: 24rpx;
  color: rgba(255,255,255,0.8);
  margin-top: 4rpx;
  display: block;
}
.cta-arrow {
  font-size: 40rpx;
  color: rgba(255,255,255,0.7);
  font-weight: 300;
}

/* 快捷入口 */
.quick-grid {
  display: flex;
  padding: 0 24rpx 20rpx;
  gap: 16rpx;
}
.quick-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12rpx;
  padding: 24rpx 0;
  background: #fff;
  border-radius: 20rpx;
  box-shadow: var(--shadow-sm);
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

/* 最近学习 */
.section {
  padding: 8rpx 24rpx 0;
}
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16rpx;
}
.section-title {
  font-size: 30rpx;
  font-weight: 700;
  color: var(--on-surface);
}
.section-more {
  font-size: 24rpx;
  color: var(--primary);
  font-weight: 500;
}
.section-more:active { opacity: 0.6; }

.recent-list {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}
.recent-card {
  display: flex;
  align-items: center;
  background: #fff;
  border-radius: 20rpx;
  padding: 24rpx;
  box-shadow: var(--shadow-sm);
  transition: transform 0.15s;
}
.recent-card:active { transform: scale(0.98); }
.recent-left { flex: 1; min-width: 0; }
.recent-tag-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-bottom: 8rpx;
}
.recent-tag {
  font-size: 20rpx;
  padding: 4rpx 14rpx;
  border-radius: 20rpx;
  font-weight: 600;
  background: var(--primary-container);
  color: var(--on-primary-container);
}
.recent-status { font-size: 20rpx; }
.recent-status.done { color: var(--success); font-weight: 600; }
.recent-status.todo { color: var(--on-surface-muted); }
.recent-title {
  font-size: 28rpx;
  font-weight: 700;
  color: var(--on-surface);
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.recent-desc {
  font-size: 24rpx;
  color: var(--on-surface-variant);
  margin-top: 4rpx;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.recent-arrow {
  font-size: 32rpx;
  color: var(--on-surface-muted);
  margin-left: 12rpx;
  flex-shrink: 0;
}

/* 空状态提示 */
.empty-hint {
  text-align: center;
  padding: 48rpx 0;
}
.empty-hint-text {
  font-size: 26rpx;
  color: var(--on-surface-muted);
}
</style>
