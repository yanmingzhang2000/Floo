<template>
  <view class="page-container">
    <view class="nav-bar">
      <view class="nav-left">
        <view class="nav-back" @tap="navBackSafe"><text>‹</text></view>
      </view>
      <text class="nav-title">文章详情</text>
      <view class="nav-right">
        <view class="nav-avatar">
          <text>{{ usernameInitial }}</text>
        </view>
      </view>
    </view>

    <view v-if="loading" class="loading">
      <view class="spinner"></view>
    </view>

    <view v-else-if="content" class="detail-wrap">
      <!-- 文章内容 -->
        <view class="card detail-card">
        <view class="detail-meta">
          <text v-if="!isBookChapter" class="tag tag-primary">{{ content.content_date }}</text>
          <text v-if="isBookChapter && bookContext?.series_name" class="tag tag-primary">{{ bookContext.series_name }}</text>
          <text class="tag tag-success">{{ content.difficulty_level }}</text>
        </view>
        <text class="detail-title">{{ content.title }}</text>

        <view class="learned-toggle" @tap="toggleLearned">
          <text class="learned-icon">{{ learnedIds.includes(content.id) ? '✅' : '☑️' }}</text>
          <text class="learned-text">{{ learnedIds.includes(content.id) ? '已学过' : '标记已学' }}</text>
        </view>

        <!-- 非书籍章节：一整块正文 -->
        <view v-if="!isBookChapter" class="article-body">
          <text
            v-for="(part, i) in articleParts"
            :key="i"
            :class="['word-span', part.isWord ? (part.isKey ? 'keyword' : 'clickable-word') : '']"
            @tap="part.isWord && handleWordTap(part.text)"
          >{{ part.text }}</text>
        </view>

        <!-- 书籍章节：按 segment 边界分组渲染，每段可单独默写 -->
        <template v-else>
          <view
            v-for="group in segmentGroups"
            :key="group.segment.segment_id"
            class="segment-group"
          >
            <view class="segment-header">
              <text class="segment-label">段 {{ group.segment.order_no + 1 }} · {{ group.segment.word_count }} 词</text>
              <view
                class="segment-dict-btn"
                :class="{ disabled: preparingSegmentId === group.segment.segment_id }"
                @tap="startSegmentDictation(group.segment)"
              >
                <text>{{ preparingSegmentId === group.segment.segment_id ? '准备中...' : '✏️ 默写此段' }}</text>
              </view>
            </view>
            <view class="article-body">
              <text
                v-for="(part, i) in group.parts"
                :key="i"
                :class="['word-span', part.isWord ? (part.isKey ? 'keyword' : 'clickable-word') : '']"
                @tap="part.isWord && handleWordTap(part.text)"
              >{{ part.text }}</text>
            </view>
          </view>
        </template>
      </view>

      <!-- 译文 -->
      <!-- 非书籍章节：直接使用 content.translation -->
      <view v-if="!isBookChapter && showTranslation && content.translation" class="card">
        <text class="section-label">中文译文</text>
        <text class="translation-text">{{ content.translation }}</text>
      </view>

      <!-- 书籍章节：整章译文按需拉取 -->
      <view v-if="isBookChapter && showTranslation" class="card">
        <text class="section-label">中文译文</text>
        <view v-if="loadingChapterTranslation" class="translation-loading">
          <view class="spinner-small"></view>
          <text class="translation-loading-text">首次翻译整章 4000+ 词，需要 5-10 秒...</text>
        </view>
        <view v-else-if="chapterTranslationError" class="translation-error">
          <text class="translation-error-text">译文加载失败：{{ chapterTranslationError }}</text>
          <button class="btn btn-sm btn-outline" @tap="loadChapterTranslation">重试</button>
        </view>
        <text v-else class="translation-text">{{ chapterTranslation }}</text>
      </view>

      <!-- 译文生成失败提示（仅非书籍章节的自定义内容） -->
      <view v-if="!isBookChapter && content && isGenerationFailed(content)" class="card gen-failed-card">
        <view class="gen-failed-header">
          <text class="gen-failed-icon">⚠️</text>
          <text class="gen-failed-text">译文或词组生成失败</text>
        </view>
        <text class="gen-failed-hint">AI 处理时出现异常，点击下方按钮重新生成</text>
        <button
          class="btn btn-primary btn-block btn-sm"
          :disabled="regenerating"
          @tap="regenerateContent"
        >
          <text>{{ regenerating ? '重新生成中...' : '🔄 重新生成译文和词组' }}</text>
        </button>
      </view>

      <!-- 朗读评测结果 -->
      <view v-if="evalResult" class="card eval-card">
        <view class="eval-scores-row">
          <view class="eval-score">
            <text class="eval-score-num" :class="getScoreClass(evalResult.overall)">{{ evalResult.overall }}</text>
            <text class="eval-score-label">总分</text>
          </view>
          <view class="eval-score">
            <text class="eval-score-num" :class="getScoreClass(evalResult.pronunciation)">{{ evalResult.pronunciation }}</text>
            <text class="eval-score-label">发音</text>
          </view>
          <view class="eval-score">
            <text class="eval-score-num" :class="getScoreClass(evalResult.fluency)">{{ evalResult.fluency }}</text>
            <text class="eval-score-label">流利度</text>
          </view>
          <view class="eval-score">
            <text class="eval-score-num" :class="getScoreClass(evalResult.integrity)">{{ evalResult.integrity }}</text>
            <text class="eval-score-label">完整度</text>
          </view>
        </view>
        <text class="eval-suggestion">{{ evalResult.suggestion }}</text>
        <button class="btn btn-sm btn-outline" @tap="resetEval">重新评测</button>
      </view>

      <!-- 核心词汇 -->
      <view v-if="content.words && content.words.length" class="card">
        <text class="section-label">核心词汇</text>
        <view class="words-wrap">
          <view v-for="w in content.words" :key="w.word" class="word-chip" @tap="showWordDetail(w)">
            <text class="word-text">{{ w.word }}</text>
            <text v-if="w.phonetic" class="word-phonetic">{{ w.phonetic }}</text>
            <text class="word-meaning">{{ w.meaning }}</text>
          </view>
        </view>
      </view>

      <!-- 底部留白 -->
      <view style="height: 160rpx;"></view>
    </view>

    <!-- 底部浮动工具栏 -->
    <view v-if="content" class="bottom-float-bar">
      <view class="float-item" @tap="speakContent">
        <text class="float-icon">🔊</text>
        <text class="float-label">朗读</text>
      </view>
      <view class="float-item" @tap="toggleEval">
        <text class="float-icon" :class="{ 'recording-icon': isRecording }">🎤</text>
        <text class="float-label">{{ isRecording ? '录音中' : '评测' }}</text>
      </view>
      <view class="float-item" @tap="toggleChapterTranslation">
        <text class="float-icon">{{ showTranslation ? '📖' : '📕' }}</text>
        <text class="float-label">{{ showTranslation ? '隐藏译文' : '译文' }}</text>
      </view>
      <!-- 非书籍：底部默写按钮（整篇默写）；书籍：默写按钮下沉到每段内 -->
      <view v-if="!isBookChapter" class="float-item" @tap="openDictation">
        <text class="float-icon">✏️</text>
        <text class="float-label">默写</text>
      </view>
    </view>

    <!-- 单词弹窗 -->
    <view v-if="wordPopup" class="modal-overlay" @tap="wordPopup = null">
      <view class="word-popup" @tap.stop>
        <view class="popup-header">
          <text class="popup-word">{{ wordPopup.word }}</text>
          <view class="btn-icon" @tap="speakWord(wordPopup.word)"><text>🔊</text></view>
          <view class="btn-icon fav-btn" :class="{ active: isFavorited }" @tap="toggleFavorite">
            <text>{{ isFavorited ? '⭐' : '☆' }}</text>
          </view>
        </view>
        <text v-if="wordPopup.phonetic" class="popup-phonetic">{{ wordPopup.phonetic }}</text>
        <text class="popup-meaning">{{ wordPopup.meaning }}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { onLoad, onShow, onHide } from '@dcloudio/uni-app'
import { dailyApi, dictionaryApi, speechApi, favoritesApi, bookApi } from '@/api'
import { speakWord, initVoices } from '@/composables/useSpeech'
import { useRecorder } from '@/composables/useRecorder'
import { getBaseForm } from '@/composables/useWordForm'
import { useAuthStore } from '@/stores'
import { navBackSafe } from '@/utils/router'
import type { LearningContent, WordItem } from '@/types'

// 书籍章节的段信息（从 /api/book/content/{id}/context 拿到）
interface BookSegment {
  segment_id: number
  order_no: number
  content_id: number
  word_count: number
  start_char: number | null
  end_char: number | null
}
interface BookContext {
  is_book_chapter: boolean
  chapter_id?: number
  series_id?: number
  series_name?: string
  chapter_title?: string
  segments?: BookSegment[]
}

const auth = useAuthStore()
const loading = ref(true)
const content = ref<LearningContent | null>(null)
const wordPopup = ref<{ word: string; phonetic?: string; meaning: string } | null>(null)
const showTranslation = ref(false)
const isFavorited = ref(false)
const { isRecording, startRecording, stopRecording } = useRecorder()
const evalResult = ref<{ overall: number; pronunciation: number; fluency: number; integrity: number; suggestion: string } | null>(null)
const learnedIds = ref<number[]>([])
let autoLearnTimer: ReturnType<typeof setTimeout> | null = null
let contentId = 0
const regenerating = ref(false)

// 书籍章节相关状态
const bookContext = ref<BookContext | null>(null)
const isBookChapter = computed(() => bookContext.value?.is_book_chapter === true)
// 整章译文按需拉取
const chapterTranslation = ref('')
const loadingChapterTranslation = ref(false)
const chapterTranslationError = ref('')
// 段默写准备状态：正在向后端申请的 segment_id（避免重复点击）
const preparingSegmentId = ref<number | null>(null)

const usernameInitial = computed(() => (auth.username?.[0] || '?').toUpperCase())

onLoad((query) => {
  contentId = Number(query?.id || 0)
  loadContent()
  loadBookContext()
})

onShow(() => {
  initVoices()
  loadLearnedIds()
  startAutoLearnTimer()
})

onHide(() => {
  clearAutoLearnTimer()
})

interface ArticlePart {
  text: string
  isWord: boolean
  isKey: boolean
  // 该 part 在整篇 article 中的起始字符位置（含），用来在书籍模式下匹配到 segment
  start: number
  end: number
}

const articleParts = computed<ArticlePart[]>(() => {
  if (!content.value) return []
  const article = content.value.article || ''
  const words = content.value.words || []
  
  // 构建关键词/词组映射（大小写不敏感）
  const keyMap = new Map<string, boolean>()
  words.forEach(w => keyMap.set(w.word.toLowerCase(), true))
  
  // 提取所有词组（含空格或 is_phrase 标记），按长度降序排列
  const phrases = words
    .filter(w => w.word.includes(' ') || w.is_phrase)
    .map(w => w.word)
    .sort((a, b) => b.length - a.length)
  
  const parts: ArticlePart[] = []
  let i = 0
  
  while (i < article.length) {
    // 1. 尝试匹配词组（贪心：最长优先）
    let matched = false
    for (const phrase of phrases) {
      const chunk = article.slice(i, i + phrase.length)
      if (chunk.toLowerCase() === phrase.toLowerCase()) {
        parts.push({ text: chunk, isWord: true, isKey: true, start: i, end: i + phrase.length })
        i += phrase.length
        matched = true
        break
      }
    }
    if (matched) continue
    
    // 2. 尝试匹配单个单词
    const wordMatch = article.slice(i).match(/^[a-zA-Z]+(?:'[a-zA-Z]+)?/)
    if (wordMatch) {
      const word = wordMatch[0]
      parts.push({ text: word, isWord: true, isKey: keyMap.has(word.toLowerCase()), start: i, end: i + word.length })
      i += word.length
      continue
    }
    
    // 3. 非单词字符，收集到下一个单词/词组开始
    let j = i + 1
    while (j < article.length && !/[a-zA-Z]/.test(article[j])) j++
    parts.push({ text: article.slice(i, j), isWord: false, isKey: false, start: i, end: j })
    i = j
  }
  
  return parts
})

/**
 * 书籍章节模式下把 articleParts 按 segment 边界分组。
 *
 * 分组规则：每个 part 落到 start >= segment.start_char && start < segment.end_char 的段里。
 * 边界处的 part（跨段的空白/标点）归属为其起始位置所在段。
 * 段间的字符（例如段落间的换行）会归到上一个段的末尾，视觉上不影响。
 */
interface SegmentGroup {
  segment: BookSegment
  parts: ArticlePart[]
}

const segmentGroups = computed<SegmentGroup[]>(() => {
  if (!isBookChapter.value || !bookContext.value?.segments) return []
  const segments = bookContext.value.segments
    .slice()
    .sort((a, b) => a.order_no - b.order_no)
  const groups: SegmentGroup[] = segments.map(s => ({ segment: s, parts: [] }))

  for (const part of articleParts.value) {
    // 找 part.start 落在哪个 segment 区间内
    let placed = false
    for (let idx = 0; idx < segments.length; idx++) {
      const s = segments[idx]
      const startCh = s.start_char ?? 0
      const endCh = s.end_char ?? Number.MAX_SAFE_INTEGER
      if (part.start >= startCh && part.start < endCh) {
        groups[idx].parts.push(part)
        placed = true
        break
      }
    }
    if (!placed) {
      // 落不进任何段：可能是尾部零头 / 段间空白 → 归到最后一段
      groups[groups.length - 1]?.parts.push(part)
    }
  }
  // 空段过滤（一般不会出现，防御性）
  return groups.filter(g => g.parts.length > 0)
})

function startAutoLearnTimer() {
  clearAutoLearnTimer()
  if (!content.value || !contentId || !auth.currentUserId) return
  autoLearnTimer = setTimeout(async () => {
    if (!content.value || !auth.currentUserId) return
    try {
      const { data } = await dailyApi.markLearned(auth.currentUserId, contentId)
      if (data.learned && !learnedIds.value.includes(contentId)) {
        learnedIds.value = [...learnedIds.value, contentId]
      }
    } catch { /* silent */ }
  }, 5 * 60 * 1000)
}

function clearAutoLearnTimer() {
  if (autoLearnTimer !== null) {
    clearTimeout(autoLearnTimer)
    autoLearnTimer = null
  }
}

async function loadLearnedIds() {
  if (!auth.currentUserId) return
  try {
    const { data } = await dailyApi.getLearnedIds(auth.currentUserId)
    learnedIds.value = data.content_ids || []
  } catch { /* ignore */ }
}

async function toggleLearned() {
  if (!auth.currentUserId || !contentId) return
  try {
    const { data } = await dailyApi.toggleLearned(auth.currentUserId, contentId)
    if (data.learned) {
      if (!learnedIds.value.includes(contentId)) {
        learnedIds.value = [...learnedIds.value, contentId]
      }
    } else {
      learnedIds.value = learnedIds.value.filter(id => id !== contentId)
    }
  } catch {
    uni.showToast({ title: '操作失败', icon: 'none' })
  }
}

async function loadContent() {
  loading.value = true
  try {
    const { data } = await dailyApi.getContent(contentId)
    content.value = data
  } catch { content.value = null }
  loading.value = false
}

/**
 * 并行加载 bookContext 判断当前 content 是不是书籍章节。
 * 失败静默：非书籍 content 时后端可能返回 404 / is_book_chapter=false，都当作普通内容。
 */
async function loadBookContext() {
  try {
    const { data } = await bookApi.getContentContext(contentId, auth.currentUserId)
    if (data?.is_book_chapter) {
      bookContext.value = data
    } else {
      bookContext.value = null
    }
  } catch {
    bookContext.value = null
  }
}

/** 切换整章译文显隐；首次显示时按需拉取。 */
async function toggleChapterTranslation() {
  showTranslation.value = !showTranslation.value
  if (!showTranslation.value) return
  // 非书籍章节直接切换 content.translation 显隐，无需 API
  if (!isBookChapter.value) return
  // 已加载过缓存直接展示
  if (chapterTranslation.value && !chapterTranslationError.value) return
  await loadChapterTranslation()
}

async function loadChapterTranslation() {
  if (!isBookChapter.value || !bookContext.value?.chapter_id) return
  loadingChapterTranslation.value = true
  chapterTranslationError.value = ''
  try {
    const { data } = await bookApi.getChapterTranslation(bookContext.value.chapter_id, auth.currentUserId)
    chapterTranslation.value = data?.translation || ''
    if (!chapterTranslation.value) {
      chapterTranslationError.value = '译文为空'
    }
  } catch (e: any) {
    chapterTranslationError.value = e?.data?.detail || '译文服务暂时不可用'
  }
  loadingChapterTranslation.value = false
}

/** 段级默写：调后端准备译文和词汇，成功后跳 dictation 页。 */
async function startSegmentDictation(segment: BookSegment) {
  if (preparingSegmentId.value !== null) return
  preparingSegmentId.value = segment.segment_id
  uni.showLoading({ title: '准备中...', mask: true })
  try {
    const { data } = await bookApi.prepareSegmentDictation(segment.segment_id, auth.currentUserId)
    uni.hideLoading()
    if (data?.content_id) {
      uni.navigateTo({ url: `/pages/dictation/index?id=${data.content_id}` })
    } else {
      uni.showToast({ title: '准备失败', icon: 'none' })
    }
  } catch (e: any) {
    uni.hideLoading()
    const detail = e?.data?.detail || '准备失败，请重试'
    uni.showToast({ title: detail, icon: 'none', duration: 2500 })
  }
  preparingSegmentId.value = null
}

function speakContent() {
  if (content.value?.article) speakWord(content.value.article.slice(0, 500))
}

async function handleWordTap(rawWord: string) {
  const word = getBaseForm(rawWord)
  speakWord(word)
  
  // 先检查是否是 AI 已提供的词汇/词组
  const knownWord = content.value?.words?.find(w => w.word.toLowerCase() === word.toLowerCase())
  if (knownWord) {
    // 直接用 AI 给的释义，不查字典
    wordPopup.value = { 
      word: knownWord.word, 
      phonetic: knownWord.phonetic, 
      meaning: knownWord.meaning 
    }
    checkFavorite(knownWord.word)
    return
  }
  
  // 未知词：查字典
  wordPopup.value = { word, meaning: '查询中...' }
  isFavorited.value = false
  try {
    const [dictRes, favRes] = await Promise.all([
      dictionaryApi.lookup(word),
      favoritesApi.check(auth.currentUserId, word),
    ])
    const ec = dictRes.data?.ec?.word?.[0]
    const phonetic = ec?.usphone || ec?.ukphone || ''
    const trs = ec?.trs || []
    const meaning = trs.map((t: any) => t?.tr?.[0]?.l?.i?.[0]).filter(Boolean).join('；')
    wordPopup.value = meaning
      ? { word, phonetic: phonetic ? `/${phonetic}/` : undefined, meaning }
      : { word, meaning: '未找到释义' }
    isFavorited.value = favRes.data?.is_favorited ?? false
  } catch { wordPopup.value = { word, meaning: '查询失败' } }
}

function showWordDetail(w: WordItem) {
  wordPopup.value = { word: w.word, phonetic: w.phonetic, meaning: w.meaning }
  checkFavorite(w.word)
}

async function checkFavorite(word: string) {
  try {
    const { data } = await favoritesApi.check(auth.currentUserId, word)
    isFavorited.value = data?.is_favorited ?? false
  } catch { isFavorited.value = false }
}

async function toggleFavorite() {
  if (!wordPopup.value) return
  const { word, phonetic, meaning } = wordPopup.value
  try {
    if (isFavorited.value) {
      await favoritesApi.remove(auth.currentUserId, word)
      isFavorited.value = false
      uni.showToast({ title: '已取消收藏', icon: 'none' })
    } else {
      await favoritesApi.add(auth.currentUserId, word, phonetic || '', meaning, 'article', contentId)
      isFavorited.value = true
      uni.showToast({ title: '已收藏', icon: 'success' })
    }
  } catch { uni.showToast({ title: '操作失败', icon: 'none' }) }
}

function goReview() { uni.switchTab({ url: '/pages/review/index' }) }

function openDictation() {
  uni.navigateTo({ url: `/pages/dictation/index?id=${contentId}` })
}

function getScoreClass(score: number) {
  if (score >= 90) return 'score-green'
  if (score >= 70) return 'score-orange'
  return 'score-red'
}

async function toggleEval() {
  if (!content.value?.article) return
  if (isRecording.value) {
    const audioBase64 = await stopRecording()
    if (!audioBase64) {
      uni.showToast({ title: '录音失败', icon: 'none' })
      return
    }
    uni.showLoading({ title: '评测中...' })
    try {
      const { data } = await speechApi.evaluate(audioBase64, content.value.article, 'en')
      evalResult.value = {
        overall: data.overall || 0,
        pronunciation: data.pronunciation || 0,
        fluency: data.fluency || 0,
        integrity: data.integrity || 0,
        suggestion: data.suggestion || '',
      }
    } catch {
      evalResult.value = { overall: 0, pronunciation: 0, fluency: 0, integrity: 0, suggestion: '评测失败，请稍后重试' }
    }
    uni.hideLoading()
  } else {
    if (!await startRecording()) {
      uni.showToast({ title: '麦克风权限获取失败', icon: 'none' })
    }
  }
}

function resetEval() { evalResult.value = null }
function navBack() { navBackSafe() }

// 判断自定义内容是否生成失败（译文缺失或词汇为空）
function isGenerationFailed(item: LearningContent): boolean {
  if (!item || item.creator_type !== 1) return false
  const tr = (item.translation || '').trim()
  const failedTranslation = !tr || tr.startsWith('（翻译生成失败')
  const emptyWords = !item.words || item.words.length === 0
  return failedTranslation || emptyWords
}

// 重新触发 AI 生成译文和词汇
async function regenerateContent() {
  if (!content.value || !auth.currentUserId || regenerating.value) return
  regenerating.value = true
  try {
    const { data } = await dailyApi.regenerateCustomContent(contentId, auth.currentUserId)
    content.value = data
    uni.showToast({ title: '重新生成成功', icon: 'success' })
  } catch {
    uni.showToast({ title: '生成失败，请稍后重试', icon: 'none' })
  }
  regenerating.value = false
}
</script>

<style scoped>
.detail-wrap { padding-bottom: 0; }

.detail-card { margin: 0 0 24rpx; }
.learned-toggle {
  display: inline-flex; align-items: center; gap: 8rpx;
  padding: 8rpx 20rpx; border-radius: 40rpx;
  background: #fff; border: 3rpx solid var(--outline-variant);
  font-size: 24rpx; color: var(--on-surface-variant);
  margin-bottom: 20rpx;
}
.learned-toggle:active { opacity: 0.6; }
.learned-icon { font-size: 28rpx; }
.learned-text { font-weight: 500; }

.detail-meta { display: flex; gap: 12rpx; margin-bottom: 20rpx; }
.detail-title {
  font-size: 36rpx; font-weight: 700; margin-bottom: 24rpx;
  display: block; line-height: 1.5; color: #111;
}
.article-body { line-height: 1.9; }
.word-span { font-size: 30rpx; color: #111; line-height: 1.9; }
.clickable-word { color: #111; }
.keyword { color: var(--primary); font-weight: 600; }

.section-label {
  font-size: 26rpx; color: var(--on-surface-variant);
  margin-bottom: 16rpx; display: block; font-weight: 600;
}
.translation-text { font-size: 28rpx; line-height: 1.8; display: block; }

/* 书籍章节段落分组 */
.segment-group {
  padding-top: 28rpx;
  margin-top: 28rpx;
  border-top: 3rpx dashed var(--outline-variant);
}
.segment-group:first-child {
  padding-top: 0;
  margin-top: 0;
  border-top: none;
}
.segment-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  margin-bottom: 16rpx;
}
.segment-label {
  font-size: 24rpx;
  color: var(--on-surface-variant);
  font-weight: 600;
}
.segment-dict-btn {
  font-size: 24rpx;
  padding: 8rpx 20rpx;
  border-radius: 24rpx;
  background: var(--primary-container);
  color: var(--primary);
  font-weight: 600;
  border: 2rpx solid var(--primary);
}
.segment-dict-btn:active { opacity: 0.7; }
.segment-dict-btn.disabled { opacity: 0.5; }

/* 译文按需加载状态 */
.translation-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16rpx;
  padding: 40rpx 0;
}
.translation-loading-text {
  font-size: 24rpx;
  color: var(--on-surface-variant);
}
.spinner-small {
  width: 40rpx;
  height: 40rpx;
  border: 4rpx solid var(--outline-variant);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
.translation-error {
  padding: 24rpx 0;
  text-align: center;
}
.translation-error-text {
  font-size: 26rpx;
  color: var(--error);
  display: block;
  margin-bottom: 16rpx;
}

/* 底部浮动工具栏 */
.float-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4rpx;
  padding: 12rpx 20rpx;
  border-radius: 16rpx;
  transition: background var(--transition-fast);
}
.float-item:active {
  background: rgba(91,154,168,0.1);
}
.float-icon { font-size: 36rpx; }
.float-label {
  font-size: 20rpx;
  color: var(--on-surface-variant);
  font-weight: 500;
}

.speak-btn { background: var(--primary-container); }
.fav-btn.active { background: #FFF8E1; }

/* 朗读评测 */
.eval-card { text-align: center; padding: 32rpx; }
.eval-scores-row { display: flex; justify-content: space-around; margin-bottom: 24rpx; }
.eval-score { display: flex; flex-direction: column; align-items: center; gap: 8rpx; }
.eval-score-num { font-size: 48rpx; font-weight: 800; }
.eval-score-label { font-size: 22rpx; color: var(--on-surface-variant); }
.eval-suggestion { font-size: 26rpx; color: var(--on-surface-variant); line-height: 1.6; display: block; margin-bottom: 20rpx; }
.score-green { color: var(--success); }
.score-orange { color: var(--warning); }
.score-red { color: var(--error); }
.recording-icon { color: var(--error); animation: pulse 1s infinite; }
@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(1.2); }
}

</style>
