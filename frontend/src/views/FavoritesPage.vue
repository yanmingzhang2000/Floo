<template>
  <div class="page-container">
    <div class="page-header">
      <h1>单词书</h1>
      <p class="subtitle">共 {{ favorites.length }} 个单词</p>
    </div>

    <div v-if="loading" class="loading"><div class="spinner"></div></div>

    <div v-else-if="favorites.length === 0" class="empty-state">
      <div class="icon">📚</div>
      <p>还没有收藏单词</p>
      <p style="font-size:13px;color:var(--on-surface-variant);margin-top:8px">在学习页面点击单词即可收藏</p>
    </div>

    <div v-else class="word-list">
      <div v-for="fav in favorites" :key="fav.id" class="word-card card" @click="playWord(fav.word)">
        <div class="word-main">
          <div class="word-text">{{ fav.word }}</div>
          <button class="fav-btn is-fav" @click.stop="handleRemove(fav.word)">★</button>
        </div>
        <div class="word-phonetic" v-if="fav.phonetic">{{ fav.phonetic }}</div>
        <div class="word-meaning">{{ fav.meaning }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { favoritesApi } from '@/api'
import { useAuthStore } from '@/stores'
import { speakWord } from '@/composables/useSpeech'
import { useConfirm } from '@/composables/useConfirm'

const auth = useAuthStore()
const { confirm } = useConfirm()
const loading = ref(true)
const favorites = ref<Array<{
  id: number
  word: string
  phonetic?: string
  meaning?: string
  source?: string
  created_at: string
}>>([])

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
  const ok = await confirm({
    title: '取消收藏',
    message: `确定取消收藏 "${word}" 吗？`,
    confirmText: '取消收藏',
    confirmClass: 'btn-danger',
  })
  if (!ok) return
  try {
    await favoritesApi.remove(auth.currentUserId, word)
    favorites.value = favorites.value.filter(f => f.word !== word)
  } catch { /* ignore */ }
}
</script>

<style scoped>
.page-container { padding-bottom: 20px; }
.page-header { padding: 16px; }

.word-list {
  padding: 0 16px;
}

.word-card {
  padding: 14px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: background 0.2s;
}

.word-card:hover { background: var(--surface-container); }

.word-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.word-text {
  font-size: 18px;
  font-weight: 600;
  color: var(--on-surface);
}

.fav-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  font-size: 20px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.fav-btn.is-fav { color: #f59e0b; }

.word-phonetic {
  font-size: 13px;
  color: var(--on-surface-variant);
  margin-bottom: 4px;
}

.word-meaning {
  font-size: 14px;
  color: var(--on-surface-variant);
}
</style>
