# Floo! uni-app 版本

使用 uni-app 框架重写的 Floo! 英语学习应用，支持同时编译到微信小程序和 H5 网页。

## 项目结构

```
uni-app/
├── src/
│   ├── api/                    # API 接口层
│   ├── pages/                  # 页面目录
│   │   ├── home/               # 每日首次启动欢迎页（非 tab）
│   │   ├── learning/           # 图书馆（tab 1，AI 资讯/自定义/精选书籍）
│   │   ├── notes/              # 笔记（tab 2，今日背词 + 默写存档）
│   │   ├── reading/            # 在读（tab 3，正在学习/已读完存档）
│   │   ├── floo/               # Floo（tab 4，积分 + 打卡 + 商城）
│   │   ├── dictionary/         # 单词书（从笔记页进入）
│   │   ├── review/             # 复习/背单词（从笔记/详情页进入）
│   │   ├── checkin/            # 打卡详情页
│   │   ├── shop/               # 商城完整页
│   │   ├── detail/             # 文章详情
│   │   ├── dictation/          # 默写练习
│   │   ├── dictation-detail/   # 默写详情
│   │   ├── ai-coach/           # AI 陪练
│   │   ├── book/               # 书籍精读（白名单）
│   │   ├── weekly/             # 每周报告
│   │   ├── preference/         # 学习偏好
│   │   └── login/              # 登录
│   ├── stores/                 # Pinia 状态管理
│   ├── types/                  # TypeScript 类型定义
│   ├── App.vue                 # 应用入口（含每日首次启动跳首页逻辑）
│   ├── main.ts                 # 主入口文件
│   ├── pages.json              # 页面配置（tabBar 4 项）
│   └── manifest.json           # 应用配置
├── package.json                # 依赖配置
└── vite.config.ts              # Vite 配置
```

## Tab 结构

底部 tabBar 固定 4 项：

| Tab | 路由 | 说明 |
|---|---|---|
| 图书馆 | `pages/learning/index` | 素材广场：AI 资讯 / 自定义文稿 / 精选书籍 |
| 笔记 | `pages/notes/index` | 今日背词入口 + 默写历史存档 |
| 在读 | `pages/reading/index` | 全部读物存档：正在学习 / 已读完存档 |
| Floo | `pages/floo/index` | 积分总览 + 月度打卡日历 + 积分商城 |

首页 `pages/home/index` 不在 tabBar，仅每天第一次进入 App 时以欢迎屏形式展示，
之后自动 `switchTab` 到图书馆。逻辑见 `src/App.vue` 的 `last_home_shown_date`。

## 快速开始

### 1. 安装依赖

```bash
cd uni-app
npm install
```

### 2. 开发模式

#### H5 网页版

```bash
npm run dev:h5
```

访问 http://localhost:5173 预览

#### 微信小程序版

```bash
npm run dev:mp-weixin
```

用微信开发者工具打开 `dist/dev/mp-weixin` 目录

### 3. 构建生产版本

#### H5 网页版

```bash
npm run build:h5
```

#### 微信小程序版

```bash
npm run build:mp-weixin
```

## 配置说明

### 1. 微信小程序 AppID

编辑 `src/manifest.json`，填入你的微信小程序 AppID：

```json
{
  "mp-weixin": {
    "appid": "your-app-id-here"
  }
}
```

### 2. API 地址

编辑 `src/api/index.ts`，修改后端 API 地址：

```typescript
const API_BASE = 'https://floo-production.up.railway.app'
```

## 部署说明

### H5 网页版

1. 构建生产版本：`npm run build:h5`
2. 将 `dist/build/h5` 目录部署到 GitHub Pages 或其他静态托管服务

### 微信小程序版

1. 构建生产版本：`npm run build:mp-weixin`
2. 在微信开发者工具中导入 `dist/build/mp-weixin` 目录
3. 提交审核并发布

## 功能特性

- ✅ 每日英语学习
- ✅ 词汇查询和收藏
- ✅ 默写练习
- ✅ 打卡记录
- ✅ 语音评测
- ✅ 积分商城
- ✅ 复习计划
- ✅ 书籍精读（白名单授权，按段翻页阅读 + 段级默写 + 段级按需译文）

## 注意事项

1. **微信小程序限制**：个人主体小程序无法使用 `<web-view>` 组件，需要使用 uni-app 重写
2. **语音评测**：需要后端支持有道智云 API
3. **数据同步**：H5 和小程序版本使用同一个后端 API，数据完全同步

## Admin：书籍导入与授权

书籍精读功能采用白名单授权，仅对指定用户开放。

### 1. 触发导入（后端接口）

```bash
curl -X POST https://<backend>/api/book/admin/import \
  -H "X-Admin-Token: <FLOO_ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"source_url": "https://novel.tingroom.com/jingdian/96/"}'
```

同一 `source_url` 幂等，重复调用会跳过已存在的章节。

### 2. 给用户授权

```bash
curl -X POST https://<backend>/api/book/admin/grant \
  -H "X-Admin-Token: <FLOO_ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 42, "series_id": 1}'
```

### 3. 撤销授权

```bash
curl -X DELETE https://<backend>/api/book/admin/grant/42/1 \
  -H "X-Admin-Token: <FLOO_ADMIN_TOKEN>"
```

### 4. 查看所有已导入书籍

```bash
curl https://<backend>/api/book/admin/series \
  -H "X-Admin-Token: <FLOO_ADMIN_TOKEN>"
```

配置 `FLOO_ADMIN_TOKEN` 环境变量（Railway Variables），未设置时后端使用弱口令
`floo-dev-admin-token`，仅用于本地开发。
