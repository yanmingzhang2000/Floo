<template>
  <div class="page-container">
    <div class="page-header">
      <h1>历史内容</h1>
    </div>

    <div v-if="loading" class="loading"><div class="spinner"></div></div>

    <div v-else-if="list.length === 0" class="empty-state">
      <div class="icon">📚</div>
      <p>暂无历史内容</p>
    </div>

    <div v-else class="list-view">
      <router-link v-for="item in list" :key="item.id" :to="`/learning/content/${item.id}`" class="list-item card">
        <div class="item-icon">📄</div>
        <div class="item-info">
          <div class="item-title">{{ item.title }}</div>
          <div class="item-meta">
            <span>{{ item.content_date }}</span>
            <span class="tag tag-primary" style="margin-left:8px">{{ item.difficulty_level }}</span>
          </div>
        </div>
        <span class="arrow">›</span>
      </router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { dailyApi } from '@/api'
import type { LearningContent } from '@/types'

const loading = ref(true)
const list = ref<LearningContent[]>([])

onMounted(async () => {
  try {
    const { data } = await dailyApi.getList(50)
    list.value = data
  } catch { list.value = [] }
  loading.value = false
})
</script>

<style scoped>
.list-view { padding: 8px 16px; }
.list-item {
  display: flex;
  align-items: center;
  gap: 12px;
  text-decoration: none;
  color: inherit;
  margin-bottom: 8px;
}
.item-icon { font-size: 28px; }
.item-info { flex: 1; }
.item-title { font-weight: 600; font-size: 15px; }
.item-meta { font-size: 13px; color: var(--on-surface-variant); margin-top: 4px; display: flex; align-items: center; }
.arrow { font-size: 20px; color: var(--on-surface-variant); }
</style>
