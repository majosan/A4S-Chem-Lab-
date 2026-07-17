# A4S Chem-Lab — 全项目协作中枢

> ⚡ 传感前锋（服务器） + 🧑 Josan（物理执行） + 🤖 Claude Code（多机编码）

## 架构

```
传感前锋（服务器）
   └─ 统筹协调、写 task、审核产出、数据分析
        │
   GitHub 私有仓库 ← 单源真理
        │
   ├─ 公司台式 (Claude Code) ← 认领 task A
   ├─ 笔记本 (Claude Code)   ← 认领 task B
   └─ 家里台式 (Claude Code) ← 认领 task C
```

## 工作流

```
传感前锋 → 写 task 到 tasks/ 目录
   ↓
Claude Code 机器 → git pull → 读自己的 task → 执行 → push
   ↓
传感前锋 → review 结果 → 决定下一步
```

## 项目目录

```
projects/
├── tech-project-sensor/    ← 全柔性织物压力传感阵列
│   └── subprojects/
│       └── tactile-glove/  ← 触觉手套（当前活跃子项目）
└── ai-chem-lab/            ← AI 化学实验室（概念阶段）

tasks/          ← 任务板（传感前锋发活）
shared/         ← 共享上下文（agent 协作用）
```

## 三台机器分工建议

| 机器 | 适合做什么 |
|------|-----------|
| 公司台式 | 主力编码（数据分析脚本、可视化工具） |
| 笔记本 | 数据采集、现场测试、快速验证 |
| 家里台式 | 仿真训练、RL 训练、GPU 密集型任务 |

> **Windows 用户**：打开终端，运行 `.\bridge.ps1` 即可一键 pull → 显示待办 → 完成时 push
