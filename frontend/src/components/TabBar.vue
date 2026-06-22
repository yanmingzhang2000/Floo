/**
 * 顶部导航栏（合并 logo + tabs + 个人中心）
 *
 * 为什么从底部移到顶部：底部 TabBar 在 iPhone 上被 Home Indicator 遮挡，
 * 且 sub-pages（DailyList / Weekly 等）已经有顶部返回按钮，导航逻辑分散。
 * 合并为单顶栏后，导航体验统一，也不需要在 sub-pages 重复加返回按钮。
 */
<template>
  <div class="app-layout">
    <header class="top-nav">
      <div class="nav-left">
        <router-link to="/learning" class="logo-link">
          <img :src="'/Floo/logo.jpg'" alt="Floo!" class="logo-img" />
          <span class="logo-text">Floo!</span>
        </router-link>
      </div>

      <nav class="nav-tabs">
        <router-link
          v-for="tab in tabs"
          :key="tab.path"
          :to="tab.path"
          class="tab-item"
          :class="{ active: isActive(tab.path) }"
        >
          <span class="tab-icon">{{ tab.icon }}</span>
          <span class="tab-label">{{ tab.label }}</span>
        </router-link>
      </nav>

      <div class="nav-right">
        <div class="avatar-btn" @click="showProfile = true">
          <span class="avatar-text">{{ auth.username?.[0]?.toUpperCase() || '?' }}</span>
        </div>
      </div>
    </header>

    <main class="app-content">
      <router-view />
    </main>

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
                ✨ Floo！
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
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const showProfile = ref(false)

const tabs = [
  { path: '/learning', label: '学习', icon: '📖' },
  { path: '/dictionary', label: '单词', icon: '📚' },
  { path: '/review', label: '复习', icon: '🔄' },
  { path: '/checkin', label: '打卡', icon: '📅' },
]

function isActive(path: string) {
  return route.path === path || route.path.startsWith(path + '/')
}

function handleLogout() {
  auth.logout()
  showProfile.value = false
  router.push('/login')
}
</script>

<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

/* ===== 顶栏 ===== */
.top-nav {
  position: fixed;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: 480px;
  display: flex;
  align-items: center;
  padding: 0 12px;
  height: 52px;
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
  z-index: 90;
  gap: 8px;
}

.nav-left {
  flex-shrink: 0;
}

.logo-link {
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 6px;
}

.logo-img {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  object-fit: contain;
}

.logo-text {
  color: white;
  font-size: 18px;
  font-weight: 800;
}

/* ===== Tabs ===== */
.nav-tabs {
  display: flex;
  gap: 2px;
  flex: 1;
  justify-content: center;
}

.tab-item {
  display: flex;
  align-items: center;
  gap: 3px;
  padding: 6px 10px;
  border-radius: 20px;
  text-decoration: none;
  color: rgba(255, 255, 255, 0.7);
  font-size: 13px;
  font-weight: 500;
  transition: all 0.2s;
  white-space: nowrap;
}

.tab-item:hover {
  color: white;
  background: rgba(255, 255, 255, 0.15);
}

.tab-item.active {
  color: white;
  background: rgba(255, 255, 255, 0.25);
  font-weight: 600;
}

.tab-icon {
  font-size: 15px;
}

.tab-label {
  font-size: 12px;
}

/* ===== 头像 ===== */
.nav-right {
  flex-shrink: 0;
}

.avatar-btn {
  width: 34px;
  height: 34px;
  background: rgba(255, 255, 255, 0.25);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.2s;
}

.avatar-btn:hover {
  background: rgba(255, 255, 255, 0.4);
}

.avatar-text {
  color: white;
  font-size: 15px;
  font-weight: 700;
}

/* ===== 内容区 ===== */
.app-content {
  flex: 1;
  padding-top: 52px;
  padding-bottom: env(safe-area-inset-bottom, 0px);
}

/* ===== Profile Sheet ===== */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.3);
  z-index: 150;
}

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
  padding-bottom: calc(20px + env(safe-area-inset-bottom, 0px));
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

.username {
  font-size: 18px;
  font-weight: 600;
}

.sheet-item {
  display: block;
  padding: 14px 0;
  font-size: 16px;
  color: var(--on-surface);
  text-decoration: none;
  cursor: pointer;
  border-bottom: 1px solid var(--surface-container);
}

.sheet-item.danger {
  color: var(--error);
}
</style>
