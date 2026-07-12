<script setup lang="ts">
import { onLaunch } from '@dcloudio/uni-app'
import { storage } from '@/utils/storage'

onLaunch(() => {
  // 全局登录态检查：未登录跳登录页
  const userId = storage.get('user_id')
  const expiry = storage.getNumber('session_expiry')
  if (expiry && Date.now() > expiry) {
    // 过期了，清登录态
    storage.remove('user_id')
    storage.remove('username')
    storage.remove('session_expiry')
  }
  if (!userId || (expiry && Date.now() > expiry)) {
    setTimeout(() => {
      uni.reLaunch({ url: '/pages/login/index' })
    }, 0)
  }
})
</script>

<style>
@import './static/styles/main.css';
</style>
