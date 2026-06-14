<template>
  <view class="page-container">
    <view class="page-header">
      <text class="title">Floo! 商店</text>
      <text class="subtitle">当前积分：{{ balance }}</text>
    </view>

    <view v-if="loading" class="loading">
      <view class="spinner"></view>
    </view>

    <view v-else>
      <view class="card shop-card">
        <text class="card-emoji">🎁</text>
        <text class="card-label">美好品质盲盒</text>
        <text class="card-desc">开启盲盒，收集美好品质</text>
        <view class="box-actions">
          <button class="btn btn-primary" :disabled="opening || balance < 50" @tap="handleOpen(1)">
            <text>开1次</text>
            <text class="btn-sub">50分</text>
          </button>
          <button class="btn btn-outline" :disabled="opening || balance < 200" @tap="handleOpen(5)">
            <text>开5次</text>
            <text class="btn-sub">200分</text>
          </button>
        </view>
      </view>

      <!-- 已收藏角色 -->
      <view class="card shop-card">
        <view class="collection-header">
          <text class="collection-title">📦 我的收藏</text>
          <text class="collection-count-badge">{{ collection.length }}</text>
        </view>
        <view v-if="collection.length === 0" class="empty-hint">
          <text>还没有收藏角色，快去开盲盒吧</text>
        </view>
        <view v-else class="collection-grid">
          <view v-for="c in collection" :key="c.character_id" class="collection-item">
            <text class="collection-rarity" :class="c.rarity">
              {{ c.rarity === 'legendary' ? '🌟' : c.rarity === 'rare' ? '⭐' : '✦' }}
            </text>
            <text class="collection-name">{{ c.name }}</text>
            <text class="collection-count">x{{ c.count }}</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 抽卡动画组件 -->
    <GachaAnimation
      :visible="showAnimation"
      :characters="animationCharacters"
      :current-index="animationIndex"
      @close="handleAnimationClose"
      @next="handleAnimationNext"
    />
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { shopApi } from '@/api'
import { useAuthStore } from '@/stores'
import GachaAnimation from '@/components/GachaAnimation.vue'
import type { Character, BoxResult } from '@/types'

const auth = useAuthStore()
const loading = ref(true)
const opening = ref(false)
const balance = ref(0)
const collection = ref<Character[]>([])

// 动画相关状态
const showAnimation = ref(false)
const animationCharacters = ref<BoxResult[]>([])
const animationIndex = ref(0)

async function loadData() {
  loading.value = true
  try {
    const [balRes, colRes] = await Promise.all([
      shopApi.getBalance(auth.currentUserId),
      shopApi.getCollection(auth.currentUserId),
    ])
    balance.value = balRes.data.available_points || 0
    collection.value = colRes.data || []
  } catch {}
  loading.value = false
}

async function handleOpen(count: number) {
  opening.value = true
  try {
    const { data } = await shopApi.openBox(auth.currentUserId, count)
    const results = data.results || []

    // 开始动画
    animationCharacters.value = results
    animationIndex.value = 0
    showAnimation.value = true

    // 刷新余额和收藏
    const [balRes, colRes] = await Promise.all([
      shopApi.getBalance(auth.currentUserId),
      shopApi.getCollection(auth.currentUserId),
    ])
    balance.value = balRes.data.available_points || 0
    collection.value = colRes.data || []
  } catch {
    uni.showToast({ title: '开盒失败', icon: 'none' })
  }
  opening.value = false
}

function handleAnimationNext() {
  if (animationIndex.value < animationCharacters.value.length - 1) {
    animationIndex.value++
  }
}

function handleAnimationClose() {
  showAnimation.value = false
  animationCharacters.value = []
  animationIndex.value = 0
}

onMounted(loadData)
</script>

<style scoped>
.shop-card { text-align: center; padding: 40rpx; }
.card-emoji { font-size: 64rpx; display: block; margin-bottom: 16rpx; }
.card-label { font-size: 34rpx; font-weight: 700; display: block; margin-bottom: 8rpx; }
.card-desc { font-size: 26rpx; color: var(--on-surface-variant); display: block; margin-bottom: 32rpx; }

.box-actions { display: flex; gap: 20rpx; justify-content: center; }
.box-actions .btn { flex: 1; max-width: 280rpx; padding: 28rpx 24rpx; flex-direction: column; gap: 4rpx; }
.btn-sub { font-size: 22rpx; opacity: 0.8; font-weight: 400; }

.collection-header { display: flex; align-items: center; justify-content: center; gap: 16rpx; margin-bottom: 24rpx; }
.collection-title { font-size: 30rpx; font-weight: 700; }
.collection-count-badge {
  font-size: 22rpx; background: var(--primary-container); color: var(--on-primary-container);
  padding: 4rpx 20rpx; border-radius: 40rpx; font-weight: 600;
}

.empty-hint { text-align: center; padding: 32rpx; color: var(--on-surface-variant); font-size: 28rpx; }
.collection-grid { display: flex; flex-wrap: wrap; gap: 16rpx; justify-content: center; }
.collection-item {
  width: 30%;
  text-align: center;
  padding: 24rpx 12rpx;
  background: var(--surface-container);
  border-radius: 20rpx;
}
.collection-rarity { font-size: 44rpx; display: block; }
.collection-name { font-size: 24rpx; font-weight: 600; display: block; margin-top: 8rpx; }
.collection-count { font-size: 22rpx; color: var(--on-surface-variant); display: block; }
.rarity.legendary { color: #FFD700; }
.rarity.rare { color: #9C27B0; }
</style>
