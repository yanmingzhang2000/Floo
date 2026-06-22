/**
 * 单词弹窗管理 - 词典查询、收藏、自动收起
 *
 * 为什么独立提取：DailyPage 和 DailyDetailPage 有几乎相同的单词弹窗逻辑
 * （词典查询 + 缓存 + 收藏检查 + 5秒自动收起），提取后消除约 120 行重复代码。
 *
 * 设计决策：取词逻辑以 DailyDetailPage 的健壮版本为基准（三级回退 + prompt 兜底），
 * 收藏状态以 DailyPage 的模式为基准（isFavorite 跟随 wordPopup 对象，不分散到独立 ref）。
 */
import { ref, watch, onUnmounted } from 'vue'
import { dictionaryApi, favoritesApi } from '@/api'
import { speakWord } from '@/composables/useSpeech'
import { getBaseForm } from '@/composables/useWordForm'
import type { LearningContent } from '@/types'

export interface WordPopupData {
  word: string
  phonetic?: string
  meaning: string
  usage?: string
  isFavorite?: boolean
}

// 模块级单词查询缓存（所有实例共享，避免重复查询）
const wordCache = new Map<string, { word: string; phonetic?: string; meaning: string }>()
const CACHE_MAX = 500

function getCachedWord(word: string) {
  return wordCache.get(word.toLowerCase())
}

function setCachedWord(word: string, result: { word: string; phonetic?: string; meaning: string }) {
  wordCache.set(word.toLowerCase(), result)
  if (wordCache.size > CACHE_MAX) {
    const firstKey = wordCache.keys().next().value
    if (firstKey) wordCache.delete(firstKey)
  }
}

/**
 * @param userId 获取当前用户 ID 的函数（避免在 composable 内部直接依赖 store）
 */
export function useWordPopup(userId: () => number | null) {
  const wordPopup = ref<WordPopupData | null>(null)

  // ===== 5秒自动收起 =====
  let dismissTimer: ReturnType<typeof setTimeout> | null = null

  function clearDismissTimer() {
    if (dismissTimer) {
      clearTimeout(dismissTimer)
      dismissTimer = null
    }
  }

  watch(wordPopup, (val) => {
    clearDismissTimer()
    if (val) {
      dismissTimer = setTimeout(() => { wordPopup.value = null }, 5000)
    }
  })

  onUnmounted(clearDismissTimer)

  // ===== 取词逻辑（三级回退） =====
  async function handleWordClick(e: Event, _item?: LearningContent) {
    e.preventDefault()
    e.stopPropagation()

    const target = e.target as HTMLElement
    let rawWord = ''

    // 第一级：从 data-word 属性取
    if (target.dataset.word) {
      rawWord = target.dataset.word
    }
    // 第二级：向上查找 data-word 属性
    else if (target.closest('[data-word]')) {
      rawWord = (target.closest('[data-word]') as HTMLElement).dataset.word || ''
    }
    // 第三级：从文本提取英文单词
    else {
      const m = (target.textContent || '').match(/[a-zA-Z]+/)
      if (m) rawWord = m[0]
    }

    // 兜底：弹出输入框
    if (!rawWord) {
      const input = prompt('输入想查询的单词：')
      if (input && input.trim()) rawWord = input.trim()
    }

    if (!rawWord) return

    // 词形还原
    const word = getBaseForm(rawWord)

    // 发音
    speakWord(word)

    // 检查收藏状态
    const uid = userId()
    let isFavorite = false
    if (uid) {
      try {
        const { data } = await favoritesApi.check(uid, word)
        isFavorite = data?.is_favorite || false
      } catch { /* 查询收藏失败不影响主流程 */ }
    }

    // 查缓存
    const cached = getCachedWord(word)
    if (cached) {
      wordPopup.value = { ...cached, isFavorite }
      return
    }

    // 缓存未命中，调词典 API
    wordPopup.value = { word, meaning: '查询中...', isFavorite }

    try {
      const { data } = await dictionaryApi.lookup(word)
      const ec = data?.ec?.word?.[0]
      const phonetic = ec?.usphone || ec?.ukphone || ''
      const trs = ec?.trs || []
      const meaning = trs.map((t: any) => t?.tr?.[0]?.l?.i?.[0]).filter(Boolean).join('；')

      if (meaning) {
        const result = { word, phonetic: phonetic ? `/${phonetic}/` : undefined, meaning }
        setCachedWord(word, result)
        wordPopup.value = { ...result, isFavorite }
      } else {
        wordPopup.value = { word, meaning: '未找到释义', isFavorite }
      }
    } catch {
      wordPopup.value = { word, meaning: '查询失败，请稍后重试', isFavorite }
    }
  }

  // ===== 收藏切换 =====
  async function toggleFavorite() {
    const uid = userId()
    if (!wordPopup.value || !uid) return

    const { word, phonetic, meaning, isFavorite } = wordPopup.value

    try {
      if (isFavorite) {
        await favoritesApi.remove(uid, word)
        wordPopup.value = { ...wordPopup.value, isFavorite: false }
      } else {
        await favoritesApi.add(uid, word, phonetic, meaning)
        wordPopup.value = { ...wordPopup.value, isFavorite: true }
      }
    } catch { /* 忽略收藏操作失败 */ }
  }

  // ===== 从外部直接设置弹窗（如点击核心词汇芯片） =====
  function showWordFromChip(w: { word: string; phonetic?: string; meaning: string; usage?: string }) {
    wordPopup.value = { ...w, isFavorite: false }
    // 异步检查收藏状态
    const uid = userId()
    if (uid) {
      favoritesApi.check(uid, w.word)
        .then(({ data }) => {
          if (wordPopup.value?.word === w.word) {
            wordPopup.value = { ...wordPopup.value!, isFavorite: data?.is_favorite || false }
          }
        })
        .catch(() => {})
    }
  }

  return {
    wordPopup,
    handleWordClick,
    toggleFavorite,
    showWordFromChip,
    clearDismissTimer,
  }
}
