<template>
  <view class="page-container">
    <view class="nav-bar">
      <view class="nav-left">
        <view class="nav-back" @tap="navBack"><text>‹</text></view>
      </view>
      <text class="nav-title">文章详情</text>
      <view class="nav-right">
        <view class="nav-avatar">
          <text>{{ usernameInitial }}</text>
        </view>
      </view>
    </view>

    <view v-if="loading" class="loading">
      <view class="spinner"></view>
    </view>

    <view v-else-if="content" class="detail-wrap">
      <!-- 阅读工具栏 -->
      <view class="read-toolbar">
        <view class="toolbar-item" @tap="speakContent">
          <text class="toolbar-icon">🔊</text>
          <text class="toolbar-label">朗读</text>
        </view>
        <view class="toolbar-item" @tap="showTranslation = !showTranslation">
          <text class="toolbar-icon">{{ showTranslation ? '📖' : '📕' }}</text>
          <text class="toolbar-label">{{ showTranslation ? '隐藏译文' : '查看译文' }}</text>
        </view>
        <view class="toolbar-item" @tap="goReview">
          <text class="toolbar-icon">✏️</text>
          <text class="toolbar-label">默写</text>
        </view>
      </view>

      <!-- 文章内容 -->
      <view class="card detail-card">
        <view class="detail-meta">
          <text class="tag tag-primary">{{ content.content_date }}</text>
          <text class="tag tag-success">{{ content.difficulty_level }}</text>
        </view>
        <text class="detail-title">{{ content.title }}</text>

        <view class="article-body">
          <text
            v-for="(part, i) in articleParts"
            :key="i"
            :class="['word-span', part.isWord ? (part.isKey ? 'keyword' : 'clickable-word') : '']"
            @tap="part.isWord && handleWordTap(part.text)"
          >{{ part.text }}</text>
        </view>
      </view>

      <!-- 译文 -->
      <view v-if="showTranslation && content.translation" class="card">
        <text class="section-label">中文译文</text>
        <text class="translation-text">{{ content.translation }}</text>
      </view>

      <!-- 核心词汇 -->
      <view v-if="content.words && content.words.length" class="card">
        <text class="section-label">核心词汇</text>
        <view class="words-wrap">
          <view v-for="w in content.words" :key="w.word" class="word-chip" @tap="showWordDetail(w)">
            <text class="word-text">{{ w.word }}</text>
            <text v-if="w.phonetic" class="word-phonetic">{{ w.phonetic }}</text>
            <text class="word-meaning">{{ w.meaning }}</text>
          </view>
        </view>
      </view>

      <!-- 底部行动栏 -->
      <view class="bottom-actions">
        <button class="btn btn-primary btn-block btn-lg" @tap="goReview">
          <text>去默写练习</text>
        </button>
      </view>
    </view>

    <!-- 单词弹窗 -->
    <view v-if="wordPopup" class="modal-overlay" @tap="wordPopup = null">
      <view class="word-popup" @tap.stop>
        <view class="popup-header">
          <text class="popup-word">{{ wordPopup.word }}</text>
          <view class="speak-btn" @tap="speakWord(wordPopup.word)"><text>🔊</text></view>
        </view>
        <text v-if="wordPopup.phonetic" class="popup-phonetic">{{ wordPopup.phonetic }}</text>
        <text class="popup-meaning">{{ wordPopup.meaning }}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { dailyApi, dictionaryApi } from '@/api'
import { speakWord, initVoices } from '@/composables/useSpeech'
import { getBaseForm } from '@/composables/useWordForm'
import { useAuthStore } from '@/stores'
import type { LearningContent, WordItem } from '@/types'

const auth = useAuthStore()
const loading = ref(true)
const content = ref<LearningContent | null>(null)
const wordPopup = ref<{ word: string; phonetic?: string; meaning: string } | null>(null)
const showTranslation = ref(false)
let contentId = 0

const usernameInitial = computed(() => (auth.username?.[0] || '?').toUpperCase())

onLoad((query) => {
  contentId = Number(query?.id || 0)
  loadContent()
})

onMounted(() => { initVoices() })

const articleParts = computed(() => {
  if (!content.value) return []
  const article = content.value.article || ''
  const words = content.value.words || []
  const keyWords = new Set(words.map(w => w.word.toLowerCase()))
  const parts: { text: string; isWord: boolean; isKey: boolean }[] = []
  let lastEnd = 0
  const re = /[a-zA-Z]+(?:'[a-zA-Z]+)?/g
  let m: RegExpExecArray | null
  while ((m = re.exec(article)) !== null) {
    if (m.index > lastEnd) {
      parts.push({ text: article.slice(lastEnd, m.index), isWord: false, isKey: false })
    }
    parts.push({ text: m[0], isWord: true, isKey: keyWords.has(m[0].toLowerCase()) })
    lastEnd = m.index + m[0].length
  }
  if (lastEnd < article.length) {
    parts.push({ text: article.slice(lastEnd), isWord: false, isKey: false })
  }
  return parts
})

async function loadContent() {
  loading.value = true
  try {
    const { data } = await dailyApi.getContent(contentId)
    content.value = data
  } catch { content.value = null }
  loading.value = false
}

function speakContent() {
  if (content.value?.article) speakWord(content.value.article.slice(0, 500))
}

async function handleWordTap(rawWord: string) {
  const word = getBaseForm(rawWord)
  speakWord(word)
  wordPopup.value = { word, meaning: '查询中...' }
  try {
    const { data } = await dictionaryApi.lookup(word)
    const ec = data?.ec?.word?.[0]
    const phonetic = ec?.usphone || ec?.ukphone || ''
    const trs = ec?.trs || []
    const meaning = trs.map((t: any) => t?.tr?.[0]?.l?.i?.[0]).filter(Boolean).join('；')
    wordPopup.value = meaning
      ? { word, phonetic: phonetic ? `/${phonetic}/` : undefined, meaning }
      : { word, meaning: '未找到释义' }
  } catch { wordPopup.value = { word, meaning: '查询失败' } }
}

function showWordDetail(w: WordItem) {
  wordPopup.value = { word: w.word, phonetic: w.phonetic, meaning: w.meaning }
}

function goReview() { uni.switchTab({ url: '/pages/review/index' }) }
function navBack() { uni.navigateBack() }
</script>

<style scoped>
.detail-wrap { padding-bottom: 120rpx; }

.read-toolbar {
  display: flex;
  justify-content: space-around;
  padding: 24rpx;
  gap: 16rpx;
}
.toolbar-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
  padding: 20rpx 32rpx;
  background: #fff;
  border-radius: 20rpx;
  box-shadow: var(--shadow-sm);
  flex: 1;
}
.toolbar-item:active { opacity: 0.7; }
.toolbar-icon { font-size: 40rpx; }
.toolbar-label { font-size: 22rpx; color: var(--on-surface-variant); font-weight: 500; }

.detail-card { margin: 0 24rpx 24rpx; }
.detail-meta { display: flex; gap: 12rpx; margin-bottom: 20rpx; }
.detail-title {
  font-size: 36rpx; font-weight: 700; margin-bottom: 24rpx;
  display: block; line-height: 1.5;
}

.section-label {
  font-size: 26rpx; color: var(--on-surface-variant);
  margin-bottom: 16rpx; display: block; font-weight: 600;
}
.translation-text { font-size: 28rpx; line-height: 1.8; display: block; }

.bottom-actions { padding: 0 24rpx 48rpx; }

.speak-btn {
  width: 72rpx; height: 72rpx;
  background: var(--primary-container); border-radius: 50%;
  display: flex; align-items: center; justify-content: center; font-size: 36rpx;
}
</style>
