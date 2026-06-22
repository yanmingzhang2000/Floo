<template>
  <div class="page-container">
    <div class="page-header detail-header">
      <button class="btn-back" @click="router.back()">← 返回</button>
      <h1 v-if="content">{{ content.title }}</h1>
      <div v-if="content" class="header-tags">
        <span class="tag btn-header">{{ content.content_date }}</span>
        <span class="tag btn-header">{{ content.difficulty_level }}</span>
        <span class="tag btn-header">{{ content.theme_type }}</span>
      </div>
    </div>

    <div v-if="loading" class="loading"><div class="spinner"></div></div>

    <div v-else-if="content" class="detail-content">
      <div class="card">
        <h3 class="card-title">
          <span v-for="(part, i) in titleParts" :key="i"
            :class="part.isWord ? 'clickable-word' : ''"
            :data-word="part.isWord ? part.text : undefined"
            @click="part.isWord && handleWordClick($event)"
          >{{ part.text }}</span>
        </h3>
        <div class="article-body" v-html="renderArticle(content)" @click="handleWordClick($event)"></div>
      </div>

      <div v-if="content.translation" class="card">
        <h4 style="margin-bottom:8px;color:var(--on-surface-variant)">中文译文</h4>
        <p style="line-height:1.8">{{ content.translation }}</p>
      </div>

      <div v-if="content.words?.length" class="card">
        <h4 style="margin-bottom:10px;color:var(--on-surface-variant)">核心词汇</h4>
        <div class="words-wrap">
          <div v-for="w in content.words" :key="w.word" class="word-chip" @click="showWordFromChip(w)">
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

      <div class="detail-actions">
        <router-link :to="`/review?tab=dictation&content_id=${content.id}`" class="btn btn-primary btn-block">去默写</router-link>
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
              <button class="fav-btn" :class="{ 'is-fav': wordPopup.isFavorite }" @click="toggleFavorite">
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
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { dailyApi } from '@/api'
import { useAuthStore } from '@/stores'
import { speakWord, initVoices } from '@/composables/useSpeech'
import { renderArticle } from '@/composables/useArticleRender'
import { useWordPopup } from '@/composables/useWordPopup'
import { useSpeechEval } from '@/composables/useSpeechEval'
import type { LearningContent } from '@/types'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const loading = ref(true)
const content = ref<LearningContent | null>(null)
const todayContents = ref<LearningContent[]>([])

// 使用 composable
const { wordPopup, handleWordClick, toggleFavorite, showWordFromChip } = useWordPopup(() => auth.currentUserId)
const { isRecording, evalResult, recordingTime, startEval, resetEval, getScoreClass } = useSpeechEval(
  () => content.value?.article
)

const currentIndex = computed(() => todayContents.value.findIndex(c => c.id === content.value?.id))
const hasPrev = computed(() => currentIndex.value > 0)
const hasNext = computed(() => currentIndex.value < todayContents.value.length - 1 && currentIndex.value >= 0)

// 把标题拆成可点击的片段
const titleParts = computed(() => {
  if (!content.value) return []
  const title = content.value.title
  const result: { text: string; isWord: boolean }[] = []
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

onMounted(async () => {
  initVoices()
  try {
    const [contentRes, listRes] = await Promise.all([
      dailyApi.getContent(Number(route.params.id)),
      dailyApi.getTodayList(auth.currentUserId)
    ])
    content.value = contentRes.data
    todayContents.value = listRes.data.contents || []
  } catch { content.value = null }
  loading.value = false
})
</script>

<style scoped>
.detail-header {
  padding-bottom: 8px;
}

.header-tags {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

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
.fav-btn.is-fav { color: #f59e0b; }

.detail-actions {
  padding: 0 16px 16px;
}

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
</style>
