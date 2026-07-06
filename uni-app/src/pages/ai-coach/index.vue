<template>
  <view class="page-container">
    <view class="nav-bar">
      <view class="nav-left">
        <text class="nav-logo">AI陪练</text>
      </view>
      <view class="nav-right">
        <view class="nav-icon-btn" @tap="goBack">
          <text>✕</text>
        </view>
      </view>
    </view>

    <view class="chat-container">
      <!-- 对话历史 -->
      <scroll-view class="chat-scroll" scroll-y :scroll-top="scrollTop">
        <view class="chat-messages">
          <view v-for="(msg, index) in messages" :key="index" class="message" :class="msg.role">
            <view class="message-bubble">
              <text class="message-text">{{ msg.text }}</text>
              <text class="message-lang" v-if="msg.lang">{{ msg.lang === 'zh' ? '中文' : 'English' }}</text>
            </view>
          </view>
          
          <!-- AI思考中 -->
          <view v-if="isThinking" class="message assistant">
            <view class="message-bubble">
              <text class="message-text">思考中...</text>
            </view>
          </view>
        </view>
      </scroll-view>

      <!-- 状态提示 -->
      <view class="status-bar">
        <text class="status-text">{{ statusText }}</text>
      </view>
    </view>

    <!-- 底部控制区 -->
    <view class="control-area">
      <!-- 录音按钮 -->
      <view 
        class="record-btn" 
        :class="{ recording: isRecording, disabled: isProcessing }"
        @tap="toggleRecording"
      >
        <view class="record-btn-inner">
          <text class="record-icon">{{ isRecording ? '⏹️' : '🎙️' }}</text>
          <text class="record-text">{{ isRecording ? '点击结束' : '点击说话' }}</text>
        </view>
      </view>

      <!-- 提示文字 -->
      <text class="hint-text">
        {{ statusText }}
      </text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, onUnmounted } from 'vue'
import { navTo } from '@/utils/router'
import { aiCoachApi } from '@/api'
import { useAuthStore } from '@/stores'

const auth = useAuthStore()
const messages = ref<Array<{role: 'user' | 'assistant', text: string, lang?: string}>>([])
const isRecording = ref(false)
const isThinking = ref(false)
const isProcessing = ref(false)
const statusText = ref('准备就绪')
const scrollTop = ref(0)
const sessionId = ref(`session_${Date.now()}`)

let recorderManager: any = null
let audioInnerAudioContext: any = null
let mediaRecorder: any = null
let audioChunks: Blob[] = []
let mediaStream: any = null

const isH5 = typeof window !== 'undefined' && typeof navigator !== 'undefined'

// 初始化录音
function initRecorder() {
  if (isH5) {
    // H5环境使用 MediaRecorder
    console.log('使用 H5 MediaRecorder')
    return
  }
  
  // 小程序/App环境使用 uni.getRecorderManager
  recorderManager = uni.getRecorderManager()
  
  recorderManager.onStop((res: any) => {
    console.log('录音停止', res)
    if (res.tempFilePath) {
      processAudio(res.tempFilePath)
    }
  })

  recorderManager.onError((err: any) => {
    console.error('录音错误', err)
    statusText.value = '录音失败，请重试'
    isRecording.value = false
  })
}

// 切换录音状态
async function toggleRecording() {
  if (isProcessing.value) return
  
  if (isRecording.value) {
    // 当前正在录音，停止
    stopRecording()
  } else {
    // 当前未录音，开始
    await startRecording()
  }
}

// 开始录音
async function startRecording() {
  isRecording.value = true
  statusText.value = '正在聆听... 点击按钮结束'
  
  if (isH5) {
    try {
      // H5环境获取麦克风权限
      mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true })
      audioChunks = []
      
      mediaRecorder = new MediaRecorder(mediaStream)
      
      mediaRecorder.ondataavailable = (event: any) => {
        if (event.data.size > 0) {
          audioChunks.push(event.data)
        }
      }
      
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/mp3' })
        const reader = new FileReader()
        reader.onloadend = () => {
          const base64 = (reader.result as string).split(',')[1]
          processAudioBase64(base64)
        }
        reader.readAsDataURL(audioBlob)
      }
      
      mediaRecorder.start()
    } catch (error) {
      console.error('获取麦克风权限失败', error)
      statusText.value = '请允许麦克风权限'
      isRecording.value = false
    }
    return
  }
  
  // 小程序/App环境
  const options = {
    duration: 30000,
    sampleRate: 16000,
    numberOfChannels: 1,
    format: 'mp3',
    encodeBitRate: 96000
  }
  
  recorderManager.start(options)
}

// 停止录音
function stopRecording() {
  if (!isRecording.value) return
  
  isRecording.value = false
  isProcessing.value = true
  statusText.value = '识别中...'
  
  if (isH5) {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop()
    }
    if (mediaStream) {
      mediaStream.getTracks().forEach((track: any) => track.stop())
    }
    return
  }
  
  recorderManager.stop()
}

// 取消录音（保留给异常情况）
function cancelRecording() {
  if (!isRecording.value) return
  
  isRecording.value = false
  isProcessing.value = false
  statusText.value = '已取消'
  
  if (isH5) {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop()
    }
    if (mediaStream) {
      mediaStream.getTracks().forEach((track: any) => track.stop())
    }
    return
  }
  
  recorderManager.stop()
}

// 处理音频文件路径（小程序/App环境）
async function processAudio(filePath: string) {
  try {
    statusText.value = '语音识别中...'
    const sttResult = await callSTT(filePath)
    
    if (!sttResult.text) {
      statusText.value = '未识别到内容，请重试'
      isProcessing.value = false
      return
    }
    
    messages.value.push({
      role: 'user',
      text: sttResult.text,
      lang: sttResult.lang
    })
    
    scrollToBottom()
    
    statusText.value = '思考中...'
    isThinking.value = true
    
    const llmResult = await callLLM(sttResult.text, sttResult.lang)
    
    isThinking.value = false
    
    messages.value.push({
      role: 'assistant',
      text: llmResult.reply,
      lang: llmResult.lang
    })
    
    scrollToBottom()
    
    statusText.value = '播放中...'
    await playTTS(llmResult.reply, llmResult.lang)
    
    statusText.value = '准备就绪'
    
  } catch (error) {
    console.error('处理失败', error)
    statusText.value = '处理失败，请重试'
  } finally {
    isProcessing.value = false
    isThinking.value = false
  }
}

// 处理音频base64数据
async function processAudioBase64(base64Audio: string) {
  try {
    // 1. 语音转文字 + 语言检测
    statusText.value = '语音识别中...'
    const sttResult = await callSTTFromBase64(base64Audio)
    
    if (!sttResult.text) {
      statusText.value = '未识别到内容，请重试'
      isProcessing.value = false
      return
    }
    
    // 添加用户消息
    messages.value.push({
      role: 'user',
      text: sttResult.text,
      lang: sttResult.lang
    })
    
    scrollToBottom()
    
    // 2. 调用LLM获取回复
    statusText.value = '思考中...'
    isThinking.value = true
    
    const llmResult = await callLLM(sttResult.text, sttResult.lang)
    
    isThinking.value = false
    
    // 添加AI回复
    messages.value.push({
      role: 'assistant',
      text: llmResult.reply,
      lang: llmResult.lang
    })
    
    scrollToBottom()
    
    // 3. TTS播放回复
    statusText.value = '播放中...'
    await playTTS(llmResult.reply, llmResult.lang)
    
    statusText.value = '准备就绪'
    
  } catch (error) {
    console.error('处理失败', error)
    statusText.value = '处理失败，请重试'
  } finally {
    isProcessing.value = false
    isThinking.value = false
  }
}

// 调用STT API
async function callSTT(filePath: string): Promise<{text: string, lang: string}> {
  try {
    // 读取音频文件为base64
    const base64Audio = await readFileAsBase64(filePath)
    
    // 调用后端API
    const response = await aiCoachApi.transcribe(base64Audio, 'mp3')
    
    if (response.data && response.data.success) {
      return {
        text: response.data.text,
        lang: response.data.lang || 'en'
      }
    }
    
    throw new Error(response.data?.error || '识别失败')
  } catch (error) {
    console.error('STT调用失败', error)
    throw error
  }
}

// 从base64调用STT API
async function callSTTFromBase64(base64Audio: string): Promise<{text: string, lang: string}> {
  try {
    const response = await aiCoachApi.transcribe(base64Audio, 'mp3')
    
    if (response.data && response.data.success) {
      return {
        text: response.data.text,
        lang: response.data.lang || 'en'
      }
    }
    
    throw new Error(response.data?.error || '识别失败')
  } catch (error) {
    console.error('STT调用失败', error)
    throw error
  }
}

// 调用LLM API
async function callLLM(text: string, lang: string): Promise<{reply: string, lang: string}> {
  try {
    // 构建对话历史
    const history = messages.value.map(msg => ({
      role: msg.role,
      content: msg.text
    }))
    
    // 调用后端API
    const response = await aiCoachApi.chat(text, lang, history)
    
    if (response.data && response.data.success) {
      return {
        reply: response.data.reply,
        lang: response.data.lang || lang
      }
    }
    
    throw new Error(response.data?.error || '回复失败')
  } catch (error) {
    console.error('LLM调用失败', error)
    throw error
  }
}

// 播放TTS
async function playTTS(text: string, lang: string): Promise<void> {
  try {
    // 调用后端API获取音频
    const response = await aiCoachApi.tts(text, lang)
    
    if (response.data && response.data.success && response.data.audio) {
      // 播放音频
      await playAudio(response.data.audio)
      return
    }
    
    throw new Error(response.data?.error || 'TTS失败')
  } catch (error) {
    console.error('TTS调用失败', error)
    // TTS失败不影响对话流程
  }
}

// 播放音频
function playAudio(base64Audio: string): Promise<void> {
  return new Promise((resolve, reject) => {
    try {
      // 创建音频上下文
      audioInnerAudioContext = uni.createInnerAudioContext()
      
      // 设置音频源
      audioInnerAudioContext.src = `data:audio/mp3;base64,${base64Audio}`
      
      // 监听播放结束
      audioInnerAudioContext.onEnded(() => {
        audioInnerAudioContext?.destroy()
        audioInnerAudioContext = null
        resolve()
      })
      
      // 监听错误
      audioInnerAudioContext.onError((err: any) => {
        console.error('音频播放错误', err)
        audioInnerAudioContext?.destroy()
        audioInnerAudioContext = null
        reject(err)
      })
      
      // 开始播放
      audioInnerAudioContext.play()
    } catch (error) {
      reject(error)
    }
  })
}

// 读取文件为base64
function readFileAsBase64(filePath: string): Promise<string> {
  return new Promise((resolve, reject) => {
    // #ifdef H5
    // H5环境需要通过XMLHttpRequest读取
    const xhr = new XMLHttpRequest()
    xhr.open('GET', filePath, true)
    xhr.responseType = 'arraybuffer'
    xhr.onload = function() {
      const arrayBuffer = xhr.response
      const uint8Array = new Uint8Array(arrayBuffer)
      let binary = ''
      for (let i = 0; i < uint8Array.byteLength; i++) {
        binary += String.fromCharCode(uint8Array[i])
      }
      const base64 = uni.arrayBufferToBase64(binary)
      resolve(base64)
    }
    xhr.onerror = function() {
      reject(new Error('读取文件失败'))
    }
    xhr.send()
    // #endif
    
    // #ifndef H5
    // 非H5环境直接返回路径，后端会处理
    resolve(filePath)
    // #endif
  })
}

function scrollToBottom() {
  nextTick(() => {
    // 确保 scroll-view 已挂载
    const scrollView = document.querySelector('.chat-scroll')
    if (scrollView) {
      scrollTop.value = scrollTop.value + 1
    }
  })
}

function goBack() {
  // 销毁音频上下文
  if (audioInnerAudioContext) {
    audioInnerAudioContext.destroy()
  }
  uni.navigateBack()
}

// 组件卸载时清理
onUnmounted(() => {
  if (audioInnerAudioContext) {
    audioInnerAudioContext.destroy()
  }
})

// 初始化
initRecorder()
</script>

<style scoped>
.page-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: linear-gradient(135deg, #e8f4f8, #f0f4f8, #e8f0f4, #f4f0e8);
  background-size: 400% 400%;
  animation: gradientFlow 15s ease infinite;
}

@keyframes gradientFlow {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.nav-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24rpx;
  height: 88rpx;
  background: var(--primary);
}

.nav-left {
  display: flex;
  align-items: center;
}

.nav-logo {
  font-size: 34rpx;
  font-weight: 700;
  color: #fff;
}

.nav-right {
  display: flex;
  align-items: center;
}

.nav-icon-btn {
  width: 56rpx;
  height: 56rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
  color: #fff;
  border-radius: 50%;
  background: rgba(255,255,255,0.15);
}
.nav-icon-btn:active { background: rgba(255,255,255,0.3); }

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-scroll {
  flex: 1;
  padding: 24rpx;
}

.chat-messages {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.message {
  display: flex;
}

.message.user {
  justify-content: flex-end;
}

.message.assistant {
  justify-content: flex-start;
}

.message-bubble {
  max-width: 80%;
  padding: 20rpx 28rpx;
  border-radius: 24rpx;
  background: #fff;
  box-shadow: var(--shadow-sm);
}

.message.user .message-bubble {
  background: var(--primary);
  border-bottom-right-radius: 8rpx;
}

.message.assistant .message-bubble {
  background: #fff;
  border-bottom-left-radius: 8rpx;
}

.message-text {
  font-size: 28rpx;
  color: var(--on-surface);
  line-height: 1.5;
}

.message.user .message-text {
  color: #fff;
}

.message-lang {
  display: block;
  font-size: 20rpx;
  color: var(--on-surface-muted);
  margin-top: 8rpx;
}

.message.user .message-lang {
  color: rgba(255,255,255,0.7);
}

.status-bar {
  padding: 12rpx 24rpx;
  background: var(--surface);
  border-top: 1rpx solid var(--outline);
}

.status-text {
  font-size: 24rpx;
  color: var(--on-surface-variant);
  text-align: center;
}

.control-area {
  padding: 32rpx 24rpx;
  padding-bottom: calc(32rpx + env(safe-area-inset-bottom));
  background: var(--surface);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16rpx;
}

.record-btn {
  width: 160rpx;
  height: 160rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 24rpx rgba(91,154,168,0.4);
  transition: transform 0.15s, box-shadow 0.15s;
}

.record-btn:active {
  transform: scale(0.95);
  box-shadow: 0 4rpx 12rpx rgba(91,154,168,0.3);
}

.record-btn.recording {
  background: linear-gradient(135deg, #E53935 0%, #C62828 100%);
  box-shadow: 0 8rpx 24rpx rgba(229,57,53,0.4);
  animation: pulse 1.5s infinite;
}

.record-btn.disabled {
  opacity: 0.5;
  pointer-events: none;
}

.record-btn-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
}

.record-icon {
  font-size: 48rpx;
}

.record-text {
  font-size: 20rpx;
  color: #fff;
  font-weight: 600;
}

.hint-text {
  font-size: 24rpx;
  color: var(--on-surface-muted);
}

@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
}
</style>
