/**
 * 语音朗读工具 - 使用浏览器内置 Web Speech API
 * 免费、无需外部API、支持多语言
 * 支持单词朗读和整篇文章朗读（播放/暂停/停止）
 */

let synth: SpeechSynthesis | null = null

function getSynth(): SpeechSynthesis | null {
  if (typeof window !== 'undefined') {
    synth = window.speechSynthesis || null
  }
  return synth
}

/**
 * 选择最佳英文语音
 */
function getEnVoice(): SpeechSynthesisVoice | undefined {
  const s = getSynth()
  if (!s) return undefined
  const voices = s.getVoices()
  return voices.find(v => v.lang.startsWith('en') && v.name.includes('Google'))
    || voices.find(v => v.lang.startsWith('en-US'))
    || voices.find(v => v.lang.startsWith('en'))
}

// ========== 单词朗读 ==========

export function speak(text: string, lang = 'en-US') {
  const s = getSynth()
  if (!s) return
  s.cancel()

  const utterance = new SpeechSynthesisUtterance(text)
  utterance.lang = lang
  utterance.rate = 0.9
  utterance.pitch = 1
  utterance.volume = 1

  const enVoice = getEnVoice()
  if (enVoice) utterance.voice = enVoice

  s.speak(utterance)
}

export function speakWord(word: string) {
  speak(word, 'en-US')
}

export function initVoices() {
  const s = getSynth()
  if (s) {
    s.getVoices()
    s.onvoiceschanged = () => s.getVoices()
  }
}

// ========== 文章朗读 ==========

export type ReadState = 'idle' | 'playing' | 'paused'

// 全局朗读状态
const readState = ref<ReadState>('idle')
const readSentences = ref<string[]>([])
const readIndex = ref(0)

import { ref } from 'vue'

/**
 * 将英文文本拆分为句子（按句号、问号、感叹号、换行分句）
 */
function splitSentences(text: string): string[] {
  // 去掉HTML标签
  const clean = text.replace(/<[^>]+>/g, ' ')
  // 按句号/问号/感叹号分句，保留标点
  const raw = clean.split(/(?<=[.!?])\s+|\n+/).map(s => s.trim()).filter(Boolean)
  return raw.length > 0 ? raw : [clean.trim()]
}

/**
 * 播放下一句
 */
function speakNext() {
  const s = getSynth()
  if (!s || readIndex.value >= readSentences.value.length) {
    readState.value = 'idle'
    readIndex.value = 0
    return
  }

  const text = readSentences.value[readIndex.value]
  const utterance = new SpeechSynthesisUtterance(text)
  utterance.lang = 'en-US'
  utterance.rate = 0.85
  utterance.pitch = 1
  utterance.volume = 1

  const enVoice = getEnVoice()
  if (enVoice) utterance.voice = enVoice

  utterance.onend = () => {
    if (readState.value === 'playing') {
      readIndex.value++
      speakNext()
    }
  }

  utterance.onerror = () => {
    readState.value = 'idle'
  }

  s.speak(utterance)
}

/**
 * 开始朗读文章
 */
export function startReading(article: string) {
  const s = getSynth()
  if (!s) return

  s.cancel()
  readSentences.value = splitSentences(article)
  readIndex.value = 0
  readState.value = 'playing'
  speakNext()
}

/**
 * 暂停朗读
 */
export function pauseReading() {
  const s = getSynth()
  if (!s) return
  readState.value = 'paused'
  s.pause()
}

/**
 * 继续朗读
 */
export function resumeReading() {
  const s = getSynth()
  if (!s) return
  readState.value = 'playing'
  s.resume()
}

/**
 * 停止朗读
 */
export function stopReading() {
  const s = getSynth()
  if (!s) return
  s.cancel()
  readState.value = 'idle'
  readIndex.value = 0
  readSentences.value = []
}

/**
 * 切换朗读/暂停
 */
export function toggleReading(article: string) {
  if (readState.value === 'playing') {
    pauseReading()
  } else if (readState.value === 'paused') {
    resumeReading()
  } else {
    startReading(article)
  }
}

/**
 * 获取朗读状态（响应式）
 */
export function useReadingState() {
  return { readState, readIndex, readSentences }
}
