# Floo! uni-app 迁移完成报告

本项目已成功从单独的 **网页版 (frontend)** 和 **空壳小程序 (miniprogram)** 迁移至统一的 **uni-app 架构**，实现一套代码同时编译为 **H5 网页** 和 **微信小程序**。

---

## ✅ 完成内容

### 1. 基础设施层

#### 跨端适配工具
- **`src/utils/storage.ts`**: 存储适配 (localStorage ↔ uni.getStorageSync)
- **`src/utils/request.ts`**: 网络请求适配 (axios ↔ uni.request)
- **`src/utils/router.ts`**: 路由跳转适配 (vue-router ↔ uni.navigateTo/switchTab)

#### Composables (可复用逻辑)
- **`src/composables/useSpeech.ts`**: 语音朗读 (H5 用 Web Speech API，小程序暂不支持)
- **`src/composables/useRecorder.ts`**: 录音功能 (H5 用 MediaRecorder，小程序用 uni.getRecorderManager)
- **`src/composables/useWordForm.ts`**: 词形还原工具

#### 状态管理与类型
- **`src/stores/index.ts`**: Pinia 状态管理 (auth、preference、points)
- **`src/types/index.ts`**: TypeScript 类型定义
- **`src/api/index.ts`**: 统一 API 接口层

#### 全局配置
- **`src/manifest.json`**: uni-app 配置 (H5 路径 `/Floo/`, 小程序 appid)
- **`src/pages.json`**: 页面路由和 tabBar 配置
- **`src/static/styles/main.css`**: 全局样式 (CSS 变量、rpx 单位)
- **`src/App.vue`**: 全局登录态检查

---

### 2. 页面迁移 (10个页面)

#### tabBar 页面 (4个)
1. **`pages/learning/index.vue`** - 每日学习 (核心功能页)
   - 今日内容列表 + 切换
   - 文章朗读 + 单词点击查询
   - 已学标记 + 译文展开
   - 核心词汇展示
   - 单词收藏 + 发音
   - AI 生成内容

2. **`pages/dictionary/index.vue`** - 单词书
   - 收藏词汇列表
   - 单词发音
   - 取消收藏

3. **`pages/review/index.vue`** - 复习
   - 记忆复习 (待复习任务 + 全部进度)
   - 默写练习 (全文默写 + AI 批改)
   - 词汇默写 (收藏词汇随机抽取)

4. **`pages/checkin/index.vue`** - 打卡日历
   - 月度日历视图
   - 打卡状态标记
   - 连续打卡统计

#### 非 tabBar 页面 (6个)
5. **`pages/login/index.vue`** - 登录/注册
   - 用户名密码登录
   - 记住密码 (30天免登录)
   - 注册账号

6. **`pages/detail/index.vue`** - 文章详情
   - 文章内容展示
   - 单词点击查询
   - 核心词汇
   - 中文译文

7. **`pages/list/index.vue`** - 历史内容列表
   - 历史学习内容浏览

8. **`pages/preference/index.vue`** - 学习偏好设置
   - 难度等级选择
   - 主题类型选择
   - 每日目标时长

9. **`pages/shop/index.vue`** - 积分商城
   - 积分余额显示
   - 开盲盒抽角色
   - 我的收藏展示

10. **`pages/weekly/index.vue`** - 每周学习报告
    - 打卡天数
    - 学习篇数
    - 平均准确率
    - 获得积分

---

## 📦 编译验证

### H5 网页版
```bash
cd uni-app
npm run dev:h5      # 开发环境 (http://localhost:5173)
npm run build:h5    # 生产构建
```
✅ 编译成功，产物在 `dist/build/h5`

### 微信小程序版
```bash
cd uni-app
npm run dev:mp-weixin     # 开发环境
npm run build:mp-weixin   # 生产构建
```
✅ 编译成功，产物在 `dist/build/mp-weixin`  
导入到**微信开发者工具**即可运行

---

## 🔄 与原 frontend 的主要差异

| 项目 | frontend (纯 H5) | uni-app (H5 + 小程序) |
|---|---|---|
| 标签 | `<div>` `<span>` | `<view>` `<text>` |
| 样式单位 | `px` | `rpx` (响应式像素) |
| 路由 | vue-router | uni.navigateTo / pages.json |
| 网络请求 | axios | uni.request (封装) |
| 本地存储 | localStorage | uni.getStorageSync |
| TabBar | 自定义组件 | pages.json 原生配置 |
| 录音 | MediaRecorder | uni.getRecorderManager (小程序) |
| 朗读 | Web Speech API | 仅 H5 支持 |

---

## ⚠️ 平台差异说明

### H5 独有功能
- **语音朗读**: 使用 Web Speech API，小程序暂不支持
- **录音转 WAV**: H5 端可转换，小程序返回 mp3 base64

### 小程序限制
- **网络请求域名白名单**: 需在小程序后台配置 `https://floo-production.up.railway.app`
- **不支持 `<a>` 标签**: 用 `navigator` 组件或 `uni.navigateTo` 替代
- **不支持 `document/window`**: 用 uni-app API 替代

---

## 📝 后续优化建议

### 1. TabBar 图标
当前 tabBar 未配置图标，建议添加：
- 准备 8 张图标 (每个 tab 需要普通态 + 选中态)
- 尺寸：81px × 81px (png)
- 放置路径：`src/static/images/`
- 在 `pages.json` 中配置 `iconPath` 和 `selectedIconPath`

### 2. 小程序专属功能
- **分享功能**: 实现页面分享到微信好友/群聊
- **小程序码**: 生成二维码供线下推广
- **订阅消息**: 学习提醒通知

### 3. 性能优化
- **分包加载**: 将非首页内容分包，减少主包体积
- **图片懒加载**: 长列表使用 `<image lazy-load>`
- **虚拟列表**: 历史内容列表过长时优化

### 4. 语音功能增强
- **小程序 TTS**: 对接云服务实现小程序端文本朗读
- **语音评测云端化**: 将 Web Audio 处理移至后端

---

## 🗂️ 目录清理建议

迁移完成后，可考虑删除或归档：
- **`frontend/`** - 原网页版代码 (已迁移至 uni-app)
- **`miniprogram/`** - 原生小程序空壳 (已废弃)

保留 `backend/` 作为统一后端服务。

---

## 🚀 部署指南

### H5 网页版
1. 编译: `npm run build:h5`
2. 将 `dist/build/h5` 目录部署到静态服务器
3. 配置 Nginx 确保 hash 路由正常 (base: `/Floo/`)

### 微信小程序版
1. 编译: `npm run build:mp-weixin`
2. 用微信开发者工具打开 `dist/build/mp-weixin`
3. 配置 appid、域名白名单
4. 上传代码审核发布

---

## 📞 技术支持

如遇问题，检查顺序：
1. **编译错误**: 查看 `tsconfig.json` 和 `vite.config.ts`
2. **API 调用失败**: 检查 `src/utils/request.ts` 和后端 CORS
3. **路由跳转异常**: 确认 `pages.json` 配置和 tabBar 页面路径
4. **小程序白屏**: 检查域名白名单、appid、uni-app 版本

---

**迁移完成时间**: 2025-01-XX  
**uni-app 版本**: 3.0.0-4060620250520001  
**编译器版本**: 4.66 (Vue 3)