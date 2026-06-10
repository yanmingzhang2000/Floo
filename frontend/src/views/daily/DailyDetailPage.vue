<template>
  <div class="page-container">
    <div class="page-header clickable-title" v-if="content" @click="handleWordClick($event, content)">
      <h1 v-html="renderTitle(content)"></h1>
      <div style="display:flex;gap:8px;margin-top:8px">
        <span class="tag" style="background:rgba(255,255,255,0.2);color:white">{{ content.content_date }}</span>
        <span class="tag" style="background:rgba(255,255,255,0.2);color:white">{{ content.difficulty_level }}</span>
        <span class="tag" style="background:rgba(255,255,255,0.2);color:white">{{ content.theme_type }}</span>
      </div>
    </div>
      <div style="display:flex;gap:8px;margin-top:8px">
        <span class="tag" style="background:rgba(255,255,255,0.2);color:white">{{ content.content_date }}</span>
        <span class="tag" style="background:rgba(255,255,255,0.2);color:white">{{ content.difficulty_level }}</span>
        <span class="tag" style="background:rgba(255,255,255,0.2);color:white">{{ content.theme_type }}</span>
      </div>
    </div>

    <div v-if="loading" class="loading"><div class="spinner"></div></div>

    <div v-else-if="content" class="detail-content">
      <div class="card">
        <h3 class="card-title clickable-title" v-html="renderTitle(content)" @click="handleWordClick($event, content)"></h3>
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
import { dailyApi, dictionaryApi, favoritesApi } from '@/api'
import { useAuthStore } from '@/stores'
import { speakWord, initVoices } from '@/composables/useSpeech'
import type { LearningContent, WordItem } from '@/types'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const loading = ref(true)
const content = ref<LearningContent | null>(null)
const todayContents = ref<LearningContent[]>([])
const wordPopup = ref<{ word: string; phonetic?: string; meaning: string; usage?: string } | null>(null)
const isFavorited = ref(false)

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

const currentIndex = computed(() => todayContents.value.findIndex(c => c.id === content.value?.id))
const hasPrev = computed(() => currentIndex.value > 0)
const hasNext = computed(() => currentIndex.value < todayContents.value.length - 1 && currentIndex.value >= 0)

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

function renderTitle(item: LearningContent) {
  const words = item.words || []
  return item.title.replace(/\b([a-zA-Z]+(?:'[a-zA-Z]+)?)\b/g, (match, word) => {
    const isKey = words.some(w => w.word.toLowerCase() === word.toLowerCase())
    if (isKey) {
      return `<mark class="keyword" data-word="${word}"><strong>${word}</strong></mark>`
    }
    return `<span class="clickable-word" data-word="${word}">${word}</span>`
  })
}

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
  const target = e.target as HTMLElement
  const word = target.dataset.word || target.textContent || ''
  if (!word || (!target.classList.contains('keyword') && !target.classList.contains('clickable-word'))) return

  speakWord(word)
  checkFavorite(word)

  // 显示加载状态
  wordPopup.value = { word, meaning: '查询中...' }

  // 所有词汇统一调用词典API
  try {
    const { data } = await dictionaryApi.lookup(word)
    const ec = data?.ec?.word?.[0]
    const phonetic = ec?.usphone || ec?.ukphone || ''
    const trs = ec?.trs || []
    const meaning = trs.map((t: any) => t?.tr?.[0]?.l?.i?.[0]).filter(Boolean).join('；')
    if (meaning) {
      wordPopup.value = { word, phonetic: phonetic ? `/${phonetic}/` : undefined, meaning }
    } else {
      wordPopup.value = { word, meaning: '未找到释义' }
    }
  } catch { wordPopup.value = { word, meaning: '查询失败' } }
}
</script>

<style scoped>
.detail-content { padding-bottom: 20px; }
.clickable-title { cursor: pointer; }
.clickable-title h1 { cursor: pointer; }
.clickable-title :deep(mark.keyword) { background: rgba(255,255,255,0.3); color: white; padding: 1px 3px; border-radius: 3px; cursor: pointer; }
.clickable-title :deep(.clickable-word) { cursor: pointer; border-bottom: 1px dashed rgba(255,255,255,0.5); transition: background 0.15s; }
.clickable-title :deep(.clickable-word):hover { background: rgba(255,255,255,0.2); border-radius: 2px; }
.card-title { font-size: 18px; font-weight: 700; margin-bottom: 12px; }
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
</style>
