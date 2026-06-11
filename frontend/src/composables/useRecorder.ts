/**
 * 录音功能封装
 * 使用 MediaRecorder API 录制音频，转换为 wav 格式的 base64
 */
import { ref } from 'vue'

export function useRecorder() {
  const isRecording = ref(false)
  const audioBase64 = ref('')
  let mediaRecorder: MediaRecorder | null = null
  let audioChunks: Blob[] = []
  let audioContext: AudioContext | null = null

  async function startRecording(): Promise<boolean> {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        }
      })

      audioChunks = []
      // 用 webm 格式录音（浏览器支持最好）
      const mimeType = 'audio/webm;codecs=opus'
      mediaRecorder = new MediaRecorder(stream, { mimeType })

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          audioChunks.push(e.data)
        }
      }

      mediaRecorder.start()
      isRecording.value = true
      return true
    } catch (err) {
      console.error('录音权限获取失败:', err)
      return false
    }
  }

  async function stopRecording(): Promise<string> {
    return new Promise((resolve) => {
      if (!mediaRecorder || mediaRecorder.state === 'inactive') {
        resolve('')
        return
      }

      mediaRecorder.onstop = async () => {
        const blob = new Blob(audioChunks, { type: mediaRecorder?.mimeType || 'audio/webm' })
        // 转换为 wav 格式的 base64
        const wavBase64 = await convertToWav(blob)
        audioBase64.value = wavBase64
        isRecording.value = false

        // 停止所有音轨
        mediaRecorder?.stream.getTracks().forEach(t => t.stop())
        resolve(wavBase64)
      }

      mediaRecorder.stop()
    })
  }

  /**
   * 将音频 blob 转换为 wav 格式的 base64
   */
  async function convertToWav(blob: Blob): Promise<string> {
    try {
      // 创建 AudioContext
      audioContext = new AudioContext({ sampleRate: 16000 })
      
      // 读取音频文件
      const arrayBuffer = await blob.arrayBuffer()
      
      // 解码音频
      const audioBuffer = await audioContext.decodeAudioData(arrayBuffer)
      
      // 转换为 wav
      const wavBuffer = audioBufferToWav(audioBuffer)
      
      // 转为 base64
      const base64 = arrayBufferToBase64(wavBuffer)
      
      return base64
    } catch (err) {
      console.error('WAV转换失败:', err)
      // 转换失败时返回空，让后端使用 mock
      return ''
    }
  }

  /**
   * 将 AudioBuffer 转换为 WAV 格式的 ArrayBuffer
   */
  function audioBufferToWav(buffer: AudioBuffer): ArrayBuffer {
    const numChannels = 1
    const sampleRate = 16000
    const format = 1 // PCM
    const bitDepth = 16

    const bytesPerSample = bitDepth / 8
    const blockAlign = numChannels * bytesPerSample

    const data = buffer.getChannelData(0)
    const dataLength = data.length * bytesPerSample
    const bufferLength = 44 + dataLength

    const arrayBuffer = new ArrayBuffer(bufferLength)
    const view = new DataView(arrayBuffer)

    // WAV 头部
    writeString(view, 0, 'RIFF')
    view.setUint32(4, bufferLength - 8, true)
    writeString(view, 8, 'WAVE')
    writeString(view, 12, 'fmt ')
    view.setUint32(16, 16, true) // fmt chunk size
    view.setUint16(20, format, true)
    view.setUint16(22, numChannels, true)
    view.setUint32(24, sampleRate, true)
    view.setUint32(28, sampleRate * blockAlign, true)
    view.setUint16(32, blockAlign, true)
    view.setUint16(34, bitDepth, true)
    writeString(view, 36, 'data')
    view.setUint32(40, dataLength, true)

    // 写入音频数据
    let offset = 44
    for (let i = 0; i < data.length; i++) {
      const sample = Math.max(-1, Math.min(1, data[i]))
      view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7FFF, true)
      offset += 2
    }

    return arrayBuffer
  }

  function writeString(view: DataView, offset: number, str: string) {
    for (let i = 0; i < str.length; i++) {
      view.setUint8(offset + i, str.charCodeAt(i))
    }
  }

  function arrayBufferToBase64(buffer: ArrayBuffer): string {
    const bytes = new Uint8Array(buffer)
    let binary = ''
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i])
    }
    return btoa(binary)
  }

  return {
    isRecording,
    audioBase64,
    startRecording,
    stopRecording,
  }
}
