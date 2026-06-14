<template>
  <view class="page-container">
    <view class="nav-bar">
      <view class="nav-left"></view>
      <text class="nav-title">单词书</text>
      <view class="nav-right">
        <view class="nav-avatar" @tap="showProfile = true">
          <text>{{ usernameInitial }}</text>
        </view>
      </view>
    </view>

    <!-- 搜索栏 -->
    <view class="search-bar">
      <view class="search-input-wrap">
        <text class="search-icon">🔍</text>
        <input v-model="searchWord" type="text" placeholder="搜索英文单词..." placeholder-class="search-placeholder" class="search-input" @confirm="handleSearch" />
        <text v-if="searchWord" class="search-clear" @tap="searchWord = ''; searchResult = null">✕</text>
      </view>
      <button class="btn btn-primary btn-sm" @tap="handleSearch" :disabled="!searchWord.trim()">
        <text>搜索</text>
      </button>
    </view>

    <view class="underline-tabs">
      <view class="underline-tab" :class="{ active: activeTab === 'search' }" @tap="activeTab = 'search'">
        <text>查词结果</text>
      </view>
      <view class="underline-tab" :class="{ active: activeTab === 'favorites' }" @tap="activeTab = 'favorites'">
        <text>我的收藏 ({{ favorites.length }})</text>
      </view>
    </view>

    <view v-if="loading" class="loading">
      <view class="spinner"></view>
    </view>

    <template v-else>
      <!-- 查词结果 -->
      <view v-show="activeTab === 'search'">
        <view v-if="!searchResult && !searching" class="empty-state">
          <text class="icon">🔍</text>
          <text class="empty-text">在上方输入单词搜索</text>
          <text class="empty-hint">支持中英文查询</text>
        </view>
        <view v-if="searching" class="loading">
          <view class="spinner"></view>
        </view>
        <view v-if="searchResult && !searching" class="card search-result-card">
          <view class="search-result-header">
            <text class="search-result-word">{{ searchResult.word }}</text>
            <view class="search-result-actions">
              <view class="search-result-speak" @tap="playWord(searchResult.word!)"><text>🔊</text></view>
              <view class="search-result-fav" :class="{ 'is-fav': searchResult.isFavorite }" @tap="toggleFavorite(searchResult.word!)">
                <text>{{ searchResult.isFavorite ? '★' : '☆' }}</text>
              </view>
            </view>
          </view>
          <text v-if="searchResult.phonetic" class="search-result-phonetic">{{ searchResult.phonetic }}</text>
          <text class="search-result-meaning">{{ searchResult.meaning }}</text>
          <text v-if="searchResult.usage" class="search-result-usage">{{ searchResult.usage }}</text>
        </view>
      </view>

      <!-- 收藏列表 -->
      <view v-show="activeTab === 'favorites'">
        <view v-if="favorites.length === 0" class="empty-state">
          <text class="icon">📚</text>
          <text class="empty-text">还没有收藏单词</text>
          <text class="empty-hint">在阅读页点击单词即可收藏</text>
        </view>
        <view v-else class="fav-list">
          <view v-for="fav in favorites" :key="fav.id" class="card fav-item" @tap="playWord(fav.word)">
            <view class="fav-main">
              <text class="fav-word">{{ fav.word }}</text>
              <view class="fav-remove" @tap.stop="handleRemove(fav.word)">
                <text>★</text>
              </view>
            </view>
            <text v-if="fav.phonetic" class="fav-phonetic">{{ fav.phonetic }}</text>
            <text class="fav-meaning">{{ fav.meaning }}</text>
          </view>
        </view>
      </view>
    </template>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { favoritesApi, dictionaryApi } from '@/api'
import { useAuthStore } from '@/stores'
import { speakWord } from '@/composables/useSpeech'

const auth = useAuthStore()
const loading = ref(true)
const searching = ref(false)
const searchWord = ref('')
const activeTab = ref<'search' | 'favorites'>('search')
const searchResult = ref<{
  word?: string; phonetic?: string; meaning: string; usage?: string; isFavorite?: boolean
} | null>(null)
const favorites = ref<Array<{
  id: number; word: string; phonetic?: string; meaning?: string; source?: string; created_at: string
}>>([])

const usernameInitial = computed(() => (auth.username?.[0] || '?').toUpperCase())

async function handleSearch() {
  const word = searchWord.value.trim()
  if (!word) return
  searching.value = true
  activeTab.value = 'search'
  searchResult.value = null
  try {
    const { data } = await dictionaryApi.lookup(word)
    const ec = data?.ec?.word?.[0]
    const phonetic = ec?.usphone || ec?.ukphone || ''
    const trs = ec?.trs || []
    const meaning = trs.map((t: any) => t?.tr?.[0]?.l?.i?.[0]).filter(Boolean).join('；')
    const baseWord = ec?.word?.[0]?.returnPhrase || word

    // 检查是否已收藏
    let isFavorite = false
    try {
      const { data: favData } = await favoritesApi.check(auth.currentUserId, baseWord)
      isFavorite = favData?.is_favorited || false
    } catch {}

    searchResult.value = {
      word: baseWord,
      phonetic: phonetic ? `/${phonetic}/` : undefined,
      meaning: meaning || '未找到释义',
      isFavorite,
    }
  } catch { searchResult.value = { word, meaning: '查询失败' } }
  searching.value = false
}

async function toggleFavorite(word: string) {
  try {
    if (searchResult.value?.isFavorite) {
      await favoritesApi.remove(auth.currentUserId, word)
      searchResult.value.isFavorite = false
    } else {
      await favoritesApi.add(auth.currentUserId, word)
      searchResult.value.isFavorite = true
    }
    loadFavorites()
  } catch {}
}

function playWord(word: string) { speakWord(word) }

async function handleRemove(word: string) {
  uni.showModal({
    title: '取消收藏',
    content: `确定取消收藏 "${word}" 吗？`,
    success: async (res) => {
      if (res.confirm) {
        try {
          await favoritesApi.remove(auth.currentUserId, word)
          favorites.value = favorites.value.filter(f => f.word !== word)
        } catch {}
      }
    },
  })
}

async function loadFavorites() {
  try {
    const { data } = await favoritesApi.list(auth.currentUserId)
    favorites.value = data || []
  } catch { favorites.value = [] }
}

async function loadData() {
  loading.value = true
  await loadFavorites()
  loading.value = false
}

onShow(loadData)
</script>

<style scoped>
.search-bar {
  display: flex; align-items: center; gap: 16rpx;
  padding: 20rpx 0;
  background: #fff;
  border-bottom: 2rpx solid var(--outline-variant);
}
.search-input-wrap {
  flex: 1;
  display: flex; align-items: center;
  background: var(--surface);
  border-radius: 16rpx;
  padding: 0 20rpx;
  border: 3rpx solid var(--outline-variant);
}
.search-icon { font-size: 28rpx; margin-right: 12rpx; }
.search-input {
  flex: 1; height: 72rpx; font-size: 28rpx; background: transparent; border: none;
}
.search-placeholder { color: var(--on-surface-muted); }
.search-clear { font-size: 28rpx; color: var(--on-surface-muted); padding: 8rpx; }

.search-result-card { margin: 24rpx 0; }
.search-result-header {
  display: flex; align-items: center; justify-content: space-between; margin-bottom: 16rpx;
}
.search-result-word { font-size: 40rpx; font-weight: 700; }
.search-result-actions { display: flex; gap: 16rpx; }
.search-result-speak, .search-result-fav {
  width: 64rpx; height: 64rpx; border-radius: 50%;
  display: flex; align-items: center; justify-content: center; font-size: 32rpx;
}
.search-result-speak { background: var(--primary-container); }
.search-result-fav { background: var(--surface-container); font-size: 36rpx; }
.search-result-fav.is-fav { color: #f59e0b; }
.search-result-phonetic { color: var(--on-surface-variant); font-size: 26rpx; display: block; margin-bottom: 12rpx; }
.search-result-meaning { font-size: 30rpx; line-height: 1.6; display: block; }
.search-result-usage { margin-top: 16rpx; color: var(--on-surface-variant); font-size: 26rpx; display: block; }

.fav-list { padding: 16rpx 0; }
.fav-item { padding: 28rpx; }
.fav-main { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8rpx; }
.fav-word { font-size: 34rpx; font-weight: 600; }
.fav-remove { font-size: 36rpx; color: #f59e0b; padding: 8rpx; }
.fav-phonetic { font-size: 24rpx; color: var(--on-surface-variant); display: block; margin-bottom: 8rpx; }
.fav-meaning { font-size: 26rpx; color: var(--on-surface-variant); display: block; }
</style>
