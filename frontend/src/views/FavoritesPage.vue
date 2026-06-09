<template>
  <div class="page-container">
    <div class="page-header">
      <h1>我的收藏</h1>
      <p class="subtitle">共收藏 {{ favorites.length }} 个单词</p>
    </div>

    <div v-if="loading" class="loading"><div class="spinner"></div></div>

    <div v-else-if="favorites.length === 0" class="empty-state">
      <div class="icon">📚</div>
      <p>还没有收藏单词</p>
      <p style="font-size:13px;color:var(--on-surface-variant);margin-top:8px">在学习页面点击单词即可收藏</p>
    </div>

    <div v-else class="favorites-list">
      <div v-for="fav in favorites" :key="fav.id" class="fav-card card" @click="playWord(fav.word)">
        <div class="fav-main">
          <div class="fav-word">{{ fav.word }}</div>
          <div class="fav-phonetic" v-if="fav.phonetic">{{ fav.phonetic }}</div>
        </div>
        <div class="fav-meaning">{{ fav.meaning }}</div>
        <div class="fav-meta">
          <span v-if="fav.source" class="fav-source">{{ sourceLabels[fav.source] || fav.source }}</span>
          <span class="fav-date">{{ fav.created_at }}</span>
        </div>
        <button class="fav-remove" @click.stop="handleRemove(fav.word)">×</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { favoritesApi } from '@/api'
import { useAuthStore } from '@/stores'
import { speakWord } from '@/composables/useSpeech'

const auth = useAuthStore()
const loading = ref(true)
const favorites = ref<Array<{
  id: number
  word: string
  phonetic?: string
  meaning?: string
  source?: string
  created_at: string
}>>([])

const sourceLabels: Record<string, string> = {
  daily: '每日学习',
  dictation: '默写',
  review: '复习',
}

onMounted(loadData)

async function loadData() {
  try {
    const { data } = await favoritesApi.list(auth.currentUserId)
    favorites.value = data
  } catch { /* ignore */ }
  loading.value = false
}

function playWord(word: string) {
  speakWord(word)
}

async function handleRemove(word: string) {
  if (!confirm(`确定取消收藏 "${word}" 吗？`)) return
  try {
    await favoritesApi.remove(auth.currentUserId, word)
    favorites.value = favorites.value.filter(f => f.word !== word)
  } catch { /* ignore */ }
}
</script>

<style scoped>
.page-container { padding-bottom: 20px; }
.page-header { padding: 16px; }

.favorites-list {
  padding: 0 16px;
}

.fav-card {
  position: relative;
  padding: 14px 40px 14px 14px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: background 0.2s;
}

.fav-card:hover { background: var(--surface-container); }

.fav-main {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 6px;
}

.fav-word {
  font-size: 18px;
  font-weight: 600;
  color: var(--on-surface);
}

.fav-phonetic {
  font-size: 13px;
  color: var(--on-surface-variant);
}

.fav-meaning {
  font-size: 14px;
  color: var(--on-surface-variant);
  margin-bottom: 6px;
}

.fav-meta {
  display: flex;
  gap: 8px;
  font-size: 12px;
  color: var(--on-surface-variant);
  opacity: 0.7;
}

.fav-source {
  background: var(--primary-container);
  color: var(--on-primary-container);
  padding: 1px 6px;
  border-radius: 4px;
}

.fav-remove {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  width: 28px;
  height: 28px;
  border: none;
  background: var(--surface-container-high);
  border-radius: 50%;
  font-size: 18px;
  color: var(--on-surface-variant);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.fav-remove:hover { background: #ef4444; color: white; }
</style>
