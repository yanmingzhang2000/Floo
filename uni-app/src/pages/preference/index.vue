<template>
  <view class="page-container">
    <view v-if="loading" class="loading">
      <view class="spinner"></view>
    </view>

    <view v-else>
      <view class="card">
        <text class="card-label">难度等级</text>
        <picker mode="selector" :range="difficulties" :value="difficultyIdx" @change="onDifficultyChange">
          <view class="picker-input">
            <text>{{ difficulties[difficultyIdx] }}</text>
            <text class="arrow-icon">›</text>
          </view>
        </picker>
      </view>

      <view class="card">
        <text class="card-label">主题类型</text>
        <picker mode="selector" :range="themes" :value="themeIdx" @change="onThemeChange">
          <view class="picker-input">
            <text>{{ themes[themeIdx] }}</text>
            <text class="arrow-icon">›</text>
          </view>
        </picker>
      </view>

      <view class="card">
        <text class="card-label">每日目标（分钟）</text>
        <picker mode="selector" :range="goals" :value="goalIdx" @change="onGoalChange">
          <view class="picker-input">
            <text>{{ goals[goalIdx] }} 分钟</text>
            <text class="arrow-icon">›</text>
          </view>
        </picker>
      </view>

      <view style="padding: 32rpx">
        <button class="btn btn-primary btn-block" :disabled="saving" @tap="handleSave">
          <text>{{ saving ? '保存中...' : '保存设置' }}</text>
        </button>
      </view>

      <!-- #ifdef MP-WEIXIN -->
      <view class="bind-section">
        <view class="divider">
          <view class="divider-line"></view>
          <text class="divider-text">账号绑定</text>
          <view class="divider-line"></view>
        </view>
        <button class="btn-wechat" :disabled="wxLoading" @tap="handleBindWechat">
          <text v-if="wxLoading">绑定中...</text>
          <text v-else>绑定微信</text>
        </button>
        <text class="bind-hint">绑定后可使用微信一键登录</text>
      </view>
      <!-- #endif -->
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { userApi } from '@/api'
import { useAuthStore } from '@/stores'

const auth = useAuthStore()
const loading = ref(true)
const saving = ref(false)
const wxLoading = ref(false)

const difficulties = ['easy', 'medium', 'hard']
const themes = ['daily_news', 'ai_tech', 'product_tech', 'business', 'self_growth', 'all_random']
const goals = [5, 10, 15, 30, 45, 60]

const difficultyIdx = ref(1)
const themeIdx = ref(0)
const goalIdx = ref(2)

function onDifficultyChange(e: any) {
  difficultyIdx.value = e.detail.value
}

function onThemeChange(e: any) {
  themeIdx.value = e.detail.value
}

function onGoalChange(e: any) {
  goalIdx.value = e.detail.value
}

async function handleSave() {
  saving.value = true
  try {
    await userApi.updatePreference(auth.currentUserId, {
      difficulty_level: difficulties[difficultyIdx.value],
      theme_type: themes[themeIdx.value],
      daily_goal_minutes: goals[goalIdx.value],
    })
    uni.showToast({ title: '保存成功', icon: 'success' })
    setTimeout(() => uni.navigateBack(), 1000)
  } catch {
    uni.showToast({ title: '保存失败', icon: 'none' })
  }
  saving.value = false
}

onMounted(async () => {
  loading.value = true
  try {
    const { data } = await userApi.getPreference(auth.currentUserId)
    difficultyIdx.value = difficulties.indexOf(data.difficulty_level)
    themeIdx.value = themes.indexOf(data.theme_type)
    goalIdx.value = goals.indexOf(data.daily_goal_minutes)
  } catch {}
  loading.value = false
})

// #ifdef MP-WEIXIN
async function handleBindWechat() {
  wxLoading.value = true
  try {
    const loginRes = await new Promise<UniApp.LoginRes>((resolve, reject) => {
      uni.login({ success: resolve, fail: reject })
    })
    if (!loginRes.code) {
      uni.showToast({ title: '获取code失败', icon: 'none' })
      return
    }
    await userApi.bindWechat(auth.currentUserId, loginRes.code)
    uni.showToast({ title: '绑定成功', icon: 'success' })
  } catch (e: any) {
    const msg = e.data?.detail || e.errMsg || '绑定失败'
    uni.showToast({ title: msg, icon: 'none' })
  } finally {
    wxLoading.value = false
  }
}
// #endif
</script>

<style scoped>
.card-label {
  font-size: 28rpx;
  font-weight: 600;
  color: var(--on-surface);
  margin-bottom: 16rpx;
  display: block;
}

.picker-input {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24rpx 0;
  border: 3rpx solid var(--outline);
  border-radius: 16rpx;
  padding: 28rpx 32rpx;
  font-size: 32rpx;
}

.arrow-icon {
  font-size: 40rpx;
  color: var(--on-surface-variant);
}
.bind-section {
  padding: 32rpx;
}
.divider {
  display: flex;
  align-items: center;
  margin: 32rpx 0;
  gap: 20rpx;
}
.divider-line {
  flex: 1;
  height: 2rpx;
  background: #E0E0E0;
}
.divider-text {
  color: #999;
  font-size: 26rpx;
}
.btn-wechat {
  width: 100%;
  height: 96rpx;
  line-height: 96rpx;
  background: #07C160;
  color: white;
  font-size: 32rpx;
  font-weight: 600;
  border-radius: 16rpx;
  text-align: center;
  border: none;
}
.btn-wechat[disabled] {
  opacity: 0.6;
  background: #07C160;
}
.bind-hint {
  display: block;
  text-align: center;
  font-size: 24rpx;
  color: #999;
  margin-top: 16rpx;
}
</style>