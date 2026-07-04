<template>
  <view class="page-container">
    <view class="nav-bar">
      <view class="nav-left">
        <view class="nav-back" @tap="navBackSafe"><text>‹</text></view>
      </view>
      <text class="nav-title">往期内容</text>
      <view class="nav-right">
        <view class="nav-avatar">
          <text>{{ usernameInitial }}</text>
        </view>
      </view>
    </view>

    <!-- 日期筛选区域 -->
    <view class="filter-section">
      <view class="filter-quick-btns">
        <view class="filter-btn" :class="{ active: filterStartDate === filterEndDate && filterStartDate === todayStr }" @tap="filterToday">
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
      </view>
      <view class="filter-date-row">
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
      <view v-if="filterStartDate || filterEndDate" class="filter-result-info">
        <text class="filter-result-text">共 {{ filterTotalCount }} 条结果</text>
      </view>
    </view>

    <view v-if="loading" class="loading">
      <view class="spinner"></view>
    </view>

    <view v-else-if="list.length === 0" class="empty-state">
      <text class="icon">📚</text>
      <text class="empty-text">{{ (filterStartDate || filterEndDate) ? '该时间段暂无内容' : '暂无往期内容' }}</text>
    </view>

    <view v-else class="list-view">
      <view
        v-for="item in list"
        :key="item.id"
        class="list-item"
        @tap="goDetail(item.id)"
      >
        <!-- 主信息 -->
        <view class="list-item-info">
          <text class="list-item-title">{{ item.title }}</text>
          <view class="list-item-meta">
            <text class="tag tag-success">{{ themeLabels[item.theme_type] || item.theme_type }}</text>
            <text class="list-item-date">{{ item.content_date }}</text>
          </view>
        </view>
        <!-- 箭头 -->
        <text class="list-item-arrow">›</text>
      </view>
    </view>

    <!-- 日期选择器 -->
    <picker v-if="showDatePicker" mode="date" :value="datePickerType === 'start' ? filterStartDate : filterEndDate" @change="onDateConfirm" @cancel="showDatePicker = false">
      <view></view>
    </picker>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { dailyApi } from '@/api'
import { useAuthStore } from '@/stores'
import { navTo, navBackSafe } from '@/utils/router'
import type { LearningContent } from '@/types'

const auth = useAuthStore()
const loading = ref(true)
const list = ref<LearningContent[]>([])

// 日期筛选相关
const filterStartDate = ref('')
const filterEndDate = ref('')
const filterTotalCount = ref(0)
const showDatePicker = ref(false)
const datePickerType = ref<'start' | 'end'>('start')
const todayStr = new Date().toISOString().split('T')[0]

const usernameInitial = computed(() => (auth.username?.[0] || '?').toUpperCase())

const themeLabels: Record<string, string> = {
  ai_tech: 'AI科技', product_tech: '产品技术', business: '财经商业',
  daily_news: '日常新闻', self_growth: '个人成长', all_random: '随机', custom: '自定义',
}

function goDetail(id: number) { navTo(`/pages/detail/index?id=${id}`) }

// 加载筛选后的内容
async function loadFilteredContents() {
  loading.value = true
  try {
    const userId = auth.currentUserId
    const startDate = filterStartDate.value || undefined
    const endDate = filterEndDate.value || undefined
    const { data } = await dailyApi.getFilteredLearnedContents(userId, startDate, endDate)
    list.value = data?.contents || []
    filterTotalCount.value = data?.total || 0
  } catch { list.value = [] }
  loading.value = false
}

// 快捷筛选：今天
function filterToday() {
  filterStartDate.value = todayStr
  filterEndDate.value = todayStr
  loadFilteredContents()
}

// 快捷筛选：本周
function filterThisWeek() {
  const now = new Date()
  const dayOfWeek = now.getDay() || 7
  const monday = new Date(now)
  monday.setDate(now.getDate() - dayOfWeek + 1)
  filterStartDate.value = monday.toISOString().split('T')[0]
  filterEndDate.value = todayStr
  loadFilteredContents()
}

// 快捷筛选：本月
function filterThisMonth() {
  const now = new Date()
  const firstDay = new Date(now.getFullYear(), now.getMonth(), 1)
  filterStartDate.value = firstDay.toISOString().split('T')[0]
  filterEndDate.value = todayStr
  loadFilteredContents()
}

// 清除筛选
function clearFilter() {
  filterStartDate.value = ''
  filterEndDate.value = ''
  loadFilteredContents()
}

// 打开日期选择器
function openDatePicker(type: 'start' | 'end') {
  datePickerType.value = type
  showDatePicker.value = true
}

// 日期选择确认
function onDateConfirm(e: any) {
  const date = e.detail.value
  if (datePickerType.value === 'start') {
    filterStartDate.value = date
  } else {
    filterEndDate.value = date
  }
  showDatePicker.value = false
  loadFilteredContents()
}

onMounted(() => {
  loadFilteredContents()
})
</script>

<style scoped>
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

/* 列表样式 */
.list-view {
  padding: 8rpx 0 40rpx;
}

.list-item {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 24rpx 0;
  border-bottom: 1rpx solid var(--outline-variant);
}
.list-item:last-child { border-bottom: none; }

.list-item-info {
  flex: 1;
  min-width: 0;  /* 让 flex 子项可以收缩，触发 overflow 截断 */
}
.list-item-title {
  font-size: 28rpx;
  font-weight: 600;
  color: var(--on-surface);
  display: block;
  /* 最多两行，超出省略 */
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.5;
  margin-bottom: 10rpx;
}
.list-item-meta {
  display: flex;
  align-items: center;
  gap: 16rpx;
}
.list-item-date {
  font-size: 22rpx;
  color: var(--on-surface-muted);
}

.list-item-arrow {
  font-size: 40rpx;
  color: var(--on-surface-muted);
  flex-shrink: 0;
  margin-left: 8rpx;
}
</style>
