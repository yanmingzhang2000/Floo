<template>
  <view class="page-container floo-page">
    <!-- 顶部：品牌标题 + 仅保留设置 -->
    <view class="floo-header">
      <text class="floo-title">Floo</text>
      <view class="floo-icon-btn" @tap="goPreference">
        <text>⚙️</text>
      </view>
    </view>

    <view v-if="loading" class="loading">
      <view class="spinner"></view>
    </view>

    <template v-else>
      <!-- ① 积分总览卡片 -->
      <view class="floo-points-card">
        <view class="floo-points-top">
          <view>
            <text class="floo-points-label">当前积分</text>
            <view class="floo-points-row">
              <text class="floo-points-num">{{ balance }}</text>
              <text class="floo-points-unit">分</text>
            </view>
          </view>
          <text class="floo-points-detail" @tap="goShop">积分明细 ›</text>
        </view>
        <view class="floo-points-meta">
          <text class="floo-points-streak">🔥 已连续 {{ streakDays }} 天</text>
        </view>
      </view>

      <!-- ② 月度打卡日历 -->
      <view class="floo-section">
        <view class="floo-section-header">
          <text class="floo-section-title">本月打卡</text>
          <view class="floo-month-switch">
            <text class="floo-month-btn" @tap="changeMonth(-1)">‹</text>
            <text class="floo-month-label">{{ currentYear }}年{{ currentMonth }}月</text>
            <text class="floo-month-btn" @tap="changeMonth(1)">›</text>
          </view>
        </view>

        <view class="calendar-grid">
          <text v-for="d in weekLabels" :key="d" class="calendar-weekday">{{ d }}</text>
          <view
            v-for="(day, idx) in calendarDays"
            :key="idx"
            class="calendar-cell"
            :class="getDayClass(day)"
          >
            <text v-if="day" class="calendar-day-num">{{ day }}</text>
            <view v-if="day && isChecked(day)" class="calendar-check-dot"></view>
          </view>
        </view>

        <view class="checkin-btn-wrap">
          <text
            class="checkin-btn"
            :class="{ disabled: checking || todayChecked }"
            @tap="handleCheckin"
          >{{ checking ? '打卡中...' : (todayChecked ? '今日已完成 ✓' : '今日打卡') }}</text>
        </view>
        <text class="checkin-reward-hint">每日打卡 +10 分 · 连续 7 天额外 +30 分</text>

        <view v-if="showSuccess" class="checkin-success">
          <text>打卡成功！获得 +{{ lastEarned }} 积分</text>
        </view>
      </view>

      <!-- ③ 积分商城 -->
      <view class="floo-section">
        <view class="floo-section-header">
          <text class="floo-section-title">积分商城</text>
          <text class="floo-section-more" @tap="goShop">更多 ›</text>
        </view>

        <view class="shop-list">
          <view
            v-for="item in shopItems"
            :key="item.id"
            class="shop-item"
            @tap="openShopItem(item)"
          >
            <view class="shop-item-icon-wrap">
              <text class="shop-item-icon">{{ item.icon }}</text>
            </view>
            <view class="shop-item-info">
              <text class="shop-item-title">{{ item.title }}</text>
              <text class="shop-item-desc">{{ item.desc }}</text>
            </view>
            <view class="shop-item-price">
              <text v-if="balance >= item.cost" class="shop-item-price-num">{{ item.cost }} 分</text>
              <text v-else class="shop-item-price-gap">还差 {{ item.cost - balance }} 分</text>
            </view>
          </view>
        </view>
      </view>

      <view class="floo-footer-note">
        <text>坚持每天学习，积分越攒越多</text>
      </view>
    </template>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { checkinApi, shopApi } from '@/api'
import { useAuthStore } from '@/stores'
import { navTo } from '@/utils/router'
import type { CheckinCalendar } from '@/types'

/**
 * Floo 页：打卡 + 积分商城成长页
 *
 * 结构上是原 checkin + shop 的极简整合版：
 *   - 积分总览：顶部大数字卡
 *   - 月度打卡：日历 + 今日打卡 CTA
 *   - 积分商城：3-4 条兑换/抽卡入口，"更多"跳原 shop 页看完整列表
 *
 * Why 保留原 checkin/shop 页而不删：那两个页面上还有周报按钮、盲盒动画等
 * 深链功能，删掉伤及无辜。这里做整合入口，长尾功能靠"更多"进原页。
 */

const auth = useAuthStore()
const loading = ref(true)
const checking = ref(false)
const balance = ref(0)
const streakDays = ref(0)
const calendar = ref<CheckinCalendar | null>(null)
const currentYear = ref(new Date().getFullYear())
const currentMonth = ref(new Date().getMonth() + 1)
const showSuccess = ref(false)
const lastEarned = ref(0)

const weekLabels = ['日', '一', '二', '三', '四', '五', '六']

// 商城入口固定 3 条：抽卡 + 兑换 + AI 陪练
// 数值和 shop 页的真实商品对齐，避免用户被"假入口"误导
interface ShopEntry {
  id: string
  title: string
  desc: string
  cost: number
  icon: string
  action: 'gacha' | 'coach' | 'shop'
}
const shopItems: ShopEntry[] = [
  { id: 'gacha1', title: '好词盲盒 x1', desc: '解锁 1 个性格角色，收集你的性格树', cost: 50,   icon: '◇', action: 'gacha' },
  { id: 'gacha5', title: '好词盲盒 x5', desc: '一次开 5 个，集齐全套更快', cost: 200,  icon: '◆', action: 'gacha' },
  { id: 'coach',  title: 'AI 陪练 30min', desc: '与 AI 英语对话，纠正发音和语法', cost: 100, icon: '○', action: 'coach' },
]

// -------- 日历相关 --------
const todayChecked = computed(() => {
  const now = new Date()
  const today = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
  return calendar.value?.checked_dates?.includes(today) || false
})
const calendarDays = computed(() => {
  const first = new Date(currentYear.value, currentMonth.value - 1, 1).getDay()
  const total = new Date(currentYear.value, currentMonth.value, 0).getDate()
  const days: (number | null)[] = []
  for (let i = 0; i < first; i++) days.push(null)
  for (let i = 1; i <= total; i++) days.push(i)
  return days
})

function isChecked(day: number) {
  const dateStr = `${currentYear.value}-${String(currentMonth.value).padStart(2, '0')}-${String(day).padStart(2, '0')}`
  return calendar.value?.checked_dates?.includes(dateStr)
}
function isToday(day: number) {
  const now = new Date()
  return day === now.getDate()
    && currentMonth.value === now.getMonth() + 1
    && currentYear.value === now.getFullYear()
}
function getDayClass(day: number | null) {
  if (!day) return 'empty'
  const cls: string[] = []
  if (isToday(day)) cls.push('is-today')
  if (isChecked(day)) cls.push('is-checked')
  return cls.join(' ')
}
function changeMonth(delta: number) {
  currentMonth.value += delta
  if (currentMonth.value > 12) { currentMonth.value = 1; currentYear.value++ }
  if (currentMonth.value < 1) { currentMonth.value = 12; currentYear.value-- }
  loadCalendar()
}

// -------- 数据加载 --------
async function loadData() {
  loading.value = true
  await Promise.all([loadBalance(), loadCalendar()])
  loading.value = false
}

async function loadBalance() {
  try {
    const { data } = await shopApi.getBalance(auth.currentUserId)
    balance.value = data?.available_points || 0
  } catch (e) {
    console.debug('[Floo] 积分余额加载失败 err=%o', e)
    balance.value = 0
  }
}

async function loadCalendar() {
  try {
    const { data } = await checkinApi.getCalendar(
      auth.currentUserId,
      currentYear.value,
      currentMonth.value,
    )
    calendar.value = data
    streakDays.value = data?.current_streak_days || 0
  } catch (e) {
    console.debug('[Floo] 打卡日历加载失败 err=%o', e)
    calendar.value = null
  }
}

// -------- 交互 --------
async function handleCheckin() {
  if (todayChecked.value) {
    console.debug('[Floo] 今日已打卡，拦截')
    return
  }
  checking.value = true
  try {
    const { data } = await checkinApi.doCheckin(auth.currentUserId)
    lastEarned.value = data?.checkin?.earned_points || 10
    showSuccess.value = true
    setTimeout(() => { showSuccess.value = false }, 2500)
    // 打卡成功后并行刷新余额和日历
    await Promise.all([loadCalendar(), loadBalance()])
  } catch (e) {
    console.debug('[Floo] 打卡失败 err=%o', e)
    uni.showToast({ title: '打卡失败', icon: 'none' })
  }
  checking.value = false
}

function openShopItem(item: ShopEntry) {
  if (balance.value < item.cost) {
    console.debug('[Floo] 积分不足 need=%s have=%s', item.cost, balance.value)
    uni.showToast({ title: '积分不足', icon: 'none' })
    return
  }
  if (item.action === 'gacha') {
    // 盲盒动画在 shop 页，跳过去
    navTo('/pages/shop/index')
    return
  }
  if (item.action === 'coach') {
    navTo('/pages/ai-coach/index')
    return
  }
  navTo('/pages/shop/index')
}

function goShop() { navTo('/pages/shop/index') }
function goPreference() { navTo('/pages/preference/index') }

onShow(loadData)
</script>

<style scoped>
.floo-page { padding-bottom: 40rpx; }

/* 顶部标题：青绿通栏 */
.floo-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: calc(env(safe-area-inset-top, 44px) + 16rpx) 32rpx 24rpx;
  background: var(--primary, #5B9AA8);
  margin: 0 -20rpx 0;
}
.floo-title {
  font-size: 36rpx;
  font-weight: 600;
  color: #fff;
  letter-spacing: 0.5rpx;
}
.floo-icon-btn {
  width: 56rpx;
  height: 56rpx;
  border-radius: 50%;
  background: rgba(255,255,255,0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
}

/* 积分卡 */
.floo-points-card {
  margin: 24rpx 4rpx 0;
  padding: 36rpx 32rpx;
  background: #ffffff;
  box-shadow: 0 2rpx 12rpx rgba(91, 154, 168, 0.10);
  border-radius: 24rpx;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}
.floo-points-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}
.floo-points-label {
  font-size: 22rpx;
  color: var(--on-surface-variant);
  letter-spacing: 1rpx;
}
.floo-points-row {
  display: flex;
  align-items: baseline;
  gap: 8rpx;
  margin-top: 8rpx;
}
.floo-points-num {
  font-size: 72rpx;
  font-weight: 800;
  color: var(--primary);
  line-height: 1;
}
.floo-points-unit {
  font-size: 26rpx;
  color: var(--on-surface-variant);
  font-weight: 600;
}
.floo-points-detail {
  font-size: 24rpx;
  color: var(--primary);
  font-weight: 600;
}
.floo-points-meta { margin-top: 4rpx; }
.floo-points-streak {
  font-size: 22rpx;
  color: var(--on-surface-variant);
}

/* 分区 */
.floo-section {
  margin: 24rpx 4rpx 0;
  padding: 28rpx;
  background: #ffffff;
  box-shadow: 0 2rpx 12rpx rgba(91, 154, 168, 0.10);
  border-radius: 24rpx;
}
.floo-section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
}
.floo-section-title {
  font-size: 28rpx;
  font-weight: 700;
  color: var(--on-surface);
}
.floo-section-more {
  font-size: 24rpx;
  color: var(--primary);
  font-weight: 600;
}

/* 月份切换 */
.floo-month-switch {
  display: flex;
  align-items: center;
  gap: 12rpx;
}
.floo-month-btn {
  font-size: 32rpx;
  padding: 4rpx 12rpx;
  color: var(--primary);
}
.floo-month-label {
  font-size: 24rpx;
  font-weight: 600;
  color: var(--on-surface);
}

/* 日历 */
.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 8rpx;
  margin-bottom: 24rpx;
}
.calendar-weekday {
  text-align: center;
  font-size: 20rpx;
  color: #b0b8c0;
  padding: 8rpx 0;
  font-weight: 600;
}
.calendar-cell {
  aspect-ratio: 1;
  border-radius: 10rpx;
  border: 1rpx solid #e4eff2;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  background: #fff;
}
.calendar-cell.empty { visibility: hidden; }
.calendar-cell.is-today { border-color: var(--primary); border-width: 2rpx; }
.calendar-cell.is-checked {
  background: rgba(91,154,168,0.12);
  border-color: var(--primary);
}
.calendar-day-num { font-size: 22rpx; color: var(--on-surface); font-weight: 500; }
.calendar-cell.is-checked .calendar-day-num { color: var(--primary); font-weight: 700; }
.calendar-check-dot {
  width: 6rpx; height: 6rpx; border-radius: 50%;
  background: var(--primary); margin-top: 4rpx;
}

/* 打卡按钮 */
.checkin-btn-wrap { margin-top: 8rpx; }
.checkin-btn {
  display: block;
  width: 100%;
  padding: 24rpx 0;
  text-align: center;
  font-size: 28rpx;
  font-weight: 700;
  color: #fff;
  background: var(--primary);
  border-radius: 44rpx;
}
.checkin-btn.disabled {
  background: #d0d8dc;
  color: #fff;
}
.checkin-reward-hint {
  display: block;
  text-align: center;
  font-size: 22rpx;
  color: #b0b8c0;
  margin-top: 12rpx;
}
.checkin-success {
  margin-top: 16rpx;
  padding: 16rpx;
  background: rgba(91,154,168,0.1);
  color: var(--primary);
  border-radius: 12rpx;
  text-align: center;
  font-size: 26rpx;
  font-weight: 600;
}

/* 商城列表 */
.shop-list { display: flex; flex-direction: column; gap: 12rpx; }
.shop-item {
  display: flex;
  align-items: center;
  gap: 20rpx;
  padding: 24rpx 20rpx;
  background: #fff;
  border: 1rpx solid #e4eff2;
  border-radius: 16rpx;
  transition: transform 0.15s;
}
.shop-item:active { transform: scale(0.98); }
.shop-item-icon-wrap {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  border: 2rpx solid var(--primary);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.shop-item-icon { font-size: 28rpx; color: var(--primary); font-weight: 700; }
.shop-item-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4rpx;
  min-width: 0;
}
.shop-item-title { font-size: 28rpx; font-weight: 700; color: var(--on-surface); }
.shop-item-desc { font-size: 22rpx; color: var(--on-surface-variant); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.shop-item-price { flex-shrink: 0; }
.shop-item-price-num { font-size: 26rpx; font-weight: 700; color: var(--primary); }
.shop-item-price-gap { font-size: 22rpx; color: #b0b8c0; }

/* 页脚 */
.floo-footer-note {
  text-align: center;
  padding: 32rpx 0 0;
  font-size: 22rpx;
  color: #b0b8c0;
}
</style>
