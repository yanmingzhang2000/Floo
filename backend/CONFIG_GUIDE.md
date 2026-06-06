# Floo! 后端配置指南

## 数据库配置步骤

### 1. 在 MySQL 中创建数据库

```sql
CREATE DATABASE floo_core_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. 创建 `.env` 文件

在 `backend/` 目录下创建 `.env` 文件，内容如下：

```bash
# 数据库连接（根据你的实际情况修改）
DATABASE_URL=mysql+pymysql://root:your_password@localhost:3306/floo_core_db

# 大模型配置（可选，留空时使用 mock 数据）
LLM_API_KEY=
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat

# 应用配置
APP_HOST=0.0.0.0
APP_PORT=8000
```

**重要提示：**
- `your_password` 替换为你的 MySQL 密码
- 如果 MySQL 用户不是 `root`，请修改用户名
- 如果端口不是默认 3306，请修改端口号

### 3. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 4. 初始化数据库

```bash
python init_db.py
```

这个脚本会：
- 自动创建所有 9 张表
- 创建默认测试用户
- 生成首条学习内容（AI 或 mock）

### 5. 启动后端服务

```bash
uvicorn app.main:app --reload
```

访问 http://localhost:8000/docs 查看 API 文档。

---

## 数据库结构说明

已按照 `数据库设计结构.md` 重构为 9 张表：

### 业务集群一：用户与偏好
- `user_main` - 用户主表
- `user_learning_preference` - 学习偏好（难度、主题）

### 业务集群二：内容生产
- `learning_contents` - 学习内容库（AI生成 + 用户自定义）

### 业务集群三：学习行为与记忆追踪
- `user_memory_progress` - 艾宾浩斯记忆曲线追踪
- `user_checkin_records` - 每日打卡记录
- `user_dictation_history` - 默写历史流水
- `user_weekly_summary` - 每周学习统计

### 业务集群四：游戏化激励
- `user_point_account` - 用户积分账户
- `point_log_history` - 积分流水

---

## 常见问题

**Q: pymysql 安装失败？**  
A: 确保已安装 Python 3.8+，然后重试 `pip install pymysql`

**Q: 连接数据库失败？**  
A: 检查：
1. MySQL 服务是否启动
2. 用户名密码是否正确
3. 数据库 `floo_core_db` 是否已创建
4. 防火墙是否允许 3306 端口

**Q: init_db.py 报错？**  
A: 确保：
1. `.env` 文件配置正确
2. 已安装所有依赖
3. 数据库连接正常
