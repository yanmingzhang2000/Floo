<template>
  <view class="login-page">
    <view class="login-bg"></view>
    <view class="login-content">
      <view class="logo-area">
        <view class="logo-circle">
          <text class="logo-letter">F</text>
        </view>
        <text class="logo-title">Floo!</text>
        <text class="logo-subtitle">献给对世界有一点点好奇的你</text>
      </view>

      <view v-if="error" class="login-error">
        <text>{{ error }}</text>
      </view>

      <!-- #ifdef MP-WEIXIN -->
      <view class="wx-section">
        <button class="btn-wx" :disabled="loading" @tap="handleWechatLogin">
          <text>微信一键登录</text>
        </button>
        <view class="divider">
          <view class="divider-line"></view>
          <text class="divider-text">其他方式</text>
          <view class="divider-line"></view>
        </view>
      </view>
      <!-- #endif -->

      <view class="form-section">
        <view class="input-group">
          <input v-model="form.username" type="text" placeholder="用户名" placeholder-class="input-placeholder" class="form-input" />
        </view>
        <view class="input-group">
          <input v-model="form.password" password placeholder="密码" placeholder-class="input-placeholder" class="form-input" />
        </view>

        <button class="btn btn-primary btn-block btn-lg" :disabled="loading || !canSubmit" @tap="handleSubmit">
          <text v-if="loading">{{ isRegister ? '注册中...' : '登录中...' }}</text>
          <text v-else>{{ isRegister ? '注册' : '登录' }}</text>
        </button>

        <view class="form-footer">
          <text class="form-switch" @tap="isRegister = !isRegister">
            {{ isRegister ? '已有账号？去登录' : '没有账号？立即注册' }}
          </text>
          <label class="remember-me" @tap="rememberMe = !rememberMe">
            <view class="checkbox" :class="{ checked: rememberMe }">
              <text v-if="rememberMe" class="check-icon">✓</text>
            </view>
            <text class="remember-text">30天内免登录</text>
          </label>
        </view>
      </view>

      <view class="privacy-links">
        <text class="privacy-link">隐私协议</text>
        <text class="privacy-dot">·</text>
        <text class="privacy-link">用户协议</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { userApi } from '@/api'
import { storage } from '@/utils/storage'
import { navReLaunch } from '@/utils/router'

const loading = ref(false)
const error = ref('')
const isRegister = ref(false)
const rememberMe = ref(true)
const form = ref({ username: '', password: '' })

const canSubmit = computed(() => form.value.username.length >= 3 && form.value.password.length >= 6)

async function handleSubmit() {
  loading.value = true; error.value = ''
  try {
    const api = isRegister.value ? userApi.register : userApi.login
    const { data } = await api(form.value.username, form.value.password)
    storage.set('user_id', data.user_id)
    storage.set('username', data.username)
    if (rememberMe.value) {
      storage.set('session_expiry', Date.now() + 30 * 24 * 60 * 60 * 1000)
    }
    navReLaunch('/pages/learning/index')
  } catch (e: any) {
    error.value = e.data?.detail || e.errMsg || '操作失败，请重试'
  }
  loading.value = false
}

// #ifdef MP-WEIXIN
async function handleWechatLogin() {
  loading.value = true; error.value = ''
  try {
    const loginRes = await new Promise<UniApp.LoginRes>((resolve, reject) => {
      uni.login({ success: resolve, fail: reject })
    })
    const { data } = await userApi.wechatLogin(loginRes.code)
    storage.set('user_id', data.user_id)
    storage.set('username', data.username)
    navReLaunch('/pages/learning/index')
  } catch (e: any) {
    error.value = e.data?.detail || e.errMsg || '微信登录失败'
  }
  loading.value = false
}
// #endif
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #fff;
  position: relative;
}
.login-bg {
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 480rpx;
  background: linear-gradient(180deg, var(--primary-container) 0%, transparent 100%);
  opacity: 0.3;
}
.login-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 120rpx 48rpx 48rpx;
  position: relative;
  z-index: 1;
}

.logo-area { text-align: center; margin-bottom: 80rpx; }
.logo-circle {
  width: 128rpx; height: 128rpx;
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto 32rpx;
  box-shadow: 0 8rpx 32rpx rgba(91,154,168,0.25);
}
.logo-letter { font-size: 64rpx; font-weight: 800; color: white; }
.logo-title { font-size: 48rpx; font-weight: 800; display: block; color: var(--on-surface); }
.logo-subtitle { font-size: 26rpx; color: var(--on-surface-variant); margin-top: 12rpx; display: block; }

.login-error {
  background: var(--error-container); color: var(--error);
  padding: 20rpx 24rpx; border-radius: 16rpx; font-size: 26rpx;
  margin-bottom: 32rpx; text-align: center;
}

.wx-section { margin-bottom: 32rpx; }
.btn-wx {
  width: 100%; height: 100rpx; line-height: 100rpx;
  background: #07C160; color: white; font-size: 34rpx;
  font-weight: 600; border-radius: 24rpx; text-align: center;
  border: none; box-shadow: 0 4rpx 16rpx rgba(7,193,96,0.3);
}
.btn-wx[disabled] { opacity: 0.6; }

.form-section { flex: 1; }
.form-input {
  width: 100%;
  padding: 28rpx 32rpx;
  border: 3rpx solid var(--outline-variant);
  border-radius: 16rpx;
  font-size: 30rpx;
  background: var(--surface);
}
.form-input:focus { border-color: var(--primary); }

.form-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 32rpx;
}
.form-switch { font-size: 26rpx; color: var(--primary); }
.remember-me { display: flex; align-items: center; gap: 12rpx; }
.checkbox {
  width: 36rpx; height: 36rpx;
  border: 3rpx solid var(--outline); border-radius: 8rpx;
  display: flex; align-items: center; justify-content: center;
}
.checkbox.checked { background: var(--primary); border-color: var(--primary); }
.check-icon { color: white; font-size: 24rpx; font-weight: 700; }
.remember-text { font-size: 24rpx; color: var(--on-surface-variant); }

.privacy-links {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12rpx;
  padding: 32rpx 0 16rpx;
}
.privacy-link { font-size: 22rpx; color: var(--on-surface-muted); }
.privacy-dot { font-size: 22rpx; color: var(--on-surface-muted); }
</style>
