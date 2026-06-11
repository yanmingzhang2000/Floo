<template>
  <div class="page-container">
    <div class="page-header" v-if="content">
      <h1>{{ content.title }}</h1>
      <div style="display:flex;gap:8px;margin-top:8px">
        <span class="tag" style="background:rgba(255,255,255,0.2);color:white">{{ content.content_date }}</span>
        <span class="tag" style="background:rgba(255,255,255,0.2);color:white">{{ content.difficulty_level }}</span>
        <span class="tag" style="background:rgba(255,255,255,0.2);color:white">{{ content.theme_type }}</span>
      </div>
    </div>

    <div v-if="loading" class="loading"><div class="spinner"></div></div>

    <div v-else-if="content" class="detail-content">
      <div class="card">
        <h3 class="card-title">
          <span v-for="(part, i) in titleParts" :key="i"
            :class="part.isWord ? 'clickable-word' : ''"
            :data-word="part.isWord ? part.text : undefined"
            @click="part.isWord && handleWordClick($event, content)"
          >{{ part.text }}</span>
        </h3>
        <div class="article-body" v-html="renderArticle(content)" @click="handleWordClick($event, content)"></div>
      </div>

      <div v-if="content.translation" class="card">
        <h4 style="margin-bottom:8px;color:var(--on-surface-variant)">中文译文</h4>
        <p style="line-height:1.8">{{ content.translation }}</p>
      </div>

      <div v-if="content.words?.length" class="card">
        <h4 style="margin-bottom:10px;color:var(--on-surface-variant)">核心词汇</h4>
        <div class="words-wrap">
          <div v-for="w in content.words" :key="w.word" class="word-chip" @click="wordPopup = { word: w.word, phonetic: w.phonetic, meaning: w.meaning, usage: w.usage }">
            <span class="word-text">{{ w.word }}</span>
            <span class="word-phonetic" v-if="w.phonetic">{{ w.phonetic }}</span>
            <span class="word-meaning">{{ w.meaning }}</span>
          </div>
        </div>
      </div>

      <!-- 朗读评测卡片 -->
      <div class="card eval-card">
        <div v-if="!evalResult && !isRecording" class="eval-trigger" @click="startEval">
          <span class="eval-icon">🎤</span>
          <span class="eval-text">朗读评测</span>
          <span class="eval-hint">点击开始，朗读文章后自动评分</span>
        </div>
        <div v-else-if="isRecording" class="eval-recording">
          <div class="recording-pulse"></div>
          <span>正在录音... {{ recordingTime }}s</span>
          <span class="eval-hint">再次点击结束录音</span>
        </div>
        <div v-else-if="evalResult" class="eval-result">
          <div class="eval-scores-row">
            <div class="eval-score">
              <span class="eval-score-num" :class="getScoreClass(evalResult?.overall ?? 0)">{{ evalResult?.overall ?? 0 }}</span>
              <span class="eval-score-label">总分</span>
            </div>
            <div class="eval-score">
              <span class="eval-score-num" :class="getScoreClass(evalResult?.pronunciation ?? 0)">{{ evalResult?.pronunciation ?? 0 }}</span>
              <span class="eval-score-label">发音</span>
            </div>
            <div class="eval-score">
              <span class="eval-score-num" :class="getScoreClass(evalResult?.fluency ?? 0)">{{ evalResult?.fluency ?? 0 }}</span>
              <span class="eval-score-label">流利度</span>
            </div>
            <div class="eval-score">
              <span class="eval-score-num" :class="getScoreClass(evalResult?.integrity ?? 0)">{{ evalResult?.integrity ?? 0 }}</span>
              <span class="eval-score-label">完整度</span>
            </div>
          </div>
          <p class="eval-suggestion">{{ evalResult?.suggestion }}</p>
          <button class="btn btn-outline btn-sm" @click="resetEval">重新评测</button>
        </div>
      </div>

      <div style="padding:0 16px 16px">
        <router-link :to="`/dictation?content_id=${content.id}`" class="btn btn-primary btn-block">去默写</router-link>
      </div>

      <!-- 上一篇/下一篇导航 -->
      <div v-if="todayContents.length > 1" class="nav-buttons">
        <button class="btn btn-outline" :disabled="!hasPrev" @click="goToContent(todayContents[currentIndex - 1].id)">
          ← 上一篇
        </button>
        <span class="nav-index">{{ currentIndex + 1 }} / {{ todayContents.length }}</span>
        <button class="btn btn-outline" :disabled="!hasNext" @click="goToContent(todayContents[currentIndex + 1].id)">
          下一篇 →
        </button>
      </div>
    </div>

    <Teleport to="body">
      <Transition name="fade">
        <div v-if="wordPopup" class="modal-overlay" @click.self="wordPopup = null">
          <div class="word-popup card">
            <div class="popup-header">
              <h3>{{ wordPopup.word }}</h3>
              <button class="speak-btn" @click="speakWord(wordPopup!.word)">🔊</button>
              <button class="fav-btn" :class="{ active: isFavorited }" @click="toggleFavorite">
                {{ isFavorited ? '⭐' : '☆' }}
              </button>
            </div>
            <p v-if="wordPopup.phonetic" class="phonetic">{{ wordPopup.phonetic }}</p>
            <p class="meaning">{{ wordPopup.meaning }}</p>
            <p v-if="wordPopup.usage" class="usage">{{ wordPopup.usage }}</p>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { dailyApi, dictionaryApi, favoritesApi, speechApi } from '@/api'
import { useAuthStore } from '@/stores'
import { speakWord, initVoices } from '@/composables/useSpeech'
import { useRecorder } from '@/composables/useRecorder'
import { getBaseForm } from '@/composables/useWordForm'
import type { LearningContent, WordItem } from '@/types'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const loading = ref(true)
const content = ref<LearningContent | null>(null)
const todayContents = ref<LearningContent[]>([])
const wordPopup = ref<{ word: string; phonetic?: string; meaning: string; usage?: string } | null>(null)
const isFavorited = ref(false)

// 录音和语音评测
const { isRecording, startRecording, stopRecording } = useRecorder()
const evalResult = ref<{
  overall: number;
  pronunciation: number;
  fluency: number;
  integrity: number;
  suggestion: string;
} | null>(null)
const recordingTime = ref(0)
let recordingTimer: ReturnType<typeof setInterval> | null = null

// 单词查询缓存
const wordCache = new Map<string, { word: string; phonetic?: string; meaning: string }>()

function getCachedWord(word: string) {
  return wordCache.get(word.toLowerCase())
}

function setCachedWord(word: string, result: { word: string; phonetic?: string; meaning: string }) {
  wordCache.set(word.toLowerCase(), result)
  // 限制缓存大小
  if (wordCache.size > 500) {
    const firstKey = wordCache.keys().next().value
    if (firstKey) wordCache.delete(firstKey)
  }
}

// 收藏词汇
async function toggleFavorite() {
  if (!wordPopup.value) return
  const w = wordPopup.value
  if (isFavorited.value) {
    await favoritesApi.remove(auth.currentUserId, w.word).catch(() => {})
    isFavorited.value = false
  } else {
    await favoritesApi.add(auth.currentUserId, w.word, w.phonetic, w.meaning).catch(() => {})
    isFavorited.value = true
  }
}

// 检查是否已收藏
async function checkFavorite(word: string) {
  try {
    const { data } = await favoritesApi.check(auth.currentUserId, word)
    isFavorited.value = data?.favorited || false
  } catch { isFavorited.value = false }
}

// 发音评测 - 朗读整篇文章
async function startEval() {
  if (isRecording.value) {
    // 正在录音，停止并评测
    const audioBase64 = await stopRecording()
    if (recordingTimer) { clearInterval(recordingTimer); recordingTimer = null }
    
    if (!audioBase64 || !content.value) return
    
    // 发送到后端评测
    try {
      const { data } = await speechApi.evaluate(audioBase64, content.value.article, 'en')
      evalResult.value = {
        overall: data.overall,
        pronunciation: data.pronunciation,
        fluency: data.fluency,
        integrity: data.integrity,
        suggestion: data.suggestion,
      }
    } catch (err) {
      evalResult.value = { overall: 0, pronunciation: 0, fluency: 0, integrity: 0, suggestion: '评测失败，请稍后重试' }
    }
    return
  }
  
  // 开始录音
  const started = await startRecording()
  if (!started) {
    alert('无法获取录音权限，请在浏览器设置中允许麦克风访问')
    return
  }
  
  // 开始计时
  recordingTime.value = 0
  recordingTimer = setInterval(() => { recordingTime.value++ }, 1000)
}

// 重置评测
function resetEval() {
  evalResult.value = null
  recordingTime.value = 0
}

// 根据分数返回CSS类名
function getScoreClass(score: number) {
  if (score >= 90) return 'score-excellent'
  if (score >= 80) return 'score-good'
  if (score >= 70) return 'score-ok'
  if (score >= 60) return 'score-fair'
  return 'score-poor'
}

const currentIndex = computed(() => todayContents.value.findIndex(c => c.id === content.value?.id))
const hasPrev = computed(() => currentIndex.value > 0)
const hasNext = computed(() => currentIndex.value < todayContents.value.length - 1 && currentIndex.value >= 0)

// 把标题拆成可点击的片段
const titleParts = computed(() => {
  if (!content.value) return []
  const title = content.value.title
  const words = content.value.words || []
  const result: { text: string; isWord: boolean }[] = []
  // 匹配英文单词和非英文部分
  title.replace(/([a-zA-Z]+(?:'[a-zA-Z]+)?)|([^a-zA-Z]+)/g, (match, english, other) => {
    if (english) {
      result.push({ text: english, isWord: true })
    } else {
      result.push({ text: other, isWord: false })
    }
    return match
  })
  return result
})

function goToContent(id: number) {
  router.push(`/learning/content/${id}`)
}

// 单词弹窗5秒自动收起
let wordPopupTimer: ReturnType<typeof setTimeout> | null = null
function clearWordPopupTimer() {
  if (wordPopupTimer) { clearTimeout(wordPopupTimer); wordPopupTimer = null }
}
watch(wordPopup, (val) => {
  clearWordPopupTimer()
  if (val) {
    wordPopupTimer = setTimeout(() => { wordPopup.value = null }, 5000)
  }
})
onUnmounted(clearWordPopupTimer)

onMounted(async () => {
  initVoices()
  try {
    // 并行加载当前内容和今日列表
    const [contentRes, listRes] = await Promise.all([
      dailyApi.getContent(Number(route.params.id)),
      dailyApi.getTodayList(auth.currentUserId)
    ])
    content.value = contentRes.data
    todayContents.value = listRes.data.contents || []
  } catch { content.value = null }
  loading.value = false
})

function renderArticle(item: LearningContent) {
  const words = item.words || []
  let html = item.article.replace(/<[^>]+>/g, (tag) => `___TAG${tag}___`)
  html = html.replace(/\b([a-zA-Z]+(?:'[a-zA-Z]+)?)\b/g, (match, word) => {
    const isKey = words.some(w => w.word.toLowerCase() === word.toLowerCase())
    if (isKey) {
      return `<mark class="keyword" data-word="${word}"><strong>${word}</strong></mark>`
    }
    return `<span class="clickable-word" data-word="${word}">${word}</span>`
  })
  html = html.replace(/___TAG([^_]+)___/g, '$1')
  return html
}

async function handleWordClick(e: Event, item: LearningContent) {
  e.preventDefault()
  e.stopPropagation()
  
  const target = e.target as HTMLElement
  let rawWord = ''
  
  // 从 data-word 属性取
  if (target.dataset.word) {
    rawWord = target.dataset.word
  }
  // 向上查找
  else if (target.closest('[data-word]')) {
    rawWord = (target.closest('[data-word]') as HTMLElement).dataset.word || ''
  }
  // 从文本提取
  else {
    const m = (target.textContent || '').match(/[a-zA-Z]+/)
    if (m) rawWord = m[0]
  }
  
  // 弹出输入框兜底
  if (!rawWord) {
    const input = prompt('输入想查询的单词：')
    if (input && input.trim()) rawWord = input.trim()
  }
  
  if (!rawWord) return
  
  // 词形还原：获取单词原型
  const word = getBaseForm(rawWord)
  
  speakWord(word)
  checkFavorite(word)
  
  // 先查缓存
  const cached = getCachedWord(word)
  if (cached) {
    wordPopup.value = cached
    return
  }
  
  // 缓存没有，调API
  wordPopup.value = { word, meaning: '查询中...' }

  try {
    const { data } = await dictionaryApi.lookup(word)
    const ec = data?.ec?.word?.[0]
    const phonetic = ec?.usphone || ec?.ukphone || ''
    const trs = ec?.trs || []
    const meaning = trs.map((t: any) => t?.tr?.[0]?.l?.i?.[0]).filter(Boolean).join('；')
    const result = meaning
      ? { word, phonetic: phonetic ? `/${phonetic}/` : undefined, meaning }
      : { word, meaning: '未找到释义' }
    setCachedWord(word, result)
    wordPopup.value = result
  } catch { wordPopup.value = { word, meaning: '查询失败' } }
}
</script>

<style scoped>
.detail-content { padding-bottom: 20px; }
.card-title { font-size: 18px; font-weight: 700; margin-bottom: 12px; line-height: 1.6; }
.clickable-word {
  cursor: pointer;
  color: var(--primary);
  border-bottom: 1.5px dashed var(--primary);
  padding: 0 2px;
  transition: all 0.15s;
}
.clickable-word:hover {
  background: var(--primary-container);
  border-radius: 3px;
}
.article-body { font-size: 15px; line-height: 1.8; }
.article-body :deep(mark.keyword) { background: var(--primary-container); color: var(--on-primary-container); padding: 1px 3px; border-radius: 3px; cursor: pointer; }
.article-body :deep(.clickable-word) { cursor: pointer; border-bottom: 1px dashed var(--primary-light); transition: background 0.15s; }
.article-body :deep(.clickable-word):hover { background: var(--primary-container); border-radius: 2px; }
.words-wrap { display: flex; flex-wrap: wrap; gap: 8px; }
.word-chip { display: flex; flex-direction: column; padding: 8px 12px; background: var(--surface-container); border-radius: var(--radius-sm); cursor: pointer; }
.word-chip:hover { background: var(--primary-container); }
.word-text { font-weight: 600; font-size: 14px; }
.word-phonetic { font-size: 11px; color: var(--on-surface-variant); }
.word-meaning { font-size: 12px; color: var(--on-surface-variant); }
.word-popup { position: fixed; bottom: 64px; left: 50%; transform: translateX(-50%); width: calc(100% - 32px); max-width: 452px; padding: 20px; z-index: 200; border-radius: 20px; }
.popup-header { display: flex; align-items: center; gap: 12px; }
.popup-header h3 { font-size: 22px; margin: 0; flex: 1; }
.speak-btn { width: 36px; height: 36px; border: none; background: var(--primary-container); border-radius: 50%; font-size: 18px; cursor: pointer; display: flex; align-items: center; justify-content: center; }
.speak-btn:hover { background: var(--primary); }
.fav-btn { width: 36px; height: 36px; border: none; background: var(--surface-container); border-radius: 50%; font-size: 18px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s; }
.fav-btn:hover { background: #FFF3E0; }
.fav-btn.active { background: #FFE0B2; }

.nav-buttons {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-top: 1px solid var(--surface-container-high);
}

.nav-index {
  font-size: 13px;
  color: var(--on-surface-variant);
}

.btn-outline {
  padding: 8px 16px;
  border: 1px solid var(--primary);
  background: transparent;
  color: var(--primary);
  border-radius: var(--radius-sm);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-outline:hover:not(:disabled) {
  background: var(--primary-container);
}

.btn-outline:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.word-popup .phonetic { color: var(--on-surface-variant); }
.word-popup .meaning { margin-top: 10px; font-size: 16px; }
.word-popup .usage { margin-top: 8px; color: var(--on-surface-variant); font-size: 14px; font-style: italic; }

/* 朗读评测卡片 */
.eval-card {
  margin: 0 16px 16px;
  cursor: pointer;
}
.eval-trigger {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 20px;
}
.eval-icon {
  font-size: 32px;
}
.eval-text {
  font-size: 16px;
  font-weight: 600;
}
.eval-hint {
  font-size: 12px;
  color: var(--on-surface-variant);
}
.eval-recording {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 20px;
  color: #f44336;
}
.recording-pulse {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: #f44336;
  animation: pulse 1.5s infinite;
}
@keyframes pulse {
  0% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.1); opacity: 0.7; }
  100% { transform: scale(1); opacity: 1; }
}
.eval-result {
  padding: 16px;
}
.eval-scores-row {
  display: flex;
  justify-content: space-around;
  margin-bottom: 16px;
}
.eval-score {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}
.eval-score-num {
  font-size: 28px;
  font-weight: 700;
}
.eval-score-label {
  font-size: 12px;
  color: var(--on-surface-variant);
}
.score-excellent { color: #4caf50; }
.score-good { color: #8bc34a; }
.score-ok { color: #ffc107; }
.score-fair { color: #ff9800; }
.score-poor { color: #f44336; }
.eval-suggestion {
  margin-bottom: 12px;
  padding: 12px;
  background: var(--surface-container);
  border-radius: var(--radius-sm);
  font-size: 14px;
  color: var(--on-surface-variant);
  text-align: center;
}
.btn-sm {
  padding: 6px 16px;
  font-size: 13px;
}
</style>
