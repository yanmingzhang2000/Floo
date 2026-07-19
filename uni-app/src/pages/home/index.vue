<template>
  <view class="page-container">
    <view class="home-header">
      <text class="home-title">Floo!</text>
      <UserAvatar />
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
          src="/static/images/hero_book.png"
          mode="widthFix"
          class="hero-illustration"
        />
      </view>

      <view class="cta-area">
        <!-- 主行动：有历史则「继续阅读」为主，否则「开始学习」为主 -->
        <view v-if="lastContent" class="resume-card-primary" @tap="goReviewLast">
          <view class="resume-card-left">
            <text class="resume-label">继续阅读</text>
            <text class="resume-title">{{ lastContent.title }}</text>
            <view class="resume-meta">
              <text class="resume-tag">{{ THEME_LABEL[lastContent.theme_type] || lastContent.theme_type }}</text>
            </view>
          </view>
          <text class="resume-arrow">→</text>
        </view>
        <button v-else class="cta-btn cta-btn-main" @tap="goLibrary">
          <text class="cta-text cta-text-primary">开始学习</text>
        </button>

        <!-- 次级入口：有历史时显示「去图书馆」 -->
        <view v-if="lastContent" class="secondary-link" @tap="goLibrary">
          <text class="secondary-link-text">探索图书馆</text>
        </view>

        <!-- 快捷入口（折叠） -->
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
import UserAvatar from '@/components/UserAvatar.vue'

const auth = useAuthStore()
const loading = ref(true)
const streakDays = ref(0)
const showQuick = ref(false)
const lastLearnedId = ref<number | null>(null)
const lastContent = ref<LearningContent | null>(null)

// theme_type → 中文标签映射
const THEME_LABEL: Record<string, string> = {
  daily_news: '每日新闻',
  technology: '科技',
  culture: '文化',
  business: '商业',
  science: '科学',
  sports: '体育',
  health: '健康',
  travel: '旅行',
  food: '美食',
  all_random: '随机',
  custom: '自定义',
}

async function loadData() {
  loading.value = true
  const userId = auth.currentUserId
  const safe = (p: Promise<any>) => p.catch(() => null)

  // 首页只需要连续打卡天数和上次学习 ID，不调 today-list
  // （today-list 有兜底 AI 生成逻辑，会导致首页卡住等 LLM 响应）
  const [calendarRes, learnedRes] = await Promise.all([
    safe(checkinApi.getCalendar(userId, new Date().getFullYear(), new Date().getMonth() + 1)),
    safe(dailyApi.getLearnedIds(userId)),
  ])

  if (calendarRes?.data) streakDays.value = calendarRes.data.current_streak_days || 0

  // 用 opened_ids[0] 作为"上次阅读"，后端已按 opened_at DESC 排序
  // Why：书籍章节只写 UserOpenedContent，不一定触发 UserLearnedContent（需手动/停留5分钟）
  // 用 opened_ids 能准确反映用户最近实际阅读的内容
  if (learnedRes?.data) {
    const openedIds: number[] = learnedRes.data.opened_ids || []
    lastLearnedId.value = openedIds.length > 0 ? openedIds[0] : null
  }

  // 拉上次学习内容详情，用于「继续阅读」卡片
  if (lastLearnedId.value) {
    const contentRes = await safe(dailyApi.getContent(lastLearnedId.value))
    lastContent.value = contentRes?.data ?? null
  }

  loading.value = false
}

function goReviewLast() {
  if (lastLearnedId.value) {
    navTo(`/pages/detail/index?id=${lastLearnedId.value}`)
  }
}

function goLibrary() {
  uni.switchTab({ url: '/pages/learning/index' })
}

function goCheckin() { navTo('/pages/checkin/index') }
function goDictation() { uni.navigateTo({ url: '/pages/review/index' }) }
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
/* ---- 顶部通栏（与图书馆页保持一致） ---- */
.home-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: calc(env(safe-area-inset-top, 44px) + 16rpx) 32rpx 24rpx;
  background: var(--primary, #5B9AA8);
  margin: 0 -20rpx 0;
}
.home-title {
  font-size: 36rpx;
  font-weight: 800;
  color: #fff;
  letter-spacing: 1rpx;
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
  padding: 20rpx 0 0;
}
.hero-illustration {
  width: 100%;
  max-width: 650rpx;
  height: auto;
}

.cta-area {
  margin: 24rpx 32rpx 0;
}

/* 主行动卡片：继续阅读（有历史时） */
.resume-card-primary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 36rpx 40rpx;
  background: var(--primary);
  border-radius: 28rpx;
  box-shadow: 0 6rpx 24rpx rgba(91,154,168,0.3);
  transition: transform 0.15s;
}
.resume-card-primary:active { transform: scale(0.98); }
.resume-card-left {
  flex: 1;
  overflow: hidden;
}
.resume-label {
  font-size: 22rpx;
  color: rgba(255,255,255,0.75);
  letter-spacing: 1rpx;
  display: block;
  margin-bottom: 10rpx;
}
.resume-title {
  font-size: 32rpx;
  font-weight: 700;
  color: #fff;
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.resume-meta {
  margin-top: 12rpx;
}
.resume-tag {
  font-size: 22rpx;
  color: var(--primary);
  background: rgba(255,255,255,0.9);
  padding: 4rpx 16rpx;
  border-radius: 20rpx;
  display: inline-block;
  font-weight: 600;
}
.resume-arrow {
  font-size: 40rpx;
  color: rgba(255,255,255,0.9);
  margin-left: 24rpx;
  flex-shrink: 0;
}

/* 次级入口：探索图书馆 */
.secondary-link {
  display: flex;
  justify-content: center;
  padding: 28rpx 0 8rpx;
}
.secondary-link-text {
  font-size: 28rpx;
  color: var(--on-surface-variant);
  font-weight: 500;
}
.secondary-link:active .secondary-link-text {
  color: var(--primary);
}

/* 新用户唯一主按钮 */
.cta-btn {
  width: 100%;
  height: 96rpx;
  background: #fff;
  border-radius: 48rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.15s;
}
.cta-btn:active { transform: scale(0.97); }
.cta-btn-main {
  box-shadow: 0 4rpx 16rpx rgba(91,154,168,0.18);
}
.cta-text {
  font-size: 32rpx;
  font-weight: 700;
}
.cta-text-primary { color: var(--primary); }

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


@media (min-width: 768px) {
  /* 方案一：桌面端放大标题字号 */
  .hero-title-en {
    font-size: 72rpx;
  }
  .hero-title-cn {
    font-size: 56rpx;
  }
  .hero-desc {
    font-size: 32rpx;
  }
  /* 方案三：桌面端加大左右 padding，收窄文字区域减少右侧留白感 */
  .hero-section {
    padding: 40rpx 80rpx 0;
  }
}
</style>
