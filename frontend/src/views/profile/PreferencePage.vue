<template>
  <div class="page-container">
    <div class="page-header">
      <h1>学习偏好设置</h1>
    </div>

    <div v-if="loading" class="loading"><div class="spinner"></div></div>

    <div v-else class="preference-content">
      <div class="card">
        <h3 style="margin-bottom:4px">内容主题</h3>
        <p style="font-size:13px;color:var(--on-surface-variant);margin-bottom:12px">选择你感兴趣的主题方向，我们会为你生成相关英文新闻</p>
        <div class="theme-grid">
          <div v-for="t in themes" :key="t.value" class="theme-chip" :class="{ active: theme === t.value }" @click="theme = t.value">
            <span class="theme-icon">{{ t.icon }}</span>
            <span>{{ t.label }}</span>
          </div>
        </div>
      </div>

      <div class="card">
        <h3 style="margin-bottom:4px">每日学习目标</h3>
        <p style="font-size:20px;font-weight:700;color:var(--primary);margin-bottom:8px">{{ dailyGoal }} 分钟</p>
        <input type="range" v-model.number="dailyGoal" min="5" max="60" step="5" class="slider" />
        <div style="display:flex;justify-content:space-between;font-size:12px;color:var(--on-surface-variant)">
          <span>5分钟</span>
          <span>60分钟</span>
        </div>
      </div>

      <div style="padding:16px">
        <button class="btn btn-primary btn-block btn-lg" @click="handleSave" :disabled="saving">
          {{ saving ? '保存中...' : '保存设置' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore, usePreferenceStore } from '@/stores'

const router = useRouter()
const auth = useAuthStore()
const prefStore = usePreferenceStore()

const loading = ref(true)
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

onMounted(async () => {
  await prefStore.fetchPreference(auth.currentUserId)
  if (prefStore.preference) {
    theme.value = prefStore.preference.theme_type
    dailyGoal.value = prefStore.preference.daily_goal_minutes
  }
  loading.value = false
})

async function handleSave() {
  saving.value = true
  try {
    await prefStore.updatePreference(auth.currentUserId, {
      difficulty_level: 'medium',
      theme_type: theme.value,
      daily_goal_minutes: dailyGoal.value,
    })
    router.back()
  } catch { /* ignore */ }
  saving.value = false
}
</script>

<style scoped>
.preference-content { padding-top: 8px; }

.theme-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.theme-chip {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 14px 8px;
  border: 1.5px solid var(--outline);
  border-radius: var(--radius);
  cursor: pointer;
  transition: all 0.2s;
  font-size: 13px;
  font-weight: 500;
}

.theme-chip:hover { border-color: var(--primary); }

.theme-chip.active {
  background: var(--primary);
  color: white;
  border-color: var(--primary);
}

.theme-icon { font-size: 24px; }

.slider {
  width: 100%;
  height: 6px;
  -webkit-appearance: none;
  appearance: none;
  background: var(--surface-container-high);
  border-radius: 3px;
  outline: none;
}

.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 22px;
  height: 22px;
  background: var(--primary);
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 2px 6px rgba(0,0,0,0.15);
}
</style>
