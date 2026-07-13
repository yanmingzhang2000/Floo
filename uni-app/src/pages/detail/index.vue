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

        <!-- 书籍章节：一次只显示当前段（左右箭头/按钮翻页），段下方内嵌译文 -->
        <template v-else>
          <template v-if="currentSegmentGroup">
            <!-- 顶部翻页条 -->
            <view class="segment-pager">
              <view
                class="pager-btn"
                :class="{ disabled: !canPrevSegment }"
                @tap="goPrevSegment"
              >
                <text>‹ 上一段</text>
              </view>
              <text class="pager-indicator">
                段 {{ currentSegmentIndex + 1 }} / {{ segmentGroups.length }}
              </text>
              <view
                class="pager-btn"
                :class="{ disabled: !canNextSegment }"
                @tap="goNextSegment"
              >
                <text>下一段 ›</text>
              </view>
            </view>

            <view class="segment-header">
              <text class="segment-label">{{ currentSegmentGroup.segment.word_count }} 词</text>
              <view class="segment-actions">
                <view
                  class="segment-toggle-btn"
                  @tap="toggleSegmentTranslation(currentSegmentGroup.segment)"
                >
                  <text>{{ isSegmentTranslationVisible(currentSegmentGroup.segment.segment_id) ? '收起译文' : '展开译文' }}</text>
                </view>
                <view
                  class="segment-dict-btn"
                  :class="{ disabled: preparingSegmentId === currentSegmentGroup.segment.segment_id }"
                  @tap="startSegmentDictation(currentSegmentGroup.segment)"
                >
                  <text>{{ preparingSegmentId === currentSegmentGroup.segment.segment_id ? '准备中...' : '✏️ 默写此段' }}</text>
                </view>
              </view>
            </view>

            <!-- 原文 -->
            <view class="article-body">
              <text
                v-for="(part, i) in currentSegmentGroup.parts"
                :key="i"
                :class="['word-span', part.isWord ? (part.isKey ? 'keyword' : 'clickable-word') : '']"
                @tap="part.isWord && handleWordTap(part.text)"
              >{{ part.text }}</text>
            </view>

            <!-- 段内嵌译文 -->
            <view
              v-if="isSegmentTranslationVisible(currentSegmentGroup.segment.segment_id)"
              class="segment-translation"
            >
              <text class="section-label">中文译文</text>
              <view
                v-if="segmentTranslationLoading[currentSegmentGroup.segment.segment_id]"
                class="translation-loading"
              >
                <view class="spinner-small"></view>
                <text class="translation-loading-text">正在生成译文，约 5-8 秒...</text>
              </view>
              <view
                v-else-if="segmentTranslationError[currentSegmentGroup.segment.segment_id]"
                class="translation-error"
              >
                <text class="translation-error-text">译文加载失败：{{ segmentTranslationError[currentSegmentGroup.segment.segment_id] }}</text>
                <button
                  class="btn btn-sm btn-outline"
                  @tap="ensureSegmentTranslation(currentSegmentGroup.segment)"
                >重试</button>
              </view>
              <text v-else class="translation-text">{{ segmentTranslations[currentSegmentGroup.segment.segment_id] }}</text>
            </view>

            <!-- 底部翻页条 -->
            <view class="segment-pager segment-pager-bottom">
              <view
                class="pager-btn"
                :class="{ disabled: !canPrevSegment }"
                @tap="goPrevSegment"
              >
                <text>‹ 上一段</text>
              </view>
              <text class="pager-indicator">
                段 {{ currentSegmentIndex + 1 }} / {{ segmentGroups.length }}
              </text>
              <view
                class="pager-btn"
                :class="{ disabled: !canNextSegment }"
                @tap="goNextSegment"
              >
                <text>下一段 ›</text>
              </view>
            </view>

            <text class="pager-hint">⌨️ 提示：按 ← / → 键翻页</text>
          </template>
        </template>
      </view>

      <!-- 非书籍章节：整篇译文 -->
      <view v-if="!isBookChapter && showTranslation && content.translation" class="card">
        <text class="section-label">中文译文</text>
        <text class="translation-text">{{ content.translation }}</text>
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

      <!-- 核心词汇（书籍模式下只显示当前段的词） -->
      <view v-if="segmentWords.length" class="card">
        <text class="section-label">核心词汇</text>
        <view class="words-wrap">
          <view v-for="w in segmentWords" :key="w.word" class="word-chip" @tap="showWordDetail(w)">
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
      <view class="float-item" @tap="toggleAllTranslations">
        <text class="float-icon">{{ translationButtonIcon }}</text>
        <text class="float-label">{{ translationButtonLabel }}</text>
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
import { ref, computed, reactive, watch } from 'vue'
import { onLoad, onShow, onHide } from '@dcloudio/uni-app'
import { dailyApi, dictionaryApi, favoritesApi, bookApi } from '@/api'
import { speakWord, initVoices } from '@/composables/useSpeech'
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
// 全局译文显隐（非书籍章节控制单一整篇译文；书籍章节控制所有段译文的默认可见性）
const showTranslation = ref(true)
const isFavorited = ref(false)
const learnedIds = ref<number[]>([])
let autoLearnTimer: ReturnType<typeof setTimeout> | null = null
let contentId = 0
const regenerating = ref(false)

// 书籍章节相关状态
const bookContext = ref<BookContext | null>(null)
const isBookChapter = computed(() => bookContext.value?.is_book_chapter === true)
// 段默写准备状态：正在向后端申请的 segment_id（避免重复点击）
const preparingSegmentId = ref<number | null>(null)

// ---- 段翻页 ----
// 当前显示的 segment 在 segmentGroups 里的下标
const currentSegmentIndex = ref(0)

// ---- 段级译文（阅读态）----
// segment_id -> 译文文本 / 加载中 / 错误 / 用户手动收起
const segmentTranslations = reactive<Record<number, string>>({})
const segmentTranslationLoading = reactive<Record<number, boolean>>({})
const segmentTranslationError = reactive<Record<number, string>>({})
const segmentTranslationHidden = reactive<Set<number>>(new Set())

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
  bindKeyboardShortcuts()
})

onHide(() => {
  clearAutoLearnTimer()
  unbindKeyboardShortcuts()
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

/** 当前显示的段。index 越界时自动截断到边界。 */
const currentSegmentGroup = computed<SegmentGroup | null>(() => {
  const groups = segmentGroups.value
  if (groups.length === 0) return null
  const idx = Math.min(Math.max(currentSegmentIndex.value, 0), groups.length - 1)
  return groups[idx]
})

/**
 * 核心词汇：书籍模式下只返回当前段里出现过的词，非书籍模式返回全量。
 * 为什么不做后端分段：段的 key_words 只在"默写此段"触发 LLM 挑词时才生成，
 * 阅读态只看译文不挑词；前端按 parts 文本过滤成本极低，不值得为此加一次请求。
 */
const segmentWords = computed(() => {
  if (!content.value?.words) return []
  if (!isBookChapter.value || !currentSegmentGroup.value) return content.value.words
  const textSet = new Set(
    currentSegmentGroup.value.parts
      .filter(p => p.isWord)
      .map(p => p.text.toLowerCase()),
  )
  return content.value.words.filter(w => textSet.has(w.word.toLowerCase()))
})

const canPrevSegment = computed(() => isBookChapter.value && currentSegmentIndex.value > 0)
const canNextSegment = computed(
  () => isBookChapter.value && currentSegmentIndex.value < segmentGroups.value.length - 1,
)

function goPrevSegment() {
  if (!canPrevSegment.value) {
    console.debug('[book] goPrevSegment: 已是首段，忽略')
    return
  }
  currentSegmentIndex.value -= 1
  console.debug('[book] goPrevSegment: index=', currentSegmentIndex.value)
  scrollToChapterTop()
}

function goNextSegment() {
  if (!canNextSegment.value) {
    console.debug('[book] goNextSegment: 已是末段，忽略')
    return
  }
  currentSegmentIndex.value += 1
  console.debug('[book] goNextSegment: index=', currentSegmentIndex.value)
  scrollToChapterTop()
}

/**
 * 段间切换后把页面滚回顶部。
 * Why 用 uni.pageScrollTo：uni-app 页面级滚动只能通过 API 控制。
 */
function scrollToChapterTop() {
  uni.pageScrollTo({ scrollTop: 0, duration: 200 })
}

/** 某段当前是否显示译文：全局开 + 不在 hidden 集合。 */
function isSegmentTranslationVisible(segmentId: number): boolean {
  if (!showTranslation.value) return false
  return !segmentTranslationHidden.has(segmentId)
}

/** 段级切换：只影响这一段的显隐（全局关闭时按点击视为打开全局）。 */
function toggleSegmentTranslation(segment: BookSegment) {
  if (!showTranslation.value) {
    console.debug('[book] toggleSegmentTranslation: 全局关闭状态下点段，改为打开全局 seg=', segment.segment_id)
    showTranslation.value = true
    segmentTranslationHidden.clear()
    ensureSegmentTranslation(segment)
    return
  }
  if (segmentTranslationHidden.has(segment.segment_id)) {
    segmentTranslationHidden.delete(segment.segment_id)
    console.debug('[book] toggleSegmentTranslation: 展开 seg=', segment.segment_id)
    ensureSegmentTranslation(segment)
  } else {
    segmentTranslationHidden.add(segment.segment_id)
    console.debug('[book] toggleSegmentTranslation: 收起 seg=', segment.segment_id)
  }
}

/**
 * 全局译文按钮：三态循环
 *   全局关 → 全局开且清空 hidden（全部展开）
 *   全局开且有 hidden → 清空 hidden（全部展开）
 *   全局开且无 hidden → 关闭全局（全部隐藏）
 */
function toggleAllTranslations() {
  if (!showTranslation.value) {
    showTranslation.value = true
    segmentTranslationHidden.clear()
    console.debug('[book] toggleAllTranslations: 打开全局')
    if (isBookChapter.value && currentSegmentGroup.value) {
      ensureSegmentTranslation(currentSegmentGroup.value.segment)
    }
    return
  }
  if (isBookChapter.value && segmentTranslationHidden.size > 0) {
    segmentTranslationHidden.clear()
    console.debug('[book] toggleAllTranslations: 全部展开')
    if (currentSegmentGroup.value) {
      ensureSegmentTranslation(currentSegmentGroup.value.segment)
    }
    return
  }
  showTranslation.value = false
  console.debug('[book] toggleAllTranslations: 全部隐藏')
}

const translationButtonLabel = computed(() => {
  if (!showTranslation.value) return '译文'
  if (isBookChapter.value && segmentTranslationHidden.size > 0) return '全展开'
  return '隐藏译文'
})
const translationButtonIcon = computed(() => (showTranslation.value ? '📖' : '📕'))

/** 懒加载单段译文；命中缓存/加载中直接跳过；失败保留 error 供 UI 重试。 */
async function ensureSegmentTranslation(segment: BookSegment) {
  const id = segment.segment_id
  if (segmentTranslations[id] !== undefined) {
    console.debug('[book] ensureSegmentTranslation 缓存命中 seg=', id)
    return
  }
  if (segmentTranslationLoading[id]) {
    console.debug('[book] ensureSegmentTranslation 已在加载 seg=', id)
    return
  }
  segmentTranslationLoading[id] = true
  segmentTranslationError[id] = ''
  try {
    const { data } = await bookApi.getSegmentTranslation(id, auth.currentUserId)
    segmentTranslations[id] = data?.translation || ''
    if (!segmentTranslations[id]) {
      segmentTranslationError[id] = '译文为空'
      console.debug('[book] ensureSegmentTranslation 后端返回空 seg=', id)
    }
  } catch (e: any) {
    segmentTranslationError[id] = e?.data?.detail || '译文服务暂时不可用'
    console.debug('[book] ensureSegmentTranslation 失败 seg=', id, segmentTranslationError[id])
  } finally {
    segmentTranslationLoading[id] = false
  }
}

/** 段索引变化：加载当前段译文 + 预取下一段。 */
watch(
  [currentSegmentIndex, segmentGroups],
  ([idx, groups]) => {
    if (!isBookChapter.value) return
    const list = groups as SegmentGroup[]
    if (list.length === 0) return
    if ((idx as number) >= list.length) {
      console.debug('[book] watch(segment): index 越界，归零 idx=', idx, ' len=', list.length)
      currentSegmentIndex.value = 0
      return
    }
    const cur = list[idx as number]
    if (cur && isSegmentTranslationVisible(cur.segment.segment_id)) {
      ensureSegmentTranslation(cur.segment)
    }
    const next = list[(idx as number) + 1]
    if (next && isSegmentTranslationVisible(next.segment.segment_id)) {
      ensureSegmentTranslation(next.segment)
    }
  },
  { immediate: false },
)

// ---- 键盘快捷键 ----
function onKeydown(e: KeyboardEvent) {
  if (wordPopup.value) {
    console.debug('[book] onKeydown: 弹窗打开中，忽略方向键')
    return
  }
  const target = e.target as HTMLElement | null
  if (target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable)) {
    return
  }
  if (!isBookChapter.value) return
  if (e.key === 'ArrowLeft') {
    e.preventDefault()
    goPrevSegment()
  } else if (e.key === 'ArrowRight') {
    e.preventDefault()
    goNextSegment()
  }
}

function bindKeyboardShortcuts() {
  console.debug('[book] bindKeyboardShortcuts')
  document.addEventListener('keydown', onKeydown)
}

function unbindKeyboardShortcuts() {
  console.debug('[book] unbindKeyboardShortcuts')
  document.removeEventListener('keydown', onKeydown)
}

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

/**
 * 单词查询缓存（session 内，跨 detail 页跳转保留）。
 * Why：有道 API 单次响应 20-100KB，翻页时同一批常见词反复查太慢；
 * 缓存原词、词根两种 key 都写入，避免同一词形不同大小写反复网络请求。
 */
const wordLookupCache = new Map<string, { word: string; phonetic?: string; meaning: string } | null>()

async function lookupWord(word: string): Promise<{ word: string; phonetic?: string; meaning: string } | null> {
  const key = word.toLowerCase()
  if (wordLookupCache.has(key)) {
    return wordLookupCache.get(key) ?? null
  }
  try {
    const { data } = await dictionaryApi.lookup(word)
    const meaning = extractMeaning(data)
    const phonetic = extractPhonetic(data)
    if (!meaning) {
      // 缓存 null 避免同一词反复查有道，进程内也不再重试
      console.debug('[dict] lookupWord 未提取到释义 word=%s', word)
      wordLookupCache.set(key, null)
      return null
    }
    const result = { word, phonetic: phonetic ? `/${phonetic}/` : undefined, meaning }
    wordLookupCache.set(key, result)
    return result
  } catch (e) {
    // 网络失败不写缓存，允许下次重试
    console.debug('[dict] lookupWord 网络失败 word=%s err=%s', word, e)
    return null
  }
}

/**
 * 从有道 JSON API 响应里尽力提取中文释义。
 *
 * 有道对不同词返回结构差异很大，常见有：
 *   1. ec.word[0].trs[].tr[0].l.i[0]        —— 英汉词典释义（最常见）
 *   2. web_trans["web-translation"][0].trans[0].value —— 网络翻译（生僻词兜底）
 *   3. simple.word[0].trs[].tr[0].l.i[0]    —— 简明词典（有些词只在这里）
 *   4. fanyi.tran                            —— 顶层翻译（词组 / 短语常走这个）
 *
 * 只解析 ec 一层的老实现会让相当一部分普通词（尤其时态变形和短语）显示"未找到释义"。
 * 这里按优先级依次兜底。
 */
function extractMeaning(data: any): string {
  if (!data) return ''
  // 1. ec 英汉词典
  const ecTrs = data?.ec?.word?.[0]?.trs
  if (Array.isArray(ecTrs)) {
    const parts = ecTrs
      .map((t: any) => t?.tr?.[0]?.l?.i?.[0])
      .filter((s: any) => typeof s === 'string' && s.trim())
    if (parts.length) return parts.join('；')
  }
  // 2. simple 简明词典
  const simpleTrs = data?.simple?.word?.[0]?.trs
  if (Array.isArray(simpleTrs)) {
    const parts = simpleTrs
      .map((t: any) => t?.tr?.[0]?.l?.i?.[0])
      .filter((s: any) => typeof s === 'string' && s.trim())
    if (parts.length) return parts.join('；')
  }
  // 3. web_trans 网络翻译
  const webList = data?.web_trans?.['web-translation']
  if (Array.isArray(webList) && webList.length) {
    const firstTrans = webList[0]?.trans
    if (Array.isArray(firstTrans) && firstTrans.length) {
      const values = firstTrans
        .map((t: any) => t?.value)
        .filter((s: any) => typeof s === 'string' && s.trim())
      if (values.length) return values.join('；')
    }
  }
  // 4. fanyi 顶层翻译
  const fanyi = data?.fanyi?.tran
  if (typeof fanyi === 'string' && fanyi.trim()) return fanyi.trim()
  return ''
}

/** 音标同样按 ec → simple 兜底一次。 */
function extractPhonetic(data: any): string {
  const ec = data?.ec?.word?.[0]
  if (ec) {
    const p = ec.usphone || ec.ukphone
    if (typeof p === 'string' && p.trim()) return p.trim()
  }
  const simple = data?.simple?.word?.[0]
  if (simple) {
    const p = simple.usphone || simple.ukphone
    if (typeof p === 'string' && p.trim()) return p.trim()
  }
  return ''
}

async function handleWordTap(rawWord: string) {
  const raw = rawWord.trim()
  if (!raw) {
    console.debug('[dict] handleWordTap 空词，忽略')
    return
  }
  console.debug('[dict] handleWordTap word=%s', raw)
  const baseForm = getBaseForm(raw)
  speakWord(raw)

  // 先按原词匹配 AI 关键词，其次按词根匹配
  const rawLower = raw.toLowerCase()
  const baseLower = baseForm.toLowerCase()
  const knownWord = content.value?.words?.find(
    w => w.word.toLowerCase() === rawLower || w.word.toLowerCase() === baseLower
  )
  if (knownWord) {
    wordPopup.value = {
      word: knownWord.word,
      phonetic: knownWord.phonetic,
      meaning: knownWord.meaning,
    }
    checkFavorite(knownWord.word)
    return
  }

  // 未知词：先查原词（保留 crowning/sharply 这类的独立释义），
  // 拿不到再降级到词根（families→family, came→come 这类）。
  isFavorited.value = false

  // 缓存命中则直接展示，不闪 "查询中..."
  const cachedRaw = wordLookupCache.get(rawLower)
  if (cachedRaw !== undefined) {
    if (cachedRaw) {
      wordPopup.value = cachedRaw
      checkFavorite(cachedRaw.word)
      return
    }
    // 原词缓存为 null（之前查过没结果），继续走词根
  }
  const cachedBase = baseLower !== rawLower ? wordLookupCache.get(baseLower) : undefined
  if (cachedBase) {
    wordPopup.value = cachedBase
    checkFavorite(cachedBase.word)
    return
  }

  wordPopup.value = { word: raw, meaning: '查询中...' }

  // 优先原词
  let result = await lookupWord(raw)
  // 未命中且词根不同，再试词根
  if (!result && baseLower !== rawLower) {
    result = await lookupWord(baseForm)
  }

  if (result) {
    wordPopup.value = result
    checkFavorite(result.word)
  } else {
    wordPopup.value = { word: raw, meaning: '未找到释义' }
  }
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

function goReview() {
  // review 已从 tabBar 移除，改用 navigateTo；navTo 内部会自动挑对 API
  uni.navigateTo({ url: '/pages/review/index' })
}

function openDictation() {
  uni.navigateTo({ url: `/pages/dictation/index?id=${contentId}` })
}

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
/*
 * clickable-word 视觉提示：正文颜色 + 灰色虚线下划线，暗示可点查释义，
 * 但不抢焦点。以前用 --primary 主色导致整段全绿，只有"词汇书里的词"
 * 才应该是主题色（走 .keyword）。
 */
.clickable-word {
  color: inherit;
  text-decoration: underline;
  text-decoration-style: dashed;
  text-decoration-color: var(--outline-variant);
  text-underline-offset: 4rpx;
}
.keyword {
  color: var(--on-primary-container);
  background: var(--primary-container);
  padding: 0 4rpx;
  border-radius: 4rpx;
  font-weight: 600;
}

.section-label {
  font-size: 26rpx; color: var(--on-surface-variant);
  margin-bottom: 16rpx; display: block; font-weight: 600;
}
.translation-text { font-size: 28rpx; line-height: 1.8; display: block; }

/* ===== 书籍章节：段头 + 段内嵌译文 + 段翻页 ===== */
.segment-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  margin-bottom: 16rpx;
  flex-wrap: wrap;
}
.segment-label {
  font-size: 24rpx;
  color: var(--on-surface-variant);
  font-weight: 600;
}
.segment-actions {
  display: flex;
  gap: 12rpx;
  align-items: center;
}
.segment-toggle-btn {
  font-size: 22rpx;
  padding: 8rpx 18rpx;
  border-radius: 24rpx;
  background: var(--surface-container);
  color: var(--on-surface-variant);
  border: 2rpx solid var(--outline-variant);
}
.segment-toggle-btn:active { opacity: 0.7; }
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

/* 段内嵌译文卡片：视觉上贴在原文正下方，跟原文明显同属一段 */
.segment-translation {
  margin-top: 28rpx;
  padding: 24rpx 24rpx 20rpx;
  background: #F7FBFC;
  border-left: 6rpx solid var(--primary);
  border-radius: 12rpx;
}
.segment-translation .section-label {
  margin-bottom: 12rpx;
}

/* 翻页控件 */
.segment-pager {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  margin-bottom: 24rpx;
  padding: 12rpx 4rpx;
}
.segment-pager-bottom {
  margin-top: 32rpx;
  margin-bottom: 0;
  padding-top: 20rpx;
  border-top: 2rpx dashed var(--outline-variant);
}
.pager-btn {
  padding: 12rpx 28rpx;
  border-radius: 32rpx;
  background: var(--primary-container);
  color: var(--primary);
  font-size: 26rpx;
  font-weight: 600;
  border: 2rpx solid var(--primary);
}
.pager-btn:active { opacity: 0.7; }
.pager-btn.disabled {
  opacity: 0.35;
  background: var(--surface-container);
  color: var(--on-surface-muted);
  border-color: var(--outline-variant);
}
.pager-indicator {
  font-size: 24rpx;
  color: var(--on-surface-variant);
  font-weight: 600;
}
.pager-hint {
  display: block;
  text-align: center;
  font-size: 22rpx;
  color: var(--on-surface-muted);
  margin-top: 16rpx;
}

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

.recording-icon { color: var(--error); animation: pulse 1s infinite; }
@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(1.2); }
}

</style>
