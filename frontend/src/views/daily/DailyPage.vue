<template>
  <div class="page-container">
    <OnboardingGuide />
    <div class="page-header">
      <h1>今日英语 · {{ themeLabel }}</h1>
      <p class="subtitle">共 {{ totalCount }} 篇</p>
      <div class="actions">
        <LoadingButton variant="header" size="sm" :loading="generating" :disabled="remainingCount <= 0" @click="handleGenerate">
          {{ remainingCount > 0 ? `✨ 生成新内容 (${remainingCount}次)` : '今日已用完' }}
        </LoadingButton>
        <router-link to="/learning/list" class="btn btn-sm btn-header">
          📋 历史内容
        </router-link>
        <button class="btn btn-sm btn-header" @click="showCustomContent = true">
          📝 自定义内容
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading"><div class="spinner"></div></div>

    <div v-else-if="contents.length === 0" class="empty-state">
      <div class="icon">📝</div>
      <p>今日还没有学习内容</p>
      <LoadingButton variant="primary" :loading="generating" style="margin-top:16px" @click="handleGenerate">
        AI 生成今日内容
      </LoadingButton>
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
          <span v-if="currentItem.creator_type === 1" class="tag tag-warning">自定义</span>
          <span class="tag tag-success">{{ currentItem.difficulty_level }}</span>
          <button class="read-btn" @click.stop="toggleReading(currentItem.article)" :class="{ active: readState === 'playing' }">
            {{ readState === 'playing' ? '⏸ 暂停' : readState === 'paused' ? '▶ 继续' : '🔊 朗读' }}
          </button>
          <button
            v-if="currentItem.creator_type === 1 && isGenerationFailed(currentItem)"
            class="regenerate-btn"
            :disabled="regeneratingIds.has(currentItem.id)"
            @click.stop="regenerateCurrentCustom"
            title="AI 生成失败，重新生成译文和词组"
          >
            {{ regeneratingIds.has(currentItem.id) ? '生成中...' : '🔄 重新生成' }}
          </button>
          <button v-if="currentItem.creator_type === 1" class="delete-btn" @click.stop="deleteCurrentCustom" title="删除">🗑️</button>
        </div>
        <h3 class="card-title">{{ currentItem.title }}</h3>

        <div v-if="currentItem.creator_type === 1 && isGenerationFailed(currentItem)" class="gen-failed-banner">
          <span class="gen-failed-icon">⚠️</span>
          <span class="gen-failed-text">译文或词组尚未生成，点击右上角"🔄 重新生成"重试</span>
        </div>

        <div class="learned-toggle" @click="toggleLearned(currentItem)">
          <span class="learned-icon">{{ learnedIds.has(currentItem.id) ? '✅' : '☑️' }}</span>
          <span class="learned-text">{{ learnedIds.has(currentItem.id) ? '已学过' : '标记已学' }}</span>
        </div>

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
            <div v-for="w in currentItem.words" :key="w.word" class="word-chip" @click="showWordFromChip(w)">
              <span class="word-text">{{ w.word }}</span>
              <span class="word-phonetic" v-if="w.phonetic">{{ w.phonetic }}</span>
              <span class="word-meaning">{{ w.meaning }}</span>
            </div>
          </div>
        </div>

        <!-- 朗读评测 -->
        <div class="eval-section">
          <div v-if="!evalResult && !isRecording" class="eval-trigger" @click="startEval">
            <span class="eval-icon">🎤</span>
            <span class="eval-text">朗读评测</span>
          </div>
          <div v-else-if="isRecording" class="eval-recording" @click="startEval">
            <div class="recording-pulse"></div>
            <span class="eval-text">⏹ 停止录音</span>
            <span class="eval-hint">已录制 {{ recordingTime }}s，点击停止</span>
          </div>
          <div v-else class="eval-result">
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
            </div>
            <p class="eval-suggestion">{{ evalResult?.suggestion }}</p>
            <button class="btn btn-outline btn-sm" @click="resetEval">重新评测</button>
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
    <CustomContentModal :visible="showCustomContent" @close="showCustomContent = false" @created="loadData" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { dailyApi, generationLimitApi } from '@/api'
import { useAuthStore } from '@/stores'
import { speakWord, initVoices, toggleReading, useReadingState } from '@/composables/useSpeech'
import { renderArticle } from '@/composables/useArticleRender'
import { useWordPopup } from '@/composables/useWordPopup'
import { useSpeechEval } from '@/composables/useSpeechEval'
import { useToast } from '@/composables/useToast'
import LoadingButton from '@/components/LoadingButton.vue'
import OnboardingGuide from '@/components/OnboardingGuide.vue'
import CustomContentModal from '@/components/CustomContentModal.vue'
import type { LearningContent } from '@/types'

const auth = useAuthStore()
const toast = useToast()
const loading = ref(true)
const generating = ref(false)
const showCustomContent = ref(false)
const contents = ref<LearningContent[]>([])
const expandedTranslations = ref(new Set<number>())
const regeneratingIds = ref(new Set<number>())

// 判断自定义内容是否 AI 生成失败：译文为空/降级文案，或词汇列表为空
// 后端降级文案固定以「（翻译生成失败」开头，见 backend/app/routers/daily.py:691
function isGenerationFailed(item: LearningContent): boolean {
  if (!item || item.creator_type !== 1) return false
  const tr = (item.translation || '').trim()
  const failedTranslation = !tr || tr.startsWith('（翻译生成失败')
  const emptyWords = !item.words || item.words.length === 0
  return failedTranslation || emptyWords
}
const remainingCount = ref(3)
const { readState } = useReadingState()

// 使用 composable
const { wordPopup, handleWordClick, toggleFavorite, showWordFromChip } = useWordPopup(() => auth.currentUserId)
const { isRecording, evalResult, recordingTime, startEval, resetEval, getScoreClass } = useSpeechEval(
  () => currentItem.value?.article
)

// 已学内容
const learnedIds = ref(new Set<number>())

async function toggleLearned(item: LearningContent) {
  if (!auth.currentUserId) return
  try {
    const { data } = await dailyApi.toggleLearned(auth.currentUserId, item.id)
    if (data.learned) {
      learnedIds.value.add(item.id)
    } else {
      learnedIds.value.delete(item.id)
    }
    learnedIds.value = new Set(learnedIds.value)
  } catch (e) {
    console.error('Toggle learned failed:', e)
  }
}

async function loadLearnedIds() {
  if (!auth.currentUserId) return
  try {
    const { data } = await dailyApi.getLearnedIds(auth.currentUserId)
    learnedIds.value = new Set(data.content_ids || [])
  } catch (e) {
    console.error('Load learned ids failed:', e)
  }
}

const LEARNED_AUTO_DELAY = 5 * 60 * 1000
let autoLearnTimer: ReturnType<typeof setTimeout> | null = null

function startAutoLearnTimer() {
  clearAutoLearnTimer()
  const item = currentItem.value
  if (!item || !auth.currentUserId) return
  autoLearnTimer = setTimeout(async () => {
    if (!currentItem.value || !auth.currentUserId) return
    try {
      const { data } = await dailyApi.markLearned(auth.currentUserId, currentItem.value.id)
      if (data.learned) {
        learnedIds.value = new Set(learnedIds.value).add(currentItem.value.id)
      }
    } catch { /* silent */ }
  }, LEARNED_AUTO_DELAY)
}

function clearAutoLearnTimer() {
  if (autoLearnTimer !== null) {
    clearTimeout(autoLearnTimer)
    autoLearnTimer = null
  }
}

const themeLabels: Record<string, string> = {
  ai_tech: 'AI科技', product_tech: '产品技术', business: '财经商业',
  daily_news: '日常新闻', self_growth: '个人成长', all_random: '随机主题',
  custom: '自定义',
}
const themeLabel = computed(() => themeLabels[contents.value[0]?.theme_type] || '每日学习')
const totalCount = computed(() => contents.value.length)
const currentIdx = ref(0)
const currentItem = computed(() => contents.value[currentIdx.value] || null)
const hasPrev = computed(() => currentIdx.value > 0)
const hasNext = computed(() => currentIdx.value < contents.value.length - 1)

function goNext() { if (hasNext.value) currentIdx.value++ }
function goPrev() { if (hasPrev.value) currentIdx.value-- }

// 切换文章时重置自动标记定时器
watch(currentIdx, () => { startAutoLearnTimer() })

onMounted(() => {
  initVoices()
  loadData()
  loadLearnedIds()
  startAutoLearnTimer()
})

onUnmounted(() => {
  clearAutoLearnTimer()
})

async function loadData() {
  loading.value = true
  try {
    const { data } = await dailyApi.getTodayList(auth.currentUserId)
    contents.value = data.contents || []
    const { data: limitData } = await generationLimitApi.getLimit(auth.currentUserId)
    remainingCount.value = limitData.remaining_count
  } catch { contents.value = [] }
  loading.value = false
}

async function handleGenerate() {
  if (remainingCount.value <= 0) {
    toast.warning('今日生成次数已达上限（每天最多3次），请明天再来')
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

async function deleteCurrentCustom() {
  const item = currentItem.value
  if (!item || !auth.currentUserId || item.creator_type !== 1) return
  if (!confirm('删除后无法恢复，关联的复习记录也将清除，确定删除？')) return
  try {
    await dailyApi.deleteCustomContent(item.id, auth.currentUserId)
    contents.value = contents.value.filter(c => c.id !== item.id)
    currentIdx.value = Math.min(currentIdx.value, contents.value.length - 1)
    toast.success('已删除')
  } catch (e: any) {
    toast.error(e.response?.data?.detail || '删除失败')
  }
}

async function regenerateCurrentCustom() {
  const item = currentItem.value
  if (!item || !auth.currentUserId || item.creator_type !== 1) return
  if (regeneratingIds.value.has(item.id)) {
    // 防止重复点击：同一条正在重新生成时忽略
    return
  }
  const contentId = item.id
  regeneratingIds.value = new Set(regeneratingIds.value).add(contentId)
  try {
    await dailyApi.regenerateCustomContent(contentId, auth.currentUserId)
    // 重新拉取列表以同步最新译文和词组
    await loadData()
    toast.success('重新生成成功')
  } catch (e: any) {
    const detail = e?.response?.data?.detail || '重新生成失败'
    toast.error(detail)
  } finally {
    const next = new Set(regeneratingIds.value)
    next.delete(contentId)
    regeneratingIds.value = next
  }
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

.learned-toggle {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 6px 14px; border-radius: 20px; cursor: pointer;
  background: var(--surface); border: 1.5px solid var(--outline-variant);
  font-size: 13px; color: var(--on-surface-variant);
  transition: all 0.2s;
  margin-bottom: 12px;
}
.learned-toggle:active { transform: scale(0.95); }
.learned-icon { font-size: 16px; }
.learned-text { font-weight: 500; }

.tag-warning { background: #FFF3E0; color: #E65100; font-size: 11px; padding: 2px 8px; border-radius: 10px; font-weight: 600; }
.delete-btn { background: none; border: none; font-size: 16px; cursor: pointer; padding: 4px 8px; border-radius: 8px; transition: background 0.2s; }
.delete-btn:hover { background: var(--surface-container); }

/* 重新生成按钮：仅在自定义内容生成失败时显示 */
.regenerate-btn {
  padding: 4px 12px;
  border: none;
  border-radius: 16px;
  background: #FFF3E0;
  color: #E65100;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}
.regenerate-btn:hover:not(:disabled) { background: #FFE0B2; }
.regenerate-btn:disabled { opacity: 0.6; cursor: wait; }

/* 生成失败提示条 */
.gen-failed-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  margin-bottom: 12px;
  background: #FFEBEE;
  border-left: 3px solid #C62828;
  border-radius: 6px;
  font-size: 13px;
  color: #C62828;
}
.gen-failed-icon { font-size: 16px; }

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

/* 朗读评测 */
.eval-section {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--surface-container);
}
.eval-trigger {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  cursor: pointer;
  border-radius: var(--radius-sm);
  background: var(--surface-container);
  transition: background 0.2s;
}
.eval-trigger:hover {
  background: var(--primary-container);
}
.eval-icon { font-size: 20px; }
.eval-text { font-size: 14px; font-weight: 500; }
.eval-recording {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 16px;
  color: #f44336;
  background: #ffebee;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background 0.2s;
}
.eval-recording:hover {
  background: #ffcdd2;
}
.recording-pulse {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #f44336;
  animation: pulse 1.5s infinite;
}
.eval-hint {
  font-size: 12px;
  color: #666;
}
.eval-result {
  padding: 12px;
}
.eval-scores-row {
  display: flex;
  justify-content: space-around;
  margin-bottom: 12px;
}
.eval-score {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}
.eval-score-num {
  font-size: 24px;
  font-weight: 700;
}
.eval-score-label {
  font-size: 11px;
  color: var(--on-surface-variant);
}
.score-excellent { color: #4caf50; }
.score-good { color: #8bc34a; }
.score-ok { color: #ffc107; }
.score-fair { color: #ff9800; }
.score-poor { color: #f44336; }
.eval-suggestion {
  margin-bottom: 12px;
  padding: 10px;
  background: var(--surface-container);
  border-radius: var(--radius-sm);
  font-size: 13px;
  color: var(--on-surface-variant);
  text-align: center;
}
</style>
