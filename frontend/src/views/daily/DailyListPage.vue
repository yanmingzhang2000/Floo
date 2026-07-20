<template>
  <div class="page-container">
    <div class="page-header">
      <button class="btn-back" @click="router.back()">← 返回</button>
      <h1>历史内容</h1>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <button
        v-for="f in filters"
        :key="f.value"
        class="filter-chip"
        :class="{ active: activeFilter === f.value }"
        @click="activeFilter = f.value"
      >
        {{ f.label }}
        <span class="filter-count">{{ counts[f.value] }}</span>
      </button>
    </div>

    <div v-if="loading" class="loading"><div class="spinner"></div></div>

    <div v-else-if="filteredList.length === 0" class="empty-state">
      <div class="icon">📚</div>
      <p>{{ activeFilter === 'all' ? '暂无历史内容' : '该分类下暂无内容' }}</p>
    </div>

    <div v-else class="list-view">
      <router-link
        v-for="item in filteredList"
        :key="item.id"
        :to="`/learning/content/${item.id}`"
        class="list-item card"
      >
        <div class="item-icon">{{ item.creator_type === 1 ? '✏️' : '🤖' }}</div>
        <div class="item-info">
          <div class="item-title">{{ item.title }}</div>
          <div class="item-meta">
            <span>{{ item.content_date }}</span>
            <span
              class="tag"
              :class="item.creator_type === 1 ? 'tag-custom' : 'tag-ai'"
              style="margin-left:6px"
            >{{ item.creator_type === 1 ? '自定义' : 'AI' }}</span>
          </div>
        </div>
        <span class="arrow">›</span>
      </router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { dailyApi } from '@/api'
import type { LearningContent } from '@/types'

const router = useRouter()
const loading = ref(true)
const list = ref<LearningContent[]>([])

// 当前激活的筛选项：all / ai / custom
const activeFilter = ref<'all' | 'ai' | 'custom'>('all')

const filters = [
  { value: 'all' as const,    label: '全部' },
  { value: 'ai' as const,     label: '🤖 AI生成' },
  { value: 'custom' as const, label: '✏️ 自定义' },
]

// 按筛选项过滤列表
const filteredList = computed(() => {
  if (activeFilter.value === 'ai')     return list.value.filter(i => i.creator_type !== 1)
  if (activeFilter.value === 'custom') return list.value.filter(i => i.creator_type === 1)
  return list.value
})

// 各 tab 的数量徽标
const counts = computed(() => ({
  all:    list.value.length,
  ai:     list.value.filter(i => i.creator_type !== 1).length,
  custom: list.value.filter(i => i.creator_type === 1).length,
}))

onMounted(async () => {
  try {
    const { data } = await dailyApi.getList(50)
    list.value = data
  } catch { list.value = [] }
  loading.value = false
})
</script>

<style scoped>
/* 筛选栏 */
.filter-bar {
  display: flex;
  gap: 8px;
  padding: 10px 16px 4px;
  overflow-x: auto;
}
.filter-chip {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 14px;
  border-radius: 20px;
  border: 1.5px solid var(--outline, #ccc);
  background: transparent;
  font-size: 13px;
  cursor: pointer;
  white-space: nowrap;
  color: var(--on-surface-variant);
  transition: all 0.15s;
}
.filter-chip.active {
  background: var(--primary, #6750A4);
  border-color: var(--primary, #6750A4);
  color: #fff;
}
.filter-count {
  font-size: 11px;
  opacity: 0.75;
}

/* 列表 */
.list-view { padding: 8px 16px; }
.list-item {
  display: flex;
  align-items: center;
  gap: 12px;
  text-decoration: none;
  color: inherit;
  margin-bottom: 8px;
}
.item-icon { font-size: 24px; }
.item-info { flex: 1; }
.item-title { font-weight: 600; font-size: 15px; }
.item-meta {
  font-size: 13px;
  color: var(--on-surface-variant);
  margin-top: 4px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
}
.arrow { font-size: 20px; color: var(--on-surface-variant); }

/* 来源标签 */
.tag-ai     { background: #e8f4fd; color: #1a73e8; }
.tag-custom { background: #fef3e2; color: #e67e00; }
</style>
