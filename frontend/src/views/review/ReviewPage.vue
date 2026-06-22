<template>
  <div class="page-container">
    <div class="page-header">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <h1>复习</h1>
        <button class="btn btn-sm btn-header" @click="reloadKey++">🔄 刷新</button>
      </div>
    </div>

    <!-- 功能入口 -->
    <div class="feature-tabs">
      <div class="feature-tab" :class="{ active: activeTab === 'review' }" @click="activeTab = 'review'">
        <span class="feature-icon">🔄</span>
        <span class="feature-name">记忆复习</span>
      </div>
      <div class="feature-tab" :class="{ active: activeTab === 'dictation' }" @click="activeTab = 'dictation'">
        <span class="feature-icon">✏️</span>
        <span class="feature-name">默写练习</span>
      </div>
      <div class="feature-tab" :class="{ active: activeTab === 'vocab' }" @click="activeTab = 'vocab'">
        <span class="feature-icon">📚</span>
        <span class="feature-name">词汇默写</span>
      </div>
    </div>

    <div v-if="loading" class="loading"><div class="spinner"></div></div>

    <template v-else>
      <MemoryReviewTab v-if="activeTab === 'review'" :key="reloadKey" />
      <DictationTab v-else-if="activeTab === 'dictation'" :key="reloadKey" />
      <VocabDictationTab v-else-if="activeTab === 'vocab'" :key="reloadKey" />
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import MemoryReviewTab from './MemoryReviewTab.vue'
import DictationTab from './DictationTab.vue'
import VocabDictationTab from './VocabDictationTab.vue'

const route = useRoute()
const loading = ref(true)
const activeTab = ref<'review' | 'dictation' | 'vocab'>('review')
const reloadKey = ref(0)

onMounted(() => {
  // 支持 ?tab=dictation 参数自动切换到默写 Tab
  const tab = route.query.tab as string
  if (tab && ['review', 'dictation', 'vocab'].includes(tab)) {
    activeTab.value = tab as 'review' | 'dictation' | 'vocab'
  }
  loading.value = false
})
</script>

<style scoped>
.feature-tabs {
  display: flex;
  gap: 12px;
  padding: 12px 16px;
}

.feature-tab {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 16px 12px;
  background: var(--surface-container);
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.feature-tab.active {
  background: var(--primary);
  color: white;
}

.feature-icon { font-size: 24px; }
.feature-name { font-size: 13px; font-weight: 500; }
</style>
