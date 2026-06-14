<template>
  <view v-if="visible" class="onboarding-overlay" @tap.self="handleSkip">
    <view class="onboarding-card">
      <!-- Step 1: 欢迎 -->
      <view v-if="step === 0" class="step">
        <text class="step-icon">👋</text>
        <text class="step-title">欢迎来到 Floo!</text>
        <text class="step-desc">飞路一下，用每天5分钟的英文阅读\n让你的英语能力悄悄进步</text>
        <button class="btn btn-primary btn-block btn-lg" @tap="step = 1">
          <text>开始设置 →</text>
        </button>
        <text class="skip-btn" @tap="handleSkip">稍后再说</text>
      </view>

      <!-- Step 2: 选择主题 -->
      <view v-if="step === 1" class="step">
        <text class="step-icon">🎯</text>
        <text class="step-title">选择你感兴趣的主题</text>
        <text class="step-desc">我们会根据你的兴趣生成英文阅读内容</text>
        <view class="theme-grid">
          <view
            v-for="t in themes"
            :key="t.value"
            class="theme-chip"
            :class="{ active: theme === t.value }"
            @tap="theme = t.value"
          >
            <text class="theme-icon">{{ t.icon }}</text>
            <text class="theme-label">{{ t.label }}</text>
          </view>
        </view>
        <button class="btn btn-primary btn-block btn-lg" @tap="step = 2">
          <text>下一步 →</text>
        </button>
      </view>

      <!-- Step 3: 每日目标 -->
      <view v-if="step === 2" class="step">
        <text class="step-icon">⏱️</text>
        <text class="step-title">设定每日学习时长</text>
        <text class="step-desc">选择你每天愿意花多少时间学英语</text>
        <text class="goal-display">{{ dailyGoal }} 分钟</text>
        <slider
          v-model="dailyGoal"
          :min="5"
          :max="60"
          :step="5"
          class="slider"
          activeColor="#5B9AA8"
          backgroundColor="#E0E0E0"
          block-size="24"
        />
        <view class="goal-range">
          <text>5分钟</text>
          <text>60分钟</text>
        </view>
        <text class="goal-hint" v-if="dailyGoal <= 15">每天1篇内容，轻松无压力</text>
        <text class="goal-hint" v-else-if="dailyGoal <= 30">每天1-2篇内容，稳步提升</text>
        <text class="goal-hint" v-else>每天2-3篇内容，快速进步</text>
        <button
          class="btn btn-primary btn-block btn-lg"
          :disabled="saving"
          @tap="handleComplete"
        >
          <text>{{ saving ? '保存中...' : '完成设置 🎉' }}</text>
        </button>
      </view>

      <!-- Step 4: 完成 -->
      <view v-if="step === 3" class="step">
        <text class="step-icon">🚀</text>
        <text class="step-title">一切就绪!</text>
        <text class="step-desc">每天我们会为你推送精选英文内容\n点击任意单词即可查看释义和发音</text>
        <view class="tips-list">
          <view class="tip-item"><text>📖 阅读文章，点击生词学习</text></view>
          <view class="tip-item"><text>✏️ 用默写练习巩固记忆</text></view>
          <view class="tip-item"><text>🔄 复习系统帮你科学记忆</text></view>
        </view>
        <button class="btn btn-primary btn-block btn-lg" @tap="handleFinish">
          <text>开始学习 🎯</text>
        </button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore, usePreferenceStore } from '@/stores'

const auth = useAuthStore()
const prefStore = usePreferenceStore()

const visible = ref(false)
const step = ref(0)
const saving = ref(false)
const theme = ref('daily_news')
const dailyGoal = ref(15)

const themes = [
  { value: 'ai_tech', label: 'AI科技', icon: '🧠' },
  { value: 'product_tech', label: '产品技术', icon: '💻' },
  { value: 'business', label: '财经商业', icon: '💼' },
  { value: 'daily_news', label: '日常新闻', icon: '📰' },
  { value: 'self_growth', label: '个人成长', icon: '🧘' },
  { value: 'all_random', label: '我都要', icon: '🎲' },
]

onMounted(() => {
  // 检查是否已完成过新手引导
  const userId = auth.currentUserId
  const completed = uni.getStorageSync(`onboarding_done_${userId}`)
  if (!completed) {
    visible.value = true
  }
})

function handleSkip() {
  // 跳过也标记为已完成，避免反复弹出
  uni.setStorageSync(`onboarding_done_${auth.currentUserId}`, '1')
  visible.value = false
}

async function handleComplete() {
  saving.value = true
  try {
    await prefStore.updatePreference(auth.currentUserId, {
      difficulty_level: 'medium',
      theme_type: theme.value,
      daily_goal_minutes: dailyGoal.value,
    })
    await auth.fetchPreference()
    step.value = 3
  } catch { /* ignore */ }
  saving.value = false
}

function handleFinish() {
  uni.setStorageSync(`onboarding_done_${auth.currentUserId}`, '1')
  visible.value = false
}
</script>

<style scoped>
.onboarding-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40rpx;
}

.onboarding-card {
  background: white;
  border-radius: 48rpx;
  width: 100%;
  max-width: 750rpx;
  padding: 64rpx 48rpx;
  text-align: center;
}

.step {
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from { opacity: 0; transform: translateX(20rpx); }
  to { opacity: 1; transform: translateX(0); }
}

.step-icon {
  font-size: 96rpx;
  margin-bottom: 32rpx;
  display: block;
}

.step-title {
  font-size: 44rpx;
  font-weight: 700;
  margin-bottom: 16rpx;
  color: var(--on-surface);
  display: block;
}

.step-desc {
  font-size: 28rpx;
  color: var(--on-surface-variant);
  margin-bottom: 48rpx;
  line-height: 1.6;
  display: block;
}

.skip-btn {
  margin-top: 24rpx;
  font-size: 26rpx;
  color: var(--on-surface-variant);
  display: block;
}

.theme-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 20rpx;
  margin-bottom: 48rpx;
}

.theme-chip {
  width: calc(33.33% - 14rpx);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
  padding: 24rpx 12rpx;
  border: 3rpx solid var(--outline);
  border-radius: var(--radius);
}

.theme-chip.active {
  background: var(--primary);
  color: white;
  border-color: var(--primary);
}

.theme-icon {
  font-size: 44rpx;
}

.theme-label {
  font-size: 24rpx;
}

.goal-display {
  font-size: 72rpx;
  font-weight: 800;
  color: var(--primary);
  margin-bottom: 32rpx;
  display: block;
}

.slider {
  width: 100%;
  margin-bottom: 16rpx;
}

.goal-range {
  display: flex;
  justify-content: space-between;
  font-size: 24rpx;
  color: var(--on-surface-variant);
  margin-bottom: 16rpx;
}

.goal-hint {
  font-size: 26rpx;
  color: var(--primary);
  margin-bottom: 40rpx;
  font-weight: 500;
  display: block;
}

.tips-list {
  text-align: left;
  margin: 40rpx 0;
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.tip-item {
  font-size: 28rpx;
  color: var(--on-surface);
  padding: 20rpx 28rpx;
  background: var(--surface-container);
  border-radius: 24rpx;
}
</style>
