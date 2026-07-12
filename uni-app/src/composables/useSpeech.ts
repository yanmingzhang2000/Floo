/**
 * 语音朗读工具 - H5 Web Speech API
 */

import { ref } from 'vue'

let synth: SpeechSynthesis | null = null
let voicesLoaded = false

function getSynth(): SpeechSynthesis | null {
  if (typeof window !== 'undefined') {
    synth = window.speechSynthesis || null
  }
  return synth
}

function getEnVoice(): SpeechSynthesisVoice | undefined {
  const s = getSynth()
  if (!s) return undefined
  const voices = s.getVoices()
  const voice = voices.find(v => v.lang.startsWith('en') && v.name.includes('Google'))
    || voices.find(v => v.lang.startsWith('en-US'))
    || voices.find(v => v.lang.startsWith('en'))
    || voices[0]
  return voice
}

function ensureVoicesReady(): Promise<boolean> {
  return new Promise((resolve) => {
    const s = getSynth()
    if (!s) { resolve(false); return }
    if (voicesLoaded && s.getVoices().length > 0) {
      resolve(true)
      return
    }
    const timeout = setTimeout(() => {
      voicesLoaded = true
      resolve(s.getVoices().length > 0)
    }, 1000)
    s.onvoiceschanged = () => {
      clearTimeout(timeout)
      voicesLoaded = true
      resolve(s.getVoices().length > 0)
    }
  })
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
    s.onvoiceschanged = () => {
      voicesLoaded = true
      s.getVoices()
    }
  }
}

// ========== 文章朗读 ==========

export type ReadState = 'idle' | 'playing' | 'paused'

const readState = ref<ReadState>('idle')
const readSentences = ref<string[]>([])
const readIndex = ref(0)

function splitSentences(text: string): string[] {
  const clean = text.replace(/<[^>]+>/g, ' ')
  const raw = clean.split(/(?<=[.!?])\s+|\n+/).map(s => s.trim()).filter(Boolean)
  return raw.length > 0 ? raw : [clean.trim()]
}

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
    if (readState.value === 'playing' && readIndex.value < readSentences.value.length) {
      setTimeout(() => {
        if (readState.value === 'playing') speakNext()
      }, 100)
    } else {
      readState.value = 'idle'
    }
  }
  s.speak(utterance)
}

export async function startReading(article: string) {
  const s = getSynth()
  if (!s) return
  await ensureVoicesReady()
  s.cancel()
  readSentences.value = splitSentences(article)
  readIndex.value = 0
  readState.value = 'playing'
  speakNext()
}

export function pauseReading() {
  const s = getSynth()
  if (!s) return
  readState.value = 'paused'
  s.pause()
}

export function resumeReading() {
  const s = getSynth()
  if (!s) return
  readState.value = 'playing'
  s.resume()
}

export function stopReading() {
  const s = getSynth()
  if (!s) return
  s.cancel()
  readState.value = 'idle'
  readIndex.value = 0
  readSentences.value = []
}

export function toggleReading(article: string) {
  if (readState.value === 'playing') {
    pauseReading()
  } else if (readState.value === 'paused') {
    resumeReading()
  } else {
    startReading(article)
  }
}

export function useReadingState() {
  return { readState, readIndex, readSentences }
}
