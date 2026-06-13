<template>
  <div class="landing">
    <!-- Hero -->
    <section class="hero">
      <div class="hero-bg"></div>
      <div class="hero-content">
        <div class="logo-area">
          <img src="/Floo/logo.jpg" alt="Floo!" class="logo-img" />
        </div>
        <h1 class="brand">Floo!</h1>
        <p class="tagline">飞路一下</p>
        <p class="subtitle">每天 5 分钟，英语悄悄变好</p>
        <a href="/Floo/login" class="cta-btn">开始学习 →</a>
        <p class="cta-hint">免费 · 无需下载 · 打开即用</p>
      </div>
    </section>

    <!-- Pain point -->
    <section class="section pain-section">
      <div class="container">
        <h2 class="section-title">你是不是也这样？</h2>
        <div class="pain-list">
          <div class="pain-item" v-for="p in pains" :key="p">
            <span class="pain-icon">😤</span>
            <span>{{ p }}</span>
          </div>
        </div>
        <p class="pain-answer">问题不在于你不够努力，而在于<strong>学习方式太枯燥</strong>。</p>
      </div>
    </section>

    <!-- What is Floo -->
    <section class="section feature-section">
      <div class="container">
        <h2 class="section-title">Floo! 是什么？</h2>
        <p class="feature-desc">
          一个<strong>极简英语学习工具</strong>。不背单词、不刷题、不考试。<br />
          每天 AI 给你推送一篇精选文章，5-10 分钟轻松读完。
        </p>
        <div class="philosophy">
          <div class="phil-item" v-for="ph in philosophy" :key="ph.text">
            <span class="phil-icon">{{ ph.icon }}</span>
            <span class="phil-text">{{ ph.text }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- Features -->
    <section class="section features-section">
      <div class="container">
        <h2 class="section-title">核心功能</h2>
        <div class="feature-grid">
          <div class="feature-card" v-for="f in features" :key="f.title">
            <div class="feature-icon">{{ f.icon }}</div>
            <h3>{{ f.title }}</h3>
            <p>{{ f.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Who is it for -->
    <section class="section audience-section">
      <div class="container">
        <h2 class="section-title">适合谁？</h2>
        <div class="audience-grid">
          <div class="audience-item" v-for="a in audience" :key="a">
            <span class="audience-check">✓</span>
            <span>{{ a }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- Tech stack -->
    <section class="section tech-section">
      <div class="container">
        <h2 class="section-title">技术栈</h2>
        <div class="tech-tags">
          <span class="tech-tag" v-for="t in techStack" :key="t">{{ t }}</span>
        </div>
        <p class="tech-note">全栈独立开发 · 开源 · 无广告</p>
      </div>
    </section>

    <!-- CTA -->
    <section class="section cta-section">
      <div class="container">
        <div class="cta-card">
          <h2>不逼你卷，不制造焦虑</h2>
          <p>安安静静帮你学英语</p>
          <a href="/Floo/login" class="cta-btn cta-btn-large">立即体验 Floo! →</a>
        </div>
      </div>
    </section>

    <!-- Footer -->
    <footer class="footer">
      <p>Floo! 飞路一下 · Made with ❤️</p>
    </footer>
  </div>
</template>

<script setup lang="ts">
const pains = [
  '下定决心学英语，三天热度就过了',
  '下载了十几个 App，全部吃灰',
  '背单词太枯燥，坚持不下来',
  '买了好多资料，一本也没看完',
]

const philosophy = [
  { icon: '📰', text: '不贪多' },
  { icon: '😌', text: '不焦虑' },
  { icon: '🌱', text: '每天一点点' },
]

const features = [
  {
    icon: '📰',
    title: '每日精选文章',
    desc: 'AI 根据你的水平和兴趣量身定制，难度可选、主题可选，每篇配有翻译和重点词汇。',
  },
  {
    icon: '✍️',
    title: '默写检验',
    desc: '看完就能默写，AI 自动批改并给出详细反馈，写错的词重点标记。',
  },
  {
    icon: '🧠',
    title: '智能复习',
    desc: '基于艾宾浩斯记忆曲线，自动安排第 1、2、4、7、15 天复习计划，不用自己记。',
  },
  {
    icon: '🎤',
    title: '语音评测',
    desc: '接入有道智云，朗读单词和句子，从准确度、流利度、完整度三个维度打分。',
  },
  {
    icon: '📅',
    title: '打卡日历',
    desc: '莫兰迪色系热力图，连续打卡颜色渐变，看着日历一天天填满，比鸡汤管用。',
  },
  {
    icon: '🐱',
    title: '积分商城',
    desc: '学习攒积分，积分抽盲盒。10 只手绘小猫角色，有普通、稀有、传说级。',
  },
]

const audience = [
  '想学英语但总是坚持不下来的人',
  '不喜欢背单词、刷题的「反卷」选手',
  '想利用碎片时间提升英语的上班族',
  '喜欢轻量级工具、讨厌广告打扰的人',
]

const techStack = [
  'Vue 3', 'TypeScript', 'FastAPI', 'PostgreSQL',
  'Pinia', 'Vue Router', 'Vite', 'Railway',
]
</script>

<style scoped>
* { margin: 0; padding: 0; box-sizing: border-box; }

.landing {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
  color: #3A3A3A;
  background: #FAF8F5;
  line-height: 1.6;
  overflow-x: hidden;
}

.container {
  max-width: 680px;
  margin: 0 auto;
  padding: 0 24px;
}

/* ===== Hero ===== */
.hero {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  overflow: hidden;
}

.hero-bg {
  position: absolute;
  inset: 0;
  background: linear-gradient(160deg, #E8C4C4 0%, #C9D6DF 40%, #D5C9D1 70%, #C8D5BB 100%);
  opacity: 0.45;
}

.hero-content {
  position: relative;
  z-index: 1;
  padding: 40px 24px;
  width: 100%;
}

.logo-area {
  margin-bottom: 20px;
  text-align: center;
}

.logo-img {
  width: 88px;
  height: 88px;
  border-radius: 22px;
  object-fit: contain;
  box-shadow: 0 4px 16px rgba(91, 154, 168, 0.3);
}

.brand {
  font-size: 56px;
  font-weight: 800;
  color: #2C3E50;
  letter-spacing: -1px;
  margin-bottom: 4px;
}

.tagline {
  font-size: 20px;
  color: #5B9AA8;
  font-weight: 600;
  margin-bottom: 16px;
}

.subtitle {
  font-size: 17px;
  color: #666;
  margin-bottom: 36px;
}

.cta-btn {
  display: inline-block;
  padding: 14px 40px;
  background: #5B9AA8;
  color: white;
  text-decoration: none;
  border-radius: 50px;
  font-size: 17px;
  font-weight: 600;
  transition: all 0.3s ease;
  box-shadow: 0 4px 20px rgba(91, 154, 168, 0.3);
}

.cta-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 28px rgba(91, 154, 168, 0.4);
  background: #4E8A97;
}

.cta-hint {
  margin-top: 14px;
  font-size: 13px;
  color: #999;
}

/* ===== Sections ===== */
.section {
  padding: 72px 0;
}

.section-title {
  font-size: 26px;
  font-weight: 700;
  text-align: center;
  margin-bottom: 32px;
  color: #2C3E50;
}

/* ===== Pain ===== */
.pain-section {
  background: white;
}

.pain-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-bottom: 28px;
}

.pain-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  background: #FFF8F0;
  border-radius: 12px;
  font-size: 15px;
}

.pain-icon { font-size: 20px; }

.pain-answer {
  text-align: center;
  font-size: 16px;
  color: #666;
}

.pain-answer strong {
  color: #5B9AA8;
}

/* ===== Feature desc ===== */
.feature-desc {
  text-align: center;
  font-size: 16px;
  color: #555;
  margin-bottom: 32px;
  line-height: 1.8;
}

.philosophy {
  display: flex;
  justify-content: center;
  gap: 32px;
}

.phil-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.phil-icon { font-size: 32px; }
.phil-text { font-size: 15px; font-weight: 600; color: #5B9AA8; }

/* ===== Features Grid ===== */
.features-section {
  background: white;
}

.feature-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.feature-card {
  padding: 24px 20px;
  background: #FAF8F5;
  border-radius: 16px;
  transition: transform 0.2s;
}

.feature-card:hover {
  transform: translateY(-3px);
}

.feature-icon {
  font-size: 28px;
  margin-bottom: 10px;
}

.feature-card h3 {
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 6px;
  color: #2C3E50;
}

.feature-card p {
  font-size: 13px;
  color: #777;
  line-height: 1.5;
}

/* ===== Audience ===== */
.audience-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.audience-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  background: white;
  border-radius: 12px;
  font-size: 15px;
  border: 1px solid #eee;
}

.audience-check {
  color: #5B9AA8;
  font-weight: 700;
  font-size: 18px;
}

/* ===== Tech ===== */
.tech-section {
  background: white;
}

.tech-tags {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 10px;
  margin-bottom: 16px;
}

.tech-tag {
  padding: 6px 16px;
  background: #F0F0F0;
  border-radius: 20px;
  font-size: 13px;
  color: #666;
  font-weight: 500;
}

.tech-note {
  text-align: center;
  font-size: 14px;
  color: #999;
}

/* ===== CTA ===== */
.cta-section {
  background: linear-gradient(135deg, #E8C4C4 0%, #C9D6DF 50%, #D5C9D1 100%);
  opacity: 0.9;
}

.cta-card {
  text-align: center;
  padding: 48px 24px;
  background: rgba(255,255,255,0.85);
  border-radius: 24px;
  backdrop-filter: blur(10px);
}

.cta-card h2 {
  font-size: 24px;
  font-weight: 700;
  color: #2C3E50;
  margin-bottom: 8px;
}

.cta-card p {
  font-size: 16px;
  color: #666;
  margin-bottom: 28px;
}

.cta-btn-large {
  padding: 16px 48px;
  font-size: 18px;
}

/* ===== Footer ===== */
.footer {
  text-align: center;
  padding: 32px 24px;
  font-size: 13px;
  color: #bbb;
}

/* ===== Responsive ===== */
@media (max-width: 480px) {
  .brand { font-size: 44px; }
  .feature-grid { grid-template-columns: 1fr; }
  .philosophy { gap: 24px; }
  .section { padding: 56px 0; }
}
</style>
