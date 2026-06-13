<template>
  <view class="page-container">
    <view class="login-page">
      <view class="logo-area">
        <view class="logo-icon">
          <text class="logo-letter">F</text>
        </view>
        <text class="logo-title">Floo! 飞路一下</text>
        <text class="logo-subtitle">送给对这个世界有一点点好奇的你</text>
      </view>

      <view class="login-form">
        <view v-if="error" class="error-msg">
          <text>{{ error }}</text>
        </view>

        <view class="input-group">
          <input
            v-model="form.username"
            type="text"
            placeholder="用户名（至少3位）"
            placeholder-style="color: #999"
            class="form-input"
          />
        </view>

        <view class="input-group">
          <input
            v-model="form.password"
            password
            placeholder="密码（至少6位）"
            placeholder-style="color: #999"
            class="form-input"
          />
        </view>

        <view class="remember-me" @tap="rememberMe = !rememberMe">
          <view class="checkbox" :class="{ checked: rememberMe }">
            <text v-if="rememberMe" class="check-icon">✓</text>
          </view>
          <text class="remember-text">30天内免登录</text>
        </view>

        <button
          class="btn btn-primary btn-block btn-lg"
          :disabled="loading || !canSubmit"
          @tap="handleSubmit"
        >
          <text v-if="loading">{{ isRegister ? '注册中...' : '登录中...' }}</text>
          <text v-else>{{ isRegister ? '注册' : '登录' }}</text>
        </button>

        <view class="switch-mode" @tap="isRegister = !isRegister">
          <text>{{ isRegister ? '已有账号？去登录' : '没有账号？立即注册' }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { userApi } from '@/api'
import { useAuthStore } from '@/stores'
import { storage } from '@/utils/storage'
import { navReLaunch } from '@/utils/router'

const auth = useAuthStore()
const isRegister = ref(false)
const loading = ref(false)
const error = ref('')
const form = ref({ username: '', password: '' })
const rememberMe = ref(true)

const canSubmit = computed(() => {
  return form.value.username.trim().length >= 3 && form.value.password.trim().length >= 6
})

onMounted(() => {
  const saved = storage.getJSON<{ username: string; password: string }>('floo_saved_credentials')
  if (saved) {
    form.value.username = saved.username || ''
    form.value.password = saved.password || ''
  }
})

function saveCredentials() {
  storage.setJSON('floo_saved_credentials', {
    username: form.value.username,
    password: form.value.password,
  })
}

async function handleSubmit() {
  if (!canSubmit.value) return
  loading.value = true
  error.value = ''
  try {
    const apiCall = isRegister.value ? userApi.register : userApi.login
    const { data } = await apiCall(form.value)
    saveCredentials()
    auth.setSession(data.user_id, data.username, rememberMe.value)
    uni.showToast({ title: isRegister.value ? '注册成功' : '登录成功', icon: 'success', duration: 1500 })
    setTimeout(() => navReLaunch('/pages/learning/index'), 1500)
  } catch (e: any) {
    error.value = e.data?.detail || e.errMsg || '操作失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 40rpx;
}
.logo-area {
  text-align: center;
  margin-bottom: 80rpx;
}
.logo-icon {
  width: 160rpx;
  height: 160rpx;
  background: linear-gradient(135deg, #5B9AA8 0%, #7FB3BE 100%);
  border-radius: 40rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 32rpx;
}
.logo-letter {
  font-size: 72rpx;
  font-weight: 800;
  color: white;
}
.logo-title {
  font-size: 56rpx;
  color: #5B9AA8;
  font-weight: 700;
  display: block;
  margin-bottom: 16rpx;
}
.logo-subtitle {
  color: #6F7680;
  font-size: 28rpx;
  display: block;
}
.login-form {
  width: 100%;
  max-width: 720rpx;
}
.form-input {
  width: 100%;
  padding: 28rpx 32rpx;
  border: 3rpx solid #C4C9CE;
  border-radius: 16rpx;
  font-size: 32rpx;
  background: #fff;
  box-sizing: border-box;
}
.input-group {
  margin-bottom: 28rpx;
}
.error-msg {
  color: #BA1A1A;
  font-size: 28rpx;
  margin-bottom: 24rpx;
  text-align: center;
  padding: 20rpx;
  background: #FFEBEE;
  border-radius: 16rpx;
}
.remember-me {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-bottom: 32rpx;
  font-size: 28rpx;
  color: #6F7680;
}
.checkbox {
  width: 36rpx;
  height: 36rpx;
  border: 3rpx solid #C4C9CE;
  border-radius: 8rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
}
.checkbox.checked {
  background: #5B9AA8;
  border-color: #5B9AA8;
}
.check-icon {
  color: white;
  font-size: 24rpx;
  font-weight: 700;
}
.remember-text {
  flex: 1;
}
.switch-mode {
  text-align: center;
  margin-top: 40rpx;
  color: #5B9AA8;
  font-size: 28rpx;
  padding: 20rpx;
}
</style>