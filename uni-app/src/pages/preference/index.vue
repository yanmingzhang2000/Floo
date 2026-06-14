<template>
  <view class="page-container">
    <view class="nav-bar">
      <view class="nav-left">
        <view class="nav-back" @tap="uni.navigateBack()"><text>‹</text></view>
      </view>
      <text class="nav-title">学习偏好</text>
      <view class="nav-right">
        <view class="nav-avatar">
          <text>{{ usernameInitial }}</text>
        </view>
      </view>
    </view>

    <view v-if="loading" class="loading">
      <view class="spinner"></view>
    </view>

    <view v-else class="pref-wrap">
      <view class="pref-group">
        <text class="pref-group-title">文章设置</text>
        <view class="card pref-card">
          <view class="pref-row">
            <text class="pref-label">难度等级</text>
            <picker mode="selector" :range="difficultyLabels" :value="difficultyIdx" @change="e => difficultyIdx = e.detail.value">
              <view class="pref-value">
                <text>{{ difficultyLabels[difficultyIdx] }}</text>
                <text class="pref-arrow">›</text>
              </view>
            </picker>
          </view>
        </view>
        <view class="card pref-card">
          <view class="pref-row">
            <text class="pref-label">阅读主题</text>
            <picker mode="selector" :range="themeLabels" :value="themeIdx" @change="e => themeIdx = e.detail.value">
              <view class="pref-value">
                <text>{{ themeLabels[themeIdx] }}</text>
                <text class="pref-arrow">›</text>
              </view>
            </picker>
          </view>
        </view>
      </view>

      <view class="pref-group">
        <text class="pref-group-title">学习目标</text>
        <view class="card pref-card">
          <view class="pref-row">
            <text class="pref-label">每日学习目标</text>
            <picker mode="selector" :range="goalLabels" :value="goalIdx" @change="e => goalIdx = e.detail.value">
              <view class="pref-value">
                <text>{{ goalLabels[goalIdx] }}</text>
                <text class="pref-arrow">›</text>
              </view>
            </picker>
          </view>
        </view>
      </view>

      <view class="pref-save">
        <button class="btn btn-primary btn-block btn-lg" :disabled="saving" @tap="handleSave">
          <text>{{ saving ? '保存中...' : '保存设置' }}</text>
        </button>
      </view>

      <!-- #ifdef MP-WEIXIN -->
      <view class="pref-group">
        <text class="pref-group-title">账号</text>
        <view class="card pref-card">
          <view class="pref-row">
            <text class="pref-label">绑定微信</text>
            <button class="btn btn-sm btn-success" :disabled="wxLoading" @tap="handleBindWechat">
              <text>{{ wxLoading ? '绑定中...' : '立即绑定' }}</text>
            </button>
          </view>
        </view>
        <text class="pref-hint">绑定后可使用微信一键登录</text>
      </view>
      <!-- #endif -->
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { userApi } from '@/api'
import { useAuthStore } from '@/stores'

const auth = useAuthStore()
const loading = ref(true)
const saving = ref(false)
const wxLoading = ref(false)

const difficulties = ['easy', 'medium', 'hard']
const difficultyLabels = ['简单', '中等', '困难']
const themes = ['daily_news', 'ai_tech', 'product_tech', 'business', 'self_growth', 'all_random']
const themeLabels = ['日常新闻', 'AI科技', '产品技术', '财经商业', '个人成长', '随机主题']
const goals = [5, 10, 15, 30, 45, 60]
const goalLabels = ['5分钟', '10分钟', '15分钟', '30分钟', '45分钟', '60分钟']

const difficultyIdx = ref(1)
const themeIdx = ref(0)
const goalIdx = ref(2)

const usernameInitial = computed(() => (auth.username?.[0] || '?').toUpperCase())

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
  } catch { uni.showToast({ title: '保存失败', icon: 'none' }) }
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
    if (!loginRes.code) { uni.showToast({ title: '获取code失败', icon: 'none' }); return }
    await userApi.bindWechat(auth.currentUserId, loginRes.code)
    uni.showToast({ title: '绑定成功', icon: 'success' })
  } catch (e: any) {
    uni.showToast({ title: e.data?.detail || '绑定失败', icon: 'none' })
  } finally { wxLoading.value = false }
}
// #endif
</script>

<style scoped>
.pref-wrap { padding-bottom: 48rpx; }
.pref-group { margin-top: 32rpx; }
.pref-group:first-child { margin-top: 0; }
.pref-group-title {
  font-size: 26rpx; color: var(--on-surface-variant);
  padding: 0 32rpx; margin-bottom: 12rpx; display: block; font-weight: 600;
}
.pref-card { padding: 0; }
.pref-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 28rpx 32rpx;
}
.pref-label { font-size: 28rpx; color: var(--on-surface); }
.pref-value { display: flex; align-items: center; gap: 8rpx; }
.pref-value text:first-child { font-size: 28rpx; color: var(--primary); }
.pref-arrow { font-size: 36rpx; color: var(--on-surface-muted); }
.pref-hint { font-size: 22rpx; color: var(--on-surface-muted); padding: 12rpx 32rpx 0; display: block; }

.pref-save { padding: 48rpx 32rpx; }
</style>
