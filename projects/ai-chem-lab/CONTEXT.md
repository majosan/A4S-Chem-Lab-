# AI化学实验室项目 — CONTEXT.md

## 项目代号
ai-chem-lab（暂定，可改）

## 项目定位
打造高通量无人化学实验平台，类比晶泰科技（XtalPi）在生物制药领域的路径，聚焦化学实验领域。

**核心定位（2026-07-05校正）**：聚焦**具体实验室场景的8种操作**，触觉手套角色为**示教器/数据捕捉器**，为物理AI提供现实数据通道。

## 物理实验室现状（2026-07-06 更新 ✨）
- **地点**：浙江大学（联合浙大朋友搭建）
- **方向**：**催化剂合成高通量实验**
- **已就绪**：表征设备 + 实验平台已搭建完成
- **缺口**：具身智能/机器人自动化层——这是现在正在攻的方向

## 核心逻辑
**前端**：大模型生成化学配方/实验方案 → **后端**：高通量无人实验室快速验证

## 三大技术支柱

### 1️⃣ 高通量无人化学实验
- LLM生成配方 → 自动执行验证
- 对标：晶泰科技（生物制药）的化学版

### 2️⃣ 具身智能机器人 + 人机协同
- 实验室配置：1人 + 多个具身智能机器人
- 人机协同操作：机器能预判人的下一步动作
  - 例：人拿起烧杯 → 机器人递来吸管
- 8种核心操作：抓取/倾倒/插入/旋转/按压/滑动/擦拭/夹取

### 3️⃣ 物理AI / 世界模型
- 输入模态：视觉 + 触觉手套(124点) + IMU
- **编码方案**：借鉴T-Rex的VQ-VAE(时间)+CNN(空间)双通道，适配织物手套
- 近期路线(0-6月)：走VLA路线（LabVLA+触觉编码），远期考虑世界模型

## 核心技术复用
- **柔性织物触觉手套**（来自 tech-project-sensor 的 tactile-glove）：124个感知点
- **IMU**：已调试成功（BNO055替换型号）
- **视觉**：Intel RealSense D435（待购）

## 当前阶段
**技术路线深化期** — 物理实验室已就绪，现需明确具身智能/自动化技术选型

## 2026-07-13 里程碑更新 ✨

### 核心决策
| 决策 | 结论 | 状态 |
|------|------|------|
| 触觉编码方案 | 12×12 网格 + 3 通道 (Ch1压力/Ch2变化率/Ch3振动) | ✅ 定稿 |
| 编码融合必要性 | 必须编码+融合，模型无触觉入口 | ✅ 确认 |
| 换臂决策 | Phase 2 暂用 Franka，OpenArm 决策推迟到 Phase 3 | ✅ 确认 |
| IMU 定位 | 不是可选项，是核心姿态信息来源 | ✅ 确认 |
| Phase 2 范围 | 纯 MuJoCo 仿真闭环，不等待硬件 | ✅ 确认 |

### 新增知识文档
- `data/learning/tactile-encoding-fusion.md` — 触觉编码融合完整技术讲解

### 参考论文（2026-07-05）
| 论文 | 核心内容 | 对本项目价值 |
|------|---------|------------|
| **T-Rex** | MoT架构+触觉编码，频率解耦 | 触觉编码方法可借鉴；6D力传感器与织物手套互补 |
| **LabVLA** | 科学实验室VLA，全开源 | **主参考框架**，直接复用其代码栈 |
| **RoboGenesis** | 仿真数据引擎，11原子技能 | 直接复用数据生成管线 |

### 关键技术决策
1. **主参考框架** → LabVLA（不开新坑，直接复用浙大开源代码）
2. **数据策略** → 仿真+真机双通道：RoboGenesis造仿真预训练→真实数据微调
3. **近期路线** → VLA路线（LabVLA+触觉编码）先跑通管线，再考虑世界模型
4. **编码方案** → VQ-VAE(时间)压缩16帧趋势 + CNN(空间)提取压力分布，压缩比~169:1
5. **原子技能映射** → 11种中9种直接可用，需自定义2种（旋转瓶盖+擦拭）

### 8种操作→原子技能对照
| 操作 | RoboGenesis技能 | 需自定义？ |
|------|----------------|-----------|
| ① 抓取烧杯/试管 | pick(7阶段) | ❌ 已有 |
| ② 倾倒液体 | pour(6阶段) | ❌ 已有 |
| ③ 插入(移液枪头/pH计) | pressZ(3-4阶段) | ❌ 已有 |
| ④ 旋转(瓶盖/旋钮) | — | ✅ 需自定义 |
| ⑤ 按压(移液枪/按钮) | press/pressZ(3阶段) | ❌ 已有 |
| ⑥ 滑动(沿实验台) | move(无固定阶段) | ❌ 已有 |
| ⑦ 擦拭(清洁/涂抹) | — | ✅ 需自定义 |
| ⑧ 夹取(镊子取物) | pick(小物体适配) | ❌ 参数调整 |

## 技术选型

### 仿真引擎
- **主力**：MuJoCo + MJX（刚体物理、触觉仿真）
- **数据引擎**：RoboGenesis（基于MuJoCo，自动生成训练数据）
- **辅助（待评估）**：Genesis（流体仿真，v0.3.0关注中）

### 模型
- **参考框架**：LabVLA（Qwen3-VL-4B + DiT动作专家）
- **训练阶段**：FAST预训练→Flow Matching后训练(知识隔离)→任务微调
- **近期走VLA路线，远期考虑世界模型**

### 开发环境
- **Windows 11 → WSL2 (Ubuntu 22.04)**
- **Python 3.10+**
- **PyTorch + CUDA**

## 2026-07-08 更新：LabVLA 本地部署启动 🚀

### 核心决策
- ⚡ **TechSpark 完成首次技术全景评估**（详见 `sessions/2026-07-08.md`）
- ✅ **路线确定**：LabVLA → MuJoCo 四阶段跑通计划
- ⚠️ **RoboGenesis 尚未开源**（GitHub 仓库 `Ylr9933/RoboGenesis` 为空壳），改为：先用公开数据集（Open X-Embodiment/DROID），再自建 MuJoCo 数据生成管道
- ⚠️ GPU 限制：RTX 4060 (8GB VRAM) → LabVLA-5B 需 **4-bit 量化**（bitsandbytes）才能本地推理

### LabVLA→MuJoCo 四阶段计划
| 阶段 | 任务 | 状态 |
|------|------|------|
| 1 | 环境搭建 + 量化推理 + WebSocket 验证 | ✅ 已完成（2026-07-10） |
| 2 | MuJoCo 场景 + WebSocket 客户端 | 🔄 任务书已下发 Claude Code |
| 3 | 原子技能 + 自建数据管道 | 📅 |
| 4 | 微调（需 24GB+ 显存） | 📅 远期 |

### Phase 1 关键成果
- LabVLA-5B-Base 4-bit 量化在 RTX 4060 8GB 上成功推理
- WebSocket 通信协议（msgpack）打通，往返延迟 ~2.2s
- Action 输出格式：(50x8) float32, delta mode
- `labvla_schema.json` 已本地化到 `scripts/` 目录管理
- 详细报告见 `data/setup/PHASE1-REPORT.md`

### 关键发现
- HF Space `zjunlp/lab-vla` 包含比 GitHub 更完整的推理代码和 schema 定义
- BluePrint 框架可用于后续自定义数据格式（加触觉维度）
- 模型加载耗时 ~208 秒（4-bit 量化加载正常）

### 已沉淀文档（Phase 1-2）
- `data/setup/labvla-phase1-mission.md` — Phase 1 任务书
- `data/setup/PHASE1-REPORT.md` — Phase 1 验证报告
- `data/setup/labvla-phase2-mission.md` — Phase 2 任务书 (v1)
- `data/setup/labvla-phase2-mission-v2.md` — Phase 2 任务书 (v2，含今日讨论背景)
- `data/learning/tactile-encoding-fusion.md` — 触觉编码+多模态融合知识文档

## 项目角色

| 角色 | 文件 | 状态 |
|------|------|------|
| CEO/参谋长 | （主Agent） | ✅ |
| 仿真技术专家 | `agents/simulation-engineer/profile.md` | ✅ |
| **TechSpark** ⚡ | `subagents/tech-discuss.md` | ✅ |

## 关联项目
- **tech-project-sensor** → 触觉传感技术底座（`subprojects/tactile-glove/`）
- **patents** → 专利管理（触觉手套专利已完成待提交）

## 待办
1. ⏳ **Phase 2（07-13 继续）** — Claude Code 执行 MuJoCo 场景搭建 + WebSocket 客户端集成
2. ⏳ 触觉手套缝制完成 → 测试 124 点信号质量（频率/稳定性/噪声）
3. ⏳ 购买 Intel RealSense D435
4. ⏳ 研究 RoboGenesis GitHub 代码仓库，评估直接复用的工程量
5. ⏳ 设计旋转瓶盖+擦拭 2 个自定义原子技能
6. ⏳ 设计织物手套的 VQ-VAE+CNN 编码实现

## 2026-07-09 更新：管线角色澄清 + 开发模式确定 🎯

### 核心概念澄清（关键纠正）

| 误解 | 纠正 |
|------|------|
| "在 MuJoCo 上训练" | ❌ 训练在 PyTorch (GPU) 进行，MuJoCo 仅参与验证 |
| "MuJoCo 调用 LabVLA" | ❌ 反过来，LabVLA 框架调用 MuJoCo 执行动作 |
| "LabVLA-5B = 5亿参数" | ❌ 是 **50亿（Billion）**，模型文件 ~10GB |
| "Qwen3-VL-4B 是框架里的" | ❌ 它是 **模型内部的一个部件**（大脑），不是框架 |

### 组件角色定义

| 组件 | 角色 | 什么时候用 |
|------|------|-----------|
| **LabVLA 框架** | 整条流水线（数据流+训练管子+推理服务） | 训练 + 推理 |
| **LabVLA-5B-Base** | 预训练通用机器人操作模型（待微调的初始权重） | 训练时的初始参数 |
| **Qwen3-VL-4B** | LabVLA-5B 内部的视觉语言理解"大脑" | 微调时一般不动它 |
| **MuJoCo** | 纯物理仿真引擎+可视化器 | 仅验证阶段（评估模型效果） |
| **PyTorch + GPU** | 训练引擎（算梯度、更新权重） | 训练阶段 |

### 完整数据流（已确认）
```
采集 → 预处理(自己写管道) → 训练(LabVLA框架+GPU) → 验证(MuJoCo) → 部署
```

### 开发分工（确定）
| 角色 | 负责 |
|------|------|
| **Josan（操作手）** | 运行脚本、采集数据、硬件操作、贴报错信息 |
| **传感前锋（总工+调试员）** | 架构设计、方案评审、问题排查、调参建议 |
| **Claude Code（码农）** | 写脚本、搭环境、实现代码 |

### 招人策略
- 先不急着招人：我们三个跑通 Demo（一个化学实验操作）
- **Demo 跑通后**拿成果去招专业人 → 新人接手有基础，效率高
- 需要招人的信号：真机臂部署、十万级数据管道、商用精度（>95%）

### 已沉淀文档
- `data/learning/pipeline-roles.md` — 完整管线角色详解（含架构图）

### 当前进度（四阶段计划）
| 阶段 | 任务 | 状态 |
|------|------|------|
| 1 | 环境搭建 + 量化推理 + WebSocket 验证 | ✅ **Phase 1 验收通过**（2026-07-10） |
| 2 | MuJoCo 场景 + WebSocket 客户端 | 🔄 任务书已下发 Claude Code |
| 3 | 原子技能 + 自建数据管道 | 📅 |
| 4 | 微调（需 24GB+ 显存） | 📅 远期 |

## 参考文件
- `references/T-Rex.md` — T-Rex论文摘要
- `references/LabVLA.md` — LabVLA论文摘要
- `pipeline/` — 传感→仿真数据管线设计
- `simulation/` — MuJoCo学习文档和RL训练计划
- `hardware/` — 机器人臂选型
- `learning/pipeline-roles.md` — 框架/模型/仿真角色详解 ⭐ 新增
- RoboGenesis文档：lxj-kai.github.io/robogenesis/v0.5/zh/
- RoboGenesis代码：github.com/Ylr9933/RoboGenesis
- LabVLA代码：github.com/zjunlp/LabVLA

---

## 2026-07-16 更新：触觉手套 + 协作桥

### 手套进展
- 两套手套样品已缝制完成，初步握物体测试通过
- 进入验收测试期（4 轮测试方案见 `tech-project-sensor/subprojects/tactile-glove/test-protocol-v1.md`）
- 已知约束：跨点一致性差（柔性织物固有）、阈值 < 7、灵敏度调低
- 下一步：Josan 按测试方案执行 → Claude Code 写分析脚本 → 传感前锋分析

### Git 协作桥（即将建立）
- GitHub 私有仓库连接服务器 + Josan 3 台 Windows
- 传感前锋写任务 → push → Josan pull → Claude Code 执行 → push → 分析
- 待明天 Josan 创建仓库后初始化
