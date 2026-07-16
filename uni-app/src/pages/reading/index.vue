<template>
  <view class="page-container reading-page">
    <!-- 顶部通栏：主题青绿色 + 白色标题 -->
    <view class="rd-header">
      <text class="rd-title">在读</text>
    </view>

    <!-- 二级切换：文字变色 + 底部细短线 -->
    <view class="rd-tabs">
      <view
        class="rd-tab"
        :class="{ active: activeTab === 'ongoing' }"
        @tap="activeTab = 'ongoing'"
      >
        <text>正在学习</text>
        <text v-if="ongoingItems.length" class="rd-tab-count">{{ ongoingItems.length }}</text>
      </view>
      <view
        class="rd-tab"
        :class="{ active: activeTab === 'archived' }"
        @tap="activeTab = 'archived'"
      >
        <text>已读完存档</text>
        <text v-if="archivedItems.length" class="rd-tab-count">{{ archivedItems.length }}</text>
      </view>
    </view>

    <view v-if="loading" class="loading">
      <view class="spinner"></view>
    </view>

    <template v-else>
      <!-- 空态 -->
      <view v-if="currentList.length === 0" class="empty-state">
        <text class="icon">📚</text>
        <text class="empty-text">
          {{ activeTab === 'ongoing' ? '暂无正在学习的读物' : '还没有已读完的存档' }}
        </text>
        <text class="empty-hint" @tap="goLibrary">去图书馆添加素材 ›</text>
      </view>

      <!-- 卡片列表 -->
      <view v-else class="rd-list">
        <view
          v-for="item in currentList"
          :key="item.key"
          class="rd-card"
          @tap="openItem(item)"
        >
          <!-- 标题 -->
          <text class="rd-card-title">{{ item.title }}</text>
          <text v-if="item.subtitle" class="rd-card-subtitle">{{ item.subtitle }}</text>

          <!-- 进度条（突出显示） -->
          <view class="rd-progress">
            <view class="rd-progress-track">
              <view class="rd-progress-fill" :style="{ width: item.progress + '%' }"></view>
            </view>
            <text class="rd-progress-num">{{ item.progress }}%</text>
          </view>

          <!-- 底部：弱化时间 + 操作提示 -->
          <view class="rd-card-footer">
            <text class="rd-time">{{ item.lastReadLabel }}</text>
            <text class="rd-open-hint">
              {{ activeTab === 'ongoing' ? '继续 ›' : '回顾 ›' }}
            </text>
          </view>
        </view>
      </view>
    </template>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { dailyApi, bookApi } from '@/api'
import { useAuthStore } from '@/stores'
import { navTo } from '@/utils/router'
import type { LearningContent } from '@/types'

/**
 * 在读页：全部已保存读物存档
 *
 * 数据来源（前端合成，不加新表）：
 *   - AI 资讯     ：dailyApi.getList → 一篇一个"读物"
 *   - 自定义文稿  ：dailyApi.getCustomContents → 一篇一个"读物"
 *   - 精选书籍    ：bookApi.listMine + bookApi.getChapters → 一本一个"读物"
 *
 * 进度算法：
 *   - 文章类：learned 则 100%，否则 0%
 *   - 书籍类：learned 章节数 / total_chapters * 100
 *
 * 分类算法：
 *   - "正在学习"：进度 < 100
 *   - "已读完存档"：进度 = 100
 *
 * 上次阅读时间：
 *   - 文章类已学 → learned_at
 *   - 书籍类 → 该书任一已学章节的最晚 learned_at
 *   - 都没读过 → content_date（AI 用生成日期）/ 无（书籍空）
 */

// -------- 统一读物模型 --------
interface ReadingItem {
  key: string            // vue :key，用 type + id 组合防止 AI/自定义碰撞
  type: 'ai' | 'custom' | 'book'
  id: number             // content_id 或 series_id
  title: string
  subtitle?: string      // 书籍：作者/章节数；文章：可选简短摘要
  progress: number       // 0-100
  learnedAt: number      // 时间戳，用于排序；0 表示无
  lastReadLabel: string  // 展示文案
  archived: boolean      // 是否已读完
  raw: any               // 原始数据，供 openItem/toggleArchive 用
}

const auth = useAuthStore()
const loading = ref(true)
const items = ref<ReadingItem[]>([])
const activeTab = ref<'ongoing' | 'archived'>('ongoing')

const ongoingItems = computed(() => items.value.filter(i => !i.archived))
const archivedItems = computed(() => items.value.filter(i => i.archived))
const currentList = computed(() =>
  activeTab.value === 'ongoing' ? ongoingItems.value : archivedItems.value,
)

// -------- 主加载 --------
async function loadData() {
  loading.value = true
  const userId = auth.currentUserId
  const safe = <T>(p: Promise<T>): Promise<T | null> => p.catch(() => null)

  // 4 路并行拉取，任一失败不影响其它
  const [aiRes, customRes, bookRes, learnedRes] = await Promise.all([
    safe(dailyApi.getList(300)),
    safe(dailyApi.getCustomContents(userId)),
    safe(bookApi.listMine(userId)),
    safe(dailyApi.getLearnedIds(userId)),
  ])

  // 建立 content_id -> learned_at 映射（毫秒时间戳）
  const learnedMap: Map<number, number> = new Map()
  const learnedItems = learnedRes?.data?.items || []
  for (const it of learnedItems) {
    const ts = it.learned_at ? new Date(it.learned_at).getTime() : 0
    learnedMap.set(it.content_id, Number.isFinite(ts) ? ts : 0)
  }

  // 建立「已打开」集合：只有打开过的内容才出现在读书页
  // 已学完的内容也算打开过（兼容旧数据：learned 但无 opened 记录的情形）
  const openedSet: Set<number> = new Set(learnedRes?.data?.opened_ids || [])
  for (const id of learnedMap.keys()) {
    openedSet.add(id)
  }

  const results: ReadingItem[] = []

  // ---- AI 内容 ----
  const aiList: LearningContent[] = (aiRes?.data as any) || []
  for (const c of aiList) {
    // 只保留 AI（creator_type=0），后端 getList 混着两种，前端过滤一下
    if ((c as any).creator_type === 1) continue
    // 从未打开过的内容不出现在读书页，避免"正在学习"堆满未接触过的文章
    if (!openedSet.has(c.id)) continue
    const learnedAt = learnedMap.get(c.id) ?? -1
    const archived = learnedMap.has(c.id)
    results.push(buildArticleItem('ai', c, archived, learnedAt))
  }

  // ---- 自定义 ----
  const customList: LearningContent[] = customRes?.data?.contents || []
  for (const c of customList) {
    // 同 AI 内容：未打开过的不出现
    if (!openedSet.has(c.id)) continue
    const learnedAt = learnedMap.get(c.id) ?? -1
    const archived = learnedMap.has(c.id)
    results.push(buildArticleItem('custom', c, archived, learnedAt))
  }

  // ---- 书籍 ----
  const books = bookRes?.data?.books || []
  if (books.length > 0) {
    console.debug('[Reading] 拉取书籍章节列表 books=%d', books.length)
    // 并行拉每本书的章节，避免串行等待
    const chapterResults = await Promise.all(
      books.map((b: any) => safe(bookApi.getChapters(b.series_id, userId))),
    )
    for (let i = 0; i < books.length; i++) {
      const book = books[i]
      const chapRes: any = chapterResults[i]
      const chapters: any[] = chapRes?.data?.chapters || []
      // 计算已读章节数 + 该书最晚阅读时间
      let learnedCount = 0
      let lastTs = 0
      for (const ch of chapters) {
        if (learnedMap.has(ch.content_id)) {
          learnedCount++
          const t = learnedMap.get(ch.content_id) || 0
          if (t > lastTs) lastTs = t
        }
      }
      const total = chapters.length || book.total_chapters || 1
      const progress = total > 0 ? Math.round((learnedCount / total) * 100) : 0
      // 书籍规则：只要读过任意章节就展示在"正在学习"，全读完进"已读完存档"
      // 一章都没读的书不出现（还没"加入在读"的语义）
      if (learnedCount === 0) {
        console.debug('[Reading] 书籍 series_id=%s 未开读，跳过', book.series_id)
        continue
      }
      const archived = progress >= 100
      results.push({
        key: `book-${book.series_id}`,
        type: 'book',
        id: book.series_id,
        title: book.name_cn || book.name,
        subtitle: `${learnedCount} / ${total} 章 · ${book.name}`,
        progress,
        learnedAt: lastTs,
        lastReadLabel: lastTs > 0 ? `上次阅读 ${formatDate(lastTs)}` : '尚未开读',
        archived,
        raw: book,
      })
    }
  }

  // 按最近阅读时间倒序（无时间的排最后）
  results.sort((a, b) => b.learnedAt - a.learnedAt)
  items.value = results
  console.debug('[Reading] 读物总数=%d 正在学习=%d 已归档=%d',
    results.length, ongoingItems.value.length, archivedItems.value.length)

  loading.value = false
}

// 文章类"读物"组装
function buildArticleItem(
  type: 'ai' | 'custom',
  c: LearningContent,
  archived: boolean,
  learnedAt: number,
): ReadingItem {
  const progress = archived ? 100 : 0
  // 已学用 learned_at；未学退化用 content_date（生成日期）
  let ts = 0
  let label = ''
  if (learnedAt > 0) {
    ts = learnedAt
    label = `上次阅读 ${formatDate(ts)}`
  } else if (c.content_date) {
    const t = new Date(c.content_date).getTime()
    if (Number.isFinite(t)) ts = t
    label = c.content_date ? `${c.content_date} 加入` : ''
  }
  return {
    key: `${type}-${c.id}`,
    type,
    id: c.id,
    title: c.title,
    subtitle: (c.article || '').slice(0, 60),
    progress,
    learnedAt: ts,
    lastReadLabel: label,
    archived,
    raw: c,
  }
}

// -------- 交互 --------
function openItem(item: ReadingItem) {
  if (item.type === 'book') {
    // 书籍跳章节列表页
    const name = encodeURIComponent(item.title)
    navTo(`/pages/book/chapters?series_id=${item.id}&name=${name}`)
    return
  }
  // 文章直接跳详情
  navTo(`/pages/detail/index?id=${item.id}`)
}

function goLibrary() {
  uni.switchTab({ url: '/pages/learning/index' })
}

// -------- 视觉辅助 --------

// 时间戳 → "MM.DD" 或 "今天"
function formatDate(ts: number): string {
  if (!ts) return ''
  const d = new Date(ts)
  const now = new Date()
  const sameDay = d.getFullYear() === now.getFullYear()
    && d.getMonth() === now.getMonth()
    && d.getDate() === now.getDate()
  if (sameDay) {
    const hh = String(d.getHours()).padStart(2, '0')
    const mi = String(d.getMinutes()).padStart(2, '0')
    return `今天 ${hh}:${mi}`
  }
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${mm}.${dd}`
}

onShow(loadData)
</script>

<style scoped>
.reading-page {
  padding-bottom: 40rpx;
}

/* 顶部通栏：主题青绿色 + 白色标题 */
.rd-header {
  padding: calc(env(safe-area-inset-top, 44px) + 16rpx) 32rpx 24rpx;
  background: var(--primary, #5B9AA8);
  margin: 0 -20rpx 0;
}
.rd-title {
  font-size: 36rpx;
  font-weight: 600;
  color: #fff;
  letter-spacing: 0.5rpx;
}

/* 二级切换：文字变色 + 极细短线 */
.rd-tabs {
  display: flex;
  background: #fff;
  padding: 0 20rpx;
  margin: 0 -20rpx 24rpx;
}
.rd-tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
  padding: 24rpx 0;
  font-size: 28rpx;
  color: #b0b8c0;
  font-weight: 500;
  position: relative;
}
.rd-tab.active {
  color: var(--primary);
  font-weight: 700;
}
.rd-tab.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 25%;
  right: 25%;
  height: 3rpx;
  border-radius: 2rpx;
  background: var(--primary);
}
.rd-tab-count {
  font-size: 20rpx;
  padding: 2rpx 10rpx;
  background: rgba(91,154,168,0.12);
  border-radius: 16rpx;
  font-weight: 600;
  color: var(--primary);
}

/* 卡片列表 */
.rd-list {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
  padding: 0 4rpx;
}
.rd-card {
  padding: 28rpx;
  background: #ffffff;
  box-shadow: 0 2rpx 12rpx rgba(91, 154, 168, 0.10);
  border-radius: 24rpx;
  display: flex;
  flex-direction: column;
  gap: 14rpx;
  transition: transform 0.15s;
}
.rd-card:active {
  transform: scale(0.98);
}

.rd-card-title {
  font-size: 32rpx;
  font-weight: 700;
  line-height: 1.35;
  color: var(--on-surface);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.rd-card-subtitle {
  font-size: 24rpx;
  color: var(--on-surface-variant);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 进度条（突出） */
.rd-progress {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-top: 4rpx;
}
.rd-progress-track {
  flex: 1;
  height: 10rpx;
  background: #e4eff2;
  border-radius: 5rpx;
  overflow: hidden;
}
.rd-progress-fill {
  height: 100%;
  background: var(--primary);
  border-radius: 5rpx;
  transition: width 0.4s ease;
}
.rd-progress-num {
  font-size: 26rpx;
  color: var(--primary);
  font-weight: 700;
  min-width: 60rpx;
  text-align: right;
}

.rd-card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 4rpx;
}
.rd-time {
  font-size: 22rpx;
  color: #b0b8c0;
}
.rd-open-hint {
  font-size: 26rpx;
  color: var(--primary);
  font-weight: 600;
}
</style>
