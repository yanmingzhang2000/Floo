<template>
  <div>
    <!-- 未开始默写时显示的界面 -->
    <div v-if="!vocabDictationActive">
      <div class="section">
        <h3 class="section-title">📚 收藏词汇默写</h3>
        <p style="color:var(--on-surface-variant);font-size:14px;margin-bottom:16px">
          从你的收藏词汇中随机抽取，背单词咯！
        </p>

        <div v-if="favoriteWords.length === 0" class="empty-state">
          <div class="icon">📝</div>
          <p>暂无收藏词汇</p>
          <p style="font-size:13px;color:var(--on-surface-variant)">在学习页面点击单词即可收藏</p>
        </div>

        <div v-else>
          <div class="vocab-info-card card">
            <div class="vocab-info-row">
              <span class="vocab-info-label">收藏词汇数</span>
              <span class="vocab-info-value">{{ favoriteWords.length }}</span>
            </div>
            <div class="vocab-info-row">
              <span class="vocab-info-label">每次默写</span>
              <span class="vocab-info-value">
                <select v-model="vocabCount" class="vocab-select">
                  <option :value="5">5个</option>
                  <option :value="10">10个</option>
                  <option :value="20">20个</option>
                  <option :value="favoriteWords.length">全部</option>
                </select>
              </span>
            </div>
          </div>
          <button class="btn btn-primary btn-block" @click="startVocabDictation" style="margin-top:16px">
            开始默写
          </button>
        </div>
      </div>
    </div>

    <!-- 默写进行中 -->
    <div v-else>
      <!-- 进度条 -->
      <div class="vocab-progress">
        <div class="vocab-progress-bar" :style="{ width: `${(vocabIdx + 1) / vocabWords.length * 100}%` }"></div>
      </div>
      <div class="vocab-progress-text">{{ vocabIdx + 1 }} / {{ vocabWords.length }}</div>

      <!-- 中文提示 -->
      <div class="card vocab-hint-card">
        <div class="vocab-hint-label">中文释义</div>
        <div class="vocab-hint-meaning">{{ vocabCurrentWord?.meaning || '' }}</div>
      </div>

      <!-- 输入框 -->
      <div class="card vocab-input-card">
        <input
          v-model="vocabInput"
          type="text"
          placeholder="输入英文单词..."
          class="vocab-input"
          @keyup.enter="vocabShowResult ? nextVocabWord() : checkVocabWord()"
          autofocus
        />
      </div>

      <!-- 操作按钮 -->
      <div class="vocab-actions">
        <button v-if="!vocabShowResult" class="btn btn-primary btn-block" @click="checkVocabWord" :disabled="!vocabInput.trim()">
          确认
        </button>
        <button v-if="!vocabShowResult" class="btn btn-outline" @click="showVocabAnswer">
          不会，看答案
        </button>
        <button v-if="vocabShowResult" class="btn btn-primary btn-block" @click="nextVocabWord">
          {{ vocabIdx < vocabWords.length - 1 ? '下一个' : '查看结果' }}
        </button>
      </div>

      <!-- 结果展示 -->
      <Transition name="slide-up">
        <div v-if="vocabShowResult" class="card vocab-result-card">
          <div class="vocab-result-status" :class="{ correct: vocabIsCorrect, wrong: !vocabIsCorrect }">
            {{ vocabIsCorrect ? '✅ 正确' : '❌ 错误' }}
          </div>
          <div v-if="!vocabIsCorrect" class="vocab-result-correct">
            正确答案：<strong>{{ vocabCurrentWord?.word }}</strong>
          </div>
        </div>
      </Transition>

      <!-- 完成统计 -->
      <div v-if="vocabDone" class="card vocab-done-card">
        <div class="vocab-done-title">🎉 默写完成</div>
        <div class="vocab-done-stats">
          <div class="vocab-stat">
            <span class="vocab-stat-num" style="color:var(--success)">{{ vocabCorrectCount }}</span>
            <span class="vocab-stat-label">正确</span>
          </div>
          <div class="vocab-stat">
            <span class="vocab-stat-num" style="color:var(--error)">{{ vocabWords.length - vocabCorrectCount }}</span>
            <span class="vocab-stat-label">错误</span>
          </div>
          <div class="vocab-stat">
            <span class="vocab-stat-num" style="color:var(--primary)">{{ Math.round(vocabCorrectCount / vocabWords.length * 100) }}%</span>
            <span class="vocab-stat-label">正确率</span>
          </div>
        </div>
        <button class="btn btn-primary btn-block" @click="resetVocabDictation">返回</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { favoritesApi } from '@/api'
import { useAuthStore } from '@/stores'

const auth = useAuthStore()

const favoriteWords = ref<{ word: string; phonetic?: string; meaning?: string }[]>([])
const vocabDictationActive = ref(false)
const vocabWords = ref<{ word: string; phonetic?: string; meaning?: string }[]>([])
const vocabIdx = ref(0)
const vocabInput = ref('')
const vocabShowResult = ref(false)
const vocabIsCorrect = ref(false)
const vocabDone = ref(false)
const vocabCorrectCount = ref(0)
const vocabCount = ref(10)

const vocabCurrentWord = computed(() => vocabWords.value[vocabIdx.value] || null)

function shuffleArray<T>(array: T[]): T[] {
  const shuffled = [...array]
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
  }
  return shuffled
}

function isInflectedForm(word: string): boolean {
  const lower = word.toLowerCase()
  const inflectionPatterns = [
    /ing$/i, /ed$/i, /s$/i, /es$/i, /ly$/i, /tion$/i, /sion$/i,
    /ment$/i, /ness$/i, /ful$/i, /less$/i, /er$/i, /est$/i, /able$/i, /ible$/i,
  ]
  if (lower.length <= 3) return false
  for (const pattern of inflectionPatterns) {
    if (pattern.test(lower)) {
      const root = lower.replace(/(?:ing|ed|s|es|ly|tion|sion|ment|ness|ful|less|er|est|able|ible)$/, '')
      if (root.length >= 2) return true
    }
  }
  return false
}

function filterToBaseForms(words: { word: string; phonetic?: string; meaning?: string }[]): { word: string; phonetic?: string; meaning?: string }[] {
  const seen = new Set<string>()
  const result: { word: string; phonetic?: string; meaning?: string }[] = []
  for (const w of words) {
    const lower = w.word.toLowerCase().trim()
    if (!lower) continue
    if (isInflectedForm(lower)) {
      const baseForm = lower
        .replace(/ing$/, '').replace(/ed$/, '').replace(/s$/, '').replace(/es$/, '')
        .replace(/ly$/, '').replace(/tion$/, '').replace(/ment$/, '').replace(/ness$/, '')
        .replace(/ful$/, '').replace(/less$/, '').replace(/er$/, '').replace(/est$/, '')
        .replace(/able$/, '').replace(/ible$/, '')
      if (baseForm && !seen.has(baseForm) && baseForm.length >= 2) {
        seen.add(baseForm)
        result.push({ ...w, word: baseForm })
      }
      continue
    }
    if (!seen.has(lower)) {
      seen.add(lower)
      result.push(w)
    }
  }
  return result
}

async function loadFavorites() {
  try {
    const { data } = await favoritesApi.list(auth.currentUserId, 200)
    const allWords = (data || []).map((f: any) => ({
      word: f.word,
      phonetic: f.phonetic || '',
      meaning: f.meaning || '',
    }))
    favoriteWords.value = filterToBaseForms(allWords)
  } catch { favoriteWords.value = [] }
}

function startVocabDictation() {
  if (favoriteWords.value.length === 0) return
  const shuffled = shuffleArray(favoriteWords.value)
  vocabWords.value = shuffled.slice(0, Math.min(vocabCount.value, shuffled.length))
  vocabIdx.value = 0
  vocabInput.value = ''
  vocabShowResult.value = false
  vocabIsCorrect.value = false
  vocabDone.value = false
  vocabCorrectCount.value = 0
  vocabDictationActive.value = true
}

function checkVocabWord() {
  if (!vocabCurrentWord.value || !vocabInput.value.trim()) return
  const input = vocabInput.value.trim().toLowerCase()
  const correct = vocabCurrentWord.value.word.toLowerCase()
  vocabIsCorrect.value = input === correct
  if (vocabIsCorrect.value) vocabCorrectCount.value++
  vocabShowResult.value = true
}

function showVocabAnswer() {
  vocabIsCorrect.value = false
  vocabShowResult.value = true
}

function nextVocabWord() {
  if (vocabIdx.value < vocabWords.value.length - 1) {
    vocabIdx.value++
    vocabInput.value = ''
    vocabShowResult.value = false
    vocabIsCorrect.value = false
  } else {
    vocabDone.value = true
  }
}

function resetVocabDictation() {
  vocabDictationActive.value = false
  vocabWords.value = []
  vocabIdx.value = 0
  vocabInput.value = ''
  vocabShowResult.value = false
  vocabIsCorrect.value = false
  vocabDone.value = false
  vocabCorrectCount.value = 0
}

onMounted(loadFavorites)
</script>

<style scoped>
.section { padding: 0 16px; margin-bottom: 16px; }
.section-title { font-size: 15px; font-weight: 700; margin-bottom: 10px; }

.vocab-info-card { padding: 16px; }
.vocab-info-row { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; }
.vocab-info-row + .vocab-info-row { border-top: 1px solid var(--surface-container); }
.vocab-info-label { font-size: 14px; color: var(--on-surface-variant); }
.vocab-info-value { font-size: 16px; font-weight: 600; }
.vocab-select {
  padding: 6px 12px; border: 1px solid var(--outline); border-radius: var(--radius-sm);
  font-size: 14px; background: white; cursor: pointer;
}

.vocab-progress {
  height: 6px; background: var(--surface-container); border-radius: 3px;
  margin: 16px 16px 0; overflow: hidden;
}
.vocab-progress-bar {
  height: 100%; background: var(--primary); border-radius: 3px;
  transition: width 0.3s ease;
}
.vocab-progress-text {
  text-align: center; font-size: 13px; color: var(--on-surface-variant);
  margin-top: 8px;
}

.vocab-hint-card { margin: 16px; text-align: center; }
.vocab-hint-label { font-size: 12px; color: var(--on-surface-variant); margin-bottom: 8px; }
.vocab-hint-meaning { font-size: 22px; font-weight: 600; line-height: 1.4; }

.vocab-input-card { margin: 0 16px; }
.vocab-input {
  width: 100%; border: 1.5px solid var(--outline); border-radius: var(--radius-sm);
  padding: 14px; font-size: 18px; outline: none; font-family: inherit;
  text-align: center; letter-spacing: 1px;
}
.vocab-input:focus { border-color: var(--primary); }
.vocab-input:disabled { background: var(--surface-container); }

.vocab-actions { padding: 12px 16px; display: flex; flex-direction: column; gap: 10px; }

.vocab-result-card { margin: 0 16px 16px; text-align: center; padding: 16px; }
.vocab-result-status { font-size: 18px; font-weight: 700; margin-bottom: 8px; }
.vocab-result-status.correct { color: var(--success); }
.vocab-result-status.wrong { color: var(--error); }
.vocab-result-correct { font-size: 15px; }

.vocab-done-card { margin: 0 16px 16px; text-align: center; padding: 20px; }
.vocab-done-title { font-size: 20px; font-weight: 700; margin-bottom: 16px; }
.vocab-done-stats { display: flex; justify-content: center; gap: 24px; margin-bottom: 16px; }
.vocab-stat { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.vocab-stat-num { font-size: 28px; font-weight: 800; }
.vocab-stat-label { font-size: 12px; color: var(--on-surface-variant); }

.slide-up-enter-active, .slide-up-leave-active { transition: all 0.3s ease; }
.slide-up-enter-from, .slide-up-leave-to { opacity: 0; transform: translateY(10px); }
</style>
