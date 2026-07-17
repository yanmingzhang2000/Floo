<template>
  <!-- 头像圆圈按钮 -->
  <view class="ua-avatar" @tap.stop="open">
    <text class="ua-initial">{{ initial }}</text>
  </view>

  <!-- 退出弹窗遮罩 -->
  <view v-if="visible" class="ua-overlay" @tap.stop="close">
    <view class="ua-sheet" @tap.stop>
      <!-- 用户信息行 -->
      <view class="ua-user-row">
        <view class="ua-big-avatar">
          <text class="ua-big-initial">{{ initial }}</text>
        </view>
        <text class="ua-username">{{ auth.username || '未登录' }}</text>
      </view>
      <!-- 操作项 -->
      <view class="ua-divider" />
      <view class="ua-item" @tap="goPreference">
        <text class="ua-item-icon">⚙️</text>
        <text class="ua-item-label">学习偏好设置</text>
      </view>
      <view class="ua-item ua-item-danger" @tap="handleLogout">
        <text class="ua-item-icon">🚪</text>
        <text class="ua-item-label">退出登录</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores'

const auth = useAuthStore()
const visible = ref(false)

// 用户名首字母大写；未登录时显示 ?
const initial = computed(() => auth.username?.[0]?.toUpperCase() || '?')

function open() {
  visible.value = true
}

function close() {
  visible.value = false
}

function goPreference() {
  close()
  uni.navigateTo({ url: '/pages/preference/index' })
}

function handleLogout() {
  console.debug('[UserAvatar] handleLogout userId=%s', auth.userId)
  close()
  auth.logout()
  // 清空路由栈，跳到登录页
  uni.reLaunch({ url: '/pages/login/index' })
}
</script>

<style scoped>
/* ===== 头像圆圈 ===== */
.ua-avatar {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  border: 2rpx solid rgba(255, 255, 255, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
}

.ua-initial {
  color: #fff;
  font-size: 26rpx;
  font-weight: 700;
  line-height: 1;
}

/* ===== 遮罩 ===== */
.ua-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  z-index: 9999;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

/* ===== 底部弹出卡片 ===== */
.ua-sheet {
  width: 100%;
  max-width: 480px;
  background: #fff;
  border-radius: 24rpx 24rpx 0 0;
  padding: 32rpx 32rpx calc(32rpx + env(safe-area-inset-bottom, 0px));
}

.ua-user-row {
  display: flex;
  align-items: center;
  gap: 24rpx;
  padding-bottom: 28rpx;
}

.ua-big-avatar {
  width: 88rpx;
  height: 88rpx;
  border-radius: 50%;
  background: var(--primary, #5B9AA8);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.ua-big-initial {
  color: #fff;
  font-size: 36rpx;
  font-weight: 700;
}

.ua-username {
  font-size: 34rpx;
  font-weight: 600;
  color: #1a2730;
}

.ua-divider {
  height: 1rpx;
  background: #f0f4f5;
  margin-bottom: 8rpx;
}

/* ===== 操作项 ===== */
.ua-item {
  display: flex;
  align-items: center;
  gap: 20rpx;
  padding: 28rpx 0;
  border-bottom: 1rpx solid #f5f8f9;
  cursor: pointer;
}

.ua-item:last-child {
  border-bottom: none;
}

.ua-item-icon {
  font-size: 32rpx;
  width: 40rpx;
  text-align: center;
}

.ua-item-label {
  font-size: 30rpx;
  color: #2c3e50;
}

.ua-item-danger .ua-item-label {
  color: #e74c3c;
}
</style>
