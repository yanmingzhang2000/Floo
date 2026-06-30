<template>
  <view class="page-container">
    <view class="nav-bar">
      <view class="nav-left">
        <view class="nav-back" @tap="navBackSafe"><text>‹</text></view>
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
      <!-- 文章内容 -->
        <view class="card detail-card">
        <view class="detail-meta">
          <text class="tag tag-primary">{{ content.content_date }}</text>
          <text class="tag tag-success">{{ content.difficulty_level }}</text>
        </view>
        <text class="detail-title">{{ content.title }}</text>

        <view class="learned-toggle" @tap="toggleLearned">
          <text class="learned-icon">{{ learnedIds.includes(content.id) ? '✅' : '☑️' }}</text>
          <text class="learned-text">{{ learnedIds.includes(content.id) ? '已学过' : '标记已学' }}</text>
        </view>

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

      <!-- 朗读评测结果 -->
      <view v-if="evalResult" class="card eval-card">
        <view class="eval-scores-row">
          <view class="eval-score">
            <text class="eval-score-num" :class="getScoreClass(evalResult.overall)">{{ evalResult.overall }}</text>
            <text class="eval-score-label">总分</text>
          </view>
          <view class="eval-score">
            <text class="eval-score-num" :class="getScoreClass(evalResult.pronunciation)">{{ evalResult.pronunciation }}</text>
            <text class="eval-score-label">发音</text>
          </view>
          <view class="eval-score">
            <text class="eval-score-num" :class="getScoreClass(evalResult.fluency)">{{ evalResult.fluency }}</text>
            <text class="eval-score-label">流利度</text>
          </view>
          <view class="eval-score">
            <text class="eval-score-num" :class="getScoreClass(evalResult.integrity)">{{ evalResult.integrity }}</text>
            <text class="eval-score-label">完整度</text>
          </view>
        </view>
        <text class="eval-suggestion">{{ evalResult.suggestion }}</text>
        <button class="btn btn-sm btn-outline" @tap="resetEval">重新评测</button>
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

      <!-- 底部留白 -->
      <view style="height: 160rpx;"></view>
    </view>

    <!-- 底部浮动工具栏 -->
    <view v-if="content" class="bottom-float-bar">
      <view class="float-item" @tap="speakContent">
        <text class="float-icon">🔊</text>
        <text class="float-label">朗读</text>
      </view>
      <view class="float-item" @tap="toggleEval">
        <text class="float-icon" :class="{ 'recording-icon': isRecording }">🎤</text>
        <text class="float-label">{{ isRecording ? '录音中' : '评测' }}</text>
      </view>
      <view class="float-item" @tap="showTranslation = !showTranslation">
        <text class="float-icon">{{ showTranslation ? '📖' : '📕' }}</text>
        <text class="float-label">{{ showTranslation ? '隐藏译文' : '译文' }}</text>
      </view>
      <view class="float-item" @tap="openDictation">
        <text class="float-icon">✏️</text>
        <text class="float-label">默写</text>
      </view>
    </view>

    <!-- 单词弹窗 -->
    <view v-if="wordPopup" class="modal-overlay" @tap="wordPopup = null">
      <view class="word-popup" @tap.stop>
        <view class="popup-header">
          <text class="popup-word">{{ wordPopup.word }}</text>
          <view class="btn-icon" @tap="speakWord(wordPopup.word)"><text>🔊</text></view>
          <view class="btn-icon fav-btn" :class="{ active: isFavorited }" @tap="toggleFavorite">
            <text>{{ isFavorited ? '⭐' : '☆' }}</text>
          </view>
        </view>
        <text v-if="wordPopup.phonetic" class="popup-phonetic">{{ wordPopup.phonetic }}</text>
        <text class="popup-meaning">{{ wordPopup.meaning }}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { onLoad, onShow, onHide } from '@dcloudio/uni-app'
import { dailyApi, dictionaryApi, speechApi, favoritesApi } from '@/api'
import { speakWord, initVoices } from '@/composables/useSpeech'
import { useRecorder } from '@/composables/useRecorder'
import { getBaseForm } from '@/composables/useWordForm'
import { useAuthStore } from '@/stores'
import { navBackSafe } from '@/utils/router'
import type { LearningContent, WordItem } from '@/types'

const auth = useAuthStore()
const loading = ref(true)
const content = ref<LearningContent | null>(null)
const wordPopup = ref<{ word: string; phonetic?: string; meaning: string } | null>(null)
const showTranslation = ref(false)
const isFavorited = ref(false)
const { isRecording, startRecording, stopRecording } = useRecorder()
const evalResult = ref<{ overall: number; pronunciation: number; fluency: number; integrity: number; suggestion: string } | null>(null)
const learnedIds = ref<number[]>([])
let autoLearnTimer: ReturnType<typeof setTimeout> | null = null
let contentId = 0

const usernameInitial = computed(() => (auth.username?.[0] || '?').toUpperCase())

onLoad((query) => {
  contentId = Number(query?.id || 0)
  loadContent()
})

onShow(() => {
  initVoices()
  loadLearnedIds()
  startAutoLearnTimer()
})

onHide(() => {
  clearAutoLearnTimer()
})

const articleParts = computed(() => {
  if (!content.value) return []
  const article = content.value.article || ''
  const words = content.value.words || []
  
  // 构建关键词/词组映射（大小写不敏感）
  const keyMap = new Map<string, boolean>()
  words.forEach(w => keyMap.set(w.word.toLowerCase(), true))
  
  // 提取所有词组（含空格或 is_phrase 标记），按长度降序排列
  const phrases = words
    .filter(w => w.word.includes(' ') || w.is_phrase)
    .map(w => w.word)
    .sort((a, b) => b.length - a.length)
  
  const parts: { text: string; isWord: boolean; isKey: boolean }[] = []
  let i = 0
  
  while (i < article.length) {
    // 1. 尝试匹配词组（贪心：最长优先）
    let matched = false
    for (const phrase of phrases) {
      const chunk = article.slice(i, i + phrase.length)
      if (chunk.toLowerCase() === phrase.toLowerCase()) {
        parts.push({ text: chunk, isWord: true, isKey: true })
        i += phrase.length
        matched = true
        break
      }
    }
    if (matched) continue
    
    // 2. 尝试匹配单个单词
    const wordMatch = article.slice(i).match(/^[a-zA-Z]+(?:'[a-zA-Z]+)?/)
    if (wordMatch) {
      const word = wordMatch[0]
      parts.push({ text: word, isWord: true, isKey: keyMap.has(word.toLowerCase()) })
      i += word.length
      continue
    }
    
    // 3. 非单词字符，收集到下一个单词/词组开始
    let j = i + 1
    while (j < article.length && !/[a-zA-Z]/.test(article[j])) j++
    parts.push({ text: article.slice(i, j), isWord: false, isKey: false })
    i = j
  }
  
  return parts
})

function startAutoLearnTimer() {
  clearAutoLearnTimer()
  if (!content.value || !contentId || !auth.currentUserId) return
  autoLearnTimer = setTimeout(async () => {
    if (!content.value || !auth.currentUserId) return
    try {
      const { data } = await dailyApi.markLearned(auth.currentUserId, contentId)
      if (data.learned && !learnedIds.value.includes(contentId)) {
        learnedIds.value = [...learnedIds.value, contentId]
      }
    } catch { /* silent */ }
  }, 5 * 60 * 1000)
}

function clearAutoLearnTimer() {
  if (autoLearnTimer !== null) {
    clearTimeout(autoLearnTimer)
    autoLearnTimer = null
  }
}

async function loadLearnedIds() {
  if (!auth.currentUserId) return
  try {
    const { data } = await dailyApi.getLearnedIds(auth.currentUserId)
    learnedIds.value = data.content_ids || []
  } catch { /* ignore */ }
}

async function toggleLearned() {
  if (!auth.currentUserId || !contentId) return
  try {
    const { data } = await dailyApi.toggleLearned(auth.currentUserId, contentId)
    if (data.learned) {
      if (!learnedIds.value.includes(contentId)) {
        learnedIds.value = [...learnedIds.value, contentId]
      }
    } else {
      learnedIds.value = learnedIds.value.filter(id => id !== contentId)
    }
  } catch {
    uni.showToast({ title: '操作失败', icon: 'none' })
  }
}

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
  
  // 先检查是否是 AI 已提供的词汇/词组
  const knownWord = content.value?.words?.find(w => w.word.toLowerCase() === word.toLowerCase())
  if (knownWord) {
    // 直接用 AI 给的释义，不查字典
    wordPopup.value = { 
      word: knownWord.word, 
      phonetic: knownWord.phonetic, 
      meaning: knownWord.meaning 
    }
    checkFavorite(knownWord.word)
    return
  }
  
  // 未知词：查字典
  wordPopup.value = { word, meaning: '查询中...' }
  isFavorited.value = false
  try {
    const [dictRes, favRes] = await Promise.all([
      dictionaryApi.lookup(word),
      favoritesApi.check(auth.currentUserId, word),
    ])
    const ec = dictRes.data?.ec?.word?.[0]
    const phonetic = ec?.usphone || ec?.ukphone || ''
    const trs = ec?.trs || []
    const meaning = trs.map((t: any) => t?.tr?.[0]?.l?.i?.[0]).filter(Boolean).join('；')
    wordPopup.value = meaning
      ? { word, phonetic: phonetic ? `/${phonetic}/` : undefined, meaning }
      : { word, meaning: '未找到释义' }
    isFavorited.value = favRes.data?.is_favorited ?? false
  } catch { wordPopup.value = { word, meaning: '查询失败' } }
}

function showWordDetail(w: WordItem) {
  wordPopup.value = { word: w.word, phonetic: w.phonetic, meaning: w.meaning }
  checkFavorite(w.word)
}

async function checkFavorite(word: string) {
  try {
    const { data } = await favoritesApi.check(auth.currentUserId, word)
    isFavorited.value = data?.is_favorited ?? false
  } catch { isFavorited.value = false }
}

async function toggleFavorite() {
  if (!wordPopup.value) return
  const { word, phonetic, meaning } = wordPopup.value
  try {
    if (isFavorited.value) {
      await favoritesApi.remove(auth.currentUserId, word)
      isFavorited.value = false
      uni.showToast({ title: '已取消收藏', icon: 'none' })
    } else {
      await favoritesApi.add(auth.currentUserId, word, phonetic || '', meaning, 'article', contentId)
      isFavorited.value = true
      uni.showToast({ title: '已收藏', icon: 'success' })
    }
  } catch { uni.showToast({ title: '操作失败', icon: 'none' }) }
}

function goReview() { uni.switchTab({ url: '/pages/review/index' }) }

function openDictation() {
  uni.navigateTo({ url: `/pages/dictation/index?id=${contentId}` })
}

function getScoreClass(score: number) {
  if (score >= 90) return 'score-green'
  if (score >= 70) return 'score-orange'
  return 'score-red'
}

async function toggleEval() {
  if (!content.value?.article) return
  if (isRecording.value) {
    const audioBase64 = await stopRecording()
    if (!audioBase64) {
      uni.showToast({ title: '录音失败', icon: 'none' })
      return
    }
    uni.showLoading({ title: '评测中...' })
    try {
      const { data } = await speechApi.evaluate(audioBase64, content.value.article, 'en')
      evalResult.value = {
        overall: data.overall || 0,
        pronunciation: data.pronunciation || 0,
        fluency: data.fluency || 0,
        integrity: data.integrity || 0,
        suggestion: data.suggestion || '',
      }
    } catch {
      evalResult.value = { overall: 0, pronunciation: 0, fluency: 0, integrity: 0, suggestion: '评测失败，请稍后重试' }
    }
    uni.hideLoading()
  } else {
    if (!await startRecording()) {
      uni.showToast({ title: '麦克风权限获取失败', icon: 'none' })
    }
  }
}

function resetEval() { evalResult.value = null }
function navBack() { navBackSafe() }
</script>

<style scoped>
.detail-wrap { padding-bottom: 0; }

.detail-card { margin: 0 0 24rpx; }
.learned-toggle {
  display: inline-flex; align-items: center; gap: 8rpx;
  padding: 8rpx 20rpx; border-radius: 40rpx;
  background: #fff; border: 3rpx solid var(--outline-variant);
  font-size: 24rpx; color: var(--on-surface-variant);
  margin-bottom: 20rpx;
}
.learned-toggle:active { opacity: 0.6; }
.learned-icon { font-size: 28rpx; }
.learned-text { font-weight: 500; }

.detail-meta { display: flex; gap: 12rpx; margin-bottom: 20rpx; }
.detail-title {
  font-size: 36rpx; font-weight: 700; margin-bottom: 24rpx;
  display: block; line-height: 1.5; color: #111;
}
.article-body { line-height: 1.9; }
.word-span { font-size: 30rpx; color: #111; line-height: 1.9; }
.clickable-word { color: #111; }
.keyword { color: var(--primary); font-weight: 600; }

.section-label {
  font-size: 26rpx; color: var(--on-surface-variant);
  margin-bottom: 16rpx; display: block; font-weight: 600;
}
.translation-text { font-size: 28rpx; line-height: 1.8; display: block; }

/* 底部浮动工具栏 */
.float-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4rpx;
  padding: 12rpx 20rpx;
  border-radius: 16rpx;
  transition: background var(--transition-fast);
}
.float-item:active {
  background: rgba(91,154,168,0.1);
}
.float-icon { font-size: 36rpx; }
.float-label {
  font-size: 20rpx;
  color: var(--on-surface-variant);
  font-weight: 500;
}

.speak-btn { background: var(--primary-container); }
.fav-btn.active { background: #FFF8E1; }

/* 朗读评测 */
.eval-card { text-align: center; padding: 32rpx; }
.eval-scores-row { display: flex; justify-content: space-around; margin-bottom: 24rpx; }
.eval-score { display: flex; flex-direction: column; align-items: center; gap: 8rpx; }
.eval-score-num { font-size: 48rpx; font-weight: 800; }
.eval-score-label { font-size: 22rpx; color: var(--on-surface-variant); }
.eval-suggestion { font-size: 26rpx; color: var(--on-surface-variant); line-height: 1.6; display: block; margin-bottom: 20rpx; }
.score-green { color: var(--success); }
.score-orange { color: var(--warning); }
.score-red { color: var(--error); }
.recording-icon { color: var(--error); animation: pulse 1s infinite; }
@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(1.2); }
}

</style>
