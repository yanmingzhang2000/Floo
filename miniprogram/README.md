# Floo! 微信小程序

## 快速开始

### 1. 注册小程序账号
1. 访问 https://mp.weixin.qq.com/
2. 注册小程序账号（需要营业执照或个人身份）
3. 获取 AppID

### 2. 配置 AppID
1. 打开 `project.config.json`
2. 将 `wx__YOUR_APPID__` 替换为你的 AppID

### 3. 导入项目
1. 下载并安装 [微信开发者工具](https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html)
2. 打开微信开发者工具
3. 选择「导入项目」
4. 选择 `miniprogram` 目录
5. 填入你的 AppID

### 4. 配置业务域名（重要！）
1. 登录微信公众平台 (mp.weixin.qq.com)
2. 进入「开发」→「开发管理」→「开发设置」→「业务域名」
3. 添加以下域名：
   - `yanmingzhang2000.github.io`（前端）
   - `floo-ai.duckdns.org`（后端 API）

### 5. 预览和发布
1. 在微信开发者工具中点击「预览」生成二维码
2. 用微信扫码在手机上预览
3. 确认无误后点击「上传」提交审核

## 限制说明

由于使用 `<web-view>` 嵌入网页，有以下限制：

1. **无法使用微信登录**：用户登录仍需通过网页内的账号密码
2. **无法发送模板消息**：不能主动推送学习提醒
3. **无法使用微信支付**：积分购买需通过网页内实现
4. **部分 iOS 设备可能有兼容性问题**

## 文件结构

```
miniprogram/
├── app.js                    # 小程序入口
├── app.json                  # 全局配置
├── app.wxss                  # 全局样式
├── pages/
│   └── index/
│       ├── index.js          # 页面逻辑
│       ├── index.json        # 页面配置
│       ├── index.wxml        # 页面模板
│       └── index.wxss        # 页面样式
├── project.config.json       # 项目配置
└── sitemap.json              # 站点地图配置
```
