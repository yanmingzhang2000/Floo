<script setup lang="ts">
import { onLaunch } from '@dcloudio/uni-app'
import { storage } from '@/utils/storage'

/**
 * 应用启动：登录态校验 + 每日首次启动展示首页
 *
 * Why 首页每天只展示一次：
 *   首页承载"品牌 + 连续天数 + 每日 CTA"的仪式感，塞进 tabBar 会挤掉
 *   四大功能位。本轮改造后首页从 tabBar 移除，改为每日第一次进入 App
 *   时用 redirectTo 展示一次，之后所有导航都走 tabBar 四页。
 */
onLaunch(() => {
  // ---- 1. 登录态校验 ----
  const userId = storage.get('user_id')
  const expiry = storage.getNumber('session_expiry')
  if (expiry && Date.now() > expiry) {
    log_expire()
    // 过期了，清登录态
    storage.remove('user_id')
    storage.remove('username')
    storage.remove('session_expiry')
  }
  if (!userId || (expiry && Date.now() > expiry)) {
    // 未登录：跳登录页，跳过每日欢迎逻辑
    console.debug('[App] 未登录/会话过期，跳转登录页')
    setTimeout(() => {
      uni.reLaunch({ url: '/pages/login/index' })
    }, 0)
    return
  }

  // ---- 2. 每日首次启动展示首页 ----
  const today = todayStr()
  const last = storage.get('last_home_shown_date')
  if (last === today) {
    // 今天已经进过首页，直接跳图书馆
    console.debug('[App] 今日已展示过首页，直接进图书馆')
    setTimeout(() => {
      uni.switchTab({ url: '/pages/learning/index' })
    }, 0)
    return
  }
  // 今日首次启动：记录日期后进首页
  console.debug('[App] 今日首次启动，展示首页欢迎屏')
  storage.set('last_home_shown_date', today)
  setTimeout(() => {
    uni.reLaunch({ url: '/pages/home/index' })
  }, 0)
})

// YYYY-MM-DD 本地日期字符串，用作每日 key
function todayStr(): string {
  const d = new Date()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${m}-${day}`
}

// 空函数占位（保留原 log 语义，供未来接入统一日志用）
function log_expire() {
  console.debug('[App] 会话已过期')
}
</script>

<style>
@import './static/styles/main.css';
</style>
