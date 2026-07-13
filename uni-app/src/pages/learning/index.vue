<template>
  <view class="page-container library-page">
    <!-- 顶部通栏：仅保留标题，移除搜索图标 -->
    <view class="lib-header">
      <text class="lib-title">图书馆</text>
    </view>

    <view v-if="loading" class="loading">
      <view class="spinner"></view>
    </view>

    <template v-else>
      <!-- 二级分类横向滑动标签 -->
      <scroll-view class="lib-tabs" scroll-x show-scrollbar="false">
        <view class="lib-tabs-inner">
          <view
            v-for="t in tabDefs"
            :key="t.value"
            class="lib-tab"
            :class="{ active: activeTab === t.value }"
            @tap="switchTab(t.value)"
          >
            <text>{{ t.label }}</text>
          </view>
        </view>
      </scroll-view>

      <!-- ====== AI 资讯 Tab ====== -->
      <view v-if="activeTab === 'ai'" class="lib-section">
        <view v-if="contents.length === 0" class="empty-state">
          <text class="icon">📰</text>
          <text class="empty-text">今日还没有 AI 资讯</text>
          <text
            class="empty-action"
            :class="{ disabled: generating || remainingCount <= 0 }"
            @tap="handleGenerate"
          >{{ generating ? '生成中...' : (remainingCount > 0 ? `生成今日资讯 (${remainingCount})` : '今日次数已用完') }}</text>
        </view>
        <view v-else class="lib-list">
          <view class="lib-section-hint-row">
            <text
              class="lib-refresh-btn"
              :class="{ disabled: generating || remainingCount <= 0 }"
              @tap="handleGenerate"
            >{{ remainingCount > 0 ? `换一批 (${remainingCount})` : '今日已用完' }}</text>
          </view>
          <view
            v-for="item in contents"
            :key="item.id"
            class="lib-card"
            @tap="goDetail(item.id)"
          >
            <view class="lib-card-body">
              <view class="lib-card-header">
                <text class="tag tag-ai">{{ themeLabels[item.theme_type] || item.theme_type }}</text>
              </view>
              <text class="lib-card-title">{{ item.title }}</text>
              <text class="lib-card-desc">{{ (item.article || '').slice(0, 80) }}...</text>
              <view class="lib-card-footer">
                <text class="lib-card-action" @tap.stop="goDetail(item.id)">开始阅读</text>
              </view>
            </view>
          </view>
        </view>
      </view>

      <!-- ====== 自定义文稿 Tab ====== -->
      <view v-if="activeTab === 'custom'" class="lib-section">
        <!-- 空态：仅显示一张"新建"大卡片 -->
        <view v-if="customContents.length === 0" class="lib-new-card" @tap="showCustomContent = true">
          <text class="lib-new-plus">＋</text>
          <text class="lib-new-title">创建我的学习文稿</text>
          <text class="lib-new-hint">粘贴或上传英文文本，AI 自动生成词组、译文</text>
        </view>
        <template v-else>
          <view class="lib-section-hint-row">
            <text class="lib-refresh-btn" @tap="showCustomContent = true">+ 新建文稿</text>
          </view>
          <view class="lib-list">
            <view
              v-for="item in customContents"
              :key="item.id"
              class="lib-card"
            >
              <view class="lib-card-body">
                <view class="lib-card-header">
                  <text class="tag tag-warning">自定义</text>
                  <text v-if="isGenerationFailed(item)" class="tag tag-error">生成失败</text>
                </view>
                <text class="lib-card-title" @tap="goDetail(item.id)">{{ item.title }}</text>
                <text class="lib-card-desc" @tap="goDetail(item.id)">{{ (item.article || '').slice(0, 80) }}...</text>
                <view v-if="isGenerationFailed(item)" class="lib-card-fail-row">
                  <text class="lib-card-fail-hint">译文或词组生成失败</text>
                  <text
                    class="lib-card-action"
                    :class="{ disabled: regeneratingIds.includes(item.id) }"
                    @tap.stop="regenerateCustom(item.id)"
                  >{{ regeneratingIds.includes(item.id) ? '重生成中...' : '重新生成' }}</text>
                </view>
                <view v-else class="lib-card-footer">
                  <text class="lib-card-action" @tap.stop="goDetail(item.id)">开始阅读</text>
                  <text class="lib-card-action-secondary" @tap.stop="deleteCustomContent(item.id)">删除</text>
                </view>
              </view>
            </view>
          </view>
        </template>
      </view>

      <!-- ====== 精选书籍 Tab ====== -->
      <view v-if="activeTab === 'book'" class="lib-section">
        <view v-if="myBooks.length === 0" class="empty-state">
          <text class="icon">📚</text>
          <text class="empty-text">暂无精选书籍</text>
          <text class="empty-hint">书籍精读采用白名单授权，敬请期待</text>
        </view>
        <view v-else class="lib-list">
          <view
            v-for="book in myBooks"
            :key="book.series_id"
            class="lib-book-card"
            @tap="goBook(book)"
          >
            <!-- 封面线稿 SVG 占位 -->
            <view class="lib-book-cover">
              <svg viewBox="0 0 100 130" xmlns="http://www.w3.org/2000/svg">
                <rect x="14" y="10" width="72" height="110" rx="4"
                      fill="#F0F9FF" stroke="#5B9AA8" stroke-width="1.5"/>
                <path d="M14 10 L14 120" stroke="#5B9AA8" stroke-width="1" opacity="0.4"/>
                <path d="M28 32 L72 32" stroke="#5B9AA8" stroke-width="1" opacity="0.5"/>
                <path d="M28 44 L64 44" stroke="#5B9AA8" stroke-width="1" opacity="0.4"/>
                <path d="M28 56 L68 56" stroke="#5B9AA8" stroke-width="1" opacity="0.3"/>
                <path d="M28 68 L60 68" stroke="#5B9AA8" stroke-width="1" opacity="0.3"/>
              </svg>
            </view>
            <view class="lib-book-info">
              <text class="lib-book-title">{{ book.name_cn || book.name }}</text>
              <text v-if="book.name_cn && book.name !== book.name_cn" class="lib-book-en">{{ book.name }}</text>
              <text class="lib-book-desc">{{ book.total_chapters }} 章</text>
              <view class="lib-book-footer">
                <text class="lib-card-action" @tap.stop="goBook(book)">加入在读</text>
              </view>
            </view>
          </view>
          <text class="lib-book-more-hint">更多英文读物持续更新</text>
        </view>
      </view>
    </template>

    <!-- 自定义内容弹窗 -->
    <CustomContentModal :visible="showCustomContent" @close="showCustomContent = false" @created="onCustomCreated" />
    <OnboardingGuide />
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { dailyApi, generationLimitApi, bookApi } from '@/api'
import { useAuthStore } from '@/stores'
import { navTo } from '@/utils/router'
import { storage } from '@/utils/storage'
import type { LearningContent } from '@/types'
import CustomContentModal from '@/components/CustomContentModal.vue'
import OnboardingGuide from '@/components/OnboardingGuide.vue'

/**
 * 图书馆页：素材广场，用户在这里找新内容
 *
 * 3 个 tab：
 *   - ai     ：AI 生成的每日资讯
 *   - custom ：用户自定义文稿（支持粘贴/上传）
 *   - book   ：精选书籍（白名单授权，未授权空态）
 *
 * 原 learning 页的"往期内容"tab 已迁移到「在读」页，
 * 底部固定 CTA 也已删除，符合"素材广场"的定位。
 */

const auth = useAuthStore()
const loading = ref(true)
const generating = ref(false)
const contents = ref<LearningContent[]>([])
const customContents = ref<LearningContent[]>([])
const learnedIds = ref<number[]>([])
const remainingCount = ref(3)
const showCustomContent = ref(false)
const regeneratingIds = ref<number[]>([])

interface MyBook { series_id: number; name: string; name_cn?: string; total_chapters: number }
const myBooks = ref<MyBook[]>([])

type TabKey = 'ai' | 'custom' | 'book'
const activeTab = ref<TabKey>('ai')

const tabDefs: Array<{ value: TabKey; label: string }> = [
  { value: 'ai',     label: 'AI 资讯' },
  { value: 'custom', label: '自定义文稿' },
  { value: 'book',   label: '精选书籍' },
]

const themeLabels: Record<string, string> = {
  ai_tech: 'AI科技', product_tech: '产品技术', business: '财经商业',
  daily_news: '日常新闻', self_growth: '个人成长', all_random: '随机',
  custom: '自定义',
}

// 判断自定义内容是否生成失败（译文降级或词组为空）
// 后端降级文案固定以「（翻译生成失败」开头，见 backend/app/routers/daily.py:691
function isGenerationFailed(item: LearningContent): boolean {
  const tr = (item.translation || '').trim()
  const failedTranslation = !tr || tr.startsWith('（翻译生成失败')
  const emptyWords = !item.words || item.words.length === 0
  return failedTranslation || emptyWords
}

onLoad(() => {
  // 从 storage 读取外部传入的 tab 参数（如从首页跳转带过来的偏好）
  const savedTab = storage.get('learning_active_tab')
  if (savedTab && ['ai', 'custom', 'book'].includes(savedTab)) {
    activeTab.value = savedTab as TabKey
  }
  storage.remove('learning_active_tab')
})

function switchTab(tab: TabKey) {
  activeTab.value = tab
  // 首次进入某个 tab 才拉数据，避免每次切换重复请求
  if (tab === 'custom' && customContents.value.length === 0) {
    console.debug('[Library] 首次进入自定义 tab，加载列表')
    loadCustomContents()
  }
  // book tab 数据在 loadData 里已经拉过（一次请求已完成，不需要再拉）
}

async function loadData() {
  loading.value = true
  const userId = auth.currentUserId
  const safe = (p: Promise<any>) => p.catch(() => null)

  // 并行拉今日 AI 内容 / 生成次数 / 已学 ID / 授权书籍
  // 书籍列表也放这里预取：即使当前 tab 不是 book，切过去时也不用等
  const [contentRes, limitRes, learnedRes, bookRes] = await Promise.all([
    safe(dailyApi.getTodayList(userId)),
    safe(generationLimitApi.getLimit(userId)),
    safe(dailyApi.getLearnedIds(userId)),
    safe(bookApi.listMine(userId)),
  ])

  if (contentRes?.data) contents.value = contentRes.data.contents || []
  if (learnedRes?.data) learnedIds.value = learnedRes.data.content_ids || []
  if (limitRes?.data) remainingCount.value = limitRes.data.remaining_count ?? 3
  if (bookRes?.data) myBooks.value = bookRes.data.books || []

  loading.value = false
}

async function loadCustomContents() {
  const userId = auth.currentUserId
  try {
    const { data } = await dailyApi.getCustomContents(userId)
    customContents.value = data?.contents || []
  } catch {
    console.debug('[Library] 自定义内容加载失败，置空')
    customContents.value = []
  }
}

function onCustomCreated() {
  // 创建成功后切到自定义 tab 并刷新列表
  activeTab.value = 'custom'
  loadCustomContents()
}

async function regenerateCustom(contentId: number) {
  if (regeneratingIds.value.includes(contentId)) {
    // 防止重复点击：同一条正在重新生成时忽略
    console.debug('[Library] 该内容正在重生成，忽略重复点击 content_id=%s', contentId)
    return
  }
  const userId = auth.currentUserId
  regeneratingIds.value.push(contentId)
  uni.showLoading({ title: '重新生成中...', mask: true })
  try {
    await dailyApi.regenerateCustomContent(contentId, userId)
    await loadCustomContents()
    uni.hideLoading()
    uni.showToast({ title: '重新生成成功', icon: 'success' })
  } catch (e: any) {
    // AI 仍然失败时后端返回 503，其它是网络/服务异常
    console.debug('[Library] 重生成失败 content_id=%s err=%o', contentId, e)
    uni.hideLoading()
    const detail = e?.data?.detail || e?.errMsg || '重新生成失败'
    uni.showToast({ title: detail, icon: 'none', duration: 2500 })
  } finally {
    regeneratingIds.value = regeneratingIds.value.filter(id => id !== contentId)
  }
}

async function deleteCustomContent(contentId: number) {
  const userId = auth.currentUserId
  uni.showModal({
    title: '确认删除',
    content: '删除后无法恢复，关联的复习记录也将清除',
    success: async (res) => {
      if (res.confirm) {
        try {
          await dailyApi.deleteCustomContent(contentId, userId)
          customContents.value = customContents.value.filter(c => c.id !== contentId)
          uni.showToast({ title: '已删除', icon: 'success' })
        } catch {
          console.debug('[Library] 自定义内容删除失败 content_id=%s', contentId)
          uni.showToast({ title: '删除失败', icon: 'none' })
        }
      } else {
        console.debug('[Library] 用户取消删除 content_id=%s', contentId)
      }
    },
  })
}

async function handleGenerate() {
  if (remainingCount.value <= 0) {
    console.debug('[Library] 今日生成次数已用完，拦截')
    uni.showToast({ title: '今日生成次数已用完', icon: 'none' })
    return
  }
  generating.value = true
  try {
    const res: any = await dailyApi.generate(auth.currentUserId)
    if (res.statusCode && res.statusCode >= 400) {
      const msg = res.data?.detail || res.data?.message || `请求失败 (${res.statusCode})`
      console.debug('[Library] AI 生成返回错误 status=%s msg=%s', res.statusCode, msg)
      uni.showToast({ title: msg, icon: 'none' })
      generating.value = false
      return
    }
    await loadData()
  } catch (e: any) {
    console.debug('[Library] AI 生成异常 err=%o', e)
    const msg = e?.errMsg || e?.message || '网络异常'
    uni.showToast({ title: msg, icon: 'none' })
  }
  generating.value = false
}

function goDetail(id: number) { navTo(`/pages/detail/index?id=${id}`) }

function goBook(book: MyBook) {
  // 「加入在读」= 直接跳该书章节页开始阅读
  // 只要读过任意章节，该书就会在「在读」页出现
  const name = encodeURIComponent(book.name_cn || book.name)
  navTo(`/pages/book/chapters?series_id=${book.series_id}&name=${name}`)
}

onShow(loadData)
</script>

<style scoped>
/* 图书馆页整体：浅色底 + 上下留白 */
.library-page {
  padding-bottom: 40rpx;
}

/* ---- 顶部通栏 ---- */
.lib-header {
  display: flex;
  align-items: center;
  padding: calc(env(safe-area-inset-top, 44px) + 16rpx) 32rpx 24rpx;
  background: var(--primary, #5B9AA8);
  margin: 0 -20rpx 0;
}
.lib-title {
  font-size: 36rpx;
  font-weight: 600;
  color: #fff;
  letter-spacing: 0.5rpx;
}

/* ---- 二级 tab 横向滑动（极简细线） ---- */
.lib-tabs {
  background: #fff;
  white-space: nowrap;
  margin: 0 -20rpx 32rpx;
}
.lib-tabs-inner {
  display: inline-flex;
  padding: 0 20rpx;
  gap: 8rpx;
}
.lib-tab {
  flex-shrink: 0;
  padding: 20rpx 24rpx;
  font-size: 28rpx;
  font-weight: 500;
  color: #b0b8c0;
  position: relative;
  transition: color 0.2s;
}
.lib-tab.active {
  color: var(--primary);
  font-weight: 700;
}
.lib-tab.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 28rpx;
  right: 28rpx;
  height: 3rpx;
  border-radius: 2rpx;
  background: var(--primary);
}

/* ---- 内容分区 ---- */
.lib-section { padding: 0 4rpx; }

/* ---- 操作提示行（换一批 / 新建文稿） ---- */
.lib-section-hint-row {
  display: flex;
  justify-content: flex-end;
  padding: 0 8rpx 20rpx;
}
.lib-refresh-btn {
  font-size: 24rpx;
  color: var(--primary);
  font-weight: 600;
}
.lib-refresh-btn.disabled {
  color: #c0c8d0;
  pointer-events: none;
}

/* ---- 列表 ---- */
.lib-list {
  display: flex;
  flex-direction: column;
  gap: 28rpx;
}

/* ---- 卡片：极淡浅青底 + 超细边框 ---- */
.lib-card {
  background: #f6fbfc;
  border: 1rpx solid #e4eff2;
  border-radius: 24rpx;
  padding: 32rpx;
  transition: transform 0.15s;
}
.lib-card:active {
  transform: scale(0.98);
}
.lib-card-body { display: flex; flex-direction: column; gap: 14rpx; }
.lib-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.lib-card-title {
  font-size: 32rpx;
  font-weight: 700;
  line-height: 1.35;
  color: var(--on-surface);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.lib-card-desc {
  font-size: 26rpx;
  color: var(--on-surface-variant);
  line-height: 1.55;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.lib-card-footer {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 24rpx;
  padding-top: 8rpx;
}

/* ---- 按钮极简化：纯文字链接 ---- */
.lib-card-action {
  font-size: 26rpx;
  color: var(--primary);
  font-weight: 600;
}
.lib-card-action.disabled {
  color: #c0c8d0;
  pointer-events: none;
}
.lib-card-action-secondary {
  font-size: 24rpx;
  color: #b0b8c0;
  font-weight: 500;
}

/* ---- 失败行 ---- */
.lib-card-fail-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  padding-top: 12rpx;
  border-top: 1rpx dashed #e4eff2;
}
.lib-card-fail-hint {
  font-size: 22rpx;
  color: var(--error);
  flex: 1;
}

/* ---- 自定义"新建"大卡片（空态用） ---- */
.lib-new-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16rpx;
  padding: 80rpx 40rpx;
  background: #f6fbfc;
  border: 2rpx dashed #c8e0e6;
  border-radius: 24rpx;
  margin-top: 40rpx;
}
.lib-new-card:active { transform: scale(0.98); }
.lib-new-plus {
  width: 80rpx;
  height: 80rpx;
  border-radius: 50%;
  border: 2rpx solid var(--primary);
  color: var(--primary);
  font-size: 48rpx;
  line-height: 80rpx;
  text-align: center;
  font-weight: 400;
  background: transparent;
}
.lib-new-title {
  font-size: 30rpx;
  font-weight: 700;
  color: var(--primary);
}
.lib-new-hint {
  font-size: 24rpx;
  color: var(--on-surface-variant);
  text-align: center;
  line-height: 1.5;
}

/* ---- 空态操作文字 ---- */
.empty-action {
  font-size: 26rpx;
  font-weight: 600;
  color: var(--primary);
  margin-top: 12rpx;
}
.empty-action.disabled {
  color: #c0c8d0;
  pointer-events: none;
}

/* ---- 精选书籍卡 ---- */
.lib-book-card {
  display: flex;
  gap: 24rpx;
  padding: 28rpx;
  background: #f6fbfc;
  border: 1rpx solid #e4eff2;
  border-radius: 24rpx;
  transition: transform 0.15s;
}
.lib-book-card:active {
  transform: scale(0.98);
}
.lib-book-cover {
  width: 120rpx;
  height: 160rpx;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}
.lib-book-cover svg {
  width: 100%;
  height: 100%;
}
.lib-book-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  justify-content: space-between;
}
.lib-book-title {
  font-size: 32rpx;
  font-weight: 700;
  color: var(--on-surface);
  line-height: 1.35;
}
.lib-book-en {
  font-size: 22rpx;
  color: var(--on-surface-muted);
  font-style: italic;
}
.lib-book-desc {
  font-size: 24rpx;
  color: var(--on-surface-variant);
}
.lib-book-footer {
  display: flex;
  justify-content: flex-end;
  padding-top: 12rpx;
}
.lib-book-more-hint {
  display: block;
  text-align: center;
  font-size: 24rpx;
  color: #b0b8c0;
  padding: 32rpx 0 8rpx;
}

/* ---- 标签 ---- */
.tag {
  font-size: 20rpx;
  padding: 4rpx 16rpx;
  border-radius: 20rpx;
  font-weight: 600;
}
.tag-ai { background: var(--primary-container); color: var(--on-primary-container); }
.tag-warning { background: #FFF3E0; color: #E65100; }
.tag-error { background: #FFEBEE; color: #C62828; }
</style>
