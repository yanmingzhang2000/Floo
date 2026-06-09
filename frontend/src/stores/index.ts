import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { userApi } from '@/api'
import type { UserPreference, PointAccount } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const userId = ref<number | null>(Number(localStorage.getItem('user_id')) || null)
  const username = ref<string | null>(localStorage.getItem('username'))
  const preference = ref<UserPreference | null>(null)

  const isLoggedIn = computed(() => userId.value !== null)
  const currentUserId = computed(() => userId.value ?? 1)

  function setSession(id: number, name: string) {
    userId.value = id
    username.value = name
    localStorage.setItem('user_id', String(id))
    localStorage.setItem('username', name)
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
    localStorage.removeItem('user_id')
    localStorage.removeItem('username')
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
