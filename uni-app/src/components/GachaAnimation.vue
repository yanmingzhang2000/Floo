<template>
  <!-- 全屏动画遮罩 -->
  <view v-if="visible" class="gacha-overlay" @tap.stop>
    <!-- 背景光效 -->
    <view class="gacha-bg" :class="[currentRarity, { 'bg-active': showCard }]"></view>

    <!-- 卡牌区域 -->
    <view class="card-area">
      <!-- 卡背 -->
      <view v-if="!showCard" class="card-wrapper card-back-wrapper">
        <view class="card-back">
          <view class="card-back-pattern">
            <text class="card-back-icon">✨</text>
            <text class="card-back-text">品质盲盒</text>
          </view>
        </view>
      </view>

      <!-- 卡牌翻转 -->
      <view v-else class="card-wrapper card-flip-wrapper" :class="{ 'flip-active': flipped }">
        <view class="card-front" :class="currentRarity">
          <!-- 光效层 -->
          <view class="card-glow" :class="currentRarity"></view>

          <!-- 角色内容 -->
          <view class="card-content">
            <view class="card-rarity-badge" :class="currentRarity">
              <text>{{ rarityText }}</text>
            </view>
            <view class="card-character-icon" v-html="characterSvg"></view>
            <text class="card-name">{{ currentCharacter?.name }}</text>
            <text class="card-meaning">{{ currentCharacter?.meaning }}</text>
            <view class="card-divider" :class="currentRarity"></view>
            <text class="card-blessing">{{ currentBlessing }}</text>
            <text v-if="currentCharacter?.is_new" class="card-new-badge">NEW!</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 提示文字 -->
    <view v-if="showCard && flipped" class="tap-hint" @tap="handleTap">
      <text class="tap-hint-text">{{ isLastCard ? '点击关闭' : '点击继续' }}</text>
    </view>

    <!-- 多连抽进度 -->
    <view v-if="totalCount > 1" class="progress-dots">
      <view
        v-for="(_, idx) in totalCount"
        :key="idx"
        class="dot"
        :class="{ active: idx === currentIndex, done: idx < currentIndex }"
      ></view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'

interface GachaCharacter {
  character_id: number
  name: string
  meaning: string
  rarity: string
  is_new: boolean
  description?: string
}

const props = defineProps<{
  visible: boolean
  characters: GachaCharacter[]
  currentIndex: number
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'next'): void
}>()

const flipped = ref(false)
const showCard = ref(false)

const currentCharacter = computed(() => props.characters[props.currentIndex])
const currentRarity = computed(() => currentCharacter.value?.rarity || 'common')
const totalCount = computed(() => props.characters.length)
const isLastCard = computed(() => props.currentIndex === totalCount.value - 1)

const rarityText = computed(() => {
  const map: Record<string, string> = {
    legendary: '传说',
    rare: '稀有',
    common: '普通',
  }
  return map[currentRarity.value] || '普通'
})

// 按稀有度返回线条风格 SVG 图标，白色描边 + 透明填充，视觉上与各自卡面配色呼应
const characterSvg = computed(() => {
  const map: Record<string, string> = {
    // 皇冠：三个冠尖 + 顶端圆点，象征最高荣誉
    legendary: `<svg width="80" height="80" viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M10 64 L10 36 L24 50 L40 12 L56 50 L70 36 L70 64 Q70 68 66 68 L14 68 Q10 68 10 64 Z" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/><circle cx="40" cy="11" r="3.5" fill="white"/><circle cx="10" cy="36" r="3" fill="white"/><circle cx="70" cy="36" r="3" fill="white"/></svg>`,
    // 宝石：竖向切割钻石 + 内部棱面线
    rare: `<svg width="80" height="80" viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg"><polygon points="40,8 66,32 40,72 14,32" stroke="white" stroke-width="2.5" stroke-linejoin="round"/><line x1="14" y1="32" x2="66" y2="32" stroke="white" stroke-width="1.5" stroke-opacity="0.55"/><line x1="27" y1="20" x2="40" y2="32" stroke="white" stroke-width="1.5" stroke-opacity="0.4"/><line x1="53" y1="20" x2="40" y2="32" stroke="white" stroke-width="1.5" stroke-opacity="0.4"/></svg>`,
    // 四角星：纤细四尖星，线条简洁优雅
    common: `<svg width="80" height="80" viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M40 6 L45 28 L74 40 L45 52 L40 74 L35 52 L6 40 L35 28 Z" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
  }
  return map[currentRarity.value] || map['common']
})

// 品质祝福语
const blessings: Record<string, string[]> = {
  legendary: [
    '愿你拥有卓越的智慧，照亮前行的路',
    '愿这份美好品质，成为你生命中的光芒',
    '传说级的品质，愿你心中永远闪耀',
    '愿你如星辰般璀璨，绽放独特光彩',
    '这份珍贵的品质，愿它伴你走向辉煌',
  ],
  rare: [
    '愿你拥有这份独特的美好品质',
    '稀有的品质，愿你善用它的力量',
    '这份品质如同宝石，愿你珍惜',
    '愿你在这份品质中找到力量',
    '美好的品质，愿你活出精彩',
  ],
  common: [
    '每一份美好都值得珍惜',
    '愿这份品质给你带来温暖',
    '平凡中的美好，最是珍贵',
    '愿你每天都能感受到这份美好',
    '美好的品质，从小事做起',
  ],
}

const currentBlessing = computed(() => {
  const pool = blessings[currentRarity.value] || blessings.common
  return pool[Math.floor(Math.random() * pool.length)]
})

// 监听 visible 变化，开始动画
watch(
  () => props.visible,
  (val) => {
    if (val) {
      flipped.value = false
      showCard.value = false
      startAnimation()
    }
  }
)

function startAnimation() {
  // 先显示卡背，延迟后翻转
  setTimeout(() => {
    showCard.value = true
    // 翻转动画
    setTimeout(() => {
      flipped.value = true
      // 播放音效
      playSound()
    }, 100)
  }, 800)
}

function playSound() {
  try {
    const audio = new Audio()
    const soundMap: Record<string, string> = {
      legendary: '/static/sounds/gacha_legendary.mp3',
      rare: '/static/sounds/gacha_rare.mp3',
      common: '/static/sounds/gacha_common.mp3',
    }
    audio.src = soundMap[currentRarity.value] || soundMap.common
    audio.volume = 0.5
    audio.play().catch(() => {})
  } catch {}
}

function handleTap() {
  if (isLastCard.value) {
    emit('close')
  } else {
    emit('next')
  }
}
</script>

<style scoped>
.gacha-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.9);
}

.gacha-bg {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 600rpx;
  height: 600rpx;
  border-radius: 50%;
  opacity: 0;
  transition: all 0.8s ease-out;
  filter: blur(60rpx);
}

.gacha-bg.bg-active {
  opacity: 0.6;
}

.gacha-bg.legendary {
  background: radial-gradient(circle, #FFD700, #FFA500);
}

.gacha-bg.rare {
  background: radial-gradient(circle, #9C27B0, #7B1FA2);
}

.gacha-bg.common {
  background: radial-gradient(circle, #E0E0E0, #9E9E9E);
}

.card-area {
  position: relative;
  width: 400rpx;
  height: 560rpx;
  perspective: 1200rpx;
}

.card-wrapper {
  width: 100%;
  height: 100%;
  position: relative;
}

.card-back-wrapper {
  animation: float 2s ease-in-out infinite;
}

.card-flip-wrapper {
  transform-style: preserve-3d;
  transition: transform 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

.card-flip-wrapper.flip-active {
  transform: rotateY(180deg);
}

.card-back,
.card-front {
  position: absolute;
  width: 100%;
  height: 100%;
  backface-visibility: hidden;
  border-radius: 24rpx;
  overflow: hidden;
}

.card-back {
  background: linear-gradient(135deg, #5B9AA8 0%, #3D7A85 100%);
  box-shadow: 0 20rpx 60rpx rgba(0, 0, 0, 0.5);
}

.card-back-pattern {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: repeating-linear-gradient(
    45deg,
    transparent,
    transparent 20rpx,
    rgba(255, 255, 255, 0.05) 20rpx,
    rgba(255, 255, 255, 0.05) 40rpx
  );
}

.card-back-icon {
  font-size: 80rpx;
  margin-bottom: 16rpx;
}

.card-back-text {
  color: white;
  font-size: 28rpx;
  font-weight: 600;
  letter-spacing: 8rpx;
}

.card-front {
  transform: rotateY(180deg);
  background: white;
  box-shadow: 0 20rpx 60rpx rgba(0, 0, 0, 0.5);
}

.card-front.legendary {
  background: linear-gradient(180deg, #FFF8E1 0%, #FFE082 50%, #FFD54F 100%);
}

.card-front.rare {
  background: linear-gradient(180deg, #F3E5F5 0%, #CE93D8 50%, #AB47BC 100%);
}

.card-front.common {
  background: linear-gradient(180deg, #FAFAFA 0%, #E0E0E0 50%, #BDBDBD 100%);
}

.card-glow {
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  opacity: 0.3;
  animation: glow-pulse 2s ease-in-out infinite;
}

.card-glow.legendary {
  background: radial-gradient(circle, #FFD700 0%, transparent 70%);
}

.card-glow.rare {
  background: radial-gradient(circle, #CE93D8 0%, transparent 70%);
}

.card-glow.common {
  background: radial-gradient(circle, #E0E0E0 0%, transparent 70%);
}

.card-content {
  position: relative;
  z-index: 1;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32rpx;
  box-sizing: border-box;
}

.card-rarity-badge {
  position: absolute;
  top: 20rpx;
  right: 20rpx;
  padding: 8rpx 20rpx;
  border-radius: 20rpx;
  font-size: 20rpx;
  font-weight: 700;
  color: white;
}

.card-rarity-badge.legendary {
  background: linear-gradient(135deg, #FFD700, #FFA000);
}

.card-rarity-badge.rare {
  background: linear-gradient(135deg, #9C27B0, #7B1FA2);
}

.card-rarity-badge.common {
  background: linear-gradient(135deg, #9E9E9E, #757575);
}

.card-character-icon {
  width: 120rpx;
  height: 120rpx;
  margin-bottom: 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-name {
  font-size: 40rpx;
  font-weight: 800;
  color: #333;
  margin-bottom: 8rpx;
}

.card-meaning {
  font-size: 28rpx;
  color: #666;
  margin-bottom: 24rpx;
}

.card-divider {
  width: 120rpx;
  height: 4rpx;
  border-radius: 2rpx;
  margin-bottom: 24rpx;
}

.card-divider.legendary {
  background: linear-gradient(90deg, transparent, #FFD700, transparent);
}

.card-divider.rare {
  background: linear-gradient(90deg, transparent, #9C27B0, transparent);
}

.card-divider.common {
  background: linear-gradient(90deg, transparent, #9E9E9E, transparent);
}

.card-blessing {
  font-size: 24rpx;
  color: #666;
  text-align: center;
  line-height: 1.6;
  font-style: italic;
}

.card-new-badge {
  position: absolute;
  bottom: 24rpx;
  left: 50%;
  transform: translateX(-50%);
  background: linear-gradient(135deg, #FF6B6B, #FF8E53);
  color: white;
  font-size: 24rpx;
  font-weight: 700;
  padding: 8rpx 32rpx;
  border-radius: 24rpx;
  animation: badge-bounce 0.6s ease-out;
}

.tap-hint {
  position: absolute;
  bottom: 120rpx;
  left: 50%;
  transform: translateX(-50%);
  animation: fadeIn 0.5s ease-out 0.5s both;
}

.tap-hint-text {
  color: rgba(255, 255, 255, 0.7);
  font-size: 26rpx;
}

.progress-dots {
  position: absolute;
  bottom: 60rpx;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 16rpx;
}

.dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  transition: all 0.3s ease;
}

.dot.active {
  background: white;
  transform: scale(1.3);
}

.dot.done {
  background: rgba(255, 255, 255, 0.6);
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-20rpx); }
}

@keyframes glow-pulse {
  0%, 100% { opacity: 0.3; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.1); }
}

@keyframes badge-bounce {
  0% { transform: translateX(-50%) scale(0); }
  50% { transform: translateX(-50%) scale(1.2); }
  100% { transform: translateX(-50%) scale(1); }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style>
