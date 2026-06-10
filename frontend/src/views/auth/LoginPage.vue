<template>
  <div class="page-container">
    <div class="login-page">
      <div class="logo-area">
        <div class="logo-icon">F</div>
        <h1>Floo! 飞路一下</h1>
        <p>送给对这个世界有一点点好奇的你</p>
      </div>

      <form @submit.prevent="handleSubmit" class="login-form">
        <div v-if="error" class="error-msg">{{ error }}</div>

        <div class="input-group">
          <input v-model="form.username" type="text" placeholder="用户名（至少3位）" required minlength="3" />
        </div>

        <div class="input-group">
          <input v-model="form.password" type="password" placeholder="密码（至少6位）" required minlength="6" />
        </div>

        <button type="submit" class="btn btn-primary btn-block btn-lg" :disabled="loading">
          <span v-if="loading" class="spinner-sm"></span>
          {{ isRegister ? '注册' : '登录' }}
        </button>

        <p class="switch-mode" @click="isRegister = !isRegister">
          {{ isRegister ? '已有账号？去登录' : '没有账号？立即注册' }}
        </p>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { userApi } from '@/api'
import { useAuthStore } from '@/stores'

const router = useRouter()
const auth = useAuthStore()

const isRegister = ref(false)
const loading = ref(false)
const error = ref('')
const form = reactive({ username: '', password: '' })

// 页面加载时读取保存的账号密码
onMounted(() => {
  const saved = localStorage.getItem('floo_saved_credentials')
  if (saved) {
    try {
      const { username, password } = JSON.parse(saved)
      form.username = username || ''
      form.password = password || ''
    } catch { /* ignore */ }
  }
})

// 保存账号密码到本地
function saveCredentials() {
  localStorage.setItem('floo_saved_credentials', JSON.stringify({
    username: form.username,
    password: form.password,
  }))
}

async function handleSubmit() {
  loading.value = true
  error.value = ''
  try {
    const { data } = isRegister.value
      ? await userApi.register(form)
      : await userApi.login(form)
    // 登录/注册成功后保存账号密码
    saveCredentials()
    auth.setSession(data.user_id, data.username)
    router.push('/learning')
  } catch (e: any) {
    error.value = e.response?.data?.detail || '操作失败，请重试'
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
  padding: 20px;
}

.logo-area {
  text-align: center;
  margin-bottom: 40px;
}

.logo-icon {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36px;
  font-weight: 800;
  color: white;
  margin: 0 auto 16px;
}

.logo-area h1 {
  font-size: 28px;
  color: var(--primary);
}

.logo-area p {
  color: var(--on-surface-variant);
  margin-top: 4px;
  font-size: 14px;
}

.login-form {
  width: 100%;
  max-width: 360px;
}

.login-form input {
  width: 100%;
  padding: 14px 16px;
  border: 1.5px solid var(--outline);
  border-radius: var(--radius);
  font-size: 16px;
  margin-bottom: 14px;
  outline: none;
  transition: border-color 0.2s;
}

.login-form input:focus {
  border-color: var(--primary);
}

.error-msg {
  color: var(--error);
  font-size: 14px;
  margin-bottom: 12px;
  text-align: center;
}

.switch-mode {
  text-align: center;
  margin-top: 20px;
  color: var(--primary);
  font-size: 14px;
  cursor: pointer;
}

.switch-mode:hover { text-decoration: underline; }

.spinner-sm {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  display: inline-block;
}
</style>
