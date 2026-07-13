<template>
  <view class="page-container dict-page">
    <!-- 顶部通栏：主题青绿色 + 白色标题 -->
    <view class="dict-header">
      <text class="dict-header-title">单词书</text>
    </view>

    <view v-if="loading" class="loading">
      <view class="spinner"></view>
    </view>

    <template v-else>
      <!-- 搜索栏 -->
      <view class="search-bar">
        <view class="search-input-wrap">
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
          <text class="vb-entry-title">背单词</text>
          <text class="vb-entry-desc">选义 + 默写，间隔重复记忆</text>
        </view>
        <text class="vb-entry-arrow">›</text>
      </view>

      <!-- 查词结果 -->
      <view v-if="dictResult" class="dict-result-card">
        <view class="dict-result-header">
          <text class="dict-result-word">{{ dictResult.word }}</text>
          <view class="dict-result-actions">
            <text class="dict-action-btn" @tap="playWord(dictResult.word!)">🔊</text>
            <text class="dict-action-btn" :class="{ favorited: dictResult.isFavorite }" @tap="toggleDictFavorite">{{ dictResult.isFavorite ? '★' : '☆' }}</text>
          </view>
        </view>
        <text v-if="dictResult.phonetic" class="dict-result-phonetic">{{ dictResult.phonetic }}</text>
        <text class="dict-result-meaning">{{ dictResult.meaning }}</text>
      </view>

      <!-- 单词列表 -->
      <view v-if="filteredFavorites.length > 0" class="word-list">
        <view
          v-for="fav in filteredFavorites"
          :key="fav.id"
          class="word-item"
          @tap="playWord(fav.word)"
        >
          <view class="word-info">
            <text class="word-text">{{ fav.word }}</text>
            <text v-if="fav.phonetic" class="word-phonetic">{{ fav.phonetic }}</text>
            <text class="word-meaning">{{ fav.meaning }}</text>
          </view>
          <text class="word-remove" @tap.stop="handleRemove(fav.word)">✕</text>
        </view>
      </view>

      <!-- 空状态 -->
      <view v-else-if="!dictResult" class="empty-state">
        <text class="icon">📚</text>
        <text class="empty-text">{{ searchWord ? '没有匹配的单词' : '还没有收藏单词哦' }}</text>
        <text class="empty-hint">{{ searchWord ? '换个关键词试试' : '在学习页面点击单词即可收藏' }}</text>
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

function goVocabReview() {
  // review 已从 tabBar 移除到普通页栈，用 navigateTo；?tab=vocab 直落背单词分区
  uni.navigateTo({ url: '/pages/review/index?tab=vocab' })
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
.dict-page { padding-bottom: 40rpx; }

/* 顶部通栏 */
.dict-header {
  padding: calc(env(safe-area-inset-top, 44px) + 16rpx) 32rpx 24rpx;
  background: var(--primary, #5B9AA8);
  margin: 0 -20rpx 0;
}
.dict-header-title {
  font-size: 36rpx;
  font-weight: 600;
  color: #fff;
  letter-spacing: 0.5rpx;
}

/* 搜索栏 */
.search-bar { padding: 24rpx 0 12rpx; }
.search-input-wrap {
  display: flex;
  align-items: center;
  background: #f6fbfc;
  border-radius: 20rpx;
  padding: 0 24rpx;
  border: 1rpx solid #e4eff2;
}
.search-input {
  flex: 1;
  height: 72rpx;
  font-size: 28rpx;
  background: transparent;
  border: none;
}
.search-placeholder { color: #b0b8c0; }
.search-clear { font-size: 28rpx; color: #b0b8c0; padding: 8rpx; }

/* 背单词入口 */
.vb-entry {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 28rpx;
  margin: 12rpx 0 20rpx;
  background: #f6fbfc;
  border: 1rpx solid #e4eff2;
  border-radius: 20rpx;
}
.vb-entry:active { transform: scale(0.98); }
.vb-entry-left { display: flex; flex-direction: column; gap: 4rpx; }
.vb-entry-title { font-size: 28rpx; font-weight: 700; color: var(--on-surface); }
.vb-entry-desc { font-size: 22rpx; color: var(--on-surface-variant); }
.vb-entry-arrow { font-size: 32rpx; color: #b0b8c0; }

/* 查词结果 */
.dict-result-card {
  margin: 0 0 20rpx;
  padding: 28rpx;
  background: #f6fbfc;
  border: 1rpx solid #e4eff2;
  border-radius: 20rpx;
}
.dict-result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12rpx;
}
.dict-result-word { font-size: 36rpx; font-weight: 700; color: var(--on-surface); }
.dict-result-actions { display: flex; gap: 20rpx; }
.dict-action-btn { font-size: 32rpx; color: var(--on-surface-variant); }
.dict-action-btn.favorited { color: var(--primary); }
.dict-result-phonetic { color: var(--on-surface-variant); font-size: 24rpx; display: block; margin-bottom: 8rpx; }
.dict-result-meaning { font-size: 28rpx; line-height: 1.6; display: block; color: var(--on-surface); }

/* 单词列表 */
.word-list {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}
.word-item {
  display: flex;
  align-items: center;
  padding: 24rpx 28rpx;
  background: #f6fbfc;
  border: 1rpx solid #e4eff2;
  border-radius: 16rpx;
}
.word-info { flex: 1; }
.word-text { font-size: 30rpx; font-weight: 600; display: block; color: var(--on-surface); }
.word-phonetic { font-size: 22rpx; color: var(--on-surface-variant); display: block; margin: 4rpx 0; }
.word-meaning { font-size: 24rpx; color: var(--on-surface-variant); display: block; }
.word-remove { font-size: 24rpx; color: #b0b8c0; padding: 12rpx; flex-shrink: 0; }
</style>
