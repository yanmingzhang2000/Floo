/**
 * 语音朗读工具 - uni-app 版本
 * H5 用 Web Speech API，小程序用后端 TTS 接口 + uni.createInnerAudioContext
 */

import { ref } from 'vue'
import { ttsApi } from '@/api'

let synth: SpeechSynthesis | null = null
let voicesLoaded = false

// 小程序音频上下文
let innerAudio: UniApp.InnerAudioContext | null = null

function getSynth(): SpeechSynthesis | null {
  // #ifdef H5
  if (typeof window !== 'undefined') {
    synth = window.speechSynthesis || null
  }
  // #endif
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
  // #ifdef H5
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
  // #endif

  // #ifdef MP-WEIXIN
  // 小程序端使用后端 TTS 接口
  speakWithTTS(text)
  // #endif
}

// 小程序端 TTS 播放
async function speakWithTTS(text: string) {
  try {
    uni.showLoading({ title: '加载语音...' })
    const { data } = await ttsApi.synthesize(text, '0')  // 0=英文
    uni.hideLoading()
    
    if (data && data.audio) {
      // 创建临时音频文件并播放
      const fs = uni.getFileSystemManager()
      const filePath = `${wx.env.USER_DATA_PATH}/tts_${Date.now()}.wav`
      
      // 解码 base64 音频并保存为文件
      const audioData = base64ToArrayBuffer(data.audio)
      fs.writeFile({
        filePath,
        data: audioData,
        encoding: 'binary',
        success: () => {
          playAudioFile(filePath)
        },
        fail: (err) => {
          console.error('保存音频文件失败:', err)
          uni.showToast({ title: '语音播放失败', icon: 'none' })
        }
      })
    }
  } catch (e) {
    uni.hideLoading()
    console.error('TTS 请求失败:', e)
    // 静默失败，不打扰用户
  }
}

// 播放音频文件
function playAudioFile(filePath: string) {
  if (innerAudio) {
    innerAudio.destroy()
  }
  innerAudio = uni.createInnerAudioContext()
  innerAudio.src = filePath
  innerAudio.onEnded(() => {
    // 播放完成后删除临时文件
    const fs = uni.getFileSystemManager()
    fs.unlink({ filePath, fail: () => {} })
  })
  innerAudio.onError((err) => {
    console.error('音频播放失败:', err)
    // 清理临时文件
    const fs = uni.getFileSystemManager()
    fs.unlink({ filePath, fail: () => {} })
  })
  innerAudio.play()
}

// base64 转 ArrayBuffer
function base64ToArrayBuffer(base64: string): ArrayBuffer {
  const binary = atob(base64)
  const len = binary.length
  const buffer = new ArrayBuffer(len)
  const view = new Uint8Array(buffer)
  for (let i = 0; i < len; i++) {
    view[i] = binary.charCodeAt(i)
  }
  return buffer
}

export function speakWord(word: string) {
  speak(word, 'en-US')
}

export function initVoices() {
  // #ifdef H5
  const s = getSynth()
  if (s) {
    s.getVoices()
    s.onvoiceschanged = () => {
      voicesLoaded = true
      s.getVoices()
    }
  }
  // #endif
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
  // #ifdef H5
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
  // #endif

  // #ifdef MP-WEIXIN
  // 小程序端逐句朗读
  if (readIndex.value >= readSentences.value.length) {
    readState.value = 'idle'
    readIndex.value = 0
    return
  }
  const text = readSentences.value[readIndex.value]
  speakWithTTSForArticle(text, () => {
    if (readState.value === 'playing') {
      readIndex.value++
      speakNext()
    }
  })
  // #endif
}

// 小程序端文章朗读 TTS
async function speakWithTTSForArticle(text: string, onEnd: () => void) {
  try {
    const { data } = await ttsApi.synthesize(text, '0')
    if (data && data.audio) {
      const fs = uni.getFileSystemManager()
      const filePath = `${wx.env.USER_DATA_PATH}/tts_article_${Date.now()}.wav`
      const audioData = base64ToArrayBuffer(data.audio)
      
      fs.writeFile({
        filePath,
        data: audioData,
        encoding: 'binary',
        success: () => {
          const audio = uni.createInnerAudioContext()
          audio.src = filePath
          audio.onEnded(() => {
            fs.unlink({ filePath, fail: () => {} })
            onEnd()
          })
          audio.onError(() => {
            fs.unlink({ filePath, fail: () => {} })
            onEnd()
          })
          audio.play()
        },
        fail: () => {
          onEnd()
        }
      })
    } else {
      onEnd()
    }
  } catch {
    onEnd()
  }
}

export async function startReading(article: string) {
  // #ifdef H5
  const s = getSynth()
  if (!s) return
  await ensureVoicesReady()
  s.cancel()
  readSentences.value = splitSentences(article)
  readIndex.value = 0
  readState.value = 'playing'
  speakNext()
  // #endif

  // #ifdef MP-WEIXIN
  readSentences.value = splitSentences(article)
  readIndex.value = 0
  readState.value = 'playing'
  speakNext()
  // #endif
}

export function pauseReading() {
  // #ifdef H5
  const s = getSynth()
  if (!s) return
  readState.value = 'paused'
  s.pause()
  // #endif

  // #ifdef MP-WEIXIN
  readState.value = 'paused'
  if (innerAudio) {
    innerAudio.pause()
  }
  // #endif
}

export function resumeReading() {
  // #ifdef H5
  const s = getSynth()
  if (!s) return
  readState.value = 'playing'
  s.resume()
  // #endif

  // #ifdef MP-WEIXIN
  readState.value = 'playing'
  if (innerAudio) {
    innerAudio.play()
  }
  // #endif
}

export function stopReading() {
  // #ifdef H5
  const s = getSynth()
  if (!s) return
  s.cancel()
  readState.value = 'idle'
  readIndex.value = 0
  readSentences.value = []
  // #endif

  // #ifdef MP-WEIXIN
  readState.value = 'idle'
  readIndex.value = 0
  readSentences.value = []
  if (innerAudio) {
    innerAudio.stop()
    innerAudio.destroy()
    innerAudio = null
  }
  // #endif
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