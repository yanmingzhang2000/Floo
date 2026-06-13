import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory('/Floo/'),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/auth/LoginPage.vue'),
    },
    {
      path: '/',
      component: () => import('@/components/TabBar.vue'),
      children: [
        { path: '', redirect: '/learning' },
        { path: 'learning', name: 'learning', component: () => import('@/views/daily/DailyPage.vue') },
        { path: 'dictionary', name: 'dictionary', component: () => import('@/views/FavoritesPage.vue') },
        { path: 'review', name: 'review', component: () => import('@/views/review/ReviewPage.vue') },
        { path: 'checkin', name: 'checkin', component: () => import('@/views/checkin/CheckinPage.vue') },
        { path: 'shop', name: 'shop', component: () => import('@/views/shop/ShopPage.vue') },
        { path: 'preference', name: 'preference', component: () => import('@/views/profile/PreferencePage.vue') },
      ],
    },
    { path: '/learning/list', name: 'daily-list', component: () => import('@/views/daily/DailyListPage.vue') },
    { path: '/learning/content/:id', name: 'daily-detail', component: () => import('@/views/daily/DailyDetailPage.vue') },
    { path: '/weekly', name: 'weekly', component: () => import('@/views/weekly/WeeklyPage.vue') },
    { path: '/landing', name: 'landing', component: () => import('@/views/LandingPage.vue') },
  ],
})

router.beforeEach((to) => {
  const userId = localStorage.getItem('user_id')
  if (to.name === 'landing') return
  if (to.name !== 'login' && !userId) {
    return { name: 'login' }
  }
  if (to.name === 'login' && userId) {
    return { name: 'learning' }
  }
})

export default router
