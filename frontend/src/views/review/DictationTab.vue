<template>
  <div>
    <!-- 默写历史 -->
    <div class="section" v-if="history.length">
      <h3 class="section-title">📝 近期默写记录</h3>
      <div class="card history-card">
        <div v-for="h in history" :key="h.dictation_id" class="history-item" @click="startDictationById(h.content_id)">
          <div class="history-left">
            <span class="history-date">{{ h.created_at?.slice(5, 10) }}</span>
            <span class="history-title" v-if="getContentTitle(h.content_id)">{{ getContentTitle(h.content_id) }}</span>
          </div>
          <div class="history-right">
            <span :style="{ color: getAccuracyColor(h.accuracy_rate) }">{{ h.accuracy_rate.toFixed(0) }}%</span>
            <span style="color:var(--success)">+{{ h.earned_points }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 今日学习内容 -->
    <div class="section">
      <div class="section-header-row">
        <h3 class="section-title">📚 今日学习 <span class="section-hint">（{{ visibleContents.length }} 条）</span></h3>
        <button class="filter-btn" :class="{ active: learnedOnly }" @click="learnedOnly = !learnedOnly">
          {{ learnedOnly ? '✅ 已学' : '☑️ 已学筛选' }}
        </button>
      </div>
      <div v-if="todayContents.length === 0" class="empty-state">
        <div class="icon">📝</div>
        <p>暂无学习内容</p>
      </div>
      <div v-else class="content-list">
        <div v-for="item in visibleContents" :key="item.id" class="card content-item">
          <div class="content-left">
            <div class="content-title">{{ item.title }}</div>
            <div class="content-meta">
              <span>{{ item.content_date }}</span>
              <span v-if="item.words?.length" style="margin-left:8px;font-size:11px;color:var(--primary)">重点词汇 {{ item.words.length }} 个</span>
            </div>
          </div>
          <div class="content-actions">
            <button class="btn btn-sm btn-outline" @click="startDictation(item)">默写全文</button>
            <button v-if="item.words?.length" class="btn btn-sm btn-primary" @click="startWordDictation(item)">默写词汇</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 默写练习区 -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="dictatingContent" class="modal-overlay" @click.self="dictatingContent = null">
          <div class="dictation-sheet">
            <div class="sheet-header">
              <span class="tag tag-primary">默写练习</span>
              <button class="close-btn" @click="dictatingContent = null">✕</button>
            </div>

            <div class="card" style="margin:12px 16px">
              <h4 style="margin-bottom:8px;color:var(--on-surface-variant)">中文翻译提示</h4>
              <p style="line-height:1.6">{{ dictatingContent.translation || '暂无翻译' }}</p>
            </div>

            <Transition name="slide-up">
              <div v-if="showOriginal" class="card" style="margin:0 16px;background:var(--primary-container)">
                <h4 style="margin-bottom:8px;color:var(--on-primary-container)">英文原文</h4>
                <p style="line-height:1.8;font-size:15px">{{ dictatingContent.article }}</p>
              </div>
            </Transition>

            <div style="padding:8px 16px">
              <button class="btn btn-sm btn-outline" @click="showOriginal = !showOriginal" style="margin-bottom:8px">
                {{ showOriginal ? '🙈 隐藏原文' : '👁️ 显示原文' }}
              </button>
            </div>

            <div class="card" style="margin:0 16px">
              <textarea v-model="userInput" rows="8" placeholder="在这里输入你默写的英文内容..." class="dictation-input"></textarea>
            </div>

            <div style="padding:12px 16px;display:flex;gap:10px">
              <button class="btn btn-primary btn-block" @click="handleSubmit" :disabled="submitting || !userInput.trim()">
                {{ submitting ? 'AI 批改中...' : '提交批改' }}
              </button>
              <button class="btn btn-outline" @click="userInput = ''">清空</button>
            </div>

            <!-- 批改结果 -->
            <div v-if="result" class="card result-card" style="margin:0 16px 16px">
              <div class="score-area">
                <div class="score" :class="{ green: result.feedback.score >= 80, orange: result.feedback.score >= 60, red: result.feedback.score < 60 }">
                  {{ result.feedback.score }}
                </div>
                <div class="score-meta">
                  <div>准确率 {{ result.accuracy_rate.toFixed(0) }}%</div>
                  <div style="color:var(--success)">+{{ result.earned_points }} 积分</div>
                  <div style="color:var(--primary)">S{{ result.review_stage }} · {{ result.next_review_at?.slice(5, 10) || '-' }}</div>
                </div>
              </div>

              <div class="feedback-section" v-if="result.feedback.summary">
                <h4>AI 总评</h4>
                <p>{{ result.feedback.summary }}</p>
              </div>

              <div v-if="result.feedback.diffs?.length" class="feedback-section">
                <h4>差异分析</h4>
                <div v-for="(d, i) in result.feedback.diffs" :key="i" class="diff-item" :class="d.type">
                  <span class="diff-type">{{ d.type === 'missing' ? '遗漏' : d.type === 'wrong' ? '错误' : '多余' }}</span>
                  <span>应为 <strong>{{ d.expected }}</strong></span>
                  <span v-if="d.type !== 'missing'">你写 <strong>{{ d.actual }}</strong></span>
                </div>
              </div>

              <div v-if="result.feedback.suggestions?.length" class="feedback-section">
                <h4>改进建议</h4>
                <ul>
                  <li v-for="(s, i) in result.feedback.suggestions" :key="i">{{ s }}</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- 词汇默写弹窗 -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="wordDictationContent" class="modal-overlay" @click.self="wordDictationContent = null">
          <div class="dictation-sheet">
            <div class="sheet-header">
              <span class="tag tag-primary">词汇默写</span>
              <span class="word-progress">{{ wordDictationIdx + 1 }} / {{ wordDictationWords.length }}</span>
              <button class="close-btn" @click="wordDictationContent = null">✕</button>
            </div>

            <div class="card" style="margin:12px 16px">
              <div class="word-hint-label">中文释义</div>
              <div class="word-hint-meaning">{{ currentWordMeaning }}</div>
            </div>

            <div class="card" style="margin:0 16px">
              <input v-model="wordInput" type="text" placeholder="输入英文单词..." class="word-input"
                @keyup.enter="showWordResult ? nextWord() : handleSubmitWord()" />
            </div>

            <div style="padding:12px 16px;display:flex;gap:10px">
              <button v-if="!showWordResult" class="btn btn-primary btn-block" @click="handleSubmitWord"
                :disabled="!wordInput.trim()">
                确认
              </button>
              <button v-if="!showWordResult" class="btn btn-outline" @click="showWordResult = true; wordResultCorrect = false">
                不会，看答案
              </button>
              <button v-if="showWordResult" class="btn btn-primary btn-block" @click="nextWord">
                {{ wordDictationIdx < wordDictationWords.length - 1 ? '下一个' : '完成' }}
              </button>
            </div>

            <Transition name="slide-up">
              <div v-if="showWordResult" class="card word-result-card" style="margin:0 16px 16px">
                <div class="word-result-status" :class="{ correct: wordResultCorrect, wrong: !wordResultCorrect }">
                  {{ wordResultCorrect ? '✅ 正确' : '❌ 错误' }}
                </div>
                <div v-if="!wordResultCorrect" class="word-result-correct">
                  正确答案：<strong>{{ currentWord }}</strong>
                </div>
                <div class="word-result-usage" v-if="currentWordUsage">
                  用法：{{ currentWordUsage }}
                </div>
              </div>
            </Transition>

            <div v-if="wordDictationDone" class="card word-done-card" style="margin:0 16px 16px">
              <div class="word-done-title">🎉 默写完成</div>
              <div class="word-done-stats">
                <div class="word-stat">
                  <span class="word-stat-num" style="color:var(--success)">{{ wordCorrectCount }}</span>
                  <span class="word-stat-label">正确</span>
                </div>
                <div class="word-stat">
                  <span class="word-stat-num" style="color:var(--error)">{{ wordDictationWords.length - wordCorrectCount }}</span>
                  <span class="word-stat-label">错误</span>
                </div>
                <div class="word-stat">
                  <span class="word-stat-num" style="color:var(--primary)">{{ Math.round(wordCorrectCount / wordDictationWords.length * 100) }}%</span>
                  <span class="word-stat-label">正确率</span>
                </div>
              </div>
              <button class="btn btn-primary btn-block" @click="wordDictationContent = null">返回</button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { dailyApi, dictationApi } from '@/api'
import { useAuthStore } from '@/stores'
import type { LearningContent, DictationResult, DictationHistory } from '@/types'

const auth = useAuthStore()

const todayContents = ref<LearningContent[]>([])
const allContents = ref<LearningContent[]>([])
const history = ref<DictationHistory[]>([])
const dictatingContent = ref<LearningContent | null>(null)
const showOriginal = ref(false)
const userInput = ref('')
const submitting = ref(false)
const result = ref<DictationResult | null>(null)

const learnedOnly = ref(false)
const learnedIds = ref(new Set<number>())

const wordDictationContent = ref<LearningContent | null>(null)
const wordDictationIdx = ref(0)
const wordInput = ref('')
const showWordResult = ref(false)
const wordResultCorrect = ref(false)
const wordDictationDone = ref(false)
const wordCorrectCount = ref(0)

const wordDictationWords = computed(() => wordDictationContent.value?.words || [])
const currentWord = computed(() => wordDictationWords.value[wordDictationIdx.value]?.word || '')
const currentWordMeaning = computed(() => wordDictationWords.value[wordDictationIdx.value]?.meaning || '')
const currentWordUsage = computed(() => wordDictationWords.value[wordDictationIdx.value]?.usage || '')

const visibleContents = computed(() => {
  if (!learnedOnly.value) return todayContents.value
  return todayContents.value.filter(c => learnedIds.value.has(c.id))
})

function getContentTitle(contentId?: number | null): string {
  if (!contentId) return ''
  const todayItem = todayContents.value.find(c => c.id === contentId)
  if (todayItem) return todayItem.title
  const allItem = allContents.value.find(c => c.id === contentId)
  return allItem?.title || ''
}

function getAccuracyColor(acc: number): string {
  if (acc >= 80) return 'var(--success)'
  if (acc >= 60) return 'var(--warning)'
  return 'var(--error)'
}

function startDictation(item: LearningContent) {
  dictatingContent.value = item
  showOriginal.value = false
  userInput.value = ''
  result.value = null
}

function startDictationById(contentId?: number | null) {
  if (!contentId) return
  let item = todayContents.value.find(c => c.id === contentId)
  if (!item) item = allContents.value.find(c => c.id === contentId)
  if (item) startDictation(item)
}

async function handleSubmit() {
  if (!dictatingContent.value || !userInput.value.trim()) return
  submitting.value = true
  result.value = null
  try {
    const { data } = await dictationApi.submit(auth.currentUserId, dictatingContent.value.id, userInput.value)
    result.value = data
    const histRes = await dictationApi.getHistory(auth.currentUserId)
    history.value = histRes.data?.slice(0, 20) || []
  } catch { /* ignore */ }
  submitting.value = false
}

function startWordDictation(item: LearningContent) {
  wordDictationContent.value = item
  wordDictationIdx.value = 0
  wordInput.value = ''
  showWordResult.value = false
  wordResultCorrect.value = false
  wordDictationDone.value = false
  wordCorrectCount.value = 0
}

function handleSubmitWord() {
  if (!wordInput.value.trim()) return
  const input = wordInput.value.trim().toLowerCase()
  const correct = currentWord.value.toLowerCase()
  wordResultCorrect.value = input === correct
  if (wordResultCorrect.value) wordCorrectCount.value++
  showWordResult.value = true
}

function nextWord() {
  if (wordDictationIdx.value < wordDictationWords.value.length - 1) {
    wordDictationIdx.value++
    wordInput.value = ''
    showWordResult.value = false
    wordResultCorrect.value = false
  } else {
    wordDictationDone.value = true
  }
}

onMounted(async () => {
  try {
    const [todayRes, histRes, allRes, learnedRes] = await Promise.all([
      dailyApi.getTodayList(auth.currentUserId),
      dictationApi.getHistory(auth.currentUserId).catch(() => ({ data: [] })),
      dailyApi.getList(100).catch(() => ({ data: [] })),
      dailyApi.getLearnedIds(auth.currentUserId).catch(() => ({ data: { content_ids: [] } })),
    ])
    todayContents.value = todayRes.data.contents || []
    allContents.value = allRes.data || []
    history.value = histRes.data?.slice(0, 20) || []
    learnedIds.value = new Set(learnedRes.data.content_ids || [])
  } catch { /* ignore */ }
})
</script>

<style scoped>
.section { padding: 0 16px; margin-bottom: 16px; }
.section-title { font-size: 15px; font-weight: 700; margin-bottom: 10px; }
.section-header-row { display: flex; justify-content: space-between; align-items: center; }
.filter-btn {
  padding: 4px 12px; border-radius: 16px; font-size: 12px;
  border: 1.5px solid var(--outline-variant); background: var(--surface);
  color: var(--on-surface-variant); cursor: pointer; transition: all 0.2s;
}
.filter-btn.active { background: var(--primary); color: white; border-color: var(--primary); }
.section-hint { font-size: 12px; font-weight: 400; color: var(--on-surface-variant); }

.content-list { display: flex; flex-direction: column; gap: 6px; }
.content-item {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 14px; transition: background 0.15s;
}
.content-left { flex: 1; }
.content-title { font-weight: 600; font-size: 15px; }
.content-meta { font-size: 13px; color: var(--on-surface-variant); margin-top: 3px; }
.content-actions { display: flex; gap: 6px; flex-shrink: 0; }

.history-card { padding: 0 14px; }
.history-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 10px 0; border-bottom: 1px solid var(--surface-container);
  cursor: pointer; transition: background 0.15s;
}
.history-item:last-child { border-bottom: none; }
.history-item:hover { background: var(--surface-container); margin: 0 -14px; padding: 10px 14px; }
.history-left { display: flex; flex-direction: column; gap: 2px; }
.history-date { font-size: 13px; color: var(--on-surface-variant); }
.history-title { font-size: 14px; font-weight: 600; }
.history-right { display: flex; gap: 10px; font-size: 14px; font-weight: 600; }

.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.4);
  z-index: 500; display: flex; align-items: flex-end; justify-content: center;
}

.dictation-sheet {
  width: 100%; max-width: 480px; max-height: 90vh;
  background: white; border-radius: 20px 20px 0 0;
  overflow-y: auto; padding-bottom: env(safe-area-inset-bottom, 16px);
}

.sheet-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 16px 0;
}

.close-btn {
  width: 32px; height: 32px; border: none; background: var(--surface-container);
  border-radius: 50%; font-size: 16px; cursor: pointer; display: flex;
  align-items: center; justify-content: center;
}

.dictation-input {
  width: 100%; border: 1.5px solid var(--outline); border-radius: var(--radius-sm);
  padding: 12px; font-size: 15px; line-height: 1.6; resize: vertical;
  outline: none; font-family: inherit;
}
.dictation-input:focus { border-color: var(--primary); }

.word-progress { font-size: 13px; color: var(--on-surface-variant); }
.word-hint-label { font-size: 12px; color: var(--on-surface-variant); margin-bottom: 6px; }
.word-hint-meaning { font-size: 18px; font-weight: 600; line-height: 1.4; }
.word-input {
  width: 100%; border: 1.5px solid var(--outline); border-radius: var(--radius-sm);
  padding: 14px; font-size: 18px; outline: none; font-family: inherit;
  text-align: center; letter-spacing: 1px;
}
.word-input:focus { border-color: var(--primary); }
.word-result-card { text-align: center; padding: 16px; }
.word-result-status { font-size: 18px; font-weight: 700; margin-bottom: 8px; }
.word-result-status.correct { color: var(--success); }
.word-result-status.wrong { color: var(--error); }
.word-result-correct { font-size: 15px; margin-bottom: 8px; }
.word-result-usage { font-size: 13px; color: var(--on-surface-variant); margin-top: 8px; line-height: 1.5; }
.word-done-card { text-align: center; padding: 20px 16px; }
.word-done-title { font-size: 20px; font-weight: 700; margin-bottom: 16px; }
.word-done-stats { display: flex; justify-content: center; gap: 24px; margin-bottom: 16px; }
.word-stat { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.word-stat-num { font-size: 28px; font-weight: 800; }
.word-stat-label { font-size: 12px; color: var(--on-surface-variant); }

.result-card { border-left: 4px solid var(--primary); }
.score-area { display: flex; align-items: center; gap: 16px; margin-bottom: 16px; }
.score { font-size: 48px; font-weight: 800; }
.score.green { color: var(--success); }
.score.orange { color: var(--warning); }
.score.red { color: var(--error); }
.score-meta { font-size: 14px; line-height: 1.6; }

.feedback-section { margin-top: 16px; padding-top: 12px; border-top: 1px solid var(--surface-container-high); }
.feedback-section h4 { font-size: 14px; color: var(--on-surface-variant); margin-bottom: 8px; }

.diff-item { padding: 6px 0; font-size: 14px; display: flex; gap: 8px; align-items: center; }
.diff-type { font-size: 12px; padding: 2px 8px; border-radius: 4px; font-weight: 600; }
.diff-item.missing .diff-type { background: #FFEBEE; color: var(--error); }
.diff-item.wrong .diff-type { background: #FFF3E0; color: var(--warning); }
.diff-item.extra .diff-type { background: #E3F2FD; color: #1976D2; }

.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.slide-up-enter-active, .slide-up-leave-active { transition: all 0.3s ease; }
.slide-up-enter-from, .slide-up-leave-to { opacity: 0; transform: translateY(10px); }
</style>
