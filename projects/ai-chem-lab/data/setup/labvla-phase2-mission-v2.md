# LabVLA Phase 2 — MuJoCo 仿真闭环验证 (v2)

> **前置条件**：Phase 1 已通过 ✅（复测待审）  
> **项目目录**：`~/projects/labvla-mujoco/`  
> **硬件环境**：RTX 4060 (8GB VRAM) + 64GB RAM  
> **模型权重**：`LabVLA-5B-Base/`（已下载，4-bit 量化推理已验证）  
> **推理服务**：已确认 LabVLA WebSocket 服务可正常返回 (50x8) float32 action chunk  
> **执行者**：Claude Code  
> **验收者**：传感前锋（AI 总工）

---

## 一、项目背景（更新）

「AI 化学实验室」—— 打造高通量无人化学实验平台。

### 完整技术路径
```
触觉手套(124点) + IMU + 视觉(3路) → 编码融合 → LabVLA 框架微调 → MuJoCo 仿真验证 → 真机(OpenArm)部署
```

### 当前所在位置
```
Phase 1 (环境验证) ✅ → Phase 2 (MuJoCo 闭环) 🔜 → Phase 3 (数据管道+触觉编码) → Phase 4 (微调)
```

### Phase 2 与后续阶段的并行工作
> Phase 2 专注 MuJoCo 闭环，以下工作同步推进但不阻碍主线：

| 并行工作 | 归属阶段 | 负责人 |
|---------|---------|--------|
| 5指→12×12触觉网格编码方案设计 | Phase 3 预研 | 传感前锋 |
| 模拟触觉数据发生器开发 | Phase 2-3 并行 | 传感前锋 |
| OpenArm 型号调研 (DOF/URDF) | Phase 3 预研 | 传感前锋 |
| IMU 集成方案设计 | Phase 3-4 | 传感前锋 |
| 摄像头采购 (至少1个D435) | Phase 3 前备齐 | Josan |

### 关键架构决策（今日确认）
1. **Phase 2 暂用 Franka Panda 仿真**，不阻碍闭环验证。OpenArm 换臂决策推迟到 Phase 3
2. **触觉编码走 12×12 网格 + 3 通道方案**，Phase 3 实施
3. **IMU 排在触觉编码之后**，Phase 3-4 范畴
4. **仿真先跑通纯视觉闭环**，保证"LabVLA + MuJoCo"基线

---

## 二、Phase 2 任务目标

### 为什么先做纯视觉闭环

触觉手套在制作中、IMU 还没买、OpenArm 待评估。**但这些都不阻碍 Phase 2**：

1. ✅ MuJoCo 有现成的 Franka 模型（`mujoco_menagerie/franka_emika_panda/`）
2. ✅ LabVLA WebSocket + 3 路 RGB 已确认在 Phase 1 可工作
3. ✅ 纯视觉闭环能验证"仿真→推理→执行"这条主线
4. ✅ 触觉编码到时是**替换图像特征的一路输入**，不改变整体架构

### Phase 2 要回答的核心问题
1. ❓ LabVLA 输出的动作是否能正确驱动 MuJoCo 中的 Franka 机械臂？
2. ❓ 三路摄像头渲染的画面质量是否满足模型推理要求？
3. ❓ 从「仿真观测 → 模型推理 → 动作执行」的完整闭环能否跑通？
4. ❓ 模型对实验室场景的泛化能力如何（用真实照片 vs 仿真画面）？

**Phase 2 通过** = ✅ MuJoCo 仿真闭环打通，可以进入数据管道和技能开发  
**Phase 2 不通过** = ❌ 排查问题（场景配置/通信协议/动作映射）

---

## 三、任务清单（Claude Code 执行部分）

### Step 1：MuJoCo 场景搭建（Franka Panda）

**目的**：搭建包含 Franka Panda 机械臂和基础实验室器具的 MuJoCo 仿真场景。

**要求**：
- 场景包含 Franka Panda 机械臂（7-DOF + 夹爪），固定在桌面
- 桌面放置至少 1～2 个实验室物体（如烧杯、试管），位置合理
- Franka 模型的 MJCF/XML 文件从 `mujoco_menagerie/franka_emika_panda/` 获取
- 场景能正常渲染和运行

**验收标准**：
- ✅ MuJoCo 窗口正常打开，Franka 机械臂可见
- ✅ 桌面和物体可见，物理碰撞正常
- ✅ 能通过程序控制机械臂关节运动

---

### Step 2：三路摄像头渲染（224×224 RGB）

**目的**：模拟 LabVLA 模型期望的 3 路 RGB 摄像头输入。

**要求**：
- 在 MuJoCo 场景中配置 3 个 RGB 摄像头，输出分辨率 224×224
- 3 个摄像头分别对应不同的视角（参考官方 Demo 的 camera_1/camera_2/camera_3）
- 每帧能获取 3 张 RGB 图像

**验收标准**：
- ✅ 摄像头位置合理，能看到桌面和机械臂工作区域
- ✅ 图像格式为 uint8，(224, 224, 3)
- ✅ 图像质量清晰可辨

---

### Step 3：WebSocket 客户端集成

**目的**：让 MuJoCo 客户端通过 WebSocket 与 LabVLA 推理服务通信，形成完整闭环。

**要求**：
- 编写 MuJoCo 主循环客户端，每帧执行：
  1. 读取 3 路摄像头画面（uint8, 224×224×3）
  2. 读取 Franka 当前关节角度 + 夹爪宽度（共 8 维状态向量）
  3. 构造观测数据，通过 WebSocket 发送给 LabVLA 服务（msgpack 格式，key 与 `labvla_schema.json` 一致）
  4. 接收服务端返回的 action chunk（50×8 float32）
  5. 将 delta 动作（前 7 维）累加到当前关节角度，夹爪（第 8 维）按 delta mask 处理
  6. 执行一步动作，推进仿真

**数据格式参考**：
- schema: `scripts/labvla_schema.json`
- camera_keys: `["camera_1_rgb", "camera_2_rgb", "camera_3_rgb"]`
- state_keys: `["state", "observation/state"]`
- Action shape: (50, 8), dtype: float32, mode: delta

**文本指令**：先固定一句 `"pick up the beaker"` 进行测试，后续可扩展为用户输入

**验收标准**：
- ✅ 客户端能连接 LabVLA 服务（ws://localhost:8000）
- ✅ 至少完成 1 次完整闭环（观测 → 推理 → 动作 → MuJoCo 执行）
- ✅ 机械臂关节随动作输出发生可观察的运动
- ✅ 不崩溃、不 OOM

---

### Step 4：端到端验证

**目的**：确认整个 MuJoCo + LabVLA 闭环可以稳定运行。

**要求**：
- 分别启动 LabVLA 推理服务和 MuJoCo 客户端
- 输入一条简单指令（如 `"pick up the beaker"` 或 `"move to the object"`）
- 观察机械臂能否按预测轨迹运动，持续至少 **5 个推理循环**
- 输出验证报告

**验收标准**：
- ✅ 稳定运行至少 5 帧以上
- ✅ 各帧无 OOM 或连接中断
- ✅ 输出报告包含关键数据（延迟、动作范围、帧率）

---

### Step 5：输出验证报告

在项目根目录生成 `PHASE2-REPORT.md`，结构与 Phase 1 报告对齐：

```markdown
# Phase 2 技术验证报告

## 一、场景配置
- MuJoCo 场景描述（物体、摄像头位置、光照）
- Franka 初始姿态

## 二、闭环测试结果
- 动作帧数
- 平均往返延迟（ms）
- 动作数值范围（min/max/mean per dim）
- 机械臂运动描述（是否合理、是否平滑、是否碰撞）

## 三、问题记录
- 任何异常、报错、或不符合预期的行为

## 四、结论
✅ MuJoCo 闭环验证通过，建议进入 Phase 3
或
❌ 存在阻塞性问题，需要……
```

---

## 四、对 Claude Code 的要求

1. **每完成一步，输出 ✅/❌ 状态**
2. 遇到错误尝试排查修复，记录日志
3. **不修改**以下源文件：
   - `LabVLA/` 框架代码
   - `mujoco_menagerie/` 中的模型文件
4. 所有新代码放 `scripts/` 目录下
5. 最终交付物：`PHASE2-REPORT.md`

---

## 五、数据流参考

```
┌─────────────────────────────────────────────────────────────────┐
│  MuJoCo 仿真客户端                      ┌─────────────────────┐ │
│                                          │  LabVLA 推理服务    │ │
│  ┌──────────┐    ┌──────────┐           │  (4-bit 量化)       │ │
│  │ 3路摄像头 │───→│ img+state│──WS────→│  ws://localhost:8000 │ │
│  │ 渲染      │    │ msgpack  │           │                     │ │
│  └──────────┘    └──────────┘           │  ┌───────────────┐  │ │
│                      ↑                  │  │ 模型推理       │  │ │
│                      │                  │  │ Qwen3-VL-4B    │  │ │
│  ┌──────────┐    ┌──┴──────┐           │  │ + DiT 动作头   │  │ │
│  │ 驱动Franka│←──│ decode  │←──WS─────│  └───────────────┘  │ │
│  │ 执行动作  │    │ delta→abs│          └─────────────────────┘ │
│  └──────────┘    └─────────┘                                    │
└─────────────────────────────────────────────────────────────────┘
```

## 六、注意事项（来自 Phase 1 经验）

- **推理延迟约 2-3 秒**：每次等待动作返回时 MuJoCo 会卡住等待，这是正常的
- **第 1 次推理最慢**：含 CUDA kernel 预热，后续会快一些
- **delta 动作解码**：`new_pos = current_pos + delta`，前 7 维累加，第 8 维（夹爪）直接写入
- **3 路相机**：即使只有 1 路真实图像，其余 2 路也要发占位（可重复同一张）
- **PyYAML 版本**：`pyyaml-include` 用 `1.4.1` 替代 `1.4.0`
- **下载代理**：`HF_ENDPOINT=https://hf-mirror.com` 已配置
- **websocket-client**：需要单独安装，不在基础依赖中
- **labvla_schema.json**：已从 HF Space 复制到 `scripts/` 目录

---

*生成日期：2026-07-13 (v2 更新)*  
*基于 Phase 1 验收结果 ✅ + 2026-07-13 技术讨论*
