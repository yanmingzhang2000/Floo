/**
 * 文章渲染工具 - 将文章文本转换为可交互的 HTML
 *
 * 为什么独立提取：DailyPage 和 DailyDetailPage 有完全相同的 renderArticle 实现，
 * 提取后消除约 18 行重复代码，并确保两处渲染逻辑始终一致。
 */
import type { LearningContent } from '@/types'

/**
 * 将文章内容渲染为带可点击单词的 HTML
 * - 核心词汇用 <mark class="keyword"> 包裹（加粗 + 高亮）
 * - 其他单词用 <span class="clickable-word"> 包裹（可点击查询）
 * - HTML 标签保持原样不处理
 */
export function renderArticle(item: LearningContent): string {
  const words = item.words || []

  // 先用占位符保护 HTML 标签，避免正则误匹配标签内的属性
  let html = item.article.replace(/<[^>]+>/g, (tag) => `___TAG${tag}___`)

  // 把所有英文单词包裹成 span
  html = html.replace(/\b([a-zA-Z]+(?:'[a-zA-Z]+)?)\b/g, (match, word) => {
    const isKey = words.some(w => w.word.toLowerCase() === word.toLowerCase())
    if (isKey) {
      return `<mark class="keyword" data-word="${word}"><strong>${word}</strong></mark>`
    }
    return `<span class="clickable-word" data-word="${word}">${word}</span>`
  })

  // 恢复 HTML 标签
  html = html.replace(/___TAG([^_]+)___/g, '$1')
  return html
}
