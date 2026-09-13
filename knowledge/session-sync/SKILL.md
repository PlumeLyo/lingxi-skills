---
name: session-sync
description: >
  甲纪版会话收尾·六层同步：增量记忆→Scratchpad路由→共享记忆(agent-memory)→Dream→Distill→产出归位。
  适配多Agent（千问办公/Codex/灵犀/MiMo），共享记忆用 agent-memory 四文件（identity/status/decisions/evolution）。
  触发词：/sync、收尾、同步一下、整理一下、梳理一下、会话结束。
---

# 会话收尾·六层同步（v7）

> 对齐甲纪 AGENTS.md（2026-08-30 定型）。**共享记忆已由单文件 `agent-shared-memory.md` 拆分为 `agent-memory/` 四文件，收尾不再写旧单文件。** 作品集路径为 `D:\WorkFiles\作品集`（不再使用 `Desktop\work\`）。

## 路径速查

| 用途 | 路径 |
|------|------|
| 共享记忆目录 | `D:\Obsidian\人生系统知识库\0-记忆档案\agent-memory\` |
| 统一产出目录 | `C:\Users\羽涅\Desktop\甲纪\output\_inbox\` |
| 作品集（归位目标） | `D:\WorkFiles\作品集\` |
| Obsidian | `D:\Obsidian\人生系统知识库\` |
| WPS知识库 | 杉甲记忆档案（drive_id: 3116465513） |

## 流程

### 1. 增量记忆同步

回顾本会话，检查是否有需要持久化的变化（写入各 Agent 自身记忆系统）：

- **必写信号**（立即写）：用户说"记住/别再/以后/下次"、纠正行为并期望长期遵守、新路径/新工具/新账号、被记录为决策的选择
- **模糊信号**（有价值不紧急）：先入 scratchpad/当日日志，收尾时路由

写入方式按各 Agent 自身能力选择（千问办公/灵犀用记忆工具，Codex/MiMo 写本地文件）。无变化则跳过。

### 2. Scratchpad 路由

处理会话中"有价值但未归类"的信息：按热/温/冷记忆归属路由写入。无则跳过。

### 3. 共享记忆·决策日志（agent-memory）

读取 `agent-memory\decisions.md`，新增一行：`| MMDD | Agent名 | 变更摘要 |`（≤30字）。
任务状态有变更 → 更新 `agent-memory\status.md` 对应任务行。
**不再写 `agent-shared-memory.md`。**

### 4. Dream（≥7天触发）

检查 `decisions.md` 上次 Dream 日期：
- 间隔 < 7天 → 跳过
- 间隔 ≥ 7天 → 快速扫描：决策日志 >30天条目可否压缩、温记忆文件 >60天是否需更新、长期未用 skill 是否可清理。结果追加到 `decisions.md`（如 `MMDD: Dream#N - 摘要`）。≤5分钟，超时跳过。

### 5. Distill（≥30天触发）

检查 `decisions.md` 上次 Distill 日期：
- 间隔 < 30天 → 跳过
- 间隔 ≥ 30天 → 扫描近30天重复 ≥3 次的操作 → 建议固化为 skill/规则/SOP，产出建议清单交用户确认，不自动创建。结果追加到 `decisions.md`。≤5分钟，超时跳过。

### 6. 产出归位（写 inbox）

新架构下 Agent 产出**统一写入 inbox**（`C:\Users\羽涅\Desktop\甲纪\output\_inbox\`），命名 `日期-Agent标识-描述.扩展名`，由 harness 自动归位到作品集/OB，Agent 不需自行归档。

- 作品集最终目标：`D:\WorkFiles\作品集\`
- Obsidian 模块映射：`0-记忆档案/` `3-学习笔记/` `4-内容创作模块/彳亍时刻/` `4-内容创作模块/屋托邦指南/` `5-知识库模块/` `6-个人成长模块/`

无新产出则跳过。

## 摘要模板

```
## 收尾
1. 记忆：xxx（或无新增）
2. Scratchpad：路由 x 条（或无）
3. 决策日志（agent-memory/decisions.md）：+N 条
4. Dream：xxx（或跳过）
5. Distill：xxx（或跳过）
6. 产出：写 inbox xxx（或无）
```

## 规则
- 顺序执行，失败静默跳过
- **共享记忆只写 `agent-memory/` 四文件，不再写 `agent-shared-memory.md`**
- 产出只写 inbox，不自行归位到作品集/OB
- 各 Agent 按自身能力选择写入方式，本 skill 只定义"做什么"不绑定"用什么工具"
- Dream/Distill 不阻塞其他步骤，超时则跳过
- 增量写入遵循"不动>少动>轻动"：明确信号立即写，模糊信号先入日志
