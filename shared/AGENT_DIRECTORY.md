# Agent 目录 & 协作指南

> 每个 Agent 的快速名片，知道谁做什么、怎么对接。
> 最后更新：2026-07-14

---

## 架构总览

```
shared/agents/       ← 跨项目通用角色
projects/*/agents/   ← 项目专属角色
```

---

## 1. 主 Agent — 传感前锋 ⚡

| 属性 | 内容 |
|------|------|
| **身份** | AI工作伙伴，Josan 的主要对话接口 |
| **路径** | 主程序（无独立 profile 文件） |
| **职责** | 路由分发、全局协调、项目监管、记忆维护 |
| **对接方式** | Josan 直接对话 |

## 2. 跨项目通用 Agent（shared/agents/）

| 代号 | 职责 | 配置路径 |
|------|------|---------|
| **周报官 📝** | 日报收集 + 周报生成 + 周二汇报准备 | `shared/agents/report-assistant/profile.md` |
| **市场调研专家 📊** | 行业数据、竞品分析、只讲事实 | `shared/agents/market-research/profile.md` |
| **业务市场专家 💼** | 商业模式判断、商业落地评估 | `shared/agents/business-market/profile.md` |
| **CEO/参谋长 🧠** | 全局指挥、任务拆解、质量把控 | `shared/agents/ceo-chief/profile.md` |

## 3. 项目专属 Agent

### 🔬 tech-project-sensor（柔性织物压力传感）

| 代号 | 职责 | 配置路径 |
|------|------|---------|
| 技术产品专家 🔧 | 产品定义、技术路线把关 | `projects/tech-project-sensor/agents/tech-product/profile.md` |
| 产品经理 📋 | 需求定义、功能设计 | `projects/tech-project-sensor/agents/product-manager/profile.md` |
| 研发工程师 💻 | 技术实现、编码落地 | `projects/tech-project-sensor/agents/rd-engineer/profile.md` |
| 质量工程师 ✅ | 测试验证、品质把控 | `projects/tech-project-sensor/agents/qa-tester/profile.md` |

### 🧪 ai-chem-lab（AI化学实验室）

| 代号 | 职责 | 配置路径 |
|------|------|---------|
| 仿真工程师 🦾 | MuJoCo/RL 仿真技术 | `projects/ai-chem-lab/agents/simulation-engineer/profile.md` |
| chief-agent 🧠 | 化学实验室专属指挥 | `projects/ai-chem-lab/agents/chief-agent/profile.md` |

### 📜 patents（专利管理）

| 代号 | 职责 | 配置路径 |
|------|------|---------|
| **专利Agent 📜** | 专利交底书撰写与管理 | `projects/patents/agents/patent-agent/profile.md` |

## 4. 技术探讨 Agent

| 代号 | 职责 | 配置路径 | 对接方式 |
|------|------|---------|---------|
| **TechSpark ⚡** | 技术深度探讨、方案评审 | `subagents/tech-discuss.md` | 主 agent spawn |

## 3. Agent 对接协议

### 当项目 Agent 需要求助其他 Agent

```
场景示例：专利Agent写手套专利时，需要仿真技术数据

专利Agent → 输出请求给主 agent:
  "请把我这个请求转发给仿真工程师：
   - 我需要：触觉手套在 MuJoCo 中的传感点映射方式
   - 位于：ai-chem-lab/agents/simulation-engineer/
   - 我的 open_id：patent-agent"

主agent → spawn 仿真工程师 → 取数据 → 回传给专利Agent
```

### 当 TechSpark 需要讨论某个项目技术

```
TechSpark → 读 projects/<project>/CONTEXT.md
          → 读 projects/<project>/sessions/ 最新日志
          → 输出技术评审/分析
          → 主 agent 收结果归档
```

## 4. 归档标准

每次子 agent 输出后，主 agent 负责：

1. ✅ 将产出写回到对应项目目录
2. ✅ 更新 CONTEXT.md 中的状态
3. ✅ 记录 session 日志
4. ⚠️ 重大决策 → 更新 MEMORY.md + UNIFIED_CONTEXT.md
