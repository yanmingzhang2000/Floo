<template>
  <view class="page-container">
    <!-- 顶部头部 -->
    <view class="page-header">
      <view class="header-row">
        <view class="header-left">
          <text class="header-title">今日英语 · {{ themeLabel }}</text>
          <text class="header-sub">共 {{ totalCount }} 篇</text>
        </view>
        <view class="avatar-btn" @tap="showProfile = true">
          <text class="avatar-text">{{ usernameInitial }}</text>
        </view>
      </view>
      <view class="actions">
        <button
          class="btn btn-sm action-btn"
          :disabled="generating || remainingCount <= 0"
          @tap="handleGenerate"
        >
          <text>{{ generating ? '生成中...' : (remainingCount > 0 ? `✨ 生成 (${remainingCount})` : '已用完') }}</text>
        </button>
        <button class="btn btn-sm action-btn" @tap="showCustomContent = true">
          <text>📝 自定义</text>
        </button>
        <button class="btn btn-sm action-btn" @tap="goList">
          <text>📋 历史</text>
        </button>
      </view>
    </view>

    <!-- 加载中 -->
    <view v-if="loading" class="loading">
      <view class="spinner"></view>
    </view>

    <!-- 空状态 -->
    <view v-else-if="contents.length === 0" class="empty-state">
      <text class="icon">📝</text>
      <text class="empty-text">今日还没有学习内容</text>
      <button class="btn btn-primary" style="margin-top:32rpx" @tap="handleGenerate">
        <text>AI 生成今日内容</text>
      </button>
    </view>

    <!-- 内容区 -->
    <view v-else>
      <!-- 切换栏 -->
      <view v-if="totalCount > 1" class="switch-nav">
        <button class="switch-btn" :disabled="!hasPrev" @tap="goPrev"><text>← 上一篇</text></button>
        <text class="switch-index">{{ currentIdx + 1 }} / {{ totalCount }}</text>
        <button class="switch-btn" :disabled="!hasNext" @tap="goNext"><text>下一篇 →</text></button>
      </view>

      <view v-if="currentItem" class="content-card card">
        <view class="card-header">
          <text class="tag tag-primary">文章 {{ currentIdx + 1 }}</text>
          <text class="tag tag-success">{{ currentItem.difficulty_level }}</text>
        </view>
        <text class="card-title">{{ currentItem.title }}</text>

        <view class="learned-toggle" @tap="toggleLearned(currentItem)">
          <text class="learned-icon">{{ learnedIds.includes(currentItem.id) ? '✅' : '☑️' }}</text>
          <text class="learned-text">{{ learnedIds.includes(currentItem.id) ? '已学过' : '标记已学' }}</text>
        </view>

        <!-- 文章内容（按词分割可点击） -->
        <view class="article-body">
          <text
            v-for="(part, i) in articleParts"
            :key="i"
            :class="['word-span', part.isWord ? (part.isKey ? 'keyword' : 'clickable-word') : '']"
            @tap="part.isWord && handleWordTap(part.text)"
          >{{ part.text }}</text>
        </view>

        <!-- 译文展开 -->
        <view v-if="currentItem.translation" class="translation-toggle" @tap="toggleTranslation">
          <text>{{ showTranslation ? '收起译文 ▲' : '查看译文 ▼' }}</text>
        </view>
        <view v-if="showTranslation && currentItem.translation" class="translation">
          <text>{{ currentItem.translation }}</text>
        </view>

        <!-- 核心词汇 -->
        <view v-if="currentItem.words && currentItem.words.length" class="words-section">
          <text class="words-title">核心词汇</text>
          <view class="words-wrap">
            <view
              v-for="w in currentItem.words"
              :key="w.word"
              class="word-chip"
              @tap="showWordDetail(w)"
            >
              <text class="word-text">{{ w.word }}</text>
              <text class="word-phonetic" v-if="w.phonetic">{{ w.phonetic }}</text>
              <text class="word-meaning">{{ w.meaning }}</text>
            </view>
          </view>
        </view>
      </view>

      <view class="bottom-actions">
        <button class="btn btn-primary btn-block" @tap="goReview">
          <text>去默写/复习</text>
        </button>
      </view>
    </view>

    <!-- 单词查询弹窗 -->
    <view v-if="wordPopup" class="modal-overlay" @tap="wordPopup = null">
      <view class="word-popup" @tap.stop>
        <view class="popup-header">
          <text class="popup-word">{{ wordPopup.word }}</text>
          <view class="speak-btn" @tap="speakWord(wordPopup.word)"><text>🔊</text></view>
          <view class="fav-btn" :class="{ 'is-fav': wordPopup.isFavorite }" @tap="toggleFavorite">
            <text>{{ wordPopup.isFavorite ? '★' : '☆' }}</text>
          </view>
        </view>
        <text v-if="wordPopup.phonetic" class="popup-phonetic">{{ wordPopup.phonetic }}</text>
        <text class="popup-meaning">{{ wordPopup.meaning }}</text>
        <text v-if="wordPopup.usage" class="popup-usage">{{ wordPopup.usage }}</text>
      </view>
    </view>

    <!-- 个人中心弹窗 -->
    <view v-if="showProfile" class="modal-overlay" @tap="showProfile = false">
      <view class="profile-sheet" @tap.stop>
        <view class="sheet-header">
          <view class="sheet-avatar"><text>{{ usernameInitial }}</text></view>
          <text class="sheet-username">{{ auth.username || '未登录' }}</text>
        </view>
        <view class="sheet-body">
          <view class="sheet-item" @tap="goShop"><text>✨ Floo!</text></view>
          <view class="sheet-item" @tap="goPreference"><text>⚙️ 学习偏好设置</text></view>
          <view class="sheet-item danger" @tap="handleLogout"><text>🚪 退出登录</text></view>
        </view>
      </view>
    </view>

    <!-- 自定义内容弹窗 -->
    <CustomContentModal
      :visible="showCustomContent"
      @close="showCustomContent = false"
      @created="loadData"
    />

    <!-- 新手引导 -->
    <OnboardingGuide />
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { dailyApi, generationLimitApi, favoritesApi, dictionaryApi } from '@/api'
import { useAuthStore } from '@/stores'
import { speakWord, initVoices } from '@/composables/useSpeech'
import { getBaseForm } from '@/composables/useWordForm'
import { navTo, navReLaunch } from '@/utils/router'
import type { LearningContent, WordItem } from '@/types'
import CustomContentModal from '@/components/CustomContentModal.vue'
import OnboardingGuide from '@/components/OnboardingGuide.vue'

const auth = useAuthStore()
const loading = ref(true)
const generating = ref(false)
const contents = ref<LearningContent[]>([])
const currentIdx = ref(0)
const showTranslation = ref(false)
const learnedIds = ref<number[]>([])
const remainingCount = ref(3)
const wordPopup = ref<{ word: string; phonetic?: string; meaning: string; usage?: string; isFavorite?: boolean } | null>(null)
const showProfile = ref(false)
const showCustomContent = ref(false)

// 词缓存
const wordCache = new Map<string, { word: string; phonetic?: string; meaning: string }>()

const themeLabels: Record<string, string> = {
  ai_tech: 'AI科技', product_tech: '产品技术', business: '财经商业',
  daily_news: '日常新闻', self_growth: '个人成长', all_random: '随机主题',
}
const themeLabel = computed(() => themeLabels[contents.value[0]?.theme_type] || '每日学习')
const totalCount = computed(() => contents.value.length)
const currentItem = computed(() => contents.value[currentIdx.value] || null)
const hasPrev = computed(() => currentIdx.value > 0)
const hasNext = computed(() => currentIdx.value < contents.value.length - 1)
const usernameInitial = computed(() => (auth.username?.[0] || '?').toUpperCase())

// 把文章拆成可点击的片段
const articleParts = computed(() => {
  if (!currentItem.value) return []
  const article = currentItem.value.article || ''
  const words = currentItem.value.words || []
  const keyWords = new Set(words.map(w => w.word.toLowerCase()))
  const parts: { text: string; isWord: boolean; isKey: boolean }[] = []
  let lastEnd = 0
  const re = /[a-zA-Z]+(?:'[a-zA-Z]+)?/g
  let m: RegExpExecArray | null
  while ((m = re.exec(article)) !== null) {
    if (m.index > lastEnd) {
      parts.push({ text: article.slice(lastEnd, m.index), isWord: false, isKey: false })
    }
    const word = m[0]
    parts.push({ text: word, isWord: true, isKey: keyWords.has(word.toLowerCase()) })
    lastEnd = m.index + word.length
  }
  if (lastEnd < article.length) {
    parts.push({ text: article.slice(lastEnd), isWord: false, isKey: false })
  }
  return parts
})

function goPrev() { if (hasPrev.value) currentIdx.value-- }
function goNext() { if (hasNext.value) currentIdx.value++ }
function toggleTranslation() { showTranslation.value = !showTranslation.value }

function goList() { navTo('/pages/list/index') }
function goReview() { navTo('/pages/review/index') }
function goShop() { showProfile.value = false; navTo('/pages/shop/index') }
function goPreference() { showProfile.value = false; navTo('/pages/preference/index') }

function handleLogout() {
  auth.logout()
  showProfile.value = false
  navReLaunch('/pages/login/index')
}

async function loadData() {
  loading.value = true
  try {
    const { data } = await dailyApi.getTodayList(auth.currentUserId)
    contents.value = data.contents || []
    const limitRes = await generationLimitApi.getLimit(auth.currentUserId)
    remainingCount.value = limitRes.data.remaining_count
  } catch {
    contents.value = []
  }
  loading.value = false
}

async function loadLearnedIds() {
  try {
    const { data } = await dailyApi.getLearnedIds(auth.currentUserId)
    learnedIds.value = data.content_ids || []
  } catch {}
}

async function toggleLearned(item: LearningContent) {
  try {
    const { data } = await dailyApi.toggleLearned(auth.currentUserId, item.id)
    if (data.learned) {
      if (!learnedIds.value.includes(item.id)) learnedIds.value.push(item.id)
    } else {
      learnedIds.value = learnedIds.value.filter(id => id !== item.id)
    }
  } catch {}
}

async function handleGenerate() {
  if (remainingCount.value <= 0) {
    uni.showToast({ title: '今日生成次数已达上限', icon: 'none' })
    return
  }
  generating.value = true
  try {
    await dailyApi.generate(auth.currentUserId)
    await loadData()
  } catch (e) {
    uni.showToast({ title: '生成失败', icon: 'none' })
  }
  generating.value = false
}

async function handleWordTap(rawWord: string) {
  const word = getBaseForm(rawWord)
  speakWord(word)
  // 缓存命中
  const cached = wordCache.get(word.toLowerCase())
  if (cached) {
    const favRes = await favoritesApi.check(auth.currentUserId, word).catch(() => ({ data: { is_favorite: false } }))
    wordPopup.value = { ...cached, isFavorite: favRes.data.is_favorite }
    return
  }
  wordPopup.value = { word, meaning: '查询中...' }
  try {
    const { data } = await dictionaryApi.lookup(word)
    const ec = data?.ec?.word?.[0]
    const phonetic = ec?.usphone || ec?.ukphone || ''
    const trs = ec?.trs || []
    const meaning = trs.map((t: any) => t?.tr?.[0]?.l?.i?.[0]).filter(Boolean).join('；')
    if (meaning) {
      const result = { word, phonetic: phonetic ? `/${phonetic}/` : undefined, meaning }
      wordCache.set(word.toLowerCase(), result)
      const favRes = await favoritesApi.check(auth.currentUserId, word)
      wordPopup.value = { ...result, isFavorite: favRes.data.is_favorite }
    } else {
      wordPopup.value = { word, meaning: '未找到释义' }
    }
  } catch {
    wordPopup.value = { word, meaning: '查询失败' }
  }
}

function showWordDetail(w: WordItem) {
  wordPopup.value = { word: w.word, phonetic: w.phonetic, meaning: w.meaning, usage: w.usage }
}

async function toggleFavorite() {
  if (!wordPopup.value) return
  const { word, phonetic, meaning, isFavorite } = wordPopup.value
  try {
    if (isFavorite) {
      await favoritesApi.remove(auth.currentUserId, word)
      wordPopup.value = { ...wordPopup.value, isFavorite: false }
    } else {
      await favoritesApi.add(auth.currentUserId, word, phonetic, meaning)
      wordPopup.value = { ...wordPopup.value, isFavorite: true }
    }
  } catch {}
}

// 弹窗5秒自动收起
let wordPopupTimer: number | null = null
watch(wordPopup, (val) => {
  if (wordPopupTimer) clearTimeout(wordPopupTimer)
  if (val) {
    wordPopupTimer = setTimeout(() => { wordPopup.value = null }, 5000) as any
  }
})

onMounted(() => {
  initVoices()
  loadData()
  loadLearnedIds()
})

onShow(() => {
  // 切换 tab 回来时刷新
  if (contents.value.length > 0) {
    loadLearnedIds()
  }
})
</script>

<style scoped>
.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.header-left { flex: 1; }
.header-title {
  font-size: 36rpx;
  font-weight: 700;
  color: white;
  display: block;
}
.header-sub {
  font-size: 24rpx;
  color: rgba(255,255,255,0.85);
  margin-top: 4rpx;
  display: block;
}
.avatar-btn {
  width: 72rpx;
  height: 72rpx;
  background: rgba(255,255,255,0.25);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.avatar-text {
  color: white;
  font-size: 30rpx;
  font-weight: 700;
}
.action-btn {
  background: rgba(255,255,255,0.2);
  color: white;
  font-size: 24rpx;
  padding: 12rpx 28rpx;
  border-radius: 32rpx;
  border: none;
}
.action-btn[disabled] {
  opacity: 0.5;
}

.switch-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24rpx 32rpx;
  background: var(--surface-container);
  margin-top: 24rpx;
}
.switch-btn {
  padding: 16rpx 32rpx;
  border: 2rpx solid var(--primary);
  background: transparent;
  color: var(--primary);
  border-radius: 16rpx;
  font-size: 26rpx;
}
.switch-btn[disabled] {
  opacity: 0.4;
}
.switch-index {
  font-size: 26rpx;
  color: var(--on-surface-variant);
}

.content-card {
  margin-top: 24rpx;
  padding: 32rpx 32rpx 40rpx;
}
.card-header {
  display: flex;
  gap: 16rpx;
  margin-bottom: 20rpx;
  align-items: center;
}
.card-title {
  font-size: 34rpx;
  font-weight: 700;
  margin-bottom: 24rpx;
  display: block;
  line-height: 1.5;
}
.learned-toggle {
  display: inline-flex;
  align-items: center;
  gap: 12rpx;
  padding: 12rpx 28rpx;
  border-radius: 40rpx;
  background: var(--surface);
  border: 3rpx solid var(--outline-variant);
  font-size: 26rpx;
  margin-bottom: 24rpx;
}
.learned-icon { font-size: 32rpx; }
.learned-text { font-weight: 500; color: var(--on-surface-variant); }

.article-body {
  font-size: 30rpx;
  line-height: 1.8;
  color: var(--on-surface);
}
.word-span { display: inline; }
.keyword {
  background: var(--primary-container);
  color: var(--on-primary-container);
  padding: 0 4rpx;
  border-radius: 4rpx;
  font-weight: 600;
}
.clickable-word {
  color: var(--primary);
  text-decoration: underline;
  text-decoration-style: dashed;
}

.translation-toggle {
  color: var(--primary);
  font-size: 28rpx;
  margin-top: 24rpx;
  font-weight: 500;
}
.translation {
  font-size: 28rpx;
  color: var(--on-surface-variant);
  margin-top: 16rpx;
  padding: 24rpx;
  background: var(--surface-container);
  border-radius: 16rpx;
  line-height: 1.6;
}

.words-section {
  margin-top: 32rpx;
  padding-top: 24rpx;
  border-top: 2rpx solid var(--surface-container-high);
}
.words-title {
  font-size: 28rpx;
  margin-bottom: 20rpx;
  color: var(--on-surface-variant);
  display: block;
}
.words-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}
.word-chip {
  padding: 16rpx 24rpx;
  background: var(--surface-container);
  border-radius: 16rpx;
  display: flex;
  flex-direction: column;
}
.word-text { font-weight: 600; font-size: 28rpx; }
.word-phonetic { font-size: 22rpx; color: var(--on-surface-variant); }
.word-meaning { font-size: 24rpx; color: var(--on-surface-variant); }

.bottom-actions {
  padding: 32rpx;
}

.word-popup {
  width: 100%;
  max-width: 600px;
  background: white;
  border-radius: 32rpx 32rpx 0 0;
  padding: 40rpx 32rpx;
  animation: slideUp 0.3s ease;
}
@keyframes slideUp {
  from { transform: translateY(100%); }
  to { transform: translateY(0); }
}
.popup-header {
  display: flex;
  align-items: center;
  gap: 24rpx;
}
.popup-word {
  font-size: 44rpx;
  font-weight: 700;
  flex: 1;
}
.speak-btn {
  width: 72rpx;
  height: 72rpx;
  background: var(--primary-container);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36rpx;
}
.fav-btn {
  width: 72rpx;
  height: 72rpx;
  background: var(--surface-container);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40rpx;
}
.fav-btn.is-fav {
  color: #f59e0b;
}
.popup-phonetic {
  color: var(--on-surface-variant);
  margin-top: 8rpx;
  display: block;
  font-size: 26rpx;
}
.popup-meaning {
  margin-top: 20rpx;
  font-size: 32rpx;
  display: block;
}
.popup-usage {
  margin-top: 16rpx;
  color: var(--on-surface-variant);
  font-size: 26rpx;
  display: block;
}

.profile-sheet {
  width: 100%;
  max-width: 600px;
  background: white;
  border-radius: 32rpx 32rpx 0 0;
  padding: 40rpx 32rpx;
  animation: slideUp 0.3s ease;
}
.sheet-header {
  display: flex;
  align-items: center;
  gap: 24rpx;
  padding-bottom: 32rpx;
  border-bottom: 2rpx solid var(--surface-container-high);
  margin-bottom: 16rpx;
}
.sheet-avatar {
  width: 96rpx;
  height: 96rpx;
  background: var(--primary);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40rpx;
  font-weight: 700;
}
.sheet-username {
  font-size: 36rpx;
  font-weight: 600;
}
.sheet-body { display: flex; flex-direction: column; }
.sheet-item {
  padding: 28rpx 0;
  font-size: 32rpx;
  border-bottom: 2rpx solid var(--surface-container);
}
.sheet-item.danger { color: var(--error); }
</style>