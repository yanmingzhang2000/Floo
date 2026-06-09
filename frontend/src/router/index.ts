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
        { path: '', redirect: '/daily' },
        { path: 'daily', name: 'daily', component: () => import('@/views/daily/DailyPage.vue') },
        { path: 'dictation', name: 'dictation', component: () => import('@/views/dictation/DictationPage.vue') },
        { path: 'review', name: 'review', component: () => import('@/views/review/ReviewPage.vue') },
        { path: 'checkin', name: 'checkin', component: () => import('@/views/checkin/CheckinPage.vue') },
      ],
    },
    { path: '/daily/list', name: 'daily-list', component: () => import('@/views/daily/DailyListPage.vue') },
    { path: '/daily/content/:id', name: 'daily-detail', component: () => import('@/views/daily/DailyDetailPage.vue') },
    { path: '/weekly', name: 'weekly', component: () => import('@/views/weekly/WeeklyPage.vue') },
    { path: '/favorites', name: 'favorites', component: () => import('@/views/FavoritesPage.vue') },
    { path: '/preference', name: 'preference', component: () => import('@/views/profile/PreferencePage.vue') },
  ],
})

router.beforeEach((to) => {
  const userId = localStorage.getItem('user_id')
  if (to.name !== 'login' && !userId) {
    return { name: 'login' }
  }
  if (to.name === 'login' && userId) {
    return { name: 'daily' }
  }
})

export default router
