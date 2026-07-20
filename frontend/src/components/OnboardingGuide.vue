<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="visible" class="onboarding-overlay" @click.self="handleSkip">
        <div class="onboarding-card">
          <!-- Step 1: 欢迎 -->
          <div v-if="step === 0" class="step">
            <div class="step-icon">👋</div>
            <h2>欢迎来到 Floo!</h2>
            <p class="step-desc">飞路一下，用每天5分钟的英文阅读<br>让你的英语能力悄悄进步</p>
            <button class="btn btn-primary btn-block btn-lg" @click="step = 1">开始设置 →</button>
            <p class="skip-btn" @click="handleSkip">稍后再说</p>
          </div>

          <!-- Step 2: 选择主题 -->
          <div v-if="step === 1" class="step">
            <div class="step-icon">🎯</div>
            <h2>选择你感兴趣的主题</h2>
            <p class="step-desc">我们会根据你的兴趣生成英文阅读内容</p>
            <div class="theme-grid">
              <div v-for="t in themes" :key="t.value" class="theme-chip" :class="{ active: theme === t.value }" @click="theme = t.value">
                <span class="theme-icon">{{ t.icon }}</span>
                <span class="theme-label">{{ t.label }}</span>
              </div>
            </div>
            <button class="btn btn-primary btn-block btn-lg" @click="step = 2">下一步 →</button>
          </div>

          <!-- Step 3: 每日目标 -->
          <div v-if="step === 2" class="step">
            <div class="step-icon">⏱️</div>
            <h2>设定每日学习时长</h2>
            <p class="step-desc">选择你每天愿意花多少时间学英语</p>
            <div class="goal-display">{{ dailyGoal }} 分钟</div>
            <input type="range" v-model.number="dailyGoal" min="5" max="60" step="5" class="slider" />
            <div class="goal-range">
              <span>5分钟</span>
              <span>60分钟</span>
            </div>
            <p class="goal-hint" v-if="dailyGoal <= 15">每天1篇内容，轻松无压力</p>
            <p class="goal-hint" v-else-if="dailyGoal <= 30">每天1-2篇内容，稳步提升</p>
            <p class="goal-hint" v-else>每天2-3篇内容，快速进步</p>
            <button class="btn btn-primary btn-block btn-lg" @click="handleComplete" :disabled="saving">
              {{ saving ? '保存中...' : '完成设置 🎉' }}
            </button>
          </div>

          <!-- Step 4: 完成 -->
          <div v-if="step === 3" class="step">
            <div class="step-icon">🚀</div>
            <h2>一切就绪!</h2>
            <p class="step-desc">每天我们会为你推送精选英文内容<br>点击任意单词即可查看释义和发音</p>
            <div class="tips-list">
              <div class="tip-item">📖 阅读文章，点击生词学习</div>
              <div class="tip-item">✏️ 用默写练习巩固记忆</div>
              <div class="tip-item">🔄 复习系统帮你科学记忆</div>
            </div>
            <button class="btn btn-primary btn-block btn-lg" @click="handleFinish">开始学习 🎯</button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
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
  const completed = localStorage.getItem(`onboarding_done_${userId}`)
  if (!completed) {
    visible.value = true
  }
})

function handleSkip() {
  // 跳过也标记为已完成，避免反复弹出
  localStorage.setItem(`onboarding_done_${auth.currentUserId}`, '1')
  visible.value = false
}

async function handleComplete() {
  saving.value = true
  try {
    await prefStore.updatePreference(auth.currentUserId, {
      theme_type: theme.value,
      daily_goal_minutes: dailyGoal.value,
    })
    await auth.fetchPreference()
    step.value = 3
  } catch { /* ignore */ }
  saving.value = false
}

function handleFinish() {
  localStorage.setItem(`onboarding_done_${auth.currentUserId}`, '1')
  visible.value = false
}
</script>

<style scoped>
.onboarding-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.onboarding-card {
  background: white;
  border-radius: 24px;
  width: 100%;
  max-width: 380px;
  padding: 32px 24px;
  text-align: center;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

.step {
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from { opacity: 0; transform: translateX(20px); }
  to { opacity: 1; transform: translateX(0); }
}

.step-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.step h2 {
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 8px;
  color: var(--on-surface);
}

.step-desc {
  font-size: 14px;
  color: var(--on-surface-variant);
  margin-bottom: 24px;
  line-height: 1.6;
}

.skip-btn {
  margin-top: 12px;
  font-size: 13px;
  color: var(--on-surface-variant);
  cursor: pointer;
}

.skip-btn:hover {
  color: var(--primary);
}

.theme-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-bottom: 24px;
}

.theme-chip {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px 6px;
  border: 1.5px solid var(--outline);
  border-radius: var(--radius);
  cursor: pointer;
  transition: all 0.2s;
  font-size: 12px;
  font-weight: 500;
}

.theme-chip:hover {
  border-color: var(--primary);
}

.theme-chip.active {
  background: var(--primary);
  color: white;
  border-color: var(--primary);
}

.theme-icon {
  font-size: 22px;
}

.theme-label {
  font-size: 12px;
}

.goal-display {
  font-size: 36px;
  font-weight: 800;
  color: var(--primary);
  margin-bottom: 16px;
}

.slider {
  width: 100%;
  height: 6px;
  -webkit-appearance: none;
  appearance: none;
  background: var(--surface-container-high);
  border-radius: 3px;
  outline: none;
  margin-bottom: 8px;
}

.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 24px;
  height: 24px;
  background: var(--primary);
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
}

.goal-range {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--on-surface-variant);
  margin-bottom: 8px;
}

.goal-hint {
  font-size: 13px;
  color: var(--primary);
  margin-bottom: 20px;
  font-weight: 500;
}

.tips-list {
  text-align: left;
  margin: 20px 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tip-item {
  font-size: 14px;
  color: var(--on-surface);
  padding: 10px 14px;
  background: var(--surface-container);
  border-radius: 12px;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
