/**
 * 录音功能封装 - uni-app 版本
 * H5 用 MediaRecorder，小程序用 uni.getRecorderManager
 */
import { ref } from 'vue'

export function useRecorder() {
  const isRecording = ref(false)
  const audioBase64 = ref('')
  
  // #ifdef H5
  let mediaRecorder: MediaRecorder | null = null
  let audioChunks: Blob[] = []

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
        const wavBase64 = await convertToWav(blob)
        audioBase64.value = wavBase64
        isRecording.value = false
        mediaRecorder?.stream.getTracks().forEach(t => t.stop())
        resolve(wavBase64)
      }
      mediaRecorder.stop()
    })
  }

  async function convertToWav(blob: Blob): Promise<string> {
    try {
      const audioContext = new AudioContext({ sampleRate: 16000 })
      const arrayBuffer = await blob.arrayBuffer()
      const audioBuffer = await audioContext.decodeAudioData(arrayBuffer)
      const wavBuffer = audioBufferToWav(audioBuffer)
      const base64 = arrayBufferToBase64(wavBuffer)
      audioContext.close()
      return base64
    } catch (err) {
      console.error('WAV转换失败，走原始格式兜底:', err)
      try {
        const rawBase64 = await blobToBase64(blob)
        return rawBase64
      } catch {
        return ''
      }
    }
  }

  function blobToBase64(blob: Blob): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onloadend = () => {
        const result = reader.result as string
        resolve(result.split(',')[1] || '')
      }
      reader.onerror = reject
      reader.readAsDataURL(blob)
    })
  }

  function audioBufferToWav(buffer: AudioBuffer): ArrayBuffer {
    const numChannels = 1
    const sampleRate = 16000
    const format = 1
    const bitDepth = 16
    const bytesPerSample = bitDepth / 8
    const blockAlign = numChannels * bytesPerSample
    const data = buffer.getChannelData(0)
    const dataLength = data.length * bytesPerSample
    const bufferLength = 44 + dataLength
    const arrayBuffer = new ArrayBuffer(bufferLength)
    const view = new DataView(arrayBuffer)

    writeString(view, 0, 'RIFF')
    view.setUint32(4, bufferLength - 8, true)
    writeString(view, 8, 'WAVE')
    writeString(view, 12, 'fmt ')
    view.setUint32(16, 16, true)
    view.setUint16(20, format, true)
    view.setUint16(22, numChannels, true)
    view.setUint32(24, sampleRate, true)
    view.setUint32(28, sampleRate * blockAlign, true)
    view.setUint16(32, blockAlign, true)
    view.setUint16(34, bitDepth, true)
    writeString(view, 36, 'data')
    view.setUint32(40, dataLength, true)

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
  // #endif

  // #ifdef MP-WEIXIN
  const recorderManager = uni.getRecorderManager()
  let tempFilePath = ''

  async function startRecording(): Promise<boolean> {
    return new Promise((resolve) => {
      recorderManager.onStart(() => {
        isRecording.value = true
        resolve(true)
      })
      recorderManager.onError(() => {
        resolve(false)
      })
      recorderManager.start({
        format: 'mp3',
        sampleRate: 16000,
        numberOfChannels: 1,
      })
    })
  }

  async function stopRecording(): Promise<string> {
    return new Promise((resolve) => {
      recorderManager.onStop((res) => {
        tempFilePath = res.tempFilePath
        isRecording.value = false
        // 小程序录音文件需要上传到服务器，这里返回临时路径
        // 后端需要支持接收文件上传
        uni.getFileSystemManager().readFile({
          filePath: tempFilePath,
          encoding: 'base64',
          success: (fileRes) => {
            audioBase64.value = fileRes.data as string
            resolve(fileRes.data as string)
          },
          fail: () => {
            resolve('')
          },
        })
      })
      recorderManager.stop()
    })
  }
  // #endif

  return {
    isRecording,
    audioBase64,
    startRecording,
    stopRecording,
  }
}