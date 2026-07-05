<template>
  <view class="page-container">
    <view class="nav-bar">
      <view class="nav-left"></view>
      <text class="nav-title">我的单词书</text>
      <view class="nav-right"></view>
    </view>

    <view v-if="loading" class="loading">
      <view class="spinner"></view>
    </view>

    <template v-else>
      <!-- 搜索栏：全局，同时支持筛选收藏和查新词 -->
      <view class="search-bar">
        <view class="search-input-wrap">
          <text class="search-icon">🔍</text>
          <input
            v-model="searchWord"
            type="text"
            placeholder="搜索单词或释义..."
            placeholder-class="search-placeholder"
            class="search-input"
            @input="onSearchInput"
            @confirm="onSearchConfirm"
          />
          <text v-if="searchWord" class="search-clear" @tap="clearSearch">✕</text>
        </view>
      </view>

      <!-- 背单词入口 -->
      <view class="vb-entry" @tap="goVocabReview">
        <view class="vb-entry-left">
          <text class="vb-entry-icon">📖</text>
          <view>
            <text class="vb-entry-title">背单词</text>
            <text class="vb-entry-desc">选义 + 默写，间隔重复记忆</text>
          </view>
        </view>
        <text class="vb-entry-arrow">›</text>
      </view>

      <!-- 查词结果弹出层 -->
      <view v-if="dictResult" class="card dict-result-card">
        <view class="dict-header">
          <text class="dict-word">{{ dictResult.word }}</text>
          <view class="dict-actions">
          <view class="btn-icon dict-btn" @tap="playWord(dictResult.word!)"><text>🔊</text></view>
            <view class="btn-icon dict-btn" :class="{ 'is-active': dictResult.isFavorite }" @tap="toggleDictFavorite">
              <text>{{ dictResult.isFavorite ? '★' : '☆' }}</text>
            </view>
          </view>
        </view>
        <text v-if="dictResult.phonetic" class="dict-phonetic">{{ dictResult.phonetic }}</text>
        <text class="dict-meaning">{{ dictResult.meaning }}</text>
      </view>

      <!-- 单词列表 -->
      <view v-if="filteredFavorites.length > 0" class="word-list">
        <view
          v-for="fav in filteredFavorites"
          :key="fav.id"
          class="card word-item"
        >
          <view class="word-main">
            <view class="word-info" @tap="playWord(fav.word)">
              <text class="word-text">{{ fav.word }}</text>
              <text v-if="fav.phonetic" class="word-phonetic">{{ fav.phonetic }}</text>
              <text class="word-meaning">{{ fav.meaning }}</text>
            </view>
            <view class="word-actions">
              <view class="btn-icon remove-btn" @tap="handleRemove(fav.word)">
                <text>✕</text>
              </view>
            </view>
          </view>
        </view>
      </view>

      <!-- 空状态 -->
      <view v-else-if="!dictResult" class="empty-state">
        <text class="icon">📚</text>
        <text class="empty-text">{{ searchWord ? '没有匹配的单词' : '还没有收藏单词哦' }}</text>
        <text class="empty-hint">{{ searchWord ? '换个关键词试试' : '在学习页面点击单词即可收藏，这里会显示你的专属词书' }}</text>
        <button v-if="!searchWord" class="btn btn-primary btn-sm" style="margin-top: 32rpx;" @tap="navToDict">
          <text>去查词</text>
        </button>
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
import { navTo } from '@/utils/router'

interface FavWord {
  id: number; word: string; phonetic?: string; meaning?: string;
  source?: string; is_mastered: boolean; created_at: string
}

const auth = useAuthStore()
const loading = ref(true)
const searchWord = ref('')
const favorites = ref<FavWord[]>([])

const dictResult = ref<{
  word?: string; phonetic?: string; meaning: string; isFavorite?: boolean
} | null>(null)

const filteredFavorites = computed(() => {
  let list = favorites.value
  if (searchWord.value.trim()) {
    const q = searchWord.value.trim().toLowerCase()
    list = list.filter(f => f.word.includes(q) || (f.meaning || '').toLowerCase().includes(q))
  }
  return list
})

function onSearchInput() {
  // 实时筛选收藏列表，如果输入的内容不在收藏中则清空查词结果
  if (dictResult.value && searchWord.value.trim().toLowerCase() !== dictResult.value.word?.toLowerCase()) {
    dictResult.value = null
  }
}

async function onSearchConfirm() {
  const word = searchWord.value.trim()
  if (!word) return
  // 如果收藏里有这个单词，直接筛选；同时查词典获取详细释义
  const matched = favorites.value.find(f => f.word === word.toLowerCase())
  if (!matched) {
    // 收藏里没有，查词典
    await lookupWord(word)
  } else {
    dictResult.value = {
      word: matched.word,
      phonetic: matched.phonetic,
      meaning: matched.meaning || '',
      isFavorite: true,
    }
  }
}

async function lookupWord(word: string) {
  try {
    const { data } = await dictionaryApi.lookup(word)
    const ec = data?.ec?.word?.[0]
    const phonetic = ec?.usphone || ec?.ukphone || ''
    const trs = ec?.trs || []
    const meaning = trs.map((t: any) => t?.tr?.[0]?.l?.i?.[0]).filter(Boolean).join('；')
    const baseWord = ec?.word?.[0]?.returnPhrase || word

    let isFavorite = false
    try {
      const { data: favData } = await favoritesApi.check(auth.currentUserId, baseWord)
      isFavorite = favData?.is_favorite || false
    } catch {}

    dictResult.value = {
      word: baseWord,
      phonetic: phonetic ? `/${phonetic}/` : undefined,
      meaning: meaning || '未找到释义',
      isFavorite,
    }
  } catch {
    dictResult.value = { word, meaning: '查询失败' }
  }
}

async function toggleDictFavorite() {
  if (!dictResult.value?.word) return
  const word = dictResult.value.word
  try {
    if (dictResult.value.isFavorite) {
      await favoritesApi.remove(auth.currentUserId, word)
      dictResult.value.isFavorite = false
      favorites.value = favorites.value.filter(f => f.word !== word)
    } else {
      await favoritesApi.add(auth.currentUserId, word, dictResult.value.phonetic, dictResult.value.meaning)
      dictResult.value.isFavorite = true
      await loadFavorites()
    }
  } catch {}
}

function clearSearch() {
  searchWord.value = ''
  dictResult.value = null
}

function playWord(word: string) { speakWord(word) }

function handleRemove(word: string) {
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

function navToDict() {
  searchWord.value = ''
}

function goVocabReview() {
  uni.switchTab({ url: '/pages/review/index' })
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
  padding: 16rpx 0 8rpx;
}
.search-input-wrap {
  display: flex; align-items: center;
  background: #fff;
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

.dict-result-card { margin: 16rpx 0; }
.dict-header {
  display: flex; align-items: center; justify-content: space-between; margin-bottom: 12rpx;
}
.dict-word { font-size: 40rpx; font-weight: 700; }
.dict-actions { display: flex; gap: 16rpx; }
.dict-btn.is-active { color: #f59e0b; }
.dict-phonetic { color: var(--on-surface-variant); font-size: 26rpx; display: block; margin-bottom: 8rpx; }
.dict-meaning { font-size: 30rpx; line-height: 1.6; display: block; }

.word-list { padding: 8rpx 0; }
.word-item { padding: 24rpx; margin: 8rpx 0; }
.word-main { display: flex; align-items: center; justify-content: space-between; }
.word-info { flex: 1; }
.word-text { font-size: 32rpx; font-weight: 600; display: block; }
.word-phonetic { font-size: 24rpx; color: var(--on-surface-variant); display: block; margin: 4rpx 0; }
.word-meaning { font-size: 26rpx; color: var(--on-surface-variant); display: block; }
.word-actions { display: flex; gap: 12rpx; align-items: center; }
.remove-btn { font-size: 24rpx; color: var(--on-surface-muted); }

/* 背单词入口 */
.vb-entry {
  display: flex; align-items: center; justify-content: space-between;
  padding: 24rpx 28rpx; margin: 12rpx 0;
  background: linear-gradient(135deg, var(--primary-container) 0%, #E8F5E9 100%);
  border-radius: 20rpx;
}
.vb-entry:active { opacity: 0.7; }
.vb-entry-left { display: flex; align-items: center; gap: 20rpx; }
.vb-entry-icon { font-size: 44rpx; }
.vb-entry-title { font-size: 30rpx; font-weight: 700; display: block; }
.vb-entry-desc { font-size: 24rpx; color: var(--on-surface-variant); display: block; margin-top: 4rpx; }
.vb-entry-arrow { font-size: 36rpx; color: var(--on-surface-muted); }
</style>
