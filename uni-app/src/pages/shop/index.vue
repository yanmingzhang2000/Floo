<template>
  <view class="page-container shop-page">
    <!-- 顶栏统一青绿 -->
    <view class="shop-header">
      <view class="shop-back" @tap="navBackSafe"><text class="shop-back-icon">‹</text></view>
      <text class="shop-header-title">积分商城</text>
      <view class="shop-placeholder"></view>
    </view>

    <view v-if="loading" class="loading">
      <view class="spinner"></view>
    </view>

    <view v-else class="shop-body">
      <!-- 积分余额 -->
      <view class="balance-card">
        <text class="balance-label">当前积分</text>
        <view class="balance-row">
          <text class="balance-num">{{ balance }}</text>
          <text class="balance-unit">分</text>
        </view>
      </view>

      <!-- 盲盒区 -->
      <view class="section-card">
        <text class="section-card-title">好词盲盒</text>
        <text class="section-card-desc">收集美好品质，点亮你的性格树</text>
        <view class="box-actions">
          <text
            class="box-btn"
            :class="{ disabled: opening || balance < 50 }"
            @tap="handleOpen(1)"
          >开 1 次 · 50 分</text>
          <text
            class="box-btn box-btn-secondary"
            :class="{ disabled: opening || balance < 200 }"
            @tap="handleOpen(5)"
          >开 5 次 · 200 分</text>
        </view>
        <text class="odds-note">概率：普通 70% · 稀有 25% · 传说 5%</text>
      </view>

      <!-- 收藏 -->
      <view class="section-card">
        <view class="collection-header">
          <text class="section-card-title">我的收藏</text>
          <text class="collection-badge">{{ collection.length }}</text>
        </view>
        <view v-if="collection.length === 0" class="collection-empty">
          <text>还没有收藏角色，去开盲盒吧</text>
        </view>
        <view v-else class="collection-grid">
          <view v-for="c in collection" :key="c.character_id" class="collection-item">
            <text class="collection-rarity" :class="c.rarity">
              {{ c.rarity === 'legendary' ? '◆' : c.rarity === 'rare' ? '◇' : '·' }}
            </text>
            <text class="collection-name">{{ c.name }}</text>
            <text class="collection-count">x{{ c.count }}</text>
          </view>
        </view>
      </view>
    </view>

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
import { navBackSafe } from '@/utils/router'
import GachaAnimation from '@/components/GachaAnimation.vue'
import type { Character, BoxResult } from '@/types'

const auth = useAuthStore()
const loading = ref(true)
const opening = ref(false)
const balance = ref(0)
const collection = ref<Character[]>([])
const showAnimation = ref(false)
const animationCharacters = ref<BoxResult[]>([])
const animationIndex = ref(0)

async function loadData() {
  loading.value = true
  try {
    const balRes = await shopApi.getBalance(auth.currentUserId).catch(() => ({ data: { available_points: 0 } }))
    balance.value = balRes.data.available_points || 0
  } catch { console.error('加载积分余额失败') }
  try {
    const colRes = await shopApi.getCollection(auth.currentUserId).catch(() => ({ data: { collection: [] } }))
    collection.value = colRes.data.collection || []
  } catch { console.error('加载收藏列表失败') }
  loading.value = false
}

async function handleOpen(count: number) {
  opening.value = true
  try {
    const { data } = await shopApi.openBox(auth.currentUserId, count)
    const results = data.results || []
    animationCharacters.value = results
    animationIndex.value = 0
    showAnimation.value = true

    // 后台刷新积分和收藏（各自独立，互不影响）
    shopApi.getBalance(auth.currentUserId).then(r => { balance.value = r.data.available_points || 0 }).catch(() => {})
    shopApi.getCollection(auth.currentUserId).then(r => { collection.value = r.data.collection || [] }).catch(() => {})
  } catch { uni.showToast({ title: '开盒失败', icon: 'none' }) }
  opening.value = false
}

function handleAnimationNext() {
  if (animationIndex.value < animationCharacters.value.length - 1) animationIndex.value++
}
function handleAnimationClose() {
  showAnimation.value = false; animationCharacters.value = []; animationIndex.value = 0
}



onMounted(loadData)
</script>

<style scoped>
.shop-page { padding-bottom: 40rpx; }

/* 顶栏 */
.shop-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  padding: calc(env(safe-area-inset-top, 44px) + 16rpx) 32rpx 24rpx;
  background: var(--primary, #5B9AA8);
}
.shop-back { width: 48rpx; height: 48rpx; display: flex; align-items: center; justify-content: center; }
.shop-back-icon { font-size: 40rpx; color: #fff; font-weight: 300; }
.shop-header-title { font-size: 36rpx; font-weight: 600; color: #fff; }
.shop-placeholder { width: 48rpx; }

.shop-body { padding: 0 4rpx; }

/* 积分余额 */
.balance-card {
  margin: 24rpx 0;
  padding: 32rpx 28rpx;
  background: #ffffff;
  box-shadow: 0 2rpx 12rpx rgba(91, 154, 168, 0.10);
  border-radius: 24rpx;
}
.balance-label { font-size: 22rpx; color: var(--on-surface-variant); display: block; }
.balance-row { display: flex; align-items: baseline; gap: 8rpx; margin-top: 8rpx; }
.balance-num { font-size: 56rpx; font-weight: 800; color: var(--primary); line-height: 1; }
.balance-unit { font-size: 26rpx; color: var(--on-surface-variant); font-weight: 600; }

/* 分区卡片 */
.section-card {
  margin-bottom: 24rpx;
  padding: 32rpx 28rpx;
  background: #ffffff;
  box-shadow: 0 2rpx 12rpx rgba(91, 154, 168, 0.10);
  border-radius: 24rpx;
}
.section-card-title { font-size: 30rpx; font-weight: 700; color: var(--on-surface); display: block; }
.section-card-desc { font-size: 24rpx; color: var(--on-surface-variant); display: block; margin: 8rpx 0 24rpx; }

/* 盲盒按钮 */
.box-actions { display: flex; gap: 16rpx; }
.box-btn {
  flex: 1;
  padding: 24rpx 0;
  text-align: center;
  font-size: 26rpx;
  font-weight: 700;
  color: #fff;
  background: var(--primary);
  border-radius: 40rpx;
}
.box-btn-secondary {
  background: transparent;
  color: var(--primary);
  border: 2rpx solid var(--primary);
}
.box-btn.disabled { background: #d0d8dc; color: #fff; border-color: #d0d8dc; }
.box-btn-secondary.disabled { background: transparent; color: #b0b8c0; border-color: #d0d8dc; }

.odds-note {
  text-align: center;
  padding: 20rpx 0 0;
  font-size: 22rpx;
  color: #b0b8c0;
}

/* 收藏区 */
.collection-header { display: flex; align-items: center; gap: 12rpx; margin-bottom: 20rpx; }
.collection-badge {
  font-size: 20rpx;
  background: rgba(91,154,168,0.12);
  color: var(--primary);
  padding: 4rpx 16rpx;
  border-radius: 20rpx;
  font-weight: 600;
}
.collection-empty { text-align: center; padding: 32rpx; color: #b0b8c0; font-size: 26rpx; }
.collection-grid { display: flex; flex-wrap: wrap; gap: 16rpx; }
.collection-item {
  width: 30%;
  text-align: center;
  padding: 24rpx 12rpx;
  background: #fff;
  border: 1rpx solid #e4eff2;
  border-radius: 16rpx;
}
.collection-rarity { font-size: 36rpx; display: block; color: var(--primary); }
.collection-rarity.legendary { color: var(--primary); font-weight: 800; }
.collection-rarity.rare { color: var(--primary); opacity: 0.7; }
.collection-name { font-size: 24rpx; font-weight: 600; display: block; margin-top: 8rpx; color: var(--on-surface); }
.collection-count { font-size: 22rpx; color: #b0b8c0; display: block; }
</style>
