<template>
  <view class="page-container">
    <view class="nav-bar">
      <view class="nav-left"></view>
      <text class="nav-title">Floo!</text>
      <view class="nav-right">
        <view class="nav-avatar" @tap="showProfile = !showProfile">
          <text>{{ usernameInitial }}</text>
        </view>
      </view>
    </view>

    <scroll-view class="home-scroll" scroll-y>
      <view class="home-hero">
        <text class="greeting">Hi{{ auth.username ? ', ' + auth.username : '' }}</text>
        <text class="question">今天想干啥？</text>
      </view>

      <view class="entry-grid">
        <view class="entry-card" @tap="goDictation">
          <view class="entry-icon" style="background:#FFF3E0; color:#E65100">✍️</view>
          <text class="entry-title">默写</text>
          <text class="entry-desc">听写文章段落，检验掌握程度</text>
        </view>
        <view class="entry-card" @tap="goCustom">
          <view class="entry-icon" style="background:#E3F2FD; color:#1565C0">📝</view>
          <text class="entry-title">自定义学习</text>
          <text class="entry-desc">粘贴文章或输入主题，AI 生成学习内容</text>
        </view>
        <view class="entry-card" @tap="goVocab">
          <view class="entry-icon" style="background:#E8F5E9; color:#2E7D32">📖</view>
          <text class="entry-title">背单词</text>
          <text class="entry-desc">间隔重复复习收藏的单词</text>
        </view>
        <view class="entry-card" @tap="goFloo">
          <view class="entry-icon" style="background:#F3E5F5; color:#7B1FA2">🌊</view>
          <text class="entry-title">Floo</text>
          <text class="entry-desc">AI 生成每日英语学习内容，开刷</text>
        </view>
      </view>

      <view v-if="showProfile" class="profile-panel">
        <view class="profile-card">
          <view class="profile-avatar-lg">
            <text>{{ usernameInitial }}</text>
          </view>
          <text class="profile-name">{{ auth.username || '用户' }}</text>
          <view class="profile-menu">
            <view class="profile-item" @tap="goCheckin">
              <text>📅 打卡</text>
            </view>
            <view class="profile-item" @tap="goPreference">
              <text>⚙️ 学习偏好</text>
            </view>
            <view class="profile-item" @tap="handleLogout">
              <text>🚪 退出登录</text>
            </view>
          </view>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores'
import { navReLaunch, navTo } from '@/utils/router'
import { storage } from '@/utils/storage'

const auth = useAuthStore()
const showProfile = ref(false)

const usernameInitial = computed(() => (auth.username?.[0] || 'F').toUpperCase())

function goDictation() {
  navReLaunch('/pages/review/index?tab=dictation')
}

function goCustom() {
  navReLaunch('/pages/learning/index?tab=custom')
}

function goVocab() {
  navTo('/pages/dictionary/index')
}

function goFloo() {
  navTo('/pages/learning/index')
}

function goCheckin() {
  navTo('/pages/checkin/index')
}

function goPreference() {
  navTo('/pages/preference/index')
}

function handleLogout() {
  storage.remove('user_id')
  storage.remove('username')
  navReLaunch('/pages/login/index')
}
</script>

<style scoped>
.home-scroll { flex: 1; padding: 0 20rpx; }

.home-hero { padding: 48rpx 0 40rpx; }
.greeting { font-size: 32rpx; color: var(--on-surface-variant); display: block; }
.question { font-size: 44rpx; font-weight: 800; color: var(--on-surface); margin-top: 8rpx; display: block; }

.entry-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20rpx; margin-bottom: 32rpx; }
.entry-card {
  background: white; border-radius: 20rpx; padding: 32rpx 24rpx;
  box-shadow: 0 2rpx 12rpx rgba(0,0,0,0.04);
  transition: transform 0.15s;
}
.entry-card:active { transform: scale(0.97); }
.entry-icon {
  width: 80rpx; height: 80rpx; border-radius: 20rpx;
  display: flex; align-items: center; justify-content: center;
  font-size: 36rpx; margin-bottom: 20rpx;
}
.entry-title { font-size: 32rpx; font-weight: 700; color: var(--on-surface); display: block; }
.entry-desc { font-size: 24rpx; color: var(--on-surface-variant); line-height: 1.5; margin-top: 8rpx; display: block; }

/* 个人面板 */
.profile-panel { position: fixed; top: 0; left: 0; right: 0; bottom: 0; z-index: 100; background: rgba(0,0,0,0.3); display: flex; align-items: flex-start; justify-content: flex-end; padding: 120rpx 20rpx 0 0; }
.profile-card { width: 420rpx; background: white; border-radius: 24rpx; padding: 40rpx 32rpx; text-align: center; box-shadow: 0 8rpx 40rpx rgba(0,0,0,0.12); }
.profile-avatar-lg { width: 96rpx; height: 96rpx; border-radius: 50%; background: var(--primary-container); display: flex; align-items: center; justify-content: center; margin: 0 auto 16rpx; }
.profile-avatar-lg text { font-size: 40rpx; font-weight: 700; color: var(--primary); }
.profile-name { font-size: 30rpx; font-weight: 600; margin-bottom: 32rpx; display: block; }
.profile-menu { border-top: 2rpx solid var(--surface-container-high); padding-top: 16rpx; }
.profile-item { padding: 24rpx 0; font-size: 28rpx; border-bottom: 2rpx solid var(--surface-container); }
.profile-item:last-child { border-bottom: none; }
</style>
