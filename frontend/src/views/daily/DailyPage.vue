<template>
  <div class="page-container">
    <OnboardingGuide />
    <div class="page-header">
      <h1>今日英语 · {{ themeLabel }}</h1>
      <p class="subtitle">共 {{ totalCount }} 篇</p>
      <div class="actions">
        <button class="btn btn-sm" style="background:rgba(255,255,255,0.2);color:white" @click="handleGenerate" :disabled="generating || remainingCount <= 0">
          {{ generating ? '生成中...' : remainingCount > 0 ? `✨ 生成新内容 (${remainingCount}次)` : '今日已用完' }}
        </button>
        <router-link to="/learning/list" class="btn btn-sm" style="background:rgba(255,255,255,0.2);color:white">
          📋 历史内容
        </router-link>
      </div>
    </div>

    <div v-if="loading" class="loading"><div class="spinner"></div></div>

    <div v-else-if="contents.length === 0" class="empty-state">
      <div class="icon">📝</div>
      <p>今日还没有学习内容</p>
      <button class="btn btn-primary" style="margin-top:16px" @click="handleGenerate" :disabled="generating">
        AI 生成今日内容
      </button>
    </div>

    <div v-else>
      <!-- 切换导航 -->
      <div v-if="totalCount > 1" class="switch-nav">
        <button class="switch-btn" :disabled="!hasPrev" @click="goPrev">← 上一篇</button>
        <span class="switch-index">{{ currentIdx + 1 }} / {{ totalCount }}</span>
        <button class="switch-btn" :disabled="!hasNext" @click="goNext">下一篇 →</button>
      </div>

      <div v-if="currentItem" class="content-card card">
        <div class="card-header">
          <span class="tag tag-primary">{{ currentItem.content_type === 'overview' ? '今日总览' : `文章 ${currentIdx + 1}` }}</span>
          <span class="tag tag-success">{{ currentItem.difficulty_level }}</span>
          <button class="read-btn" @click.stop="toggleReading(currentItem.article)" :class="{ active: readState === 'playing' }">
            {{ readState === 'playing' ? '⏸ 暂停' : readState === 'paused' ? '▶ 继续' : '🔊 朗读' }}
          </button>
        </div>
        <h3 class="card-title">{{ currentItem.title }}</h3>

        <div class="article-body" v-html="renderArticle(currentItem)" @click="handleWordClick($event, currentItem)"></div>

        <div v-if="currentItem.translation" class="translation-toggle" @click="toggleTranslation(currentItem.id)">
          {{ expandedTranslations.has(currentItem.id) ? '收起译文 ▲' : '查看译文 ▼' }}
        </div>
        <div v-if="expandedTranslations.has(currentItem.id) && currentItem.translation" class="translation">
          {{ currentItem.translation }}
        </div>

        <div v-if="currentItem.words?.length" class="words-section">
          <h4>核心词汇</h4>
          <div class="words-wrap">
            <div v-for="w in currentItem.words" :key="w.word" class="word-chip" @click="showWordDetail(w)">
              <span class="word-text">{{ w.word }}</span>
              <span class="word-phonetic" v-if="w.phonetic">{{ w.phonetic }}</span>
              <span class="word-meaning">{{ w.meaning }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="bottom-actions">
        <router-link to="/review" class="btn btn-primary btn-block">去默写/复习</router-link>
      </div>
    </div>

    <!-- 单词弹窗 -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="wordPopup" class="modal-overlay" @click.self="wordPopup = null">
          <div class="word-popup card">
            <div class="popup-header">
              <h3>{{ wordPopup.word }}</h3>
              <button class="speak-btn" @click="speakWord(wordPopup!.word)">🔊</button>
              <button
                class="fav-btn"
                :class="{ 'is-fav': wordPopup.isFavorite }"
                @click="toggleFavorite"
              >
                {{ wordPopup.isFavorite ? '★' : '☆' }}
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
import { dailyApi, generationLimitApi, favoritesApi } from '@/api'
import { useAuthStore } from '@/stores'
import { dictionaryApi } from '@/api'
import { speakWord, initVoices, toggleReading, stopReading, useReadingState } from '@/composables/useSpeech'
import OnboardingGuide from '@/components/OnboardingGuide.vue'
import type { LearningContent, WordItem } from '@/types'

const auth = useAuthStore()
const loading = ref(true)
const generating = ref(false)
const contents = ref<LearningContent[]>([])
const expandedTranslations = ref(new Set<number>())
const wordPopup = ref<{ word: string; phonetic?: string; meaning: string; usage?: string; isFavorite?: boolean } | null>(null)
const remainingCount = ref(3)
const { readState } = useReadingState()
const cardRefs = ref<(Element | null)[]>([])
const activeAnchor = ref(0)

// 单词查询缓存
const wordCache = new Map<string, { word: string; phonetic?: string; meaning: string }>()

function getCachedWord(word: string) {
  return wordCache.get(word.toLowerCase())
}

function setCachedWord(word: string, result: { word: string; phonetic?: string; meaning: string }) {
  wordCache.set(word.toLowerCase(), result)
  if (wordCache.size > 500) {
    const firstKey = wordCache.keys().next().value
    if (firstKey) wordCache.delete(firstKey)
  }
}

function scrollToCard(idx: number) {
  const el = cardRefs.value[idx]
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    activeAnchor.value = idx
  }
}

function setCardRef(idx: number) {
  return (el: any) => {
    cardRefs.value[idx] = el?.$el || el
  }
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

const themeLabels: Record<string, string> = {
  ai_tech: 'AI科技', product_tech: '产品技术', business: '财经商业',
  daily_news: '日常新闻', self_growth: '个人成长', all_random: '随机主题',
}
const themeLabel = computed(() => themeLabels[contents.value[0]?.theme_type] || '每日学习')
const totalCount = computed(() => contents.value.length)
const currentIdx = ref(0)
const currentItem = computed(() => contents.value[currentIdx.value] || null)
const hasPrev = computed(() => currentIdx.value > 0)
const hasNext = computed(() => currentIdx.value < contents.value.length - 1)

function goNext() { if (hasNext.value) currentIdx.value++ }
function goPrev() { if (hasPrev.value) currentIdx.value-- }

onMounted(() => {
  initVoices()
  loadData()
  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  clearWordPopupTimer()
  window.removeEventListener('scroll', handleScroll)
})

function handleScroll() {
  const scrollY = window.scrollY + 120
  for (let i = cardRefs.value.length - 1; i >= 0; i--) {
    const el = cardRefs.value[i] as HTMLElement | null
    if (el && el.offsetTop <= scrollY) {
      activeAnchor.value = i
      break
    }
  }
}

async function loadData() {
  loading.value = true
  try {
    const { data } = await dailyApi.getTodayList(auth.currentUserId)
    contents.value = data.contents || []
    // 加载生成次数限制
    const { data: limitData } = await generationLimitApi.getLimit(auth.currentUserId)
    remainingCount.value = limitData.remaining_count
  } catch { contents.value = [] }
  loading.value = false
}

async function handleGenerate() {
  // 检查生成次数限制
  if (remainingCount.value <= 0) {
    alert('今日生成次数已达上限（每天最多3次），请明天再来')
    return
  }
  
  generating.value = true
  try {
    await dailyApi.generate(auth.currentUserId)
    await loadData()
  } catch { /* ignore */ }
  generating.value = false
}

function toggleTranslation(id: number) {
  const s = new Set(expandedTranslations.value)
  s.has(id) ? s.delete(id) : s.add(id)
  expandedTranslations.value = s
}

function renderArticle(item: LearningContent) {
  const words = item.words || []
  // 先用占位符保护HTML标签
  let html = item.article.replace(/<[^>]+>/g, (tag) => `___TAG${tag}___`)

  // 把所有英文单词包裹成span
  html = html.replace(/\b([a-zA-Z]+(?:'[a-zA-Z]+)?)\b/g, (match, word) => {
    const isKey = words.some(w => w.word.toLowerCase() === word.toLowerCase())
    if (isKey) {
      return `<mark class="keyword" data-word="${word}"><strong>${word}</strong></mark>`
    }
    return `<span class="clickable-word" data-word="${word}">${word}</span>`
  })

  // 恢复HTML标签
  html = html.replace(/___TAG([^_]+)___/g, '$1')
  return html
}

async function handleWordClick(e: Event, item: LearningContent) {
  const target = e.target as HTMLElement
  const word = target.dataset.word || target.textContent || ''
  if (!word || !target.classList.contains('keyword') && !target.classList.contains('clickable-word')) return

  speakWord(word)

  // 先查缓存
  const cached = getCachedWord(word)
  if (cached) {
    const { data: favData } = await favoritesApi.check(auth.currentUserId, word).catch(() => ({ data: { is_favorite: false } }))
    wordPopup.value = { ...cached, isFavorite: favData.is_favorite }
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
    if (meaning) {
      const result = { word, phonetic: phonetic ? `/${phonetic}/` : undefined, meaning }
      setCachedWord(word, result)
      const { data: favData } = await favoritesApi.check(auth.currentUserId, word)
      wordPopup.value = { ...result, isFavorite: favData.is_favorite }
    } else {
      wordPopup.value = { word, meaning: '未找到释义' }
    }
  } catch (err) {
    console.error('Dictionary lookup failed:', err)
    wordPopup.value = { word, meaning: '查询失败，请稍后重试' }
  }
}

function showWordDetail(w: WordItem) {
  wordPopup.value = { word: w.word, phonetic: w.phonetic, meaning: w.meaning, usage: w.usage }
}

async function toggleFavorite() {
  if (!wordPopup.value || !auth.currentUserId) return
  const { word, phonetic, meaning, isFavorite } = wordPopup.value

  try {
    if (isFavorite) {
      await favoritesApi.remove(auth.currentUserId, word)
      wordPopup.value = { ...wordPopup.value, isFavorite: false }
    } else {
      await favoritesApi.add(auth.currentUserId, word, phonetic, meaning)
      wordPopup.value = { ...wordPopup.value, isFavorite: true }
    }
  } catch { /* ignore */ }
}
</script>

<style scoped>
.content-card { margin-top: 16px; }
.card-header { display: flex; gap: 8px; margin-bottom: 10px; align-items: center; }

.switch-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--surface-container);
  border-radius: var(--radius-sm);
  margin: 12px 0 0 0;
}

.switch-btn {
  padding: 8px 16px;
  border: 1px solid var(--primary);
  background: transparent;
  color: var(--primary);
  border-radius: var(--radius-sm);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.switch-btn:hover:not(:disabled) { background: var(--primary-container); }
.switch-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.switch-index {
  font-size: 13px;
  color: var(--on-surface-variant);
}

.card-title { font-size: 17px; font-weight: 700; margin-bottom: 12px; }

.read-btn {
  margin-left: auto;
  padding: 4px 10px;
  border: none;
  border-radius: 16px;
  background: var(--primary-container);
  color: var(--on-primary-container);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.read-btn:hover { background: var(--primary); color: white; }
.read-btn.active { background: var(--primary); color: white; animation: pulse 1.5s infinite; }

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.article-body {
  font-size: 15px;
  line-height: 1.8;
  color: var(--on-surface);
}

.article-body :deep(mark.keyword) {
  background: var(--primary-container);
  color: var(--on-primary-container);
  padding: 1px 3px;
  border-radius: 3px;
  cursor: pointer;
}

.article-body :deep(.clickable-word) {
  cursor: pointer;
  border-bottom: 1px dashed var(--primary-light);
  transition: background 0.15s;
}

.article-body :deep(.clickable-word):hover {
  background: var(--primary-container);
  border-radius: 2px;
}

.translation-toggle {
  color: var(--primary);
  font-size: 14px;
  cursor: pointer;
  margin-top: 12px;
  font-weight: 500;
}

.translation {
  font-size: 14px;
  color: var(--on-surface-variant);
  margin-top: 8px;
  padding: 12px;
  background: var(--surface-container);
  border-radius: var(--radius-sm);
  line-height: 1.6;
}

.words-section {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid var(--surface-container-high);
}

.words-section h4 { font-size: 14px; margin-bottom: 10px; color: var(--on-surface-variant); }

.words-wrap { display: flex; flex-wrap: wrap; gap: 8px; }

.word-chip {
  display: flex;
  flex-direction: column;
  padding: 8px 12px;
  background: var(--surface-container);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background 0.2s;
}

.word-chip:hover { background: var(--primary-container); }
.word-text { font-weight: 600; font-size: 14px; }
.word-phonetic { font-size: 11px; color: var(--on-surface-variant); }
.word-meaning { font-size: 12px; color: var(--on-surface-variant); }

.bottom-actions {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.word-popup {
  position: fixed;
  bottom: 64px;
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: 480px;
  padding: 20px;
  z-index: 200;
  border-radius: 20px;
  margin: 0 16px;
  width: calc(100% - 32px);
}

.popup-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.popup-header h3 { font-size: 22px; margin: 0; }

.speak-btn {
  width: 36px;
  height: 36px;
  border: none;
  background: var(--primary-container);
  border-radius: 50%;
  font-size: 18px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.speak-btn:hover { background: var(--primary); }

.fav-btn {
  width: 36px;
  height: 36px;
  border: none;
  background: var(--surface-container);
  border-radius: 50%;
  font-size: 20px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  margin-left: auto;
}

.fav-btn:hover { background: var(--primary-container); }
.fav-btn.is-fav { color: #f59e0b; }

.word-popup .phonetic { color: var(--on-surface-variant); margin-top: 4px; }
.word-popup .meaning { margin-top: 10px; font-size: 16px; }
.word-popup .usage { margin-top: 8px; color: var(--on-surface-variant); font-size: 14px; font-style: italic; }
</style>
