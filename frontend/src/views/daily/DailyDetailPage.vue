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

      <div style="padding:16px">
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
              <button class="eval-btn" @click="evaluatePronunciation(wordPopup!.word)" :disabled="isRecording">
                {{ isRecording ? '🎙️ 录音中...' : '🎤 评测发音' }}
              </button>
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

    <!-- 发音评测结果弹窗 -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="evalPopup" class="modal-overlay" @click.self="evalPopup = null">
          <div class="eval-popup card">
            <h3 class="eval-word">{{ evalPopup.word }}</h3>
            
            <div v-if="evalLoading" class="eval-loading">
              <div class="spinner"></div>
              <p>{{ evalPopup.suggestion }}</p>
            </div>
            
            <div v-else class="eval-scores">
              <div class="score-row">
                <span class="score-label">总分</span>
                <span class="score-value" :class="getScoreClass(evalPopup.overall)">{{ evalPopup.overall }}</span>
              </div>
              <div class="score-row">
                <span class="score-label">发音准确度</span>
                <span class="score-value" :class="getScoreClass(evalPopup.pronunciation)">{{ evalPopup.pronunciation }}</span>
              </div>
              <div class="score-row">
                <span class="score-label">流利度</span>
                <span class="score-value" :class="getScoreClass(evalPopup.fluency)">{{ evalPopup.fluency }}</span>
              </div>
              <div class="score-row">
                <span class="score-label">完整度</span>
                <span class="score-value" :class="getScoreClass(evalPopup.integrity)">{{ evalPopup.integrity }}</span>
              </div>
              <p class="eval-suggestion">{{ evalPopup.suggestion }}</p>
            </div>
            
            <div class="eval-actions">
              <button class="btn btn-outline" @click="evaluatePronunciation(evalPopup.word)">重新评测</button>
              <button class="btn btn-primary" @click="evalPopup = null">关闭</button>
            </div>
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
const evalPopup = ref<{
  word: string;
  overall: number;
  pronunciation: number;
  fluency: number;
  integrity: number;
  suggestion: string;
} | null>(null)
const evalLoading = ref(false)

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

// 发音评测
async function evaluatePronunciation(word: string) {
  // 关闭单词弹窗
  wordPopup.value = null
  
  // 开始录音
  const started = await startRecording()
  if (!started) {
    alert('无法获取录音权限，请在浏览器设置中允许麦克风访问')
    return
  }
  
  // 提示用户朗读
  evalLoading.value = true
  evalPopup.value = { word, overall: 0, pronunciation: 0, fluency: 0, integrity: 0, suggestion: '正在录音，请朗读这个单词...' }
  
  // 录音3秒后自动停止
  setTimeout(async () => {
    const audioBase64 = await stopRecording()
    if (!audioBase64) {
      evalPopup.value = null
      evalLoading.value = false
      return
    }
    
    // 发送到后端评测
    evalPopup.value = { word, overall: 0, pronunciation: 0, fluency: 0, integrity: 0, suggestion: '正在评测中...' }
    
    try {
      const { data } = await speechApi.evaluate(audioBase64, word)
      evalPopup.value = {
        word,
        overall: data.overall,
        pronunciation: data.pronunciation,
        fluency: data.fluency,
        integrity: data.integrity,
        suggestion: data.suggestion,
      }
    } catch (err) {
      evalPopup.value = { word, overall: 0, pronunciation: 0, fluency: 0, integrity: 0, suggestion: '评测失败，请稍后重试' }
    }
    evalLoading.value = false
  }, 3000)
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
  let word = ''
  
  // 从 data-word 属性取
  if (target.dataset.word) {
    word = target.dataset.word
  }
  // 向上查找
  else if (target.closest('[data-word]')) {
    word = (target.closest('[data-word]') as HTMLElement).dataset.word || ''
  }
  // 从文本提取
  else {
    const m = (target.textContent || '').match(/[a-zA-Z]+/)
    if (m) word = m[0]
  }
  
  // 弹出输入框兜底
  if (!word) {
    const input = prompt('输入想查询的单词：')
    if (input && input.trim()) word = input.trim()
  }
  
  if (!word) return
  
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

/* 评测按钮 */
.eval-btn {
  padding: 6px 12px;
  border: none;
  background: var(--primary);
  color: white;
  border-radius: var(--radius-sm);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}
.eval-btn:hover:not(:disabled) {
  background: var(--primary-dark, #3d7a85);
}
.eval-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 评测结果弹窗 */
.eval-popup {
  position: fixed;
  bottom: 64px;
  left: 50%;
  transform: translateX(-50%);
  width: calc(100% - 32px);
  max-width: 452px;
  padding: 24px;
  z-index: 200;
  border-radius: 20px;
  text-align: center;
}
.eval-word {
  font-size: 24px;
  margin-bottom: 20px;
}
.eval-loading {
  padding: 20px 0;
}
.eval-loading p {
  margin-top: 12px;
  color: var(--on-surface-variant);
}
.eval-scores {
  margin-bottom: 20px;
}
.score-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid var(--surface-container);
}
.score-row:last-child {
  border-bottom: none;
}
.score-label {
  font-size: 14px;
  color: var(--on-surface-variant);
}
.score-value {
  font-size: 20px;
  font-weight: 700;
}
.score-excellent { color: #4caf50; }
.score-good { color: #8bc34a; }
.score-ok { color: #ffc107; }
.score-fair { color: #ff9800; }
.score-poor { color: #f44336; }
.eval-suggestion {
  margin-top: 16px;
  padding: 12px;
  background: var(--surface-container);
  border-radius: var(--radius-sm);
  font-size: 14px;
  color: var(--on-surface-variant);
}
.eval-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}
.eval-actions .btn {
  min-width: 100px;
}
</style>
