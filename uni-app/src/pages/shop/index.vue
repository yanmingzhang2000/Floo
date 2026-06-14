<template>
  <view class="page-container">
    <view v-if="loading" class="loading">
      <view class="spinner"></view>
    </view>

    <view v-else>
      <view class="balance-card">
        <text class="balance-label">当前积分</text>
        <text class="balance-value">{{ balance }}</text>
      </view>

      <view class="card">
        <text class="card-label">🎁 美好品质盲盒</text>
        <text class="card-desc">开启盲盒，收集美好品质</text>
        <view class="box-actions">
          <button class="btn btn-primary" :disabled="opening || balance < 50" @tap="handleOpen(1)">
            <text>开1次 (50分)</text>
          </button>
          <button class="btn btn-outline" :disabled="opening || balance < 200" @tap="handleOpen(5)">
            <text>开5次 (200分)</text>
          </button>
        </view>
      </view>

      <!-- 已收藏角色 -->
      <view class="card">
        <text class="card-label">📦 我的收藏 ({{ collection.length }})</text>
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
.balance-card {
  text-align: center;
  padding: 48rpx 32rpx;
  background: linear-gradient(135deg, #5B9AA8 0%, #7FB3BE 100%);
  color: white;
}
.balance-label { font-size: 28rpx; opacity: 0.85; display: block; }
.balance-value { font-size: 72rpx; font-weight: 800; margin-top: 12rpx; display: block; }

.card-label { font-size: 32rpx; font-weight: 700; display: block; margin-bottom: 12rpx; }
.card-desc { font-size: 26rpx; color: var(--on-surface-variant); display: block; margin-bottom: 24rpx; }
.box-actions { display: flex; gap: 20rpx; }

.empty-hint { text-align: center; padding: 32rpx; color: var(--on-surface-variant); font-size: 28rpx; }
.collection-grid { display: flex; flex-wrap: wrap; gap: 16rpx; }
.collection-item {
  width: 30%;
  text-align: center;
  padding: 20rpx 12rpx;
  background: var(--surface-container);
  border-radius: 16rpx;
}
.collection-rarity { font-size: 40rpx; display: block; }
.collection-name { font-size: 24rpx; font-weight: 600; display: block; margin-top: 8rpx; }
.collection-count { font-size: 22rpx; color: var(--on-surface-variant); display: block; }
.rarity.legendary { color: #FFD700; }
.rarity.rare { color: #9C27B0; }
</style>
