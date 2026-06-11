/**
 * 录音功能封装
 * 使用 MediaRecorder API 录制音频，返回 base64 编码
 */
import { ref } from 'vue'

export function useRecorder() {
  const isRecording = ref(false)
  const audioBase64 = ref('')
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
      // 优先用 wav，否则用 webm
      const mimeType = MediaRecorder.isTypeSupported('audio/wav')
        ? 'audio/wav'
        : 'audio/webm;codecs=opus'

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

  function stopRecording(): Promise<string> {
    return new Promise((resolve) => {
      if (!mediaRecorder || mediaRecorder.state === 'inactive') {
        resolve('')
        return
      }

      mediaRecorder.onstop = async () => {
        const blob = new Blob(audioChunks, { type: mediaRecorder?.mimeType || 'audio/webm' })
        const base64 = await blobToBase64(blob)
        audioBase64.value = base64
        isRecording.value = false

        // 停止所有音轨
        mediaRecorder?.stream.getTracks().forEach(t => t.stop())
        resolve(base64)
      }

      mediaRecorder.stop()
    })
  }

  function blobToBase64(blob: Blob): Promise<string> {
    return new Promise((resolve) => {
      const reader = new FileReader()
      reader.onloadend = () => {
        const result = reader.result as string
        // 去掉 data:audio/xxx;base64, 前缀
        const base64 = result.split(',')[1] || ''
        resolve(base64)
      }
      reader.readAsDataURL(blob)
    })
  }

  return {
    isRecording,
    audioBase64,
    startRecording,
    stopRecording,
  }
}
