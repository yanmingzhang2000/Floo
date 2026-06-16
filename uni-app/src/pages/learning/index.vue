<template>
  <view class="page-container">
    <view class="nav-bar">
      <view class="nav-left"></view>
      <text class="nav-title">每日学习</text>
      <view class="nav-right">
        <view class="nav-avatar" @tap="showProfile = true">
          <text>{{ usernameInitial }}</text>
        </view>
      </view>
    </view>

    <view v-if="loading" class="loading">
      <view class="spinner"></view>
    </view>

    <template v-else>
      <!-- 数据概览 -->
      <view class="stats-banner">
        <view class="stat-item">
          <text class="stat-icon">📅</text>
          <text class="stat-value">{{ streakDays }}</text>
          <text class="stat-label">连续学习</text>
        </view>
        <view class="stat-item">
          <text class="stat-icon">📖</text>
          <text class="stat-value">{{ totalCount }}</text>
          <text class="stat-label">今日篇数</text>
        </view>
        <view class="stat-item">
          <text class="stat-icon">⭐</text>
          <text class="stat-value">{{ pointBalance }}</text>
          <text class="stat-label">积分</text>
        </view>
      </view>

      <!-- 分类标签栏 -->
      <view class="underline-tabs">
        <view class="underline-tab" :class="{ active: activeTab === 'ai' }" @tap="switchTab('ai')">
          <text>AI生成</text>
        </view>
        <view class="underline-tab" :class="{ active: activeTab === 'custom' }" @tap="switchTab('custom')">
          <text>自定义</text>
        </view>
        <view class="underline-tab" :class="{ active: activeTab === 'books' }" @tap="switchTab('books')">
          <text>学书本</text>
        </view>
        <view class="underline-tab" :class="{ active: activeTab === 'past' }" @tap="switchTab('past')">
          <text>往期内容</text>
        </view>
      </view>

      <!-- ====== AI生成 Tab ====== -->
      <view v-if="activeTab === 'ai'">
        <!-- 生成按钮 -->
        <view class="gen-action">
          <button class="btn btn-primary btn-block" :disabled="generating || remainingCount <= 0" @tap="handleGenerate">
            <text>{{ generating ? '生成中...' : (remainingCount > 0 ? `✨ AI 生成 (${remainingCount})` : '今日已用完') }}</text>
          </button>
        </view>
        <view v-if="contents.length === 0" class="empty-state">
          <text class="icon">📝</text>
          <text class="empty-text">今日还没有学习内容</text>
          <text class="empty-hint">点击上方按钮生成</text>
        </view>
        <view v-else class="content-list">
          <view
            v-for="item in contents"
            :key="item.id"
            class="list-card"
            @tap="goDetail(item.id)"
          >
            <view class="list-card-header">
              <text class="tag tag-success">{{ themeLabels[item.theme_type] || item.theme_type }}</text>
              <text class="list-card-status" :class="learnedIds.includes(item.id) ? 'done' : 'todo'">
                {{ learnedIds.includes(item.id) ? '✅已学' : '未学' }}
              </text>
            </view>
            <text class="list-card-title">{{ item.title }}</text>
            <text class="list-card-desc">{{ item.article?.slice(0, 60) }}...</text>
          </view>
        </view>
      </view>

      <!-- ====== 自定义 Tab ====== -->
      <view v-if="activeTab === 'custom'">
        <view class="gen-action">
          <button class="btn btn-primary btn-block" @tap="showCustomContent = true">
            <text>📝 粘贴新文章</text>
          </button>
        </view>
        <view v-if="customContents.length === 0" class="empty-state">
          <text class="icon">📋</text>
          <text class="empty-text">暂无自定义内容</text>
          <text class="empty-hint">粘贴英文文章开始学习</text>
        </view>
        <view v-else class="content-list">
          <view
            v-for="item in customContents"
            :key="item.id"
            class="list-card"
            @tap="goDetail(item.id)"
          >
            <view class="list-card-header">
              <text class="tag tag-warning">自定义</text>
              <text class="list-card-status" :class="learnedIds.includes(item.id) ? 'done' : 'todo'">
                {{ learnedIds.includes(item.id) ? '✅已学' : '未学' }}
              </text>
            </view>
            <text class="list-card-title">{{ item.title }}</text>
            <text class="list-card-desc">{{ item.article?.slice(0, 60) }}...</text>
          </view>
        </view>
      </view>

      <!-- ====== 学书本 Tab ====== -->
      <view v-if="activeTab === 'books'">
        <!-- 搜索框 -->
        <view class="search-bar">
          <view class="search-input-wrap">
            <text class="search-icon">🔍</text>
            <input
              v-model="bookSearch"
              type="text"
              placeholder="搜索书名 / 作者..."
              placeholder-class="search-placeholder"
              class="search-input"
              @confirm="searchBooks"
            />
            <text v-if="bookSearch" class="search-clear" @tap="clearBookSearch">✕</text>
          </view>
        </view>

        <!-- 我的书架 -->
        <view v-if="myBooks.length > 0 && !bookSearch">
          <text class="section-title">我的书架</text>
          <view class="book-grid">
            <view
              v-for="book in myBooks"
              :key="book.gutenberg_id"
              class="book-card"
              @tap="goBookDetail(book.gutenberg_id)"
            >
              <image
                v-if="book.cover_url"
                :src="book.cover_url"
                class="book-cover"
                mode="aspectFill"
              />
              <view v-else class="book-cover book-cover-placeholder">
                <text>📖</text>
              </view>
              <text class="book-title">{{ book.cn_title || book.title }}</text>
              <text class="book-author">{{ book.author || book.authors?.[0]?.name || '未知作者' }}</text>
              <text class="book-progress">已学 {{ book.chapters_read || 0 }} 章</text>
            </view>
          </view>
        </view>

        <!-- 搜索结果 -->
        <view v-if="bookSearch && searchResults.length > 0">
          <text class="section-title">搜索结果</text>
          <view class="book-grid">
            <view
              v-for="book in searchResults"
              :key="book.id"
              class="book-card"
              @tap="goBookDetail(book.id)"
            >
              <image
                v-if="book.formats?.['image/jpeg']"
                :src="book.formats['image/jpeg']"
                class="book-cover"
                mode="aspectFill"
              />
              <view v-else class="book-cover book-cover-placeholder">
                <text>📖</text>
              </view>
              <text class="book-title">{{ book.cn_title || book.title }}</text>
              <text class="book-author">{{ book.authors?.[0]?.name || '未知作者' }}</text>
            </view>
          </view>
        </view>
        <view v-else-if="bookSearch && searchResults.length === 0 && !booksLoading" class="empty-state">
          <text class="icon">🔍</text>
          <text class="empty-text">未找到相关书籍</text>
        </view>

        <!-- 热门名著（无搜索时） -->
        <view v-if="!bookSearch">
          <text class="section-title">热门名著</text>
          <view v-if="booksLoading" class="loading" style="padding: 40rpx;">
            <view class="spinner"></view>
          </view>
          <view v-else class="book-grid">
            <view
              v-for="book in popularBooks"
              :key="book.id"
              class="book-card"
              @tap="goBookDetail(book.id)"
            >
              <image
                v-if="book.formats?.['image/jpeg']"
                :src="book.formats['image/jpeg']"
                class="book-cover"
                mode="aspectFill"
              />
              <view v-else class="book-cover book-cover-placeholder">
                <text>📖</text>
              </view>
              <text class="book-title">{{ book.cn_title || book.title }}</text>
              <text class="book-author">{{ book.authors?.[0]?.name || '未知作者' }}</text>
            </view>
          </view>
        </view>
      </view>

      <!-- ====== 往期内容 Tab ====== -->
      <view v-if="activeTab === 'past'">
        <view v-if="pastContents.length === 0" class="empty-state">
          <text class="icon">📋</text>
          <text class="empty-text">暂无往期内容</text>
          <text class="empty-hint">完成学习后内容会出现在这里</text>
        </view>
        <view v-else class="content-list">
          <view
            v-for="item in pastContents"
            :key="item.id"
            class="list-card"
            @tap="goDetail(item.id)"
          >
            <view class="list-card-header">
              <text class="tag tag-success">{{ themeLabels[item.theme_type] || item.theme_type }}</text>
              <text class="list-card-status done">✅已学</text>
            </view>
            <text class="list-card-title">{{ item.title }}</text>
            <text class="list-card-desc">{{ item.article?.slice(0, 60) }}...</text>
          </view>
        </view>
      </view>

      <!-- 底部固定按钮 -->
      <view v-if="activeTab !== 'books'" class="bottom-action">
        <button v-if="activeTab === 'ai' && contents.length > 0" class="btn btn-primary btn-block btn-lg" @tap="goDetail(contents[currentIdx]?.id)">
          <text>{{ learnedIds.includes(contents[currentIdx]?.id) ? '复习当前' : '开始学习' }}</text>
        </button>
        <button v-else-if="activeTab === 'past' && pastContents.length > 0" class="btn btn-primary btn-block btn-lg" @tap="goDetail(pastContents[0]?.id)">
          <text>复习最新</text>
        </button>
      </view>
    </template>

    <!-- 个人中心弹窗 -->
    <view v-if="showProfile" class="modal-overlay" @tap="showProfile = false">
      <view class="avatar-menu" @tap.stop>
        <view class="avatar-menu-user">
          <view class="avatar-menu-avatar"><text>{{ usernameInitial }}</text></view>
          <text class="avatar-menu-name">{{ auth.username || '未登录' }}</text>
        </view>
        <view class="avatar-menu-items">
          <view class="avatar-menu-item" @tap="goPreference">
            <text class="avatar-menu-item-icon">⚙️</text>
            <text>学习偏好</text>
          </view>
          <view class="avatar-menu-item" @tap="goShop">
            <text class="avatar-menu-item-icon">✨</text>
            <text>Floo！</text>
          </view>
          <view class="avatar-menu-item danger" @tap="handleLogout">
            <text class="avatar-menu-item-icon">🚪</text>
            <text>退出登录</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 自定义内容弹窗 -->
    <CustomContentModal :visible="showCustomContent" @close="showCustomContent = false" @created="onCustomCreated" />
    <OnboardingGuide />
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { dailyApi, generationLimitApi, checkinApi, shopApi, booksApi } from '@/api'
import { useAuthStore } from '@/stores'
import { navTo, navReLaunch } from '@/utils/router'
import { storage } from '@/utils/storage'
import type { LearningContent } from '@/types'
import CustomContentModal from '@/components/CustomContentModal.vue'
import OnboardingGuide from '@/components/OnboardingGuide.vue'

const auth = useAuthStore()
const loading = ref(true)
const generating = ref(false)
const contents = ref<LearningContent[]>([])
const customContents = ref<LearningContent[]>([])
const pastContents = ref<LearningContent[]>([])
const currentIdx = ref(0)
const learnedIds = ref<number[]>([])
const remainingCount = ref(3)
const showProfile = ref(false)
const showCustomContent = ref(false)
const streakDays = ref(0)
const pointBalance = ref(0)

const activeTab = ref<'ai' | 'custom' | 'books' | 'past'>('ai')

onLoad((options) => {
  if (options?.tab === 'custom') activeTab.value = 'custom'
  if (options?.tab === 'books') activeTab.value = 'books'
})

const bookSearch = ref('')
const searchResults = ref<any[]>([])
const popularBooks = ref<any[]>([])
const myBooks = ref<any[]>([])
const booksLoading = ref(false)

const themeLabels: Record<string, string> = {
  ai_tech: 'AI科技', product_tech: '产品技术', business: '财经商业',
  daily_news: '日常新闻', self_growth: '个人成长', all_random: '随机',
}
const totalCount = computed(() => contents.value.length)
const usernameInitial = computed(() => (auth.username?.[0] || '?').toUpperCase())

function switchTab(tab: typeof activeTab.value) {
  activeTab.value = tab
  if (tab === 'books' && popularBooks.value.length === 0) {
    loadPopularBooks()
  }
  if (tab === 'past' && pastContents.value.length === 0) {
    loadPastContents()
  }
  if (tab === 'custom' && customContents.value.length === 0) {
    loadCustomContents()
  }
}

async function loadData() {
  loading.value = true
  const userId = auth.currentUserId
  const safe = (p: Promise<any>) => p.catch(() => null)
  const [contentRes, limitRes, learnedRes, calendarRes, balanceRes] = await Promise.all([
    safe(dailyApi.getTodayList(userId)),
    safe(generationLimitApi.getLimit(userId)),
    safe(dailyApi.getLearnedIds(userId)),
    safe(checkinApi.getCalendar(userId, new Date().getFullYear(), new Date().getMonth() + 1)),
    safe(shopApi.getBalance(userId)),
  ])
  if (contentRes?.data) contents.value = contentRes.data.contents || []
  if (learnedRes?.data) learnedIds.value = learnedRes.data.content_ids || []
  if (limitRes?.data) remainingCount.value = limitRes.data.remaining_count ?? 3
  if (calendarRes?.data) streakDays.value = calendarRes.data.current_streak_days || 0
  if (balanceRes?.data) pointBalance.value = balanceRes.data.available_points || 0
  loading.value = false
}

async function loadCustomContents() {
  const userId = auth.currentUserId
  try {
    const { data } = await dailyApi.getCustomContents(userId)
    customContents.value = data?.contents || []
  } catch { customContents.value = [] }
}

function onCustomCreated() {
  // 创建成功后切到自定义 Tab 并刷新列表
  activeTab.value = 'custom'
  loadCustomContents()
}

async function loadPastContents() {
  const userId = auth.currentUserId
  try {
    const { data } = await dailyApi.getLearnedIds(userId)
    const ids = data?.content_ids || []
    if (ids.length > 0) {
      const safe = (p: Promise<any>) => p.catch(() => null)
      const results = await Promise.all(ids.slice(0, 20).map((id: number) => safe(dailyApi.getContent(id))))
      pastContents.value = results.filter((r: any) => r?.data).map((r: any) => r.data)
    }
  } catch { pastContents.value = [] }
}

async function loadPopularBooks() {
  booksLoading.value = true
  try {
    const { data } = await booksApi.getPopular(1)
    popularBooks.value = data?.results || []
  } catch { popularBooks.value = [] }
  booksLoading.value = false
}

async function searchBooks() {
  if (!bookSearch.value.trim()) return
  booksLoading.value = true
  try {
    const { data } = await booksApi.search(bookSearch.value.trim())
    searchResults.value = data?.results || []
  } catch { searchResults.value = [] }
  booksLoading.value = false
}

function clearBookSearch() {
  bookSearch.value = ''
  searchResults.value = []
}

async function handleGenerate() {
  if (remainingCount.value <= 0) {
    uni.showToast({ title: '今日生成次数已用完', icon: 'none' })
    return
  }
  generating.value = true
  try {
    const res: any = await dailyApi.generate(auth.currentUserId)
    if (res.statusCode && res.statusCode >= 400) {
      const msg = res.data?.detail || res.data?.message || `请求失败 (${res.statusCode})`
      uni.showToast({ title: msg, icon: 'none' })
      generating.value = false
      return
    }
    await loadData()
  } catch (e: any) {
    const msg = e?.errMsg || e?.message || '网络异常'
    uni.showToast({ title: msg, icon: 'none' })
  }
  generating.value = false
}

function goDetail(id: number) { navTo(`/pages/detail/index?id=${id}`) }
function goBookDetail(id: number) { navTo(`/pages/book-detail/index?id=${id}`) }
function goPreference() { navTo('/pages/preference/index') }
function goShop() { navTo('/pages/shop/index') }

function handleLogout() {
  uni.showModal({
    title: '退出登录',
    content: '确定退出当前账号？',
    success: (res) => {
      if (res.confirm) {
        storage.remove('user_id'); storage.remove('username'); storage.remove('session_expiry')
        navReLaunch('/pages/login/index')
      }
    },
  })
}

onShow(loadData)
</script>

<style scoped>
/* 分类标签栏 */
.underline-tabs {
  display: flex;
  border-bottom: 2rpx solid var(--outline-variant);
  margin-bottom: 20rpx;
}
.underline-tab {
  flex: 1;
  text-align: center;
  padding: 20rpx 0;
  font-size: 28rpx;
  color: var(--on-surface-variant);
  position: relative;
  transition: color 0.2s;
}
.underline-tab.active {
  color: var(--primary);
  font-weight: 700;
}
.underline-tab.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 60%;
  height: 6rpx;
  border-radius: 3rpx;
  background: var(--primary);
}

/* 生成按钮 */
.gen-action { padding: 16rpx 0; }

/* 内容列表 */
.content-list { padding: 8rpx 0; }
.list-card {
  background: #fff;
  border-radius: 20rpx;
  padding: 28rpx;
  margin-bottom: 16rpx;
  box-shadow: var(--shadow-sm);
}
.list-card:active { opacity: 0.85; }
.list-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12rpx;
}
.list-card-status { font-size: 22rpx; }
.list-card-status.done { color: var(--success); font-weight: 600; }
.list-card-status.todo { color: var(--on-surface-muted); }
.list-card-title {
  font-size: 30rpx;
  font-weight: 700;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 8rpx;
}
.list-card-desc {
  font-size: 26rpx;
  color: var(--on-surface-variant);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 搜索框 */
.search-bar { padding: 12rpx 0; }
.search-input-wrap {
  display: flex;
  align-items: center;
  background: #fff;
  border: 2rpx solid var(--outline-variant);
  border-radius: 40rpx;
  padding: 16rpx 24rpx;
  gap: 12rpx;
}
.search-icon { font-size: 28rpx; }
.search-input { flex: 1; font-size: 28rpx; }
.search-placeholder { color: var(--on-surface-muted); }
.search-clear { font-size: 28rpx; color: var(--on-surface-muted); padding: 8rpx; }

/* 区块标题 */
.section-title {
  font-size: 30rpx;
  font-weight: 700;
  display: block;
  padding: 20rpx 0 12rpx;
}

/* 书本网格 */
.book-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 20rpx;
  padding-bottom: 16rpx;
}
.book-card {
  width: calc(33.33% - 14rpx);
  background: #fff;
  border-radius: 16rpx;
  padding: 16rpx;
  box-shadow: var(--shadow-sm);
}
.book-card:active { opacity: 0.8; }
.book-cover {
  width: 100%;
  height: 200rpx;
  border-radius: 12rpx;
  margin-bottom: 12rpx;
  background: var(--surface-container);
}
.book-cover-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 48rpx;
}
.book-title {
  font-size: 24rpx;
  font-weight: 600;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.3;
  margin-bottom: 4rpx;
}
.book-author {
  font-size: 22rpx;
  color: var(--on-surface-muted);
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.book-progress {
  font-size: 22rpx;
  color: var(--primary);
  margin-top: 4rpx;
  display: block;
}

/* 空状态 */
.empty-state { padding: 60rpx 0; text-align: center; }
.empty-state .icon { font-size: 64rpx; display: block; margin-bottom: 16rpx; }
.empty-text { font-size: 28rpx; color: var(--on-surface-variant); display: block; }
.empty-hint { font-size: 24rpx; color: var(--on-surface-muted); display: block; margin-top: 8rpx; }

/* 底部按钮 */
.bottom-action { padding: 16rpx 0 32rpx; }

/* 标签 */
.tag {
  font-size: 20rpx;
  padding: 4rpx 16rpx;
  border-radius: 20rpx;
  font-weight: 600;
}
.tag-success { background: var(--success-container); color: var(--success); }
.tag-warning { background: #FFF3E0; color: #E65100; }
</style>
