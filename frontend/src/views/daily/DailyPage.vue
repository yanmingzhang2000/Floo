<template>
  <div class="page-container">
    <div class="page-header">
      <h1>今日英语 · {{ themeLabel }}</h1>
      <p class="subtitle">已完成 {{ visibleCount }}/{{ totalCount }} 篇</p>
      <div class="actions">
        <button class="btn btn-sm" style="background:rgba(255,255,255,0.2);color:white" @click="handleGenerate" :disabled="generating">
          {{ generating ? '生成中...' : '✨ 生成新内容' }}
        </button>
        <router-link to="/daily/list" class="btn btn-sm" style="background:rgba(255,255,255,0.2);color:white">
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
      <div v-for="(item, idx) in visibleContents" :key="item.id" class="content-card card">
        <div class="card-header">
          <span class="tag tag-primary">{{ item.content_type === 'overview' ? '今日总览' : `文章 ${idx}` }}</span>
          <span class="tag tag-success">{{ item.difficulty_level }}</span>
        </div>
        <h3 class="card-title">{{ item.title }}</h3>

        <div class="article-body" v-html="renderArticle(item)" @click="handleWordClick($event, item)"></div>

        <div v-if="item.translation" class="translation-toggle" @click="toggleTranslation(item.id)">
          {{ expandedTranslations.has(item.id) ? '收起译文 ▲' : '查看译文 ▼' }}
        </div>
        <div v-if="expandedTranslations.has(item.id) && item.translation" class="translation">
          {{ item.translation }}
        </div>

        <div v-if="item.words?.length" class="words-section">
          <h4>核心词汇</h4>
          <div class="words-wrap">
            <div v-for="w in item.words" :key="w.word" class="word-chip" @click="showWordDetail(w)">
              <span class="word-text">{{ w.word }}</span>
              <span class="word-phonetic" v-if="w.phonetic">{{ w.phonetic }}</span>
              <span class="word-meaning">{{ w.meaning }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="bottom-actions">
        <router-link to="/dictation" class="btn btn-primary btn-block">开始默写练习</router-link>
        <router-link to="/review" class="btn btn-outline btn-block">查看复习任务</router-link>
      </div>
    </div>

    <!-- 单词弹窗 -->
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
import { ref, computed, onMounted } from 'vue'
import { dailyApi } from '@/api'
import { useAuthStore } from '@/stores'
import { dictionaryApi } from '@/api'
import type { LearningContent, WordItem } from '@/types'

const auth = useAuthStore()
const loading = ref(true)
const generating = ref(false)
const contents = ref<LearningContent[]>([])
const expandedTranslations = ref(new Set<number>())
const wordPopup = ref<{ word: string; phonetic?: string; meaning: string; usage?: string } | null>(null)

const themeLabels: Record<string, string> = {
  ai_tech: 'AI科技', product_tech: '产品技术', business: '财经商业',
  daily_news: '日常新闻', self_growth: '个人成长', all_random: '随机主题',
}
const themeLabel = computed(() => themeLabels[contents.value[0]?.theme_type] || '每日学习')
const visibleCount = computed(() => visibleContents.value.length)
const totalCount = computed(() => contents.value.length)
const visibleContents = computed(() => {
  const goal = auth.preference?.daily_goal_minutes || 15
  if (goal <= 30) return contents.value.slice(0, 1)
  if (goal <= 40) return contents.value.slice(0, 2)
  return contents.value
})

onMounted(loadData)

async function loadData() {
  loading.value = true
  try {
    const { data } = await dailyApi.getTodayList(auth.currentUserId)
    contents.value = data.contents || []
  } catch { contents.value = [] }
  loading.value = false
}

async function handleGenerate() {
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
  let html = item.article
  // 先把核心词高亮（带下划线+粗体）
  if (item.words?.length) {
    for (const w of item.words) {
      const regex = new RegExp(`\\b(${w.word})\\b`, 'gi')
      html = html.replace(regex, `<mark class="keyword" data-word="$1"><strong>$1</strong></mark>`)
    }
  }
  // 再把所有剩余英文单词也包裹成可点击的span
  html = html.replace(/\b([a-zA-Z]+(?:'[a-zA-Z]+)?)\b/g, (match, word) => {
    // 已经被mark包裹的不再处理
    if (match.startsWith('<mark')) return match
    return `<span class="clickable-word" data-word="${word}">${word}</span>`
  })
  return html
}

async function handleWordClick(e: Event, item: LearningContent) {
  const target = e.target as HTMLElement
  const word = target.dataset.word || target.textContent || ''
  if (!word) return

  // 核心词：优先用本地数据（包含音标和词性）
  const found = item.words?.find(w => w.word.toLowerCase() === word.toLowerCase())
  if (found) {
    wordPopup.value = { word: found.word, phonetic: found.phonetic, meaning: found.meaning, usage: found.usage }
    return
  }

  // 非核心词：调用有道词典API
  try {
    const { data } = await dictionaryApi.lookup(word)
    const ec = data?.ec?.word?.[0]
    const phonetic = ec?.usphone || ec?.ukphone || ''
    const trs = ec?.trs || []
    const meaning = trs.map((t: any) => t?.tr?.[0]?.l?.i?.[0]).filter(Boolean).join('；') || '未找到释义'
    wordPopup.value = { word, phonetic: phonetic ? `/${phonetic}/` : undefined, meaning }
  } catch { wordPopup.value = { word, meaning: '查询失败' } }
}

function showWordDetail(w: WordItem) {
  wordPopup.value = { word: w.word, phonetic: w.phonetic, meaning: w.meaning, usage: w.usage }
}
</script>

<style scoped>
.content-card { margin-top: 16px; }
.card-header { display: flex; gap: 8px; margin-bottom: 10px; }
.card-title { font-size: 17px; font-weight: 700; margin-bottom: 12px; }

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
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: 480px;
  padding: 20px;
  z-index: 200;
  border-radius: 20px 20px 0 0;
}

.word-popup h3 { font-size: 22px; }
.word-popup .phonetic { color: var(--on-surface-variant); margin-top: 4px; }
.word-popup .meaning { margin-top: 10px; font-size: 16px; }
.word-popup .usage { margin-top: 8px; color: var(--on-surface-variant); font-size: 14px; font-style: italic; }
</style>
