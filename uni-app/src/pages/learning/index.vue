<template>
  <view class="page-container">
    <view class="nav-bar">
      <view class="nav-left"></view>
      <text class="nav-title">每日学习</text>
      <view class="nav-right">
        <view class="nav-avatar" @tap="showProfile = true">
          <text>{{ usernameInitial }}</text>
        </view>
      </view>
    </view>

    <view v-if="loading" class="loading">
      <view class="spinner"></view>
    </view>

    <template v-else>
      <!-- 数据概览 -->
      <view class="stats-banner">
        <view class="stat-item">
          <text class="stat-icon">📅</text>
          <text class="stat-value">{{ streakDays }}</text>
          <text class="stat-label">连续学习</text>
        </view>
        <view class="stat-item">
          <text class="stat-icon">📖</text>
          <text class="stat-value">{{ totalCount }}</text>
          <text class="stat-label">今日篇数</text>
        </view>
        <view class="stat-item">
          <text class="stat-icon">⭐</text>
          <text class="stat-value">{{ pointBalance }}</text>
          <text class="stat-label">积分</text>
        </view>
      </view>

      <!-- 空状态 -->
      <view v-if="contents.length === 0" class="empty-state">
        <text class="icon">📝</text>
        <text class="empty-text">今日还没有学习内容</text>
        <button class="btn btn-primary" style="margin-top: 32rpx" :disabled="generating" @tap="handleGenerate">
          <text>{{ generating ? '生成中...' : 'AI 生成今日内容' }}</text>
        </button>
      </view>

      <!-- 文章卡片 -->
      <view v-else>
        <scroll-view class="card-scroll" scroll-x enhanced show-scrollbar="false">
          <view class="card-track">
            <view
              v-for="(item, idx) in contents"
              :key="item.id"
              class="article-card"
              :class="{ active: idx === currentIdx }"
              @tap="goDetail(item.id)"
            >
              <view class="article-card-tags">
                <text class="tag tag-primary">{{ item.difficulty_level }}</text>
                <text class="tag tag-success">{{ themeLabels[item.theme_type] || item.theme_type }}</text>
              </view>
              <text class="article-card-title">{{ item.title }}</text>
              <text class="article-card-desc">{{ item.article?.slice(0, 80) }}...</text>
              <view class="article-card-footer">
                <text class="article-card-index">{{ idx + 1 }} / {{ totalCount }}</text>
                <text class="article-card-learned" v-if="learnedIds.includes(item.id)">✅已学</text>
              </view>
            </view>
          </view>
        </scroll-view>

        <!-- 指示器 -->
        <view class="dot-indicators">
          <view
            v-for="(_, idx) in contents"
            :key="idx"
            class="dot"
            :class="{ active: idx === currentIdx }"
          ></view>
        </view>

        <!-- 功能按钮 -->
        <view class="action-bar">
          <button class="btn btn-primary action-btn" :disabled="generating || remainingCount <= 0" @tap="handleGenerate">
            <text>{{ generating ? '生成中...' : (remainingCount > 0 ? `✨ 生成 (${remainingCount})` : '已用完') }}</text>
          </button>
          <button class="btn btn-outline action-btn" @tap="showCustomContent = true">
            <text>📝 自定义</text>
          </button>
          <button class="btn btn-outline action-btn" @tap="goList">
            <text>📋 历史</text>
          </button>
        </view>

        <!-- 去复习 -->
        <view class="review-bar">
          <button class="btn btn-primary btn-block btn-lg" @tap="goReview">
            <text>去默写 / 复习</text>
          </button>
        </view>
      </view>
    </template>

    <!-- 个人中心弹窗 -->
    <view v-if="showProfile" class="modal-overlay" @tap="showProfile = false">
      <view class="avatar-menu" @tap.stop>
        <view class="avatar-menu-user">
          <view class="avatar-menu-avatar"><text>{{ usernameInitial }}</text></view>
          <text class="avatar-menu-name">{{ auth.username || '未登录' }}</text>
        </view>
        <view class="avatar-menu-items">
          <view class="avatar-menu-item" @tap="goPreference">
            <text class="avatar-menu-item-icon">⚙️</text>
            <text>学习偏好</text>
          </view>
          <view class="avatar-menu-item" @tap="goShop">
            <text class="avatar-menu-item-icon">✨</text>
            <text>积分商店</text>
          </view>
          <view class="avatar-menu-item danger" @tap="handleLogout">
            <text class="avatar-menu-item-icon">🚪</text>
            <text>退出登录</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 自定义内容弹窗 -->
    <CustomContentModal :visible="showCustomContent" @close="showCustomContent = false" @created="loadData" />
    <OnboardingGuide />
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { dailyApi, generationLimitApi, checkinApi, shopApi } from '@/api'
import { useAuthStore } from '@/stores'
import { navTo, navReLaunch } from '@/utils/router'
import { storage } from '@/utils/storage'
import type { LearningContent } from '@/types'
import CustomContentModal from '@/components/CustomContentModal.vue'
import OnboardingGuide from '@/components/OnboardingGuide.vue'

const auth = useAuthStore()
const loading = ref(true)
const generating = ref(false)
const contents = ref<LearningContent[]>([])
const currentIdx = ref(0)
const learnedIds = ref<number[]>([])
const remainingCount = ref(3)
const showProfile = ref(false)
const showCustomContent = ref(false)
const streakDays = ref(0)
const pointBalance = ref(0)

const themeLabels: Record<string, string> = {
  ai_tech: 'AI科技', product_tech: '产品技术', business: '财经商业',
  daily_news: '日常新闻', self_growth: '个人成长', all_random: '随机',
}
const totalCount = computed(() => contents.value.length)
const usernameInitial = computed(() => (auth.username?.[0] || '?').toUpperCase())

async function loadData() {
  loading.value = true
  try {
    const { data } = await dailyApi.getTodayList(auth.currentUserId)
    contents.value = data.contents || []
  } catch {}
  try {
    const { data } = await generationLimitApi.getLimit(auth.currentUserId)
    remainingCount.value = data?.remaining_count ?? 3
  } catch {}
  try {
    const { data } = await dailyApi.getLearnedIds(auth.currentUserId)
    learnedIds.value = data.content_ids || []
  } catch {}
  try {
    const now = new Date()
    const { data } = await checkinApi.getCalendar(auth.currentUserId, now.getFullYear(), now.getMonth() + 1)
    streakDays.value = data?.current_streak_days || 0
  } catch {}
  try {
    const { data } = await shopApi.getBalance(auth.currentUserId)
    pointBalance.value = data?.available_points || 0
  } catch {}
  loading.value = false
}

async function handleGenerate() {
  generating.value = true
  try {
    await dailyApi.generate(auth.currentUserId)
    await loadData()
  } catch (e: any) {
    uni.showToast({ title: e.data?.detail || '生成失败', icon: 'none' })
  }
  generating.value = false
}

function goDetail(id: number) { navTo(`/pages/detail/index?id=${id}`) }
function goList() { navTo('/pages/list/index') }
function goReview() { navTo('/pages/review/index') }
function goPreference() { navTo('/pages/preference/index') }
function goShop() { navTo('/pages/shop/index') }

function handleLogout() {
  uni.showModal({
    title: '退出登录',
    content: '确定退出当前账号？',
    success: (res) => {
      if (res.confirm) {
        storage.remove('user_id'); storage.remove('username'); storage.remove('session_expiry')
        navReLaunch('/pages/login/index')
      }
    },
  })
}

onShow(loadData)
</script>

<style scoped>
.card-scroll {
  white-space: nowrap;
  overflow-x: auto;
  padding: 8rpx 0 16rpx;
  -webkit-overflow-scrolling: touch;
}
.card-track {
  display: inline-flex;
  gap: 24rpx;
  padding: 0 24rpx;
}
.article-card {
  width: 520rpx;
  background: #fff;
  border-radius: 24rpx;
  padding: 32rpx;
  box-shadow: var(--shadow-sm);
  display: inline-flex;
  flex-direction: column;
  gap: 16rpx;
  white-space: normal;
  transition: all 0.2s;
  flex-shrink: 0;
}
.article-card.active {
  box-shadow: var(--shadow-md);
  transform: translateY(-4rpx);
}
.article-card-tags { display: flex; gap: 12rpx; }
.article-card-title {
  font-size: 32rpx; font-weight: 700; line-height: 1.4;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.article-card-desc {
  font-size: 26rpx; color: var(--on-surface-variant); line-height: 1.5;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.article-card-footer {
  display: flex; justify-content: space-between; align-items: center;
  margin-top: 8rpx;
}
.article-card-index { font-size: 22rpx; color: var(--on-surface-muted); }
.article-card-learned { font-size: 22rpx; color: var(--success); font-weight: 600; }

.dot-indicators {
  display: flex; justify-content: center; gap: 12rpx;
  padding: 16rpx 0 8rpx;
}
.dot {
  width: 16rpx; height: 16rpx; border-radius: 50%;
  background: var(--outline-variant); transition: all 0.2s;
}
.dot.active {
  width: 32rpx; border-radius: 8rpx; background: var(--primary);
}

.action-bar {
  display: flex;
  gap: 16rpx;
  padding: 16rpx 24rpx;
}
.action-btn { flex: 1; font-size: 24rpx; padding: 20rpx 16rpx; }

.review-bar { padding: 16rpx 24rpx 32rpx; }
</style>
