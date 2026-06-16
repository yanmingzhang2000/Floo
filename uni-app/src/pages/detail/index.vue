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
      <!-- 阅读工具栏 -->
      <view class="read-toolbar">
        <view class="toolbar-item" @tap="speakContent">
          <text class="toolbar-icon">🔊</text>
          <text class="toolbar-label">朗读</text>
        </view>
        <view class="toolbar-item" @tap="toggleEval">
          <text class="toolbar-icon" :class="{ 'recording-icon': isRecording }">🎤</text>
          <text class="toolbar-label">{{ isRecording ? '录音中...' : '朗读评测' }}</text>
        </view>
        <view class="toolbar-item" @tap="showTranslation = !showTranslation">
          <text class="toolbar-icon">{{ showTranslation ? '📖' : '📕' }}</text>
          <text class="toolbar-label">{{ showTranslation ? '隐藏译文' : '查看译文' }}</text>
        </view>
        <view class="toolbar-item" @tap="openDictation">
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

      <!-- 底部行动栏 -->
      <view class="bottom-actions">
        <button class="btn btn-primary btn-block btn-lg" @tap="openDictation">
          <text>去默写练习</text>
        </button>
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

    <!-- 默写弹窗 -->
    <view v-if="showDictation" class="modal-overlay" @tap="showDictation = false">
      <view class="dictation-sheet" @tap.stop>
        <view class="dictation-sheet-top">
          <text class="tag tag-primary">默写练习</text>
          <view class="btn-icon dictation-close" @tap="showDictation = false"><text>✕</text></view>
        </view>
        <view class="dictation-hint-card">
          <text class="dictation-hint-label">中文翻译提示</text>
          <text class="dictation-hint-text">{{ content?.translation || '暂无翻译' }}</text>
        </view>
        <view style="padding: 0 32rpx">
          <button class="btn btn-sm btn-text" @tap="dictShowOriginal = !dictShowOriginal">
            <text>{{ dictShowOriginal ? '🙈 隐藏原文' : '👁️ 显示原文' }}</text>
          </button>
        </view>
        <view v-if="dictShowOriginal" class="dictation-original-card">
          <text class="dictation-original-text">{{ content?.article }}</text>
        </view>
        <view class="dictation-input-card">
          <textarea v-model="dictUserInput" :maxlength="-1" placeholder="在这里输入默写的英文内容..." class="dictation-textarea" />
        </view>
        <view class="dictation-submit">
          <button class="btn btn-primary btn-block btn-lg" :disabled="dictSubmitting || !dictUserInput.trim()" @tap="handleDictSubmit">
            <text>{{ dictSubmitting ? 'AI 批改中...' : '提交批改' }}</text>
          </button>
        </view>
        <view v-if="dictResult" class="card dictation-result-card">
          <!-- 分数行 -->
          <view class="dictation-score-area">
            <text class="dictation-score" :class="getDictScoreClass(dictResult.feedback.score)">{{ dictResult.feedback.score }}</text>
            <view class="dictation-score-meta">
              <text>准确率 {{ dictResult.accuracy_rate.toFixed(0) }}%</text>
              <text style="color: var(--success)">+{{ dictResult.earned_points }} 积分</text>
            </view>
          </view>
          <!-- AI 总评 -->
          <view v-if="dictResult.feedback.summary" class="dictation-feedback">
            <text class="dictation-feedback-label">AI 总评</text>
            <text class="dictation-feedback-text">{{ dictResult.feedback.summary }}</text>
          </view>
          <!-- 错误明细 -->
          <view v-if="dictResult.feedback.diffs && dictResult.feedback.diffs.length" class="dictation-diffs">
            <text class="dictation-feedback-label">错误明细</text>
            <view v-for="(d, i) in dictResult.feedback.diffs" :key="i" class="diff-item">
              <text class="diff-type" :class="'diff-' + d.type">{{ { missing: '漏写', wrong: '写错', extra: '多写' }[d.type] || d.type }}</text>
              <view class="diff-detail">
                <text v-if="d.expected" class="diff-expected">✓ {{ d.expected }}</text>
                <text v-if="d.actual && d.type !== 'missing'" class="diff-actual">✗ {{ d.actual }}</text>
              </view>
            </view>
          </view>
          <!-- 学习建议 -->
          <view v-if="dictResult.feedback.suggestions && dictResult.feedback.suggestions.length" class="dictation-suggestions">
            <text class="dictation-feedback-label">建议</text>
            <view v-for="(s, i) in dictResult.feedback.suggestions" :key="i" class="suggestion-item">
              <text class="suggestion-text">• {{ s }}</text>
            </view>
          </view>
        </view>
      </view>
    </view>

    <AppTabBar />
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { dailyApi, dictionaryApi, speechApi, favoritesApi, dictationApi } from '@/api'
import { speakWord, initVoices } from '@/composables/useSpeech'
import { useRecorder } from '@/composables/useRecorder'
import { getBaseForm } from '@/composables/useWordForm'
import { useAuthStore } from '@/stores'
import { navBackSafe } from '@/utils/router'
import AppTabBar from '@/components/AppTabBar.vue'
import type { LearningContent, WordItem } from '@/types'

const auth = useAuthStore()
const loading = ref(true)
const content = ref<LearningContent | null>(null)
const wordPopup = ref<{ word: string; phonetic?: string; meaning: string } | null>(null)
const showTranslation = ref(false)
const isFavorited = ref(false)
const { isRecording, startRecording, stopRecording } = useRecorder()
const evalResult = ref<{ overall: number; pronunciation: number; fluency: number; integrity: number; suggestion: string } | null>(null)

// 默写弹窗
const showDictation = ref(false)
const dictUserInput = ref('')
const dictShowOriginal = ref(false)
const dictSubmitting = ref(false)
const dictResult = ref<any>(null)
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
  dictUserInput.value = ''
  dictShowOriginal.value = false
  dictResult.value = null
  showDictation.value = true
}

function getDictScoreClass(score: number) {
  if (score >= 80) return 'score-green'
  if (score >= 60) return 'score-orange'
  return 'score-red'
}

async function handleDictSubmit() {
  if (!content.value || !dictUserInput.value.trim()) return
  dictSubmitting.value = true
  try {
    const { data } = await dictationApi.submit(auth.currentUserId, contentId, dictUserInput.value)
    dictResult.value = data
  } catch { uni.showToast({ title: '提交失败', icon: 'none' }) }
  dictSubmitting.value = false
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
.detail-wrap { padding-bottom: 160rpx; }

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

.detail-card { margin: 0 0 24rpx; }
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

.bottom-actions { padding: 0 0 48rpx; }

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

/* 默写弹窗 */
.dictation-sheet { width: 100%; max-width: 600px; max-height: 90vh; background: white; border-radius: 32rpx 32rpx 0 0; overflow-y: auto; padding-bottom: env(safe-area-inset-bottom, 32rpx); }
.dictation-sheet-top { display: flex; justify-content: space-between; align-items: center; padding: 32rpx 32rpx 0; }
.dictation-close { background: var(--surface-container); }
.dictation-hint-card { margin: 24rpx 32rpx; padding: 28rpx; background: var(--primary-container); border-radius: 16rpx; }
.dictation-hint-label { font-size: 22rpx; color: var(--on-primary-container); margin-bottom: 12rpx; display: block; }
.dictation-hint-text { font-size: 28rpx; line-height: 1.6; display: block; color: var(--on-primary-container); }
.dictation-original-card { margin: 16rpx 32rpx; padding: 28rpx; background: var(--surface-container); border-radius: 16rpx; }
.dictation-original-text { font-size: 28rpx; line-height: 1.6; display: block; }
.dictation-input-card { padding: 16rpx 32rpx; }
.dictation-textarea { width: 100%; height: 280rpx; border: 3rpx solid var(--outline); border-radius: 16rpx; padding: 24rpx; font-size: 28rpx; line-height: 1.6; }
.dictation-submit { padding: 0 32rpx 24rpx; }
.dictation-result-card { border-left: 8rpx solid var(--primary); margin: 0 32rpx 32rpx; }
.dictation-score-area { display: flex; align-items: center; gap: 28rpx; }
.dictation-score { font-size: 80rpx; font-weight: 800; }
.dictation-score-meta { font-size: 26rpx; line-height: 1.6; }
.dictation-feedback { margin-top: 24rpx; padding-top: 20rpx; border-top: 2rpx solid var(--surface-container-high); }
.dictation-feedback-label { font-size: 24rpx; color: var(--on-surface-variant); margin-bottom: 12rpx; display: block; }
.dictation-feedback-text { font-size: 26rpx; line-height: 1.6; display: block; }

.dictation-diffs { margin-top: 20rpx; padding-top: 16rpx; border-top: 2rpx solid var(--surface-container-high); }
.diff-item { display: flex; gap: 12rpx; margin-bottom: 12rpx; padding: 12rpx; background: var(--surface-container); border-radius: 8rpx; }
.diff-type { font-size: 22rpx; font-weight: 600; padding: 4rpx 12rpx; border-radius: 12rpx; flex-shrink: 0; }
.diff-type.diff-missing { background: #FFF3E0; color: #E65100; }
.diff-type.diff-wrong { background: #FFEBEE; color: #C62828; }
.diff-type.diff-extra { background: #E3F2FD; color: #1565C0; }
.diff-detail { flex: 1; display: flex; flex-direction: column; gap: 4rpx; }
.diff-expected { font-size: 24rpx; color: var(--success); }
.diff-actual { font-size: 24rpx; color: var(--error); text-decoration: line-through; }

.dictation-suggestions { margin-top: 20rpx; padding-top: 16rpx; border-top: 2rpx solid var(--surface-container-high); }
.suggestion-item { margin-bottom: 8rpx; }
.suggestion-text { font-size: 24rpx; color: var(--on-surface); line-height: 1.6; }
</style>
