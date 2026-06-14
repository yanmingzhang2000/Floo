<template>
  <view class="page-container">
    <view v-if="loading" class="loading">
      <view class="spinner"></view>
    </view>

    <view v-else-if="content">
      <view class="card detail-card">
        <view class="tags-row">
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

      <view v-if="content.translation" class="card">
        <text class="section-label">中文译文</text>
        <text class="translation-text">{{ content.translation }}</text>
      </view>

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

      <view class="detail-bottom">
        <button class="btn btn-primary btn-block btn-lg" @tap="goDictation">
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
import { navTo } from '@/utils/router'
import type { LearningContent, WordItem } from '@/types'

const loading = ref(true)
const content = ref<LearningContent | null>(null)
const wordPopup = ref<{ word: string; phonetic?: string; meaning: string } | null>(null)
let contentId = 0

onLoad((query) => {
  contentId = Number(query?.id || 0)
  loadContent()
})

onMounted(() => {
  initVoices()
})

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
  } catch {
    content.value = null
  }
  loading.value = false
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
  } catch {
    wordPopup.value = { word, meaning: '查询失败' }
  }
}

function showWordDetail(w: WordItem) {
  wordPopup.value = { word: w.word, phonetic: w.phonetic, meaning: w.meaning }
}

function goDictation() {
  navTo('/pages/review/index')
}
</script>

<style scoped>
.tags-row { display: flex; gap: 16rpx; margin-bottom: 20rpx; }
.detail-title { font-size: 36rpx; font-weight: 700; margin-bottom: 24rpx; display: block; line-height: 1.5; }

.article-body { font-size: 30rpx; line-height: 1.8; color: var(--on-surface); }
.word-span { display: inline; }
.keyword {
  background: var(--primary-container);
  color: var(--on-primary-container);
  padding: 0 4rpx;
  border-radius: 4rpx;
  font-weight: 600;
}
.clickable-word {
  color: var(--primary);
  text-decoration: underline;
  text-decoration-style: dashed;
}

.section-label { font-size: 28rpx; color: var(--on-surface-variant); margin-bottom: 16rpx; display: block; }
.translation-text { font-size: 28rpx; line-height: 1.8; display: block; }

.words-wrap { display: flex; flex-wrap: wrap; gap: 16rpx; }
.word-chip {
  padding: 16rpx 24rpx;
  background: var(--surface-container);
  border-radius: 16rpx;
  display: flex;
  flex-direction: column;
}
.word-text { font-weight: 600; font-size: 28rpx; }
.word-phonetic { font-size: 22rpx; color: var(--on-surface-variant); }
.word-meaning { font-size: 24rpx; color: var(--on-surface-variant); }

.detail-card { margin: 24rpx; }
.detail-bottom { padding: 0 24rpx 48rpx; }
.word-popup {
  width: 100%;
  background: white;
  border-radius: 32rpx 32rpx 0 0;
  padding: 40rpx 32rpx;
}
.popup-header { display: flex; align-items: center; gap: 24rpx; }
.popup-word { font-size: 44rpx; font-weight: 700; flex: 1; }
.speak-btn {
  width: 72rpx; height: 72rpx;
  background: var(--primary-container); border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 36rpx;
}
.popup-phonetic { color: var(--on-surface-variant); margin-top: 8rpx; display: block; font-size: 26rpx; }
.popup-meaning { margin-top: 20rpx; font-size: 32rpx; display: block; }
</style>