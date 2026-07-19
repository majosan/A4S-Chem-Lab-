# LabVLA Phase 2 增强任务 — 实现稳定抓取放置

> **背景**：Phase 2 基础闭环已验证通过（MuJoCo 场景 + WebSocket 通信成功），
> 但机械臂行为呈「鬼畜」状态（抖动/振荡），未完成「抓取 A 放到 B」的完整动作。
> 此增强任务定位在 Phase 2 内部，不阻碍 Phase 3 启动。

---

## 一、问题诊断（必读）

### 当前现象
机械臂在 MuJoCo 中抖动剧烈，无法收敛到目标位置。

### 根因分析（3 个叠加）

| # | 根因 | 说明 |
|---|------|------|
| 1️⃣ | **预训练模型没见过仿真画面** | LabVLA-5B-Base 训练数据全部是真机照片，MuJoCo 渲染图的光照/纹理/阴影分布完全不同，模型输出等于"猜" |
| 2️⃣ | **按帧推理 → 帧间不一致** | 每次只执行 chunk[0] 然后重新观测→推理，50 步 chunk 只用了第 0 步，浪费了模型对后续动作的预测连贯性 |
| 3️⃣ | **无动作平滑 + 无关节限幅** | delta 动作不做任何后处理，几步累积就可能超出安全范围，产生剧烈回弹 |

### 解决方案路线

```
不依赖模型质量：先上工程措施让动作稳定下来
→ 如果仍不够：用脚本化 IK 做基线演示
→ 记录数据给 Phase 3
```

---

## 二、增强任务清单（Claude Code 执行部分）

### Task 1：修复动作执行逻辑 — 正确的 Action Chunk 调度

**目的**：解决根因 #2，让 50 步 Action Chunk 被充分利用。

**当前代码问题**（推测）：
```python
# 当前：只取 chunk[0]
action = action_chunk[0]           # shape (8,)
new_joint = current_joint + action[:7]  # 只推进 1 步
```

**需要改成 Temporal Chunk Execution**：
```python
# 修复后：一次性执行 chunk 中的 n 步
ACTION_HORIZON = 10                # 每次推理后连续执行 10 步
step_idx_in_chunk = 0              # chunk 内游标

def on_inference_response(action_chunk):
    """保存完整 chunk，不再 onetime 消费"""
    return action_chunk             # shape (50, 8)

def step_mujoco():
    global step_idx_in_chunk
    action = cached_chunk[step_idx_in_chunk]
    # 执行动作...
    step_idx_in_chunk += 1
    need_inference = (step_idx_in_chunk >= ACTION_HORIZON)
    return need_inference
```

**关键参数**（建议初始值，后续可调）：
| 参数 | 建议值 | 说明 |
|------|--------|------|
| `ACTION_HORIZON` | 10 | 每个推理 chunk 连续执行 10 步后再重新观测推理 |
| `CHUNK_STRIDE` | 5 | 如果取 10，则消费第 0-9 步，留下 40 步丢弃（位置） |

**验证标准**：
- ✅ 机械臂抖动大幅减少（从"剧烈鬼畜"变为"慢速漂移"）
- ✅ 推理频率从 ~0.5Hz 降低到 ~0.1Hz，延迟不再是瓶颈
- ✅ MuJoCo 仿真不再卡死等待 WS 返回

---

### Task 2：添加动作平滑与关节安全限幅

**目的**：解决根因 #3，防止机械臂跑飞。

**在动作执行前增加过滤层**：

```python
# ── 关节限幅 ──
JOINT_LIMITS = {
    'panda_joint1': (-2.8973, 2.8973),
    'panda_joint2': (-1.7628, 1.7628),
    'panda_joint3': (-2.8973, 2.8973),
    'panda_joint4': (-3.0718, -0.0698),
    'panda_joint5': (-2.8973, 2.8973),
    'panda_joint6': (-0.0175, 3.7525),
    'panda_joint7': (-2.8973, 2.8973),
}
GRIPPER_LIMITS = (0.0, 0.08)  # 夹爪开度

def clamp_actions(action_8d, current_pos_8d):
    """限幅 + 速度限制"""
    # 1. 计算目标位置
    target = current_pos_8d + action_8d * SCALE
    
    # 2. 限幅到关节物理范围
    for i in range(7):
        lo, hi = FRANKA_JOINT_LIMITS[i]
        target[i] = np.clip(target[i], lo, hi)
    
    # 3. 限幅到最大步进（防止单帧跳跃过大）
    max_step = 0.05  # rad/step
    delta = target - current_pos_8d
    delta = np.clip(delta, -max_step, max_step)
    
    return current_pos_8d + delta

# ── 指数平滑 ──
SMOOTH_ALPHA = 0.3  # 0=完全平滑(不动), 1=不平滑

smoothed_action = None

def smooth_action(raw_action):
    global smoothed_action
    if smoothed_action is None:
        smoothed_action = raw_action
    else:
        smoothed_action = SMOOTH_ALPHA * raw_action + (1 - SMOOTH_ALPHA) * smoothed_action
    return smoothed_action
```

**验证标准**：
- ✅ 机械臂运动边界清晰，不会跑飞到不可逆姿态
- ✅ 即使模型输出动作异常，关节也始终在安全范围内运动
- ✅ 指数平滑后轨迹连续性改善（抖动消除）

---

### Task 3：添加脚本化 Pick-and-Place 演示（可选但强烈推荐）

**目的**：当前模型无法在陌生仿真场景中可靠操作，但我们需要一个**工作演示**。
用 MuJoCo 内置的 IK / 关节空间轨迹规划实现"抓取烧杯 A 放到位置 B"的完整闭环。

**注意**：这不是放弃 VLA 路线，而是 Phase 2 需要一个可演示的能力证明。

```python
def scripted_pick_and_place(
    mj_model, mj_data, 
    object_pos, target_pos, 
    gripper_open_width=0.08,
):
    """
    完全脚本化的抓取放置流程（不依赖模型）
    7 个阶段：
    1. Home 姿态 → 2. 预抓取位（物体上方 10cm）
    3. 下降抓取 → 4. 闭合夹爪 → 5. 提升
    6. 移动到目标上方 → 7. 下降释放
    
    使用 MuJoCo 的 mj_fkine / mj_forward 计算 IK
    或直接用关节角度插值（示教模式）
    """
    phases = [
        ("home", home_qpos),                    # 初始
        ("pre_grasp", pre_grasp_qpos),          # 上方
        ("descend", descend_qpos),              # 接触
        ("close_gripper", grasp_qpos),          # 抓取
        ("lift", lift_qpos),                    # 提起
        ("pre_place", pre_place_qpos),          # 移到目标上方
        ("descend_place", place_qpos),          # 下降
        ("release", release_qpos),              # 释放
        ("retreat", retreat_qpos),              # 退回
    ]
    # 每阶段线性插值 N 步
    return episode_data  # 返回 (观测, 动作) 序列
```

**验证标准**：
- ✅ MuJoCo 渲染窗口中，Franka 机械臂执行完整的"抓住烧杯→提升→移到右侧→放下"动作
- ✅ 烧杯物理附着在夹爪上，随机械臂移动
- ✅ 动作花费 < 10 秒（仿真时间）
- ✅ 可以在每次运行时复现（确定性）

---

### Task 4：记录 Episode 数据（Phase 3 对接）

**目的**：脚本化演示中产生的 (观测, 动作) 序列，格式对齐 Phase 3 数据管道。

**数据格式标准**（对齐 LabVLA + RLDS）：

```python
episode = {
    "steps": [
        {
            "observation": {
                "camera_1_rgb": np.uint8, (224, 224, 3),
                "camera_2_rgb": np.uint8, (224, 224, 3),
                "camera_3_rgb": np.uint8, (224, 224, 3),
                "state": np.float32, (8,),  # 7 关节 + 1 夹爪
            },
            "action": np.float32, (8,),      # 7 关节 + 1 夹爪
            "timestep": int,
        },
        ...
    ],
    "language_instruction": "pick up the beaker and place it on the right",
}
```

**存储格式**：HDF5 或 npz（每 episode 一个文件，方便 Phase 3 批量加载）

**验证标准**：
- ✅ 成功保存至少 1 个完整 pick-and-place episode
- ✅ 文件可被独立加载验证（写一个简单的 load 检查脚本）
- ✅ 观测-动作序列长度对齐（每时间步都有完整观测和对应动作）

---

## 三、交付物要求

### 输出文件清单

```
~/projects/labvla-mujoco/
├── scripts/
│   ├── mujoco_client.py              ← (已存在) 增加 Task 1-2 的修改
│   ├── demo_pick_place.py             ← 新增：Task 3 脚本化演示
│   ├── check_joint_limits.py          ← 新增：关节限幅验证工具
│   └── load_episode.py                ← 新增：加载验证 episode 数据
└── data/
    └── episodes/                      ← 新增：录制的演示数据
        └── pick_place_001.npz
```

### 验收标准（权重排序）

| # | 标准 | 优先级 |
|---|------|--------|
| 1️⃣ | MuJoCo 中机械臂停止鬼畜抖动 → 动作稳定 | **P0 必须** |
| 2️⃣ | 脚本化演示能看到"抓取烧杯→放置到右侧"的完整动画 | **P0 必须** |
| 3️⃣ | 关节限幅生效，不会跑到非法位置 | P1 强烈建议 |
| 4️⃣ | episode 数据成功保存 | P1 强烈建议 |
| 5️⃣ | 动作平滑参数可调 | P2 锦上添花 |

---

## 四、对 Claude Code 的要求

1. **先诊断再动手** — 在修改代码前，先排查当前 client 代码中动作执行的逻辑，看看到底是哪种根因导致的
2. **每完成一个 Task 输出明确 ✅/❌ 状态**
3. **不修改** `LabVLA/` 框架代码和 `mujoco_menagerie/` 模型文件
4. **参数调优**：SMOOTH_ALPHA、ACTION_HORIZON、max_step 均留出可调节的常量定义
5. **最终交付**验证视频/GIF + 简短诊断报告（见下方）

### 输出报告模板

在项目根目录追加到 `PHASE2-REPORT.md` 文件末尾：

```markdown
## 四、Phase 2 Enhancements（新增 — 2026-07-19）

### 诊断结果
- [诊断原因描述]
- 原始 client 执行的逻辑是：[chunk 消费方式 / 有无限幅 / 有无平滑]

### Task 1 执行结果
- ACTION_HORIZON = __  → 机械臂行为改善：[描述]
- 推理频率从 __ Hz 降低到 __ Hz

### Task 2 执行结果
- 关节限幅：[起效/不生效/不需要]
- SMOOTH_ALPHA = __ → 抖动：[完全消除/显著减少/仍存在]
- 最终配置参数：[SMOOTH_ALPHA, ACTION_HORIZON, max_step]

### Task 3 执行结果
- 脚本化演示：[成功/部分成功/失败]
- 若成功：是否完成 7 阶段全流程：
  home → pre-grasp → descend → close → lift → pre-place → descend → release
- 烧杯是否正确附着在夹爪上移动？

### Task 4 执行结果
- episode 数据已保存：✅ 位置 `data/episodes/pick_place_001.npz`
- 验证脚本可用：✅/❌
- 观测-动作序列长度：__ 步

### 结论
✅ Phase 2 增强完成 — 可进入 Phase 3
或
❌ 存在阻塞性问题，需要……
```

---

*生成日期：2026-07-19*  
*作者：传感前锋 ⚡*  
*任务定位：Phase 2 内部增强，不改变 Phase 3 启动计划*
