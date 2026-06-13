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
        <text class="card-label">🎁 开盲盒</text>
        <text class="card-desc">消耗积分获取收藏角色</text>
        <view class="box-actions">
          <button class="btn btn-primary" :disabled="opening || balance < 50" @tap="handleOpen(1)">
            <text>开1次 (50分)</text>
          </button>
          <button class="btn btn-outline" :disabled="opening || balance < 200" @tap="handleOpen(5)">
            <text>开5次 (200分)</text>
          </button>
        </view>
      </view>

      <!-- 开盒结果 -->
      <view v-if="boxResults.length" class="card">
        <text class="card-label">🎉 获得角色</text>
        <view class="result-list">
          <view v-for="r in boxResults" :key="r.character_id" class="result-item">
            <view class="result-rarity" :class="r.rarity">
              <text>{{ r.rarity === 'legendary' ? '🌟' : r.rarity === 'rare' ? '⭐' : '✦' }}</text>
            </view>
            <view class="result-info">
              <text class="result-name">{{ r.name }}</text>
              <text class="result-meaning">{{ r.meaning }}</text>
              <text v-if="r.is_new" class="new-badge">NEW!</text>
            </view>
          </view>
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
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { shopApi } from '@/api'
import { useAuthStore } from '@/stores'
import type { Character, BoxResult } from '@/types'

const auth = useAuthStore()
const loading = ref(true)
const opening = ref(false)
const balance = ref(0)
const collection = ref<Character[]>([])
const boxResults = ref<BoxResult[]>([])

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
  boxResults.value = []
  try {
    const { data } = await shopApi.openBox(auth.currentUserId, count)
    boxResults.value = data.results || []
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

.result-list { display: flex; flex-direction: column; gap: 16rpx; }
.result-item { display: flex; align-items: center; gap: 20rpx; }
.result-rarity { font-size: 40rpx; }
.result-info { flex: 1; }
.result-name { font-weight: 600; font-size: 30rpx; display: block; }
.result-meaning { font-size: 26rpx; color: var(--on-surface-variant); display: block; }
.new-badge {
  display: inline-block;
  background: #FF9800;
  color: white;
  font-size: 20rpx;
  padding: 4rpx 12rpx;
  border-radius: 12rpx;
  font-weight: 700;
  margin-left: 12rpx;
}

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