<template>
  <view class="page-container">
    <view class="page-header">
      <text class="title">单词书</text>
      <text class="subtitle">共 {{ favorites.length }} 个单词</text>
    </view>

    <view v-if="loading" class="loading">
      <view class="spinner"></view>
    </view>

    <view v-else-if="favorites.length === 0" class="empty-state">
      <text class="icon">📚</text>
      <text class="empty-text">还没有收藏单词</text>
      <text class="empty-hint">在学习页面点击单词即可收藏</text>
    </view>

    <view v-else class="word-list">
      <view
        v-for="fav in favorites"
        :key="fav.id"
        class="word-card card"
        @tap="playWord(fav.word)"
      >
        <view class="word-main">
          <text class="word-text">{{ fav.word }}</text>
          <view class="fav-btn is-fav" @tap.stop="handleRemove(fav.word)">
            <text>★</text>
          </view>
        </view>
        <text v-if="fav.phonetic" class="word-phonetic">{{ fav.phonetic }}</text>
        <text class="word-meaning">{{ fav.meaning }}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { favoritesApi } from '@/api'
import { useAuthStore } from '@/stores'
import { speakWord } from '@/composables/useSpeech'

const auth = useAuthStore()
const loading = ref(true)
const favorites = ref<Array<{
  id: number
  word: string
  phonetic?: string
  meaning?: string
  source?: string
  created_at: string
}>>([])

async function loadData() {
  loading.value = true
  try {
    const { data } = await favoritesApi.list(auth.currentUserId)
    favorites.value = data || []
  } catch {
    favorites.value = []
  }
  loading.value = false
}

function playWord(word: string) {
  speakWord(word)
}

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

onShow(loadData)
</script>

<style scoped>
.page-header .title {
  font-size: 40rpx;
  font-weight: 700;
  color: white;
  display: block;
}
.page-header .subtitle {
  font-size: 26rpx;
  color: rgba(255,255,255,0.85);
  margin-top: 8rpx;
  display: block;
}

.empty-text {
  display: block;
  font-size: 30rpx;
  margin-bottom: 16rpx;
}
.empty-hint {
  display: block;
  font-size: 26rpx;
  color: var(--on-surface-variant);
}

.word-list { padding: 16rpx 0; }
.word-card { padding: 28rpx; }
.word-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12rpx;
}
.word-text {
  font-size: 36rpx;
  font-weight: 600;
  color: var(--on-surface);
}
.fav-btn {
  width: 64rpx;
  height: 64rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40rpx;
}
.fav-btn.is-fav { color: #f59e0b; }
.word-phonetic {
  font-size: 26rpx;
  color: var(--on-surface-variant);
  margin-bottom: 8rpx;
  display: block;
}
.word-meaning {
  font-size: 28rpx;
  color: var(--on-surface-variant);
  display: block;
}
</style>