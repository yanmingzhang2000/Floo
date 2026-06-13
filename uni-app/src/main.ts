import { createSSRApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'

export function createApp() {
  const app = createSSRApp(App)
  app.use(createPinia())
  return { app }
}

// 全局登录拦截：未登录用户自动跳转到登录页
// 注意：在 uni-app 里没有 vue-router 那种全局守卫，需要在每个 onShow 自己判断
// 这里先放在 App.vue 的 onLaunch 里
