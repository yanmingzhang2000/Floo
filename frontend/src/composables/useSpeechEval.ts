/**
 * 语音评测工具 - 录音、停止、发送后端评测、评分展示
 *
 * 为什么独立提取：DailyPage 和 DailyDetailPage 有几乎相同的录音评测逻辑
 * （startEval/resetEval/getScoreClass + 录音状态管理），提取后消除约 50 行重复代码。
 *
 * 设计决策：通过 getArticleText 回调注入当前文章文本，避免在 composable 内部
 * 依赖特定的数据源（currentItem.value.article 或 content.value.article）。
 */
import { ref } from 'vue'
import { speechApi } from '@/api'
import { useRecorder } from '@/composables/useRecorder'

export interface EvalResult {
  overall: number
  pronunciation: number
  fluency: number
  integrity: number
  suggestion: string
}

/**
 * @param getArticleText 获取当前文章原文的回调函数
 */
export function useSpeechEval(getArticleText: () => string | undefined) {
  const { isRecording, startRecording, stopRecording } = useRecorder()

  const evalResult = ref<EvalResult | null>(null)
  const recordingTime = ref(0)
  let recordingTimer: ReturnType<typeof setInterval> | null = null

  // ===== 开始/停止录音并评测 =====
  async function startEval() {
    if (isRecording.value) {
      // 正在录音 → 停止并发送评测
      const audioBase64 = await stopRecording()
      if (recordingTimer) {
        clearInterval(recordingTimer)
        recordingTimer = null
      }

      if (!audioBase64) return

      const articleText = getArticleText()
      if (!articleText) return

      try {
        const { data } = await speechApi.evaluate(audioBase64, articleText, 'en')
        // 兼容后端返回 error 字段的情况
        if (data.error) {
          evalResult.value = { overall: 0, pronunciation: 0, fluency: 0, integrity: 0, suggestion: data.error }
        } else {
          evalResult.value = {
            overall: data.overall,
            pronunciation: data.pronunciation,
            fluency: data.fluency,
            integrity: data.integrity,
            suggestion: data.suggestion,
          }
        }
      } catch {
        evalResult.value = { overall: 0, pronunciation: 0, fluency: 0, integrity: 0, suggestion: '评测失败，请稍后重试' }
      }
      return
    }

    // 未在录音 → 开始录音
    const started = await startRecording()
    if (!started) return

    recordingTime.value = 0
    recordingTimer = setInterval(() => { recordingTime.value++ }, 1000)
  }

  // ===== 重置评测状态 =====
  function resetEval() {
    evalResult.value = null
    recordingTime.value = 0
  }

  // ===== 根据分数返回 CSS 类名 =====
  function getScoreClass(score: number): string {
    if (score >= 90) return 'score-excellent'
    if (score >= 80) return 'score-good'
    if (score >= 70) return 'score-ok'
    if (score >= 60) return 'score-fair'
    return 'score-poor'
  }

  return {
    isRecording,
    evalResult,
    recordingTime,
    startEval,
    resetEval,
    getScoreClass,
  }
}
