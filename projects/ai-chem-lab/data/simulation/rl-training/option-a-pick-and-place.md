# Option A：双臂 Pick-and-Place 训练计划

> 创建日期：2026-05-29
> 目标：使用 ALOHA 双臂场景 + 实验室器皿，训练双臂分别拿取物体放到指定位置

---

## 一、训练目标

### 场景设定

```
┌─────────────────────────────────────────┐
│             实验台 (ALOHA)                │
│                                         │
│  [烧杯]      [试管架]      [量筒]        │
│   位置A       位置B         位置C        │
│                                         │
│  ──── 左臂 (ViperX 300) ────────        │
│  ──── 右臂 (ViperX 300) ────────        │
│                                         │
│  [左目标位]                  [右目标位]  │
└─────────────────────────────────────────┘
```

### 任务定义

**双臂并行执行独立 pick-and-place：**

| 臂 | 任务 | 目标 |
|----|------|------|
| **左臂** | 抓起烧杯 → 放到左目标位 | 抓取成功率 ≥ 90% |
| **右臂** | 抓起量筒 → 放到右目标位 | 放置精度 ≤ 2cm |

**约束条件：**
- 双臂可以同时动作（互不干扰）
- 每次训练 episode 随机化器皿初始位置（小幅扰动）
- 手臂不能超出工作空间（关节限位保护）

### 奖励函数设计（简洁版）

```
每个时间步的奖励 = 左臂奖励 + 右臂奖励

每臂奖励 = 
  - 到达奖励：-distance(夹爪, 目标物体) × w₁
  - 抓取奖励：+10  (当成功抓住物体时)
  - 运输奖励：-distance(物体, 目标位置) × w₂
  - 放置成功：+20  (当物体在目标位 ±2cm 内)
  - 掉落惩罚：-5   (物体脱离夹爪)
  - 时间惩罚：-0.1 (鼓励快速完成)
  - 碰撞惩罚：-1   (两臂互撞)
```

---

## 二、技术框架

```
┌──────────────────────────────────────────────────┐
│                  训练栈                            │
├──────────────────────────────────────────────────┤
│   Stable-Baselines3 (RL 算法库)                   │
│   └── SAC (Soft Actor-Critic，软演员-评论家)      │
├──────────────────────────────────────────────────┤
│   Gymnasium (环境封装标准)                         │
│   ├── MuJoCo → Gym 适配                           │
│   └── Wrapper (奖励缩放/帧堆叠/归一化)             │
├──────────────────────────────────────────────────┤
│   MuJoCo (物理引擎)                               │
│   ├── ALOHA 双臂场景 (scene.xml)                  │
│   └── 实验室器皿 (labware.xml)                     │
└──────────────────────────────────────────────────┘

可视化：TensorBoard
```

### 关键包版本
```bash
mujoco>=3.2.0        # 物理引擎
gymnasium>=1.0.0     # RL 环境接口
stable-baselines3>=2.4.0  # RL 算法库
numpy>=1.24.0        # 数值计算
tensorboard          # 训练可视化
```

### 选用 SAC 的原因
| 因素 | SAC | PPO |
|------|-----|-----|
| 样本效率 | ✅ 更高（用更少步收敛） | 中等 |
| 训练稳定性 | ⚠️ 需调参 | 默认参数就稳 |
| 适合连续控制 | ✅ 为连续动作设计 | ✅ 也行 |
| 探索能力 | ✅ 自带熵正则（主动探索） | 较弱 |

SAC 适合有耐心调参的场景，样本效率更高意味着在真机上训练时更省时间。

---

## 三、实施步骤

### Step 1：场景准备 ✅（已完成）
- [x] ALOHA 双臂场景已下载
- [x] 实验室器皿（烧杯、量筒、试管架）已加载
- [x] XML 场景文件可被 viewer 正常打开

### Step 2：编写 Gymnasium 环境

**文件：** `data/simulation/rl-training/envs/aloha_pick_and_place.py`

环境接口：
```python
import gymnasium as gym
from gymnasium import spaces

class AlohaPickAndPlaceEnv(gym.Env):
    """ALOHA 双臂 pick-and-place 环境"""
    
    def __init__(self, render_mode=None):
        self.model = mujoco.MjModel.from_xml_path("...scene.xml")
        self.data = mujoco.MjData(self.model)
        
        # 状态空间：双臂关节角度(2×6) + 末端位置(2×3) + 物体位置(3×3) + 夹爪状态(2)
        # → 约 26 维
        obs_dim = self._compute_obs_dim()
        self.observation_space = spaces.Box(-np.inf, np.inf, (obs_dim,), np.float32)
        
        # 动作空间：双臂各 6 个关节位置 + 夹爪开合(2)
        self.action_space = spaces.Box(-1.0, 1.0, (14,), np.float32)
    
    def step(self, action):
        # 应用动作 → mj_step → 计算奖励 → 返回
        ...
    
    def reset(self, seed=None, options=None):
        # 随机化器皿位置 → 复位双臂到初始姿态
        ...
```

### Step 3：训练脚本

**文件：** `data/simulation/rl-training/scripts/train_pick_and_place.py`

```python
from stable_baselines3 import SAC
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.callbacks import CheckpointCallback
from envs.aloha_pick_and_place import AlohaPickAndPlaceEnv

# 创建环境
env = AlohaPickAndPlaceEnv()
check_env(env)  # 验证环境接口

# 创建 SAC 模型
# SAC 需要更大 replay buffer，自带熵正则探索
model = SAC(
    "MlpPolicy",
    env,
    learning_rate=3e-4,
    buffer_size=100_000,
    batch_size=256,
    tau=0.005,
    gamma=0.99,
    verbose=1,
    tensorboard_log="./logs/",
)

# 训练
model.learn(total_timesteps=500_000)

# 保存
model.save("models/sac_aloha_pnp")
```

### Step 4：可视化训练

```bash
# 启动 TensorBoard
tensorboard --logdir ./logs/
```

关注指标：
- `ep_rew_mean` — 每 episode 平均奖励（应持续上升）
- `ep_len_mean` — 每 episode 步数（应下降）
- `success_rate` — 成功率（自定义 callback 记录）

### Step 5：策略评估

```python
# 加载训练好的模型，在 viewer 中观察效果
model = SAC.load("models/sac_aloha_pnp")
env = AlohaPickAndPlaceEnv(render_mode="human")

obs, _ = env.reset()
for _ in range(1000):
    action, _ = model.predict(obs, deterministic=True)
    obs, reward, terminated, truncated, info = env.step(action)
    if terminated or truncated:
        obs, _ = env.reset()
```

### Step 6：迁移到 MJX（可选，后期优化）

当 SB3/SAC 跑通且需要提升训练速度时：
```bash
pip install mujoco-mjx jax
```

参考 ALOHA 场景自带的 `mjx_scene.patch` 适配 MJX。

---

## 四、目录结构

```
data/simulation/rl-training/
├── envs/
│   └── aloha_pick_and_place.py    ← Gymnasium 环境封装
├── scripts/
│   ├── train_pick_and_place.py    ← 训练入口
│   └── evaluate.py                ← 评估脚本
├── models/                        ← 训练好的模型
│   └── sac_aloha_pnp.zip
├── logs/                          ← TensorBoard 日志
└── configs/
    └── sac_default.yaml           ← 超参数配置
```

---

## 五、训练参数建议

### 初始值（先跑通再优化）

| 参数 | 建议值 | 说明 |
|------|--------|------|
| `learning_rate` | 3e-4 | SAC 默认学习率 |
| `buffer_size` | 100_000 | 经验回放池大小（SAC 需要大 replay buffer） |
| `batch_size` | 256 | 回放采样批大小（SAC 通常比 PPO 大） |
| `gamma` | 0.99 | 折扣因子 |
| `tau` | 0.005 | 目标网络软更新系数 |
| `ent_coef` | auto | 自动调节熵系数（SAC 自带主动探索） |
| `total_timesteps` | 500k ~ 1M | 先 500k 看收敛情况 |

### 收敛判断
- 奖励曲线在 200k-500k steps 内趋于平稳 → 收敛
- 奖励曲线不上升 → 检查 reward 设计或 action space

---

## 六、提示词框架（给 Claude Code）

### 环境封装提示词模板
```
请在 projects/ai-chem-lab/data/simulation/rl-training/envs/ 下创建
aloha_pick_and_place.py：

任务：封装 ALOHA 双臂场景为 Gymnasium 环境

场景路径：data/simulation/mujoco_menagerie/aloha/scene.xml
实验室器皿：data/simulation/mujoco_menagerie/aloha/labware.xml

观测空间（obs）：[
  左臂6个关节角度, 右臂6个关节角度,        # qpos 12维
  左夹爪开合状态, 右夹爪开合状态,           # 2维
  烧杯位置(xyz), 量筒位置(xyz),            # 6维
  左目标位(xyz), 右目标位(xyz)             # 6维
] → 共26维

动作空间：左臂6关节位置控制 + 右臂6关节位置控制 + 左夹爪 + 右夹爪
         → Box(-1, 1, shape=(14,))

奖励规则：
  - 夹爪到物体的距离每减少1cm → +1
  - 抓取成功（物体随夹爪移动）→ +10
  - 物体到达目标位置±2cm → +20（本episode结束）
  - 物体掉落 → -5
  - 两臂碰撞 → -1
  - 每步时间惩罚 → -0.1

要求：
  1. 每次 reset 随机化器皿位置（±5cm 随机偏移）
  2. 使用 mujoco 原生 XML 加载（不需要 render 也能跑）
  3. 实现 check_env 兼容接口
```

### 训练脚本提示词模板
```
在 projects/ai-chem-lab/data/simulation/rl-training/scripts/
创建 train_pick_and_place.py：

使用 SB3 的 SAC 训练双臂 pick-and-place 任务

环境：../envs/aloha_pick_and_place.py 中的 AlohaPickAndPlaceEnv

要求：
  1. 验证环境（check_env）
  2. SAC 参数：lr=3e-4, buffer_size=100_000, batch_size=256, tau=0.005
  3. TensorBoard 日志记录（tensorboard_log="./logs/"）
  4. 每 10000 steps 保存一次 checkpoint
  5. 训练 500k steps
  6. 支持命令行参数（--total_timesteps, --lr 等）
```

---

## 七、管线状态跟踪

- [ ] Step 2：Gymnasium 环境封装完成
- [ ] Step 3：训练脚本编写完成
- [ ] Step 4：首次训练能跑通
- [ ] Step 5：训练收敛（成功率 > 80%）
- [ ] Step 6：MJX 加速迁移（可选）
