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
        <h3 class="card-title">{{ content.title }}</h3>
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
    </div>

    <Teleport to="body">
      <Transition name="fade">
        <div v-if="wordPopup" class="modal-overlay" @click.self="wordPopup = null">
          <div class="word-popup card">
            <h3>{{ wordPopup.word }}</h3>
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
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { dailyApi, dictionaryApi } from '@/api'
import type { LearningContent, WordItem } from '@/types'

const route = useRoute()
const loading = ref(true)
const content = ref<LearningContent | null>(null)
const wordPopup = ref<{ word: string; phonetic?: string; meaning: string; usage?: string } | null>(null)

onMounted(async () => {
  try {
    const { data } = await dailyApi.getContent(Number(route.params.id))
    content.value = data
  } catch { content.value = null }
  loading.value = false
})

function renderArticle(item: LearningContent) {
  if (!item.words?.length) return item.article
  let html = item.article
  for (const w of item.words) {
    const regex = new RegExp(`\\b(${w.word})\\b`, 'gi')
    html = html.replace(regex, `<mark class="keyword" data-word="${w.word}"><strong>$1</strong></mark>`)
  }
  return html
}

async function handleWordClick(e: Event, item: LearningContent) {
  const target = e.target as HTMLElement
  if (!target.classList.contains('keyword')) return
  const word = target.dataset.word || target.textContent || ''
  const found = item.words?.find(w => w.word.toLowerCase() === word.toLowerCase())
  if (found) {
    wordPopup.value = { word: found.word, phonetic: found.phonetic, meaning: found.meaning, usage: found.usage }
  } else {
    try {
      const { data } = await dictionaryApi.lookup(word)
      const meaning = data?.ec?.word?.[0]?.trs?.[0]?.tr?.[0]?.l?.i?.[0] || '未找到释义'
      wordPopup.value = { word, meaning }
    } catch { wordPopup.value = { word, meaning: '查询失败' } }
  }
}
</script>

<style scoped>
.detail-content { padding-bottom: 20px; }
.card-title { font-size: 18px; font-weight: 700; margin-bottom: 12px; }
.article-body { font-size: 15px; line-height: 1.8; }
.article-body :deep(mark.keyword) { background: var(--primary-container); color: var(--on-primary-container); padding: 1px 3px; border-radius: 3px; cursor: pointer; }
.words-wrap { display: flex; flex-wrap: wrap; gap: 8px; }
.word-chip { display: flex; flex-direction: column; padding: 8px 12px; background: var(--surface-container); border-radius: var(--radius-sm); cursor: pointer; }
.word-chip:hover { background: var(--primary-container); }
.word-text { font-weight: 600; font-size: 14px; }
.word-phonetic { font-size: 11px; color: var(--on-surface-variant); }
.word-meaning { font-size: 12px; color: var(--on-surface-variant); }
.word-popup { position: fixed; bottom: 0; left: 50%; transform: translateX(-50%); width: 100%; max-width: 480px; padding: 20px; z-index: 200; border-radius: 20px 20px 0 0; }
.word-popup h3 { font-size: 22px; }
.word-popup .phonetic { color: var(--on-surface-variant); }
.word-popup .meaning { margin-top: 10px; font-size: 16px; }
.word-popup .usage { margin-top: 8px; color: var(--on-surface-variant); font-size: 14px; font-style: italic; }
</style>
