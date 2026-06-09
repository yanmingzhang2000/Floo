/**
 * 语音朗读工具 - 使用浏览器内置 Web Speech API
 * 免费、无需外部API、支持多语言
 */

let synth: SpeechSynthesis | null = null

function getSynth(): SpeechSynthesis | null {
  if (typeof window !== 'undefined') {
    synth = window.speechSynthesis || null
  }
  return synth
}

/**
 * 朗读英文单词/句子
 * @param text 要朗读的文本
 * @param lang 语言代码，默认英文
 */
export function speak(text: string, lang = 'en-US') {
  const s = getSynth()
  if (!s) {
    console.warn('SpeechSynthesis not supported')
    return
  }

  // 取消之前的朗读
  s.cancel()

  const utterance = new SpeechSynthesisUtterance(text)
  utterance.lang = lang
  utterance.rate = 0.9  // 稍慢一点，学习用
  utterance.pitch = 1
  utterance.volume = 1

  // 尝试选择英文语音
  const voices = s.getVoices()
  const enVoice = voices.find(v => v.lang.startsWith('en') && v.name.includes('Google'))
    || voices.find(v => v.lang.startsWith('en'))
  if (enVoice) {
    utterance.voice = enVoice
  }

  s.speak(utterance)
}

/**
 * 朗读英文单词（快捷方法）
 */
export function speakWord(word: string) {
  speak(word, 'en-US')
}

// 预加载语音列表（某些浏览器需要）
export function initVoices() {
  const s = getSynth()
  if (s) {
    s.getVoices()
    s.onvoiceschanged = () => s.getVoices()
  }
}
