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
                <text class="list-card-status" :class="learnedIds.includes(item.id) ? 'done' : 'todo'">
                  {{ learnedIds.includes(item.id) ? '✅已学' : '未学' }}
                </text>
                <text class="delete-btn" @tap.stop="deleteCustomContent(item.id)">🗑️</text>
              </view>
            </view>
            <text class="list-card-title" @tap="goDetail(item.id)">{{ item.title }}</text>
            <text class="list-card-desc" @tap="goDetail(item.id)">{{ item.article?.slice(0, 60) }}...</text>
          </view>
        </view>
      </view>

      <!-- ====== 往期内容 Tab ====== -->
      <view v-if="activeTab === 'past'">
        <view v-if="pastContents.length === 0" class="empty-state">
          <text class="icon">📋</text>
          <text class="empty-text">暂无往期内容</text>
          <text class="empty-hint">完成学习后内容会出现在这里</text>
        </view>
        <view v-else class="content-list">
          <view
            v-for="item in pastContents"
            :key="item.id"
            class="list-card"
            @tap="goDetail(item.id)"
          >
            <view class="list-card-header">
              <text class="tag tag-success">{{ themeLabels[item.theme_type] || item.theme_type }}</text>
              <text class="list-card-status done">✅已学</text>
            </view>
            <text class="list-card-title">{{ item.title }}</text>
            <text class="list-card-desc">{{ item.article?.slice(0, 60) }}...</text>
          </view>
        </view>
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
import { dailyApi, generationLimitApi } from '@/api'
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

const activeTab = ref<'ai' | 'custom' | 'past'>('ai')

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
    loadPastContents()
  }
  if (tab === 'custom' && customContents.value.length === 0) {
    loadCustomContents()
  }
}

async function loadData() {
  loading.value = true
  const userId = auth.currentUserId
  const safe = (p: Promise<any>) => p.catch(() => null)
  const [contentRes, limitRes, learnedRes] = await Promise.all([
    safe(dailyApi.getTodayList(userId)),
    safe(generationLimitApi.getLimit(userId)),
    safe(dailyApi.getLearnedIds(userId)),
  ])
  if (contentRes?.data) contents.value = contentRes.data.contents || []
  if (learnedRes?.data) learnedIds.value = learnedRes.data.content_ids || []
  if (limitRes?.data) remainingCount.value = limitRes.data.remaining_count ?? 3
  loading.value = false
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

async function loadPastContents() {
  const userId = auth.currentUserId
  try {
    const { data } = await dailyApi.getLearnedIds(userId)
    const ids = data?.content_ids || []
    if (ids.length > 0) {
      const safe = (p: Promise<any>) => p.catch(() => null)
      const results = await Promise.all(ids.slice(0, 20).map((id: number) => safe(dailyApi.getContent(id))))
      pastContents.value = results.filter((r: any) => r?.data).map((r: any) => r.data)
    }
  } catch { pastContents.value = [] }
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
</style>
