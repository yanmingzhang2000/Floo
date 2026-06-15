<template>
  <view class="page-container">
    <view class="nav-bar">
      <view class="nav-left" @tap="navBackSafe">
        <text class="nav-back-icon">‹</text>
      </view>
      <text class="nav-title">{{ chapterTitle }}</text>
      <view class="nav-right"></view>
    </view>

    <view v-if="loading" class="loading">
      <view class="spinner"></view>
    </view>

    <template v-else>
      <!-- 阅读工具栏 -->
      <view class="reading-toolbar">
        <button class="tool-btn" @tap="toggleTTS">
          <text>{{ ttsPlaying ? '⏸️ 停止' : '🔊 朗读' }}</text>
        </button>
        <button class="tool-btn" @tap="showTranslation = !showTranslation">
          <text>{{ showTranslation ? '隐藏译文' : '📖 译文' }}</text>
        </button>
      </view>

      <!-- 章节正文 -->
      <view class="chapter-content">
        <text class="content-text" :user-select="true">{{ chapterText }}</text>
      </view>

      <!-- 译文 -->
      <view v-if="showTranslation && translation" class="translation-card">
        <text class="translation-label">译文参考</text>
        <text class="translation-text">{{ translation }}</text>
      </view>

      <!-- 标记已读 -->
      <view class="chapter-actions">
        <button class="btn btn-primary btn-block" @tap="markRead">
          <text>✅ 标记已读</text>
        </button>
      </view>
    </template>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onLoad, onUnload } from '@dcloudio/uni-app'
import { booksApi, ttsApi } from '@/api'
import { useAuthStore } from '@/stores'
import { navBackSafe } from '@/utils/router'

const auth = useAuthStore()
const loading = ref(true)
const gutenbergId = ref(0)
const chapterIdx = ref(-1)
const chapterTitle = ref('')
const chapterText = ref('')
const translation = ref('')
const showTranslation = ref(false)
const ttsPlaying = ref(false)
let innerAudio: any = null

onLoad((query: any) => {
  gutenbergId.value = Number(query?.id)
  chapterIdx.value = Number(query?.chapter)
  loadChapter()
})

onUnload(() => {
  if (innerAudio) { innerAudio.destroy() }
})

async function loadChapter() {
  loading.value = true
  try {
    const { data } = await booksApi.getChapterText(gutenbergId.value, chapterIdx.value)
    chapterText.value = data?.text || ''
    chapterTitle.value = data?.title || `第 ${chapterIdx.value + 1} 章`
  } catch {
    chapterText.value = '加载失败，请重试'
  }
  loading.value = false
}

async function toggleTTS() {
  if (ttsPlaying.value) {
    if (innerAudio) { innerAudio.stop() }
    ttsPlaying.value = false
    return
  }
  try {
    const textToSpeak = chapterText.value.slice(0, 500)
    const { data } = await ttsApi.synthesize(textToSpeak)
    if (data?.audio_url) {
      innerAudio = uni.createInnerAudioContext()
      innerAudio.src = data.audio_url
      innerAudio.onEnded(() => { ttsPlaying.value = false })
      innerAudio.onError(() => { ttsPlaying.value = false })
      innerAudio.play()
      ttsPlaying.value = true
    }
  } catch {
    uni.showToast({ title: '朗读失败', icon: 'none' })
  }
}

async function markRead() {
  try {
    await booksApi.markChapterRead(auth.currentUserId, gutenbergId.value, chapterIdx.value)
    uni.showToast({ title: '已标记', icon: 'success' })
    setTimeout(() => navBackSafe(), 800)
  } catch {
    uni.showToast({ title: '标记失败', icon: 'none' })
  }
}
</script>

<style scoped>
.reading-toolbar {
  display: flex;
  gap: 16rpx;
  padding: 16rpx 0;
}
.tool-btn {
  flex: 1;
  background: var(--surface-container);
  border-radius: 12rpx;
  padding: 16rpx;
  font-size: 26rpx;
  text-align: center;
}
.tool-btn:active { opacity: 0.7; }

.chapter-content {
  background: #fff;
  border-radius: 20rpx;
  padding: 32rpx;
  box-shadow: var(--shadow-sm);
  margin-bottom: 20rpx;
}
.content-text {
  font-size: 30rpx;
  line-height: 1.9;
  color: var(--on-surface);
  white-space: pre-wrap;
}

.translation-card {
  background: #FFF8E1;
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 20rpx;
}
.translation-label {
  font-size: 24rpx;
  color: #E65100;
  font-weight: 600;
  display: block;
  margin-bottom: 8rpx;
}
.translation-text {
  font-size: 28rpx;
  line-height: 1.8;
  color: var(--on-surface);
}

.chapter-actions { padding: 16rpx 0 32rpx; }
</style>
