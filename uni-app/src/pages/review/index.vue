<template>
  <view class="page-container">
    <!-- 顶栏统一青绿色 -->
    <view class="nav-bar-themed">
      <text class="nav-bar-title">复习</text>
    </view>

    <!-- 二级标签：极简细横线 -->
    <view class="underline-tabs">
      <view class="underline-tab" :class="{ active: activeTab === 'dictation' }" @tap="switchTab('dictation')">
        <text>默写</text>
      </view>
      <view class="underline-tab" :class="{ active: activeTab === 'vocab' }" @tap="switchTab('vocab')">
        <text>背单词</text>
      </view>
    </view>

    <view v-if="loading" class="loading">
      <view class="spinner"></view>
    </view>

    <template v-else>
      <!-- ===== 默写 ===== -->
      <view v-show="activeTab === 'dictation'">
        <view class="section">
          <text class="section-title">默写记录</text>
          <view v-if="historyLoadError" class="empty-state" @tap="loadData">
            <text class="icon">⚠️</text>
            <text class="empty-text">加载失败</text>
            <text class="empty-hint">点此重试</text>
          </view>
          <view v-else-if="historyList.length === 0" class="empty-state">
            <text class="icon">📜</text>
            <text class="empty-text">暂无默写记录</text>
            <text class="empty-hint">在文章阅读页点击「默写」开始练习</text>
          </view>
          <view v-else class="history-list">
            <view v-for="rec in historyList" :key="rec.dictation_id" class="history-item" @tap="goDictationDetail(rec.dictation_id)">
              <view class="history-left">
                <text class="history-date">{{ formatDate(rec.created_at) }}</text>
                <text class="history-title ellipsis">{{ rec.content_title || '默写练习' }}</text>
              </view>
              <view class="history-right">
                <text class="history-accuracy">{{ rec.accuracy_rate.toFixed(0) }}%</text>
              </view>
            </view>
          </view>
        </view>

        <view class="section">
          <view class="section-title-row" @tap="showTodayContent = !showTodayContent">
            <text class="section-title">今日学习内容</text>
            <text class="section-toggle">{{ showTodayContent ? '收起' : '展开' }}</text>
          </view>
          <view v-if="showTodayContent">
            <view v-if="todayContents.length === 0" class="empty-state">
              <text class="icon">📝</text>
              <text class="empty-text">暂无内容</text>
            </view>
            <view v-else class="content-list">
              <view v-for="item in todayContents" :key="item.id" class="content-item">
                <view class="content-left">
                  <text class="content-title">{{ item.title }}</text>
                  <text class="content-meta">{{ item.content_date }}</text>
                </view>
                <text class="content-action" @tap.stop="startDictation(item)">默写</text>
              </view>
            </view>
          </view>
        </view>
      </view>

      <!-- ===== 背单词 ===== -->
      <view v-show="activeTab === 'vocab'">
        <!-- 开始前 -->
        <view v-if="!vbActive" class="section">
          <text class="section-title">背单词</text>
          <view v-if="vbDueWords.length === 0" class="empty-state">
            <text class="icon">📖</text>
            <text class="empty-text">暂无待复习单词</text>
            <text class="empty-hint">收藏更多单词后再来复习</text>
          </view>
          <view v-else>
            <view class="vocab-start-card">
              <view class="vocab-info">
                <text class="vocab-info-label">待复习单词</text>
                <text class="vocab-info-count">{{ vbDueWords.length }}</text>
              </view>
              <text class="vocab-start-action" @tap="startVocab">开始背词</text>
            </view>
            <view class="vb-mode-hints">
              <text class="vb-mode-text">选义：看英文选中文 · 默写：看中文拼英文</text>
            </view>
          </view>
        </view>

        <!-- 进行中 -->
        <view v-else class="vb-active">
          <view class="vocab-progress-bar-bg">
            <view class="vocab-progress-bar-fill" :style="{ width: ((vbIdx + 1) / vbWords.length * 100) + '%' }"></view>
          </view>
          <view class="vb-progress-row">
            <text class="vocab-progress-text">{{ vbIdx + 1 }} / {{ vbWords.length }}</text>
            <text class="vb-mode-tag">{{ vbCurrentMode === 'choice' ? '选义' : '默写' }}</text>
          </view>

          <!-- ====== 选义模式 ====== -->
          <template v-if="vbCurrentMode === 'choice'">
            <view class="wc-word-card">
              <text class="wc-word-text">{{ vbCurrentWord?.word }}</text>
              <text v-if="vbCurrentWord?.phonetic" class="wc-word-phonetic">{{ vbCurrentWord.phonetic }}</text>
            </view>
            <view class="wc-options">
              <view
                v-for="(opt, i) in vbChoiceOptions"
                :key="i"
                class="wc-option"
                :class="{
                  correct: vbShowResult && opt === vbCurrentWord?.meaning,
                  wrong: vbShowResult && vbSelectedIdx === i && opt !== vbCurrentWord?.meaning,
                  selected: !vbShowResult && vbSelectedIdx === i,
                }"
                @tap="selectVbChoice(i)"
              >
                <text class="wc-option-label">{{ ['A', 'B', 'C', 'D'][i] }}</text>
                <text class="wc-option-text">{{ opt }}</text>
              </view>
            </view>
          </template>

          <!-- ====== 默写模式 ====== -->
          <template v-else>
            <view class="vocab-hint-card">
              <text class="vocab-hint-label">中文释义</text>
              <text class="vocab-hint-meaning">{{ vbCurrentWord?.meaning || '' }}</text>
            </view>
            <view class="vocab-input-card">
              <input v-model="vbDictInput" type="text" placeholder="输入英文单词..." class="vocab-input" @confirm="vbShowResult ? nextVbWord() : checkVbDict()" />
            </view>
          </template>

          <!-- 操作按钮 -->
          <view class="vb-actions">
            <template v-if="vbCurrentMode === 'choice'">
              <view v-if="vbShowResult" class="vb-result-line" :class="vbIsCorrect ? 'vb-correct' : 'vb-wrong'">
                <text>{{ vbIsCorrect ? '正确' : '错误，正确答案：' + vbCurrentWord?.meaning }}</text>
              </view>
              <text v-if="!vbShowResult" class="vb-skip-action" @tap="showVbAnswer">不会，看答案</text>
              <text v-if="vbShowResult" class="vb-next-action" @tap="nextVbWord">{{ vbIdx < vbWords.length - 1 ? '下一个' : '查看结果' }}</text>
            </template>
            <template v-else>
              <text v-if="!vbShowResult" class="vb-next-action" :class="{ disabled: !vbDictInput.trim() }" @tap="checkVbDict">确认</text>
              <text v-if="!vbShowResult" class="vb-skip-action" @tap="showVbAnswer">不会，看答案</text>
              <view v-if="vbShowResult" class="vb-result-line" :class="vbIsCorrect ? 'vb-correct' : 'vb-wrong'">
                <text>{{ vbIsCorrect ? '正确' : '错误，正确答案：' + vbCurrentWord?.word }}</text>
              </view>
              <text v-if="vbShowResult" class="vb-next-action" @tap="nextVbWord">{{ vbIdx < vbWords.length - 1 ? '下一个' : '查看结果' }}</text>
            </template>
          </view>

          <!-- 完成 -->
          <view v-if="vbDone" class="vocab-done-card">
            <text class="vocab-done-title">背单词完成</text>
            <view class="vocab-done-stats">
              <view class="vocab-done-stat">
                <text class="vocab-done-stat-num">{{ vbCorrectCount }}</text>
                <text class="vocab-done-stat-label">正确</text>
              </view>
              <view class="vocab-done-stat">
                <text class="vocab-done-stat-num wrong">{{ vbWords.length - vbCorrectCount }}</text>
                <text class="vocab-done-stat-label">错误</text>
              </view>
            </view>
            <text class="vb-next-action" @tap="resetVb">返回</text>
          </view>
        </view>
      </view>
    </template>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { dailyApi, dictationApi, wordReviewApi } from '@/api'
import { useAuthStore } from '@/stores'
import { navTo } from '@/utils/router'
import type { LearningContent, DictationHistory } from '@/types'

const auth = useAuthStore()
const loading = ref(true)
const activeTab = ref<'dictation' | 'vocab'>('dictation')

// 默写
const todayContents = ref<LearningContent[]>([])
const historyList = ref<DictationHistory[]>([])
const historyLoadError = ref(false)
const showTodayContent = ref(false)

// 背单词
const vbDueWords = ref<any[]>([])
const vbDistractors = ref<any[]>([])
const vbActive = ref(false)
const vbWords = ref<any[]>([])
const vbIdx = ref(0)
const vbCurrentMode = ref<'choice' | 'dictation'>('choice')
const vbChoiceOptions = ref<string[]>([])
const vbSelectedIdx = ref(-1)
const vbDictInput = ref('')
const vbShowResult = ref(false)
const vbIsCorrect = ref(false)
const vbDone = ref(false)
const vbCorrectCount = ref(0)

const vbCurrentWord = computed(() => vbWords.value[vbIdx.value] || null)

const autoStartVocab = ref(false)

onLoad((options) => {
  if (options?.tab === 'dictation') activeTab.value = 'dictation'
  if (options?.tab === 'vocab') activeTab.value = 'vocab'
  // 从笔记页「开始背词」跳转时带 autostart=1，数据加载完后自动开始
  if (options?.autostart === '1') autoStartVocab.value = true
})

function switchTab(tab: typeof activeTab.value) {
  activeTab.value = tab
}

function goDictationDetail(dictationId: number) { navTo(`/pages/dictation-detail/index?id=${dictationId}`) }

function formatDate(dateStr: string) {
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

// ===== 默写 =====
function startDictation(item: LearningContent) {
  navTo(`/pages/dictation/index?id=${item.id}`)
}

// ===== 背单词 =====
async function loadVocabReview() {
  try {
    const { data } = await wordReviewApi.getDue(auth.currentUserId, 20)
    vbDueWords.value = data.words || []
    vbDistractors.value = data.distractors || []
  } catch {
    vbDueWords.value = []
    vbDistractors.value = []
  }
}

function shuffleArray<T>(array: T[]): T[] {
  const shuffled = [...array]
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
  }
  return shuffled
}

function pickMode(): 'choice' | 'dictation' {
  return Math.random() < 0.5 ? 'choice' : 'dictation'
}

function startVocab() {
  if (vbDueWords.value.length === 0) return
  const pool = shuffleArray(vbDueWords.value).slice(0, Math.min(15, vbDueWords.value.length))
  // 随机为每个词分配模式
  vbWords.value = pool.map(w => ({ ...w, _mode: pickMode() }))
  vbIdx.value = 0
  vbCurrentMode.value = vbWords.value[0]._mode
  vbSelectedIdx.value = -1
  vbDictInput.value = ''
  vbShowResult.value = false
  vbIsCorrect.value = false
  vbDone.value = false
  vbCorrectCount.value = 0
  vbActive.value = true
  generateVbOptions()
}

// 兜底干扰词：当用户自己的词库不够时补充，保证始终 4 个选项
const FALLBACK_DISTRACTORS = [
  'n. 城市', 'v. 走路', 'n. 太阳', 'v. 喜爱', 'adj. 大的',
  'n. 书本', 'v. 学习', 'n. 家庭', 'adj. 漂亮的', 'v. 运动',
  'n. 时间', 'v. 写作', 'n. 水果', 'adj. 快乐的', 'n. 动物',
  'v. 阅读', 'n. 音乐', 'adj. 聪明的', 'v. 思考', 'n. 食物',
  'n. 道路', 'v. 跑步', 'n. 花朵', 'adj. 温暖的', 'n. 故事',
  'v. 唱歌', 'n. 图片', 'adj. 重要的', 'v. 帮助', 'n. 电影',
  'n. 早晨', 'v. 休息', 'n. 眼睛', 'adj. 安静的', 'n. 椅子',
  'v. 等待', 'n. 月亮', 'adj. 新的', 'v. 站立', 'n. 电话',
  'n. 礼物', 'v. 微笑', 'n. 雨伞', 'adj. 高的', 'n. 窗户',
]

function generateVbOptions() {
  const current = vbCurrentWord.value
  if (!current) return
  const correct = current.meaning || ''

  // 1. 从用户自己的干扰项池取有效释义
  const pool = shuffleArray(vbDistractors.value.filter((d: any) => d.meaning && d.meaning.trim() && d.meaning.trim() !== correct))
  const distractorMeanings = pool.slice(0, 3).map((d: any) => d.meaning)

  // 2. 不够 3 个则从兜底词库补（排除与正确答案重复的）
  if (distractorMeanings.length < 3) {
    const fallbackPool = shuffleArray(FALLBACK_DISTRACTORS.filter(m => m !== correct && !distractorMeanings.includes(m)))
    while (distractorMeanings.length < 3 && fallbackPool.length > 0) {
      distractorMeanings.push(fallbackPool.pop()!)
    }
  }

  vbChoiceOptions.value = shuffleArray([correct, ...distractorMeanings])
}

// 选义
function selectVbChoice(idx: number) {
  if (vbShowResult.value) return
  vbSelectedIdx.value = idx
  const correct = vbCurrentWord.value?.meaning
  vbIsCorrect.value = vbChoiceOptions.value[idx] === correct
  vbShowResult.value = true
  if (vbIsCorrect.value) vbCorrectCount.value++
  wordReviewApi.submit(auth.currentUserId, vbCurrentWord.value.word, vbIsCorrect.value)
}

// 默写
function checkVbDict() {
  if (!vbCurrentWord.value || !vbDictInput.value.trim()) return
  vbIsCorrect.value = vbDictInput.value.trim().toLowerCase() === vbCurrentWord.value.word.toLowerCase()
  if (vbIsCorrect.value) vbCorrectCount.value++
  vbShowResult.value = true
  wordReviewApi.submit(auth.currentUserId, vbCurrentWord.value.word, vbIsCorrect.value, vbIsCorrect.value ? 100 : 0)
}

function showVbAnswer() {
  vbIsCorrect.value = false
  vbShowResult.value = true
  wordReviewApi.submit(auth.currentUserId, vbCurrentWord.value.word, false, 0)
}

function nextVbWord() {
  if (vbIdx.value < vbWords.value.length - 1) {
    vbIdx.value++
    vbCurrentMode.value = vbWords.value[vbIdx.value]._mode
    vbSelectedIdx.value = -1
    vbDictInput.value = ''
    vbShowResult.value = false
    vbIsCorrect.value = false
    if (vbCurrentMode.value === 'choice') generateVbOptions()
  } else {
    vbDone.value = true
  }
}

function resetVb() { vbActive.value = false }

// ===== 数据加载 =====
async function loadData() {
  loading.value = true

  // 并行加载所有独立的 API 请求
  const [
    todayListRes,
    listRes,
    historyRes,
    vocabRes
  ] = await Promise.allSettled([
    dailyApi.getTodayList(auth.currentUserId),
    dailyApi.getList(30),
    dictationApi.getHistory(auth.currentUserId, 50),
    wordReviewApi.getDue(auth.currentUserId, 20)
  ])

  // 处理今日内容
  if (todayListRes.status === 'fulfilled') {
    todayContents.value = todayListRes.value.data.contents || []
  }

  // 补充更多内容
  if (listRes.status === 'fulfilled') {
    const items = listRes.value.data
    if (Array.isArray(items)) {
      const ids = new Set(todayContents.value.map(c => c.id))
      for (const item of items) {
        if (!ids.has(item.id)) todayContents.value.push(item)
      }
    }
  }

  // 处理默写历史
  if (historyRes.status === 'fulfilled') {
    const res = historyRes.value
    if (res.statusCode >= 400) {
      historyLoadError.value = true
    } else if (Array.isArray(res.data)) {
      historyList.value = res.data
      historyLoadError.value = false
    }
  } else {
    historyLoadError.value = true
  }

  // 处理背单词数据
  if (vocabRes.status === 'fulfilled') {
    vbDueWords.value = vocabRes.value.data.words || []
    vbDistractors.value = vocabRes.value.data.distractors || []
  }

  loading.value = false

  // 从笔记页带 autostart 跳转时，数据就绪后自动进入背词练习
  if (autoStartVocab.value && vbDueWords.value.length > 0) {
    console.debug('[Review] autostart 触发，自动开始背词')
    autoStartVocab.value = false
    startVocab()
  }
}

onShow(loadData)
</script>

<style scoped>
/* ---- 顶栏统一青绿 ---- */
.nav-bar-themed {
  display: flex;
  align-items: flex-end;
  padding: calc(env(safe-area-inset-top, 44px) + 16rpx) 32rpx 24rpx;
  background: var(--primary, #5B9AA8);
}
.nav-bar-title {
  font-size: 36rpx;
  font-weight: 600;
  color: #fff;
  letter-spacing: 0.5rpx;
}

/* ---- 二级标签：极简细横线 ---- */
.underline-tabs {
  display: flex;
  background: #fff;
  border-bottom: 1rpx solid #e4eff2;
  padding: 0 8rpx;
}
.underline-tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20rpx 0;
  font-size: 28rpx;
  font-weight: 500;
  color: #b0b8c0;
  position: relative;
  gap: 8rpx;
}
.underline-tab.active {
  color: var(--primary);
  font-weight: 700;
}
.underline-tab.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 25%;
  right: 25%;
  height: 3rpx;
  border-radius: 2rpx;
  background: var(--primary);
}


/* ---- 通用分区 ---- */
.section { padding: 16rpx 20rpx 24rpx; }
.section-title {
  font-size: 28rpx;
  font-weight: 700;
  margin-bottom: 20rpx;
  display: block;
  color: var(--on-surface);
}
.section-title-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20rpx; }
.section-toggle { font-size: 24rpx; color: var(--primary); }

/* ---- 默写历史 ---- */
.history-list { display: flex; flex-direction: column; gap: 12rpx; }
.history-item {
  display: flex;
  align-items: center;
  padding: 20rpx 28rpx;
  background: #ffffff;
  box-shadow: 0 2rpx 12rpx rgba(91, 154, 168, 0.10);
  border-radius: 16rpx;
}
.history-left { flex: 1; display: flex; flex-direction: column; gap: 4rpx; min-width: 0; }
.history-right { display: flex; align-items: center; gap: 16rpx; flex-shrink: 0; }
.history-title { font-size: 26rpx; font-weight: 500; }
.history-date { font-size: 22rpx; color: var(--on-surface-variant); }
.history-accuracy { font-size: 28rpx; font-weight: 700; color: var(--primary); min-width: 72rpx; text-align: right; }

/* ---- 今日内容列表 ---- */
.content-list { display: flex; flex-direction: column; gap: 12rpx; }
.content-item {
  display: flex;
  align-items: center;
  gap: 20rpx;
  padding: 20rpx 28rpx;
  background: #ffffff;
  box-shadow: 0 2rpx 12rpx rgba(91, 154, 168, 0.10);
  border-radius: 16rpx;
}
.content-left { flex: 1; }
.content-title { font-weight: 600; font-size: 28rpx; display: block; }
.content-meta { font-size: 24rpx; color: var(--on-surface-variant); margin-top: 4rpx; display: block; }
.content-action { font-size: 26rpx; color: var(--primary); font-weight: 600; flex-shrink: 0; }

/* ---- 背单词开始卡 ---- */
.vocab-start-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 32rpx 28rpx;
  background: #ffffff;
  box-shadow: 0 2rpx 12rpx rgba(91, 154, 168, 0.10);
  border-radius: 20rpx;
}
.vocab-info { display: flex; flex-direction: column; gap: 4rpx; }
.vocab-info-label { font-size: 24rpx; color: var(--on-surface-variant); }
.vocab-info-count { font-size: 44rpx; font-weight: 800; color: var(--primary); }
.vocab-start-action {
  padding: 16rpx 32rpx;
  border: 2rpx solid var(--primary);
  border-radius: 40rpx;
  font-size: 26rpx;
  font-weight: 600;
  color: var(--primary);
}
.vb-mode-hints { margin-top: 20rpx; padding: 0 4rpx; }
.vb-mode-text { font-size: 24rpx; color: var(--on-surface-variant); }

/* ---- 进行中 ---- */
.vocab-progress-bar-bg { height: 6rpx; background: #e4eff2; border-radius: 3rpx; margin: 32rpx 20rpx 0; overflow: hidden; }
.vocab-progress-bar-fill { height: 100%; background: var(--primary); border-radius: 3rpx; transition: width 0.3s; }
.vb-progress-row { display: flex; justify-content: space-between; align-items: center; padding: 12rpx 20rpx 0; }
.vocab-progress-text { font-size: 24rpx; color: var(--on-surface-variant); }
.vb-mode-tag { font-size: 24rpx; color: var(--primary); font-weight: 600; }
.vb-actions { padding: 20rpx 20rpx 32rpx; display: flex; flex-direction: column; gap: 16rpx; align-items: center; }

/* 操作文字按钮 */
.vb-next-action {
  display: block;
  width: 100%;
  padding: 28rpx 0;
  text-align: center;
  font-size: 30rpx;
  font-weight: 700;
  color: var(--primary);
  border: 2rpx solid var(--primary);
  border-radius: 48rpx;
}
.vb-next-action.disabled { color: #b0b8c0; border-color: #d0d8dc; pointer-events: none; }
.vb-skip-action { font-size: 26rpx; color: #b0b8c0; }

.vb-result-line { text-align: center; font-size: 28rpx; font-weight: 600; padding: 12rpx 0; }
.vb-correct { color: var(--primary); }
.vb-wrong { color: #666; }

/* ---- 选义卡片 ---- */
.wc-word-card { text-align: center; padding: 48rpx 32rpx; margin: 16rpx 20rpx; background: #ffffff; box-shadow: 0 2rpx 12rpx rgba(91, 154, 168, 0.10); border-radius: 20rpx; }
.wc-word-text { font-size: 52rpx; font-weight: 800; display: block; color: var(--on-surface); }
.wc-word-phonetic { font-size: 26rpx; color: var(--on-surface-variant); display: block; margin-top: 12rpx; }
.wc-options { padding: 0 20rpx; display: flex; flex-direction: column; gap: 16rpx; }
.wc-option {
  display: flex; align-items: center; gap: 20rpx; padding: 28rpx 24rpx;
  border: 1rpx solid #e4eff2; border-radius: 16rpx;
  background: #ffffff; box-shadow: 0 2rpx 12rpx rgba(91, 154, 168, 0.10); transition: all 0.15s;
}
.wc-option.selected { border-color: var(--primary); background: rgba(91,154,168,0.06); }
.wc-option.correct { border-color: var(--primary); background: rgba(91,154,168,0.1); }
.wc-option.wrong { border-color: #ccc; background: #f8f8f8; }
.wc-option-label { font-size: 28rpx; font-weight: 700; color: var(--on-surface-variant); width: 48rpx; text-align: center; }
.wc-option-text { font-size: 28rpx; flex: 1; color: var(--on-surface); }

/* ---- 默写输入 ---- */
.vocab-hint-card { text-align: center; padding: 40rpx; margin: 0 20rpx 20rpx; background: #ffffff; box-shadow: 0 2rpx 12rpx rgba(91, 154, 168, 0.10); border-radius: 20rpx; }
.vocab-hint-label { font-size: 22rpx; color: var(--on-surface-variant); margin-bottom: 16rpx; display: block; }
.vocab-hint-meaning { font-size: 40rpx; font-weight: 600; display: block; color: var(--on-surface); }
.vocab-input-card { margin: 0 20rpx 24rpx; background: #ffffff; box-shadow: 0 2rpx 12rpx rgba(91, 154, 168, 0.10); border-radius: 20rpx; }
.vocab-input { width: 100%; border: none; border-bottom: 2rpx solid var(--outline); padding: 28rpx 16rpx; min-height: 88rpx; font-size: 36rpx; text-align: center; outline: none; color: var(--on-surface); background: transparent; line-height: 1.4; box-sizing: border-box; }
.vocab-input:focus { border-bottom-color: var(--primary); }

/* ---- 完成卡 ---- */
.vocab-done-card { text-align: center; padding: 40rpx 32rpx; margin: 0 20rpx 32rpx; background: #ffffff; box-shadow: 0 2rpx 12rpx rgba(91, 154, 168, 0.10); border-radius: 20rpx; }
.vocab-done-title { font-size: 32rpx; font-weight: 700; margin-bottom: 32rpx; display: block; color: var(--on-surface); }
.vocab-done-stats { display: flex; justify-content: center; gap: 64rpx; margin-bottom: 32rpx; }
.vocab-done-stat { display: flex; flex-direction: column; align-items: center; gap: 8rpx; }
.vocab-done-stat-num { font-size: 48rpx; font-weight: 800; color: var(--primary); }
.vocab-done-stat-num.wrong { color: #999; }
.vocab-done-stat-label { font-size: 22rpx; color: var(--on-surface-variant); }
</style>
