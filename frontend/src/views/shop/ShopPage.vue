<template>
  <div class="page-container">
    <div class="page-header">
      <h1>积分商城</h1>
      <div class="points-badge">⭐ {{ balance }}</div>
    </div>

    <div v-if="loading" class="loading"><div class="spinner"></div></div>

    <div v-else>
      <!-- 标签切换 -->
      <div class="tab-bar">
        <button :class="['tab-btn', { active: activeTab === 'shop' }]" @click="activeTab = 'shop'">Floo！</button>
        <button :class="['tab-btn', { active: activeTab === 'collection' }]" @click="activeTab = 'collection'">我的收藏</button>
      </div>

      <!-- 商店标签 -->
      <div v-if="activeTab === 'shop'" class="tab-content">
        <!-- Floo卡片 -->
        <div class="box-card">
          <div class="box-icon">✨</div>
          <div class="box-info">
            <div class="box-title">Floo！</div>
            <div class="box-desc">今日份惊喜已上线</div>
          </div>
        </div>

        <!-- 抽取按钮 -->
        <div class="draw-buttons">
          <button class="draw-btn" @click="openBox(1)" :disabled="drawing || balance < 50">
            <div class="draw-price">50积分</div>
            <div class="draw-label">单抽</div>
          </button>
          <button class="draw-btn" @click="openBox(10)" :disabled="drawing || balance < 450">
            <div class="draw-price">450积分</div>
            <div class="draw-label">十连抽</div>
            <div class="draw-discount">9折</div>
          </button>
          <button class="draw-btn" @click="openBox(100)" :disabled="drawing || balance < 4000">
            <div class="draw-price">4000积分</div>
            <div class="draw-label">百连抽</div>
            <div class="draw-discount">8折</div>
          </button>
        </div>

        <!-- 角色图鉴 -->
        <div class="section-title">角色图鉴</div>
        <div class="character-grid">
          <div v-for="char in characters" :key="char.character_id" class="character-card" :class="[char.rarity, { collected: char.count > 0 }]">
            <img :src="getCharIcon(char.name)" class="char-img" :alt="char.meaning">
            <div class="char-name">{{ char.meaning }}</div>
            <div class="char-word">{{ char.name }}</div>
            <div class="char-count" v-if="char.count > 0">×{{ char.count }}</div>
          </div>
        </div>
      </div>

      <!-- 收藏标签 -->
      <div v-if="activeTab === 'collection'" class="tab-content">
        <div v-if="collection.length === 0" class="empty-state">
          <div class="empty-icon">📦</div>
          <div class="empty-text">还没有收藏，快去 Floo！吧</div>
        </div>
        <div v-else class="collection-grid">
          <div v-for="item in collection" :key="item.collection_id" class="collection-card" :class="item.rarity">
            <img :src="getCharIcon(item.name)" class="col-img" :alt="item.meaning">
            <div class="col-info">
              <div class="col-name">{{ item.meaning }}</div>
              <div class="col-word">{{ item.name }}</div>
              <div class="col-desc">{{ item.description }}</div>
            </div>
            <div class="col-count">×{{ item.count }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 抽卡结果弹窗 -->
    <div v-if="showResult" class="modal-overlay" @click="showResult = false">
      <div class="modal-content result-modal" @click.stop>
        <div class="result-title">✨ 恭喜获得</div>
        <div class="result-list">
          <div v-for="(item, idx) in resultItems" :key="idx" class="result-item" :class="item.rarity">
            <img :src="getCharIcon(item.name)" class="result-img" :alt="item.meaning">
            <div class="result-info">
              <div class="result-name">{{ item.meaning }}</div>
              <div class="result-word">{{ item.name }}</div>
              <div class="result-new" v-if="item.is_new">✨ 新收藏</div>
            </div>
          </div>
        </div>
        <div class="result-footer">
          <div class="result-points">剩余积分：{{ remainingPoints }}</div>
          <button class="btn btn-primary" @click="showResult = false">确定</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { shopApi } from '@/api'
import { useAuthStore } from '@/stores'
import type { Character, BoxResult } from '@/types'

const auth = useAuthStore()
const loading = ref(true)
const drawing = ref(false)
const balance = ref(0)
const characters = ref<Character[]>([])
const collection = ref<any[]>([])
const activeTab = ref<'shop' | 'collection'>('shop')

// 抽卡结果
const showResult = ref(false)
const resultItems = ref<BoxResult[]>([])
const remainingPoints = ref(0)

// 角色图标映射
const charIcons: Record<string, string> = {
  Wisdom: '/Floo/characters/wisdom.svg',
  Courage: '/Floo/characters/courage.svg',
  Hope: '/Floo/characters/hope.svg',
  Faith: '/Floo/characters/faith.svg',
  Grace: '/Floo/characters/grace.svg',
  Peace: '/Floo/characters/peace.svg',
  Love: '/Floo/characters/love.svg',
  Serenity: '/Floo/characters/serenity.svg',
  Brilliance: '/Floo/characters/brilliance.svg',
  Infinity: '/Floo/characters/infinity.svg',
}

function getCharIcon(name: string) {
  return charIcons[name] || '/Floo/characters/wisdom.svg'
}

onMounted(loadData)

async function loadData() {
  loading.value = true
  try {
    const userId = auth.currentUserId
    const [balanceRes, charsRes, collectionRes] = await Promise.all([
      shopApi.getBalance(userId),
      shopApi.getCharacters(userId),
      shopApi.getCollection(userId),
    ])
    balance.value = balanceRes.data.available_points
    characters.value = charsRes.data.characters
    collection.value = collectionRes.data.collection
  } catch { /* ignore */ }
  loading.value = false
}

async function openBox(count: number) {
  drawing.value = true
  try {
    const { data } = await shopApi.openBox(auth.currentUserId, count)
    resultItems.value = data.results
    remainingPoints.value = data.remaining_points
    balance.value = data.remaining_points
    showResult.value = true

    // 刷新收藏
    const collectionRes = await shopApi.getCollection(auth.currentUserId)
    collection.value = collectionRes.data.collection

    // 刷新角色列表（更新count）
    const charsRes = await shopApi.getCharacters(auth.currentUserId)
    characters.value = charsRes.data.characters
  } catch { /* ignore */ }
  drawing.value = false
}
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
}

.points-badge {
  background: linear-gradient(135deg, #FFD700, #FFA500);
  color: #fff;
  padding: 6px 12px;
  border-radius: 20px;
  font-weight: 700;
  font-size: 14px;
}

.tab-bar {
  display: flex;
  gap: 8px;
  padding: 0 16px;
  margin-bottom: 16px;
}

.tab-btn {
  flex: 1;
  padding: 10px;
  border: none;
  background: var(--surface-container);
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-btn.active {
  background: var(--primary);
  color: white;
}

.box-card {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0 16px 16px;
  padding: 16px;
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
  border-radius: 16px;
  color: white;
}

.box-icon {
  font-size: 40px;
}

.box-title {
  font-size: 18px;
  font-weight: 700;
}

.box-desc {
  font-size: 12px;
  opacity: 0.85;
}

.draw-buttons {
  display: flex;
  gap: 12px;
  padding: 0 16px;
  margin-bottom: 24px;
}

.draw-btn {
  flex: 1;
  padding: 16px 8px;
  border: 2px solid var(--primary);
  background: white;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.draw-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.draw-btn:not(:disabled):hover {
  background: var(--primary-container);
}

.draw-price {
  font-size: 16px;
  font-weight: 700;
  color: var(--primary);
}

.draw-label {
  font-size: 12px;
  color: var(--on-surface-variant);
  margin-top: 4px;
}

.draw-discount {
  position: absolute;
  top: -8px;
  right: -8px;
  background: #FF5722;
  color: white;
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 10px;
  font-weight: 600;
}

.section-title {
  padding: 0 16px;
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 12px;
}

.character-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  padding: 0 16px;
}

.character-card {
  background: var(--surface-container);
  border-radius: 12px;
  padding: 12px;
  text-align: center;
  position: relative;
  opacity: 0.5;
  transition: all 0.2s;
}

.character-card.collected {
  opacity: 1;
}

.character-card.common {
  border: 2px solid #9E9E9E;
}

.character-card.rare {
  border: 2px solid #2196F3;
}

.character-card.legendary {
  border: 2px solid #FFD700;
  background: linear-gradient(135deg, #FFF8E1, #FFFFFF);
}

.char-img {
  width: 48px;
  height: 48px;
  margin-bottom: 4px;
}

.char-name {
  font-size: 12px;
  color: var(--on-surface);
  font-weight: 600;
}

.char-word {
  font-size: 10px;
  color: var(--on-surface-variant);
}

.char-count {
  position: absolute;
  top: 4px;
  right: 4px;
  background: var(--primary);
  color: white;
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 10px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.empty-text {
  color: var(--on-surface-variant);
  font-size: 14px;
}

.collection-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 0 16px;
}

.collection-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--surface-container);
  border-radius: 12px;
}

.collection-card.common {
  border-left: 4px solid #9E9E9E;
}

.collection-card.rare {
  border-left: 4px solid #2196F3;
}

.collection-card.legendary {
  border-left: 4px solid #FFD700;
  background: linear-gradient(90deg, #FFF8E1, var(--surface-container));
}

.col-img {
  width: 48px;
  height: 48px;
  flex-shrink: 0;
}

.col-info {
  flex: 1;
}

.col-name {
  font-size: 14px;
  font-weight: 600;
}

.col-word {
  font-size: 12px;
  color: var(--on-surface-variant);
}

.col-desc {
  font-size: 11px;
  color: var(--on-surface-variant);
  margin-top: 2px;
}

.col-count {
  font-size: 14px;
  font-weight: 700;
  color: var(--primary);
}

/* 抽卡结果弹窗 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.result-modal {
  background: white;
  border-radius: 16px;
  padding: 24px;
  width: 90%;
  max-width: 400px;
  max-height: 80vh;
  overflow-y: auto;
}

.result-title {
  font-size: 20px;
  font-weight: 700;
  text-align: center;
  margin-bottom: 16px;
}

.result-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
}

.result-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 12px;
  background: var(--surface-container);
}

.result-item.common {
  border: 2px solid #9E9E9E;
}

.result-item.rare {
  border: 2px solid #2196F3;
}

.result-item.legendary {
  border: 2px solid #FFD700;
  background: linear-gradient(135deg, #FFF8E1, #FFFFFF);
}

.result-img {
  width: 48px;
  height: 48px;
  flex-shrink: 0;
}

.result-name {
  font-size: 14px;
  font-weight: 600;
}

.result-word {
  font-size: 12px;
  color: var(--on-surface-variant);
}

.result-new {
  font-size: 10px;
  color: #FF9800;
  font-weight: 600;
}

.result-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-points {
  font-size: 14px;
  color: var(--on-surface-variant);
}
</style>
