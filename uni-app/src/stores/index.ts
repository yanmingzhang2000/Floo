import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { userApi } from '@/api'
import type { UserPreference, PointAccount } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  function _checkSessionExpiry() {
    const expiry = uni.getStorageSync('session_expiry')
    if (expiry && Date.now() > Number(expiry)) {
      uni.removeStorageSync('user_id')
      uni.removeStorageSync('username')
      uni.removeStorageSync('session_expiry')
      return null
    }
    return Number(uni.getStorageSync('user_id')) || null
  }

  const userId = ref<number | null>(_checkSessionExpiry())
  const username = ref<string | null>(uni.getStorageSync('username'))
  const preference = ref<UserPreference | null>(null)

  const isLoggedIn = computed(() => userId.value !== null)
  const currentUserId = computed(() => userId.value ?? 1)

  function setSession(id: number, name: string, rememberMe = false) {
    userId.value = id
    username.value = name
    uni.setStorageSync('user_id', String(id))
    uni.setStorageSync('username', name)
    if (rememberMe) {
      uni.setStorageSync('session_expiry', String(Date.now() + 30 * 24 * 60 * 60 * 1000))
    } else {
      uni.removeStorageSync('session_expiry')
    }
  }

  async function fetchPreference() {
    try {
      const { data } = await userApi.getPreference(currentUserId.value)
      preference.value = data
    } catch {
      preference.value = { difficulty_level: 'medium', theme_type: 'daily_news', daily_goal_minutes: 15 }
    }
  }

  function logout() {
    userId.value = null
    username.value = null
    preference.value = null
    uni.removeStorageSync('user_id')
    uni.removeStorageSync('username')
    uni.removeStorageSync('session_expiry')
    uni.removeStorageSync('floo_saved_credentials')
  }

  return { userId, username, preference, isLoggedIn, currentUserId, setSession, fetchPreference, logout }
})

export const usePreferenceStore = defineStore('preference', () => {
  const preference = ref<UserPreference | null>(null)
  const loading = ref(false)

  async function fetchPreference(userId: number) {
    loading.value = true
    try {
      const { data } = await userApi.getPreference(userId)
      preference.value = data
    } catch {
      preference.value = { difficulty_level: 'medium', theme_type: 'daily_news', daily_goal_minutes: 15 }
    } finally {
      loading.value = false
    }
  }

  async function updatePreference(userId: number, data: Partial<UserPreference>) {
    const { data: updated } = await userApi.updatePreference(userId, data)
    preference.value = updated
  }

  return { preference, loading, fetchPreference, updatePreference }
})

export const usePointStore = defineStore('points', () => {
  const points = ref<PointAccount | null>(null)

  async function fetchPoints(userId: number) {
    try {
      const { data } = await userApi.getPoints(userId)
      points.value = data
    } catch {
      // ignore
    }
  }

  return { points, fetchPoints }
})
