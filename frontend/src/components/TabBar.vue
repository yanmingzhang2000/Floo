<template>
  <div class="tab-bar">
    <!-- 顶部导航栏 -->
    <header class="top-nav">
      <div class="top-left">
        <router-link to="/learning" class="logo-link">
          <span class="logo-text">Floo!</span>
        </router-link>
      </div>
      <div class="top-right">
        <div class="profile-btn" @click="showProfile = true">
          <span class="avatar-text">{{ auth.username?.[0]?.toUpperCase() || '?' }}</span>
        </div>
      </div>
    </header>

    <div class="tab-content">
      <router-view />
    </div>

    <nav class="bottom-nav">
      <router-link v-for="tab in tabs" :key="tab.path" :to="tab.path" class="nav-item" :class="{ active: $route.path === tab.path }">
        <span class="nav-icon">{{ tab.icon }}</span>
        <span class="nav-label">{{ tab.label }}</span>
      </router-link>
    </nav>

    <!-- 个人设置弹窗 -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="showProfile" class="modal-overlay" @click.self="showProfile = false">
          <div class="profile-sheet">
            <div class="sheet-header">
              <div class="avatar">{{ auth.username?.[0]?.toUpperCase() || '?' }}</div>
              <span class="username">{{ auth.username || '未登录' }}</span>
            </div>
            <div class="sheet-body">
              <router-link to="/shop" class="sheet-item" @click="showProfile = false">
                🎁 积分商城
              </router-link>
              <router-link to="/preference" class="sheet-item" @click="showProfile = false">
                ⚙️ 学习偏好设置
              </router-link>
              <div class="sheet-item danger" @click="handleLogout">
                🚪 退出登录
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores'

const router = useRouter()
const auth = useAuthStore()
const showProfile = ref(false)

const tabs = [
  { path: '/learning', label: '每日学习', icon: '📖' },
  { path: '/dictionary', label: '单词书', icon: '📚' },
  { path: '/review', label: '复习', icon: '🔄' },
  { path: '/checkin', label: '打卡', icon: '📅' },
]

function handleLogout() {
  auth.logout()
  showProfile.value = false
  router.push('/login')
}
</script>

<style scoped>
.tab-bar {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.top-nav {
  position: fixed;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: 480px;
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
  z-index: 90;
}

.top-left { display: flex; align-items: center; }
.logo-link { text-decoration: none; }
.logo-text { color: white; font-size: 20px; font-weight: 800; }

.profile-btn {
  width: 36px;
  height: 36px;
  background: rgba(255,255,255,0.25);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.2s;
}
.profile-btn:hover { background: rgba(255,255,255,0.4); }
.avatar-text { color: white; font-size: 16px; font-weight: 700; }

.tab-content {
  flex: 1;
  padding-top: 52px;
  padding-bottom: 64px;
}

.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: 480px;
  display: flex;
  background: #fff;
  border-top: 1px solid var(--surface-container-high);
  padding: 6px 0;
  z-index: 100;
}

.nav-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 6px 0;
  text-decoration: none;
  color: var(--on-surface-variant);
  transition: color 0.2s;
}

.nav-item.active {
  color: var(--primary);
}

.nav-icon { font-size: 20px; }
.nav-label { font-size: 11px; font-weight: 500; }

.profile-sheet {
  position: fixed;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: 480px;
  background: white;
  border-radius: 20px 20px 0 0;
  padding: 20px;
  z-index: 200;
}

.sheet-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--surface-container-high);
  margin-bottom: 8px;
}

.avatar {
  width: 48px;
  height: 48px;
  background: var(--primary);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 700;
}

.username { font-size: 18px; font-weight: 600; }

.sheet-item {
  display: block;
  padding: 14px 0;
  font-size: 16px;
  color: var(--on-surface);
  text-decoration: none;
  cursor: pointer;
  border-bottom: 1px solid var(--surface-container);
}

.sheet-item.danger { color: var(--error); }

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.3);
  z-index: 150;
}
</style>
