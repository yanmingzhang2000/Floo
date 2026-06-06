# Python 代码规范（Claude Code 适用）

本文件由 Claude Code 在每次会话自动加载，用于约束生成 Python 代码时的行为。
共三条规则，按编号执行；冲突时以编号小的优先。

---

## 规则一：一个方法只做一件事 + 多写注释

### 单一职责
- 一个函数 / 方法只完成 **一个语义动作**。如果方法名里出现 `and`、
  `_then_`、`do_xxx_and_yyy`，是拆分信号。
- 函数体超过 **40 行** 或局部变量超过 **8 个** 时，先考虑拆子函数，再写实现。
- I/O（DB、HTTP、文件）和纯计算（排序、转换、校验）必须分开放在不同函数里。
  本项目的分层范式：`api/` 收请求 → `services/` 编排 → `repositories/` 访问 DB
  → 工具函数做转换。生成新代码时沿用这个分层，不要在 service 里直接写 SQL，
  也不要在 repo 里发 HTTP。

### 注释要求
- 模块顶部要有 docstring：说明这个文件 **解决什么问题**，不是逐行翻译代码。
  参考 `app/core/logging.py` 顶部的写法。
- 函数 docstring 要写 **Why（为什么这么做）**，而不是 What（做了什么）。
  代码本身已经回答了 What。
- 行内注释只在以下情况写：
  - 隐藏约束（"上游保证非空，不再校验"）
  - 反直觉的写法（"这里必须用 list 而不是 generator，因为 …"）
  - 绕过某个 bug / 兼容某个老接口（注明原因或 issue）
- 不要写 `# 把 a 加到 b 上` 这种翻译式注释。
- 用中文写注释

---

## 规则二：没有指令不生成测试用例和 Markdown 文件

### 不主动新建的文件类型
- `tests/test_*.py`、`*_test.py`
- 任何 `.md` 文件（包括 README、CHANGELOG、设计文档、总结报告）
- 一次性脚本（如 `migrate_xxx.py`、`fix_xxx.py`、`debug_xxx.py`）
- 不要再更新config.yaml.example,直接更新config.yaml

### 触发条件
仅当用户消息中明确出现以下意图时才允许生成上述文件：
- "加测试" / "写一个 test" / "测一下 xxx"
- "写一份文档" / "生成 md" / "总结到 readme"
- "写个脚本跑一下" / "写个一次性工具"

### 已有文件的处理
- 修改现有 `.py` / `.md` 不受此规则限制 —— 改是允许的，**新建**才受限。
- 修复 bug 时，**不要顺手新建** `test_<bug>.py` 来"覆盖一下"。如果该模块本来就有
  对应 test 文件，可以往里面追加用例；没有就不要起新文件。

### 例外
本文件 `CLAUDE.md` 是用户明确指令创建的，不违反此规则。

---

## 规则三：分支处必须有 DEBUG 日志

### 适用的"分支"
- `if / elif / else` 的非平凡分支（一行 return 不算）
- `try / except` 的 `except` 块
- `for / while` 中带 `break` / `continue` / 提前 return 的路径
- `match / case`（Python 3.10+）的每个 case
- 早返回（guard clause）—— 在返回前打一条说明为什么返回

### 写法约定
- logger 一律用项目固定写法：模块顶部声明
  ```python
  import logging
  log = logging.getLogger(__name__)
  ```
  使用变量名 `log`，不要用 `logger`。这是项目惯例，参见
  `app/services/kol_search_service.py:30`。
- 调用 `log.debug(...)`，**禁止用 `print`**。
- 日志内容包含三要素：**进入哪个分支** + **关键变量值** + **下一步动作**。

  ```python
  if user.is_vip:
      log.debug("user %s is VIP, skipping rate limit", user.id)
      return _vip_path(user)
  log.debug("user %s is regular, applying rate limit window=%s", user.id, window)
  return _regular_path(user, window)
  ```

- 异常分支要把异常类型一起带上：
  ```python
  except TimeoutError as e:
      log.debug("vat_platform timeout for kol_id=%s, falling back to cache: %s", kol_id, e)
      return _from_cache(kol_id)
  ```

### 不需要打日志的情况
- 极小的纯计算分支（如 `return a if a > b else b`）
- 已经在外层函数入口打过日志、且分支选择本身不影响行为追溯
- hot loop 内每行执行的分支（性能敏感，靠外层一次性日志即可）

### 为什么生产环境不会被刷屏
项目已实现 DEBUG 日志默认关闭、通过请求头 `X-Log-Level: DEBUG` 按需打开
（见 `app/core/logging.py` 的 `override_enabled` 机制）。所以分支日志可以放心
多写 —— 平时不输出，排查问题时一个请求级开关就能拿到完整路径。

---

## 规则四：先读 README，必要时回写 README

### 生成代码前：先读 README.md
- 接到任何"写新代码 / 加新功能 / 改造现有模块"的需求时，**第一步**读取
  仓库根目录的 `README.md`，建立对项目的整体认识：
  - 这个服务是干什么的（业务定位）
  - 当前阶段处于什么状态（例如：本项目 README 明确写了 Apollo 已禁用、
    DB 配置走本地 YAML —— 不读 README 就可能写出基于 Apollo 启用的代码）
  - 有哪些 endpoints、配置项、依赖
  - 项目布局指向哪份设计文档（本项目指向
    `docs/superpowers/specs/2026-05-19-kol-search-service-design.md`）
- 仅修小 bug、一行改动、改注释、重命名变量等"无外部影响"的改动可以跳过，
  但凡涉及新增方法、新增字段、改接口签名、改启动方式，**必读**。
- 读 README 不算"生成 .md"，与规则二无冲突 —— 规则二限制的是新建，
  不是阅读。

### 修改代码后：判断是否要回写 README
按下表对照，命中任何一条就**必须**同步更新 README 对应章节；不命中则不要动
README，避免噪音 commit。

| 你刚做的改动 | 需要更新 README 哪一节 |
|---|---|
| 新增 / 删除 / 改动 HTTP endpoint | `## Endpoints` |
| 新增 / 删除 / 改名配置字段（如 `business.top_k_default`） | `## Configuration file` 的 YAML 示例 |
| 新增 / 删除环境变量（如 `CONFIG_FILE`、`APOLLO_META`） | `## Configuration file` 或 `## Re-enabling Apollo` |
| 改启动命令、端口、Docker 启动方式 | `## Quick start` 或 `## Docker` |
| 改 Python 版本、改依赖管理方式（pip → uv 等） | `## Quick start` |
| 改测试命令 | `## Tests` |
| 项目目录结构发生层级变化（新增 `app/xxx/` 目录） | `## Project layout` 或 design doc 引用 |
| 项目阶段状态变化（如 Apollo 重新启用） | 顶部的 `> **Current phase**` 引言块 |

### 回写 README 的原则
- **改最小段落**，不要大幅重写其它章节。
- 保持 README 现有写作风格（本项目偏简短、命令式、英文为主）。
- 不要把详细设计塞进 README —— 长内容放
  `docs/superpowers/specs/...`，README 只放指针。
- 不要因为"觉得 README 可以更好"就主动重写没改过的章节，那触发规则二
  （未指令的扩张性写作）。

### 不需要回写 README 的改动（举例）
- 修一个分支判断的 bug（行为不变、签名不变）
- 给函数加 docstring / 加日志
- 重构一个内部 helper（不暴露给外部）
- 重命名 service 内部的私有变量
- 升级一个依赖的 patch 版本（不影响 README 里的 Python 版本说明）

---

## 自检清单（生成代码后默认走一遍）

1. 开始前是否读过 `README.md`？（新功能 / 改接口必读，小修可跳过）
2. 每个新函数是否只做一件事？方法名能否用一句话说清？
3. 模块 / 复杂函数是否有 Why-注释？
4. 是否新建了 `tests/` 或 `.md` 文件？如果是，用户原话是否要求？
5. 每个 `if/except/break/early-return` 是否有 `log.debug(...)`？
6. logger 变量名是 `log` 不是 `logger`？
7. 改动是否命中规则四对照表？命中则同步更新 `README.md` 对应章节。

任何一条不满足，先改再交付。
