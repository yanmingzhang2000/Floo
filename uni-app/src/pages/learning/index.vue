<template>
  <view class="page-container">
    <view class="nav-bar">
      <view class="nav-left"></view>
      <text class="nav-title">学习</text>
      <view class="nav-right"></view>
    </view>

    <view v-if="loading" class="loading">
      <view class="spinner"></view>
    </view>

    <template v-else>
      <!-- 书籍精读入口（只有被授权的用户能看到，无授权账号完全隐藏） -->
      <view v-if="myBooks.length > 0" class="book-entry" @tap="goBookList">
        <view class="book-entry-icon"><text>📚</text></view>
        <view class="book-entry-info">
          <text class="book-entry-title">书籍精读</text>
          <text class="book-entry-subtitle">
            <text v-if="myBooks.length === 1">《{{ myBooks[0].name_cn || myBooks[0].name }}》· {{ myBooks[0].total_chapters }} 章</text>
            <text v-else>已授权 {{ myBooks.length }} 本书</text>
          </text>
        </view>
        <text class="book-entry-arrow">›</text>
      </view>

      <!-- 分类标签栏 -->
      <view class="underline-tabs">
        <view class="underline-tab" :class="{ active: activeTab === 'ai' }" @tap="switchTab('ai')">
          <text>AI生成</text>
        </view>
        <view class="underline-tab" :class="{ active: activeTab === 'custom' }" @tap="switchTab('custom')">
          <text>自定义</text>
        </view>
        <view class="underline-tab" :class="{ active: activeTab === 'past' }" @tap="switchTab('past')">
          <text>往期内容</text>
        </view>
      </view>

      <!-- ====== AI生成 Tab ====== -->
      <view v-if="activeTab === 'ai'">
        <!-- 生成按钮 -->
        <view class="gen-action">
          <button class="btn btn-primary btn-block" :disabled="generating || remainingCount <= 0" @tap="handleGenerate">
            <text>{{ generating ? '生成中...' : (remainingCount > 0 ? `✨ AI 生成 (${remainingCount})` : '今日已用完') }}</text>
          </button>
        </view>
        <view v-if="contents.length === 0" class="empty-state">
          <text class="icon">📝</text>
          <text class="empty-text">今日还没有学习内容</text>
          <text class="empty-hint">点击上方按钮生成</text>
        </view>
        <view v-else class="content-list">
          <view
            v-for="item in contents"
            :key="item.id"
            class="list-card"
            @tap="goDetail(item.id)"
          >
            <view class="list-card-header">
              <text class="tag tag-success">{{ themeLabels[item.theme_type] || item.theme_type }}</text>
              <text class="list-card-status" :class="learnedIds.includes(item.id) ? 'done' : 'todo'">
                {{ learnedIds.includes(item.id) ? '✅已学' : '未学' }}
              </text>
            </view>
            <text class="list-card-title">{{ item.title }}</text>
            <text class="list-card-desc">{{ item.article?.slice(0, 60) }}...</text>
          </view>
        </view>
      </view>

      <!-- ====== 自定义 Tab ====== -->
      <view v-if="activeTab === 'custom'">
        <view class="gen-action">
          <button class="btn btn-primary btn-block" @tap="showCustomContent = true">
            <text>📝 粘贴新文章</text>
          </button>
        </view>
        <view v-if="customContents.length === 0" class="empty-state">
          <text class="icon">📋</text>
          <text class="empty-text">暂无自定义内容</text>
          <text class="empty-hint">粘贴英文文章开始学习</text>
        </view>
        <view v-else class="content-list">
          <view
            v-for="item in customContents"
            :key="item.id"
            class="list-card"
          >
            <view class="list-card-header">
              <text class="tag tag-warning">自定义</text>
              <view class="list-card-actions">
                <text v-if="isGenerationFailed(item)" class="tag tag-error">⚠️ 生成失败</text>
                <text v-else class="list-card-status" :class="learnedIds.includes(item.id) ? 'done' : 'todo'">
                  {{ learnedIds.includes(item.id) ? '✅已学' : '未学' }}
                </text>
                <text class="delete-btn" @tap.stop="deleteCustomContent(item.id)">🗑️</text>
              </view>
            </view>
            <text class="list-card-title" @tap="goDetail(item.id)">{{ item.title }}</text>
            <text class="list-card-desc" @tap="goDetail(item.id)">{{ item.article?.slice(0, 60) }}...</text>
            <view v-if="isGenerationFailed(item)" class="regenerate-row">
              <text class="regenerate-hint">译文或词组生成失败</text>
              <button
                class="btn-regenerate"
                :disabled="regeneratingIds.includes(item.id)"
                @tap.stop="regenerateCustom(item.id)"
              >
                <text>{{ regeneratingIds.includes(item.id) ? '重新生成中...' : '🔄 重新生成' }}</text>
              </button>
            </view>
          </view>
        </view>
      </view>

      <!-- ====== 往期内容 Tab ====== -->
      <view v-if="activeTab === 'past'">
        <!-- 日期筛选区域 -->
        <view class="filter-section">
          <view class="filter-quick-btns">
            <view class="filter-btn" :class="{ active: filterStartDate === filterEndDate && filterStartDate === new Date().toISOString().split('T')[0] }" @tap="filterToday">
              <text>今天</text>
            </view>
            <view class="filter-btn" @tap="filterThisWeek">
              <text>本周</text>
            </view>
            <view class="filter-btn" @tap="filterThisMonth">
              <text>本月</text>
            </view>
            <view class="filter-btn" :class="{ active: !filterStartDate && !filterEndDate }" @tap="clearFilter">
              <text>全部</text>
            </view>
            <!-- 自定义区间展开按钮 -->
            <view class="filter-btn filter-btn-range" :class="{ active: showDateRange || (filterStartDate || filterEndDate) }" @tap="showDateRange = !showDateRange">
              <text>📅{{ (filterStartDate || filterEndDate) ? ' ' + (filterStartDate || '…') + '~' + (filterEndDate || '今') : ' 区间' }}</text>
            </view>
          </view>
          <!-- 自定义日期区间（默认收起） -->
          <view v-if="showDateRange" class="filter-date-row">
            <view class="filter-date-item" @tap="openDatePicker('start')">
              <text class="filter-date-label">开始</text>
              <text class="filter-date-value">{{ filterStartDate || '选择日期' }}</text>
            </view>
            <text class="filter-date-separator">~</text>
            <view class="filter-date-item" @tap="openDatePicker('end')">
              <text class="filter-date-label">结束</text>
              <text class="filter-date-value">{{ filterEndDate || '选择日期' }}</text>
            </view>
            <view v-if="filterStartDate || filterEndDate" class="filter-clear-btn" @tap="clearFilter">
              <text>✕</text>
            </view>
          </view>
        </view>

        <!-- 来源类型筛选 -->
        <view class="type-filter-bar">
          <view
            v-for="f in pastTypeFilters"
            :key="f.value"
            class="type-chip"
            :class="{ active: pastTypeFilter === f.value }"
            @tap="pastTypeFilter = f.value"
          >
            <text>{{ f.label }}</text>
            <text class="type-chip-count">{{ pastTypeCounts[f.value] }}</text>
          </view>
        </view>

        <!-- 学习状态筛选 -->
        <view class="type-filter-bar" style="padding-top:0;margin-top:-8rpx;">
          <view
            v-for="f in pastLearnFilters"
            :key="f.value"
            class="type-chip"
            :class="{ active: pastLearnFilter === f.value }"
            @tap="pastLearnFilter = f.value"
          >
            <text>{{ f.label }}</text>
            <text class="type-chip-count">{{ pastLearnCounts[f.value] }}</text>
          </view>
        </view>

        <view v-if="filteredPastContents.length === 0" class="empty-state">
          <text class="icon">📋</text>
          <text class="empty-text">{{ pastTypeFilter !== 'all' ? '该分类下暂无内容' : (filterStartDate || filterEndDate) ? '该时间段暂无内容' : '暂无往期内容' }}</text>
          <text class="empty-hint">{{ pastTypeFilter !== 'all' ? '换个分类试试' : (filterStartDate || filterEndDate) ? '尝试调整筛选条件' : '完成学习后内容会出现在这里' }}</text>
        </view>
        <view v-else class="content-list">
          <view
            v-for="item in filteredPastContents"
            :key="item.id"
            class="list-card"
            @tap="goDetail(item.id)"
          >
            <view class="list-card-header">
              <text class="tag tag-success">{{ themeLabels[item.theme_type] || item.theme_type }}</text>
              <view style="display:flex;align-items:center;gap:12rpx;">
                <text class="tag" :class="item.creator_type === 1 ? 'tag-warning' : 'tag-ai'">{{ item.creator_type === 1 ? '✏️ 自定义' : '🤖 AI' }}</text>
                <text class="list-card-status done">✅已学</text>
              </view>
            </view>
            <text class="list-card-title">{{ item.title }}</text>
            <text class="list-card-desc">{{ item.article?.slice(0, 60) }}...</text>
            <text class="list-card-date">{{ item.content_date }}</text>
          </view>
        </view>

        <!-- 日期选择器 -->
        <picker v-if="showDatePicker" mode="date" :value="datePickerType === 'start' ? filterStartDate : filterEndDate" @change="onDateConfirm" @cancel="showDatePicker = false">
          <view></view>
        </picker>
      </view>

      <!-- 底部固定按钮 -->
      <view class="bottom-action">
        <button v-if="activeTab === 'ai' && contents.length > 0" class="btn btn-primary btn-block btn-lg" @tap="goDetail(contents[currentIdx]?.id)">
          <text>{{ learnedIds.includes(contents[currentIdx]?.id) ? '复习当前' : '开始学习' }}</text>
        </button>
        <button v-else-if="activeTab === 'past' && pastContents.length > 0" class="btn btn-primary btn-block btn-lg" @tap="goDetail(pastContents[0]?.id)">
          <text>复习最新</text>
        </button>
      </view>
    </template>

    <!-- 自定义内容弹窗 -->
    <CustomContentModal :visible="showCustomContent" @close="showCustomContent = false" @created="onCustomCreated" />
    <OnboardingGuide />
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { dailyApi, generationLimitApi, bookApi } from '@/api'
import { useAuthStore } from '@/stores'
import { navTo } from '@/utils/router'
import { storage } from '@/utils/storage'
import type { LearningContent } from '@/types'
import CustomContentModal from '@/components/CustomContentModal.vue'
import OnboardingGuide from '@/components/OnboardingGuide.vue'

const auth = useAuthStore()
const loading = ref(true)
const generating = ref(false)
const contents = ref<LearningContent[]>([])
const customContents = ref<LearningContent[]>([])
const pastContents = ref<LearningContent[]>([])
const currentIdx = ref(0)
const learnedIds = ref<number[]>([])
const remainingCount = ref(3)
const showCustomContent = ref(false)
const regeneratingIds = ref<number[]>([])

// 书籍精读授权列表：只有此列表非空才显示入口卡片
// 未授权用户 API 返回空数组，不报 403，保证隐藏对用户透明
interface MyBook { series_id: number; name: string; name_cn?: string; total_chapters: number }
const myBooks = ref<MyBook[]>([])

const activeTab = ref<'ai' | 'custom' | 'past'>('ai')

// 判断自定义内容是否生成失败（译文降级或词组为空）
// 后端降级文案固定以「（翻译生成失败」开头，见 backend/app/routers/daily.py:691
function isGenerationFailed(item: LearningContent): boolean {
  const tr = (item.translation || '').trim()
  const failedTranslation = !tr || tr.startsWith('（翻译生成失败')
  const emptyWords = !item.words || item.words.length === 0
  return failedTranslation || emptyWords
}

// 往期内容日期筛选相关
const filterStartDate = ref('')
const filterEndDate = ref('')
const showDateRange = ref(false)
const showDatePicker = ref(false)
const datePickerType = ref<'start' | 'end'>('start')

// 往期内容来源类型筛选
const pastTypeFilter = ref<'all' | 'ai' | 'custom'>('all')
const pastTypeFilters = [
  { value: 'all' as const,    label: '全部' },
  { value: 'ai' as const,     label: '🤖 AI生成' },
  { value: 'custom' as const, label: '✏️ 自定义' },
]

// 往期内容学习状态筛选
const pastLearnFilter = ref<'all' | 'learned' | 'unlearned'>('all')
const pastLearnFilters = [
  { value: 'all' as const,       label: '全部' },
  { value: 'learned' as const,   label: '✅ 已学' },
  { value: 'unlearned' as const, label: '📖 未学' },
]

// 综合筛选：日期 + 来源类型 + 学习状态，全部客户端完成
const filteredPastContents = computed(() => {
  let list = pastContents.value
  if (filterStartDate.value) list = list.filter(i => (i.content_date || '') >= filterStartDate.value)
  if (filterEndDate.value)   list = list.filter(i => (i.content_date || '') <= filterEndDate.value)
  if (pastTypeFilter.value === 'ai')     list = list.filter(i => i.creator_type !== 1)
  if (pastTypeFilter.value === 'custom') list = list.filter(i => i.creator_type === 1)
  if (pastLearnFilter.value === 'learned')   list = list.filter(i => learnedIds.value.includes(i.id))
  if (pastLearnFilter.value === 'unlearned') list = list.filter(i => !learnedIds.value.includes(i.id))
  return list
})

// 来源类型数量（基于日期+学习状态过滤后的结果）
const pastTypeCounts = computed(() => {
  let base = pastContents.value
  if (filterStartDate.value) base = base.filter(i => (i.content_date || '') >= filterStartDate.value)
  if (filterEndDate.value)   base = base.filter(i => (i.content_date || '') <= filterEndDate.value)
  if (pastLearnFilter.value === 'learned')   base = base.filter(i => learnedIds.value.includes(i.id))
  if (pastLearnFilter.value === 'unlearned') base = base.filter(i => !learnedIds.value.includes(i.id))
  return {
    all:    base.length,
    ai:     base.filter(i => i.creator_type !== 1).length,
    custom: base.filter(i => i.creator_type === 1).length,
  }
})

// 学习状态数量（基于日期+来源类型过滤后的结果）
const pastLearnCounts = computed(() => {
  let base = pastContents.value
  if (filterStartDate.value) base = base.filter(i => (i.content_date || '') >= filterStartDate.value)
  if (filterEndDate.value)   base = base.filter(i => (i.content_date || '') <= filterEndDate.value)
  if (pastTypeFilter.value === 'ai')     base = base.filter(i => i.creator_type !== 1)
  if (pastTypeFilter.value === 'custom') base = base.filter(i => i.creator_type === 1)
  return {
    all:       base.length,
    learned:   base.filter(i => learnedIds.value.includes(i.id)).length,
    unlearned: base.filter(i => !learnedIds.value.includes(i.id)).length,
  }
})

onLoad(() => {
  // 从 storage 读取外部传入的 tab 参数（如从首页跳转）
  const savedTab = storage.get('learning_active_tab')
  if (savedTab && ['ai', 'custom', 'past'].includes(savedTab)) {
    activeTab.value = savedTab as typeof activeTab.value
  }
  storage.remove('learning_active_tab')
})

const themeLabels: Record<string, string> = {
  ai_tech: 'AI科技', product_tech: '产品技术', business: '财经商业',
  daily_news: '日常新闻', self_growth: '个人成长', all_random: '随机',
  custom: '自定义',
}
const totalCount = computed(() => contents.value.length)

function switchTab(tab: typeof activeTab.value) {
  activeTab.value = tab
  if (tab === 'past' && pastContents.value.length === 0) {
    loadAllPastContents()
  }
  if (tab === 'custom' && customContents.value.length === 0) {
    loadCustomContents()
  }
}

async function loadData() {
  loading.value = true
  const userId = auth.currentUserId
  const safe = (p: Promise<any>) => p.catch(() => null)
  // 书籍列表也并行拉取，无授权用户拿空数组，不影响 loading 时序
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

function goBookList() {
  // 只有一本书时直接跳到章节页，多本才跳列表页
  if (myBooks.value.length === 1) {
    const b = myBooks.value[0]
    const name = encodeURIComponent(b.name_cn || b.name)
    navTo(`/pages/book/chapters?series_id=${b.series_id}&name=${name}`)
    return
  }
  navTo('/pages/book/list')
}

async function loadCustomContents() {
  const userId = auth.currentUserId
  try {
    const { data } = await dailyApi.getCustomContents(userId)
    customContents.value = data?.contents || []
  } catch { customContents.value = [] }
}

function onCustomCreated() {
  // 创建成功后切到自定义 Tab 并刷新列表
  activeTab.value = 'custom'
  loadCustomContents()
}

async function regenerateCustom(contentId: number) {
  if (regeneratingIds.value.includes(contentId)) {
    // 防止重复点击：同一条正在重新生成时忽略
    return
  }
  const userId = auth.currentUserId
  regeneratingIds.value.push(contentId)
  uni.showLoading({ title: '重新生成中...', mask: true })
  try {
    await dailyApi.regenerateCustomContent(contentId, userId)
    // 成功后重新拉列表以显示最新译文和词组
    await loadCustomContents()
    uni.hideLoading()
    uni.showToast({ title: '重新生成成功', icon: 'success' })
  } catch (e: any) {
    // AI 仍然失败时后端返回 503，其它是网络/服务异常
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
          uni.showToast({ title: '删除失败', icon: 'none' })
        }
      }
    },
  })
}

async function loadAllPastContents() {
  const userId = auth.currentUserId
  try {
    // 并行拉取 AI 内容（getList）和用户自定义内容（getCustomContents）
    const [listRes, customRes] = await Promise.all([
      dailyApi.getList(300).catch(() => null),
      dailyApi.getCustomContents(userId).catch(() => null),
    ])
    const aiItems: LearningContent[] = (listRes?.data || []).filter((i: LearningContent) => i.creator_type !== 1)
    const customItems: LearningContent[] = customRes?.data?.contents || []
    // 合并去重（自定义优先，AI 内容不重复加入）
    const customIds = new Set(customItems.map(i => i.id))
    const merged = [...customItems, ...aiItems.filter(i => !customIds.has(i.id))]
    // 按日期降序排列
    merged.sort((a, b) => (b.content_date || '').localeCompare(a.content_date || ''))
    pastContents.value = merged
  } catch { pastContents.value = [] }
}

// 快捷筛选：今天（纯客户端，只更新日期 ref，computed 自动过滤）
function filterToday() {
  const today = new Date().toISOString().split('T')[0]
  filterStartDate.value = today
  filterEndDate.value = today
  showDateRange.value = false
}

// 快捷筛选：本周
function filterThisWeek() {
  const now = new Date()
  const dayOfWeek = now.getDay() || 7
  const monday = new Date(now)
  monday.setDate(now.getDate() - dayOfWeek + 1)
  filterStartDate.value = monday.toISOString().split('T')[0]
  filterEndDate.value = now.toISOString().split('T')[0]
  showDateRange.value = false
}

// 快捷筛选：本月
function filterThisMonth() {
  const now = new Date()
  const firstDay = new Date(now.getFullYear(), now.getMonth(), 1)
  filterStartDate.value = firstDay.toISOString().split('T')[0]
  filterEndDate.value = now.toISOString().split('T')[0]
  showDateRange.value = false
}

// 清除筛选
function clearFilter() {
  filterStartDate.value = ''
  filterEndDate.value = ''
  showDateRange.value = false
}

// 打开日期选择器
function openDatePicker(type: 'start' | 'end') {
  datePickerType.value = type
  showDatePicker.value = true
}

// 日期选择确认（纯客户端，只更新 ref，computed 自动重算）
function onDateConfirm(e: any) {
  const date = e.detail.value
  if (datePickerType.value === 'start') {
    filterStartDate.value = date
  } else {
    filterEndDate.value = date
  }
  showDatePicker.value = false
}

async function handleGenerate() {
  if (remainingCount.value <= 0) {
    uni.showToast({ title: '今日生成次数已用完', icon: 'none' })
    return
  }
  generating.value = true
  try {
    const res: any = await dailyApi.generate(auth.currentUserId)
    if (res.statusCode && res.statusCode >= 400) {
      const msg = res.data?.detail || res.data?.message || `请求失败 (${res.statusCode})`
      uni.showToast({ title: msg, icon: 'none' })
      generating.value = false
      return
    }
    await loadData()
  } catch (e: any) {
    const msg = e?.errMsg || e?.message || '网络异常'
    uni.showToast({ title: msg, icon: 'none' })
  }
  generating.value = false
}

function goDetail(id: number) { navTo(`/pages/detail/index?id=${id}`) }

onShow(loadData)
</script>

<style scoped>
/* 分类标签栏 */
.underline-tabs {
  display: flex;
  border-bottom: 2rpx solid var(--outline-variant);
  margin-bottom: 20rpx;
}
.underline-tab {
  flex: 1;
  text-align: center;
  padding: 20rpx 0;
  font-size: 28rpx;
  color: var(--on-surface-variant);
  position: relative;
  transition: color 0.2s;
}
.underline-tab.active {
  color: var(--primary);
  font-weight: 700;
}
.underline-tab.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 60%;
  height: 6rpx;
  border-radius: 3rpx;
  background: var(--primary);
}

/* 生成按钮 */
.gen-action { padding: 16rpx 0; }

/* 内容列表 */
.content-list { padding: 8rpx 0; }
.list-card {
  background: #fff;
  border-radius: 20rpx;
  padding: 28rpx;
  margin-bottom: 16rpx;
  box-shadow: var(--shadow-sm);
}
.list-card:active { opacity: 0.85; }
.list-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12rpx;
}
.list-card-actions { display: flex; align-items: center; gap: 16rpx; }
.list-card-status { font-size: 22rpx; }
.list-card-status.done { color: var(--success); font-weight: 600; }
.list-card-status.todo { color: var(--on-surface-muted); }
.delete-btn { font-size: 28rpx; padding: 8rpx; }
.list-card-title {
  font-size: 30rpx;
  font-weight: 700;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 8rpx;
}
.list-card-desc {
  font-size: 26rpx;
  color: var(--on-surface-variant);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 空状态 */
.empty-state { padding: 60rpx 0; text-align: center; }
.empty-state .icon { font-size: 64rpx; display: block; margin-bottom: 16rpx; }
.empty-text { font-size: 28rpx; color: var(--on-surface-variant); display: block; }
.empty-hint { font-size: 24rpx; color: var(--on-surface-muted); display: block; margin-top: 8rpx; }

/* 底部按钮 */
.bottom-action { padding: 16rpx 0 32rpx; }

/* 标签 */
.tag {
  font-size: 20rpx;
  padding: 4rpx 16rpx;
  border-radius: 20rpx;
  font-weight: 600;
}
.tag-success { background: var(--success-container); color: var(--success); }
.tag-warning { background: #FFF3E0; color: #E65100; }
.tag-error { background: #FFEBEE; color: #C62828; }

/* 重新生成入口：仅在自定义内容生成失败时出现 */
.regenerate-row {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  margin-top: 16rpx;
  padding-top: 16rpx;
  border-top: 1rpx dashed var(--outline-variant);
}
.regenerate-hint {
  flex: 1;
  font-size: 22rpx;
  color: #C62828;
}
.btn-regenerate {
  font-size: 22rpx;
  padding: 8rpx 20rpx;
  background: var(--primary-container);
  color: var(--primary);
  border-radius: 24rpx;
  border: none;
  line-height: 1.4;
}
.btn-regenerate[disabled] {
  opacity: 0.6;
}

/* 日期筛选区域 */
.filter-section {
  padding: 16rpx 0;
  margin-bottom: 16rpx;
  border-bottom: 1rpx solid var(--outline-variant);
}
.filter-quick-btns {
  display: flex;
  gap: 16rpx;
  margin-bottom: 16rpx;
}
.filter-btn {
  flex: 1;
  text-align: center;
  padding: 12rpx 0;
  font-size: 24rpx;
  color: var(--on-surface-variant);
  background: var(--surface-container);
  border-radius: 8rpx;
  transition: all 0.2s;
}
.filter-btn.active {
  color: var(--primary);
  background: var(--primary-container);
  font-weight: 600;
}
.filter-date-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
}
.filter-date-item {
  flex: 1;
  padding: 12rpx 16rpx;
  background: var(--surface-container);
  border-radius: 8rpx;
  text-align: center;
}
.filter-date-label {
  font-size: 20rpx;
  color: var(--on-surface-muted);
  display: block;
  margin-bottom: 4rpx;
}
.filter-date-value {
  font-size: 24rpx;
  color: var(--on-surface);
}
.filter-date-separator {
  color: var(--on-surface-muted);
  font-size: 28rpx;
}
.filter-clear-btn {
  width: 48rpx;
  height: 48rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--error-container);
  border-radius: 50%;
  color: var(--error);
  font-size: 24rpx;
}
.filter-result-info {
  margin-top: 12rpx;
  text-align: center;
}
.filter-result-text {
  font-size: 22rpx;
  color: var(--on-surface-muted);
}
.list-card-date {
  font-size: 22rpx;
  color: var(--on-surface-muted);
  margin-top: 8rpx;
}

/* 来源类型筛选 chips */
.type-filter-bar {
  display: flex;
  gap: 16rpx;
  padding: 16rpx 0 20rpx;
}
.type-chip {
  display: flex;
  align-items: center;
  gap: 8rpx;
  padding: 10rpx 24rpx;
  border-radius: 40rpx;
  border: 2rpx solid var(--outline-variant);
  background: transparent;
  font-size: 24rpx;
  color: var(--on-surface-variant);
}
.type-chip.active {
  background: var(--primary-container);
  border-color: var(--primary);
  color: var(--primary);
  font-weight: 600;
}
.type-chip-count {
  font-size: 20rpx;
  opacity: 0.7;
}
.filter-btn-range {
  flex: 1.6;
  font-size: 22rpx;
  overflow: hidden;
  white-space: nowrap;
}
.tag-ai { background: #E3F2FD; color: #1565C0; }

/* 书籍精读入口卡片：只对授权用户显示，样式区别于其它卡片以突出稀缺权益 */
.book-entry {
  display: flex;
  align-items: center;
  gap: 20rpx;
  padding: 24rpx;
  margin: 8rpx 0 20rpx;
  background: linear-gradient(135deg, #F0F9FF 0%, #E1F0F7 100%);
  border-radius: 20rpx;
  border: 2rpx solid #B3D9E3;
}
.book-entry:active { opacity: 0.85; }
.book-entry-icon {
  width: 72rpx;
  height: 72rpx;
  border-radius: 16rpx;
  background: var(--primary);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.book-entry-icon text { font-size: 40rpx; }
.book-entry-info { flex: 1; display: flex; flex-direction: column; gap: 6rpx; }
.book-entry-title {
  font-size: 30rpx;
  font-weight: 700;
  color: var(--primary);
}
.book-entry-subtitle {
  font-size: 24rpx;
  color: var(--on-surface-variant);
}
.book-entry-arrow {
  font-size: 40rpx;
  color: var(--primary);
}
</style>
