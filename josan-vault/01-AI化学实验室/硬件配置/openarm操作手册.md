# OpenArm 跑通指南

> 创建日期：2026-06-08
> 目标：不花一分钱先在 MuJoCo 上跑通 OpenArm 仿真，再评估是否需要手搓或购买

---

## 一、立即能在 MuJoCo 跑起来

OpenArm 官方有 **`openarm_mujoco`** 仓库，内含完整的 MJCF 文件（双臂场景），直接拖入 MuJoCo simulate 即可。

### 执行步骤（5 分钟内）

```bash
# 1. 克隆 MuJoCo 描述文件
cd ~/projects/ai-chem-lab/data/simulation/
git clone https://github.com/enactic/openarm_mujoco.git

# 2. 确认 MuJoCo 版本（文档要求 3.3.4）
# 你的环境已有 MuJoCo，检查版本：
python -c "import mujoco; print(mujoco.__version__)"

# 3. 如果版本不符，装 3.3.4
pip install mujoco==3.3.4

# 4. 用 MuJoCo simulate 加载双臂场景
mujoco_simulate openarm_mujoco/v1/openarm_bimanual.xml

# 或者用 Python 脚本加载
python openarm_mujoco/v1/openarm_bimanual.py  # 如果存在
```

### 你能看到的

| 场景文件 | 内容 |
|---------|------|
| `v1/openarm_bimanual.xml` | **双臂场景** — 左右各一个 7DOF 臂 + 基座 |
| `v1/openarm_left.xml` | 单左臂 |
| `v1/openarm_right.xml` | 单右臂 |
| `assets/` | 各种 mesh 文件（STL/OBJ） |

### 玩什么

1. **拖拽关节** — MuJoCo simulate 里可以手动拖动各关节，感受 7DOF 运动范围
2. **力矩控制** — OpenArm MJCF 使用 torque control，你可以写 Python 脚本发送力矩控制
3. **集成到我们的场景** — 把 openarm_bimanual.xml 和我们已有的器皿模型合并

---

## 二、看看官方文档（全部开源）

| 仓库 | 内容 | 作用 |
|------|------|------|
| [openarm](https://github.com/enactic/openarm) | 项目主仓库，文档入口 | 先看这个 |
| [openarm_mujoco](https://github.com/enactic/openarm_mujoco) | **MJCF 文件 + 仿真资源** | ⭐ **现在就能跑** |
| [openarm_description](https://github.com/enactic/openarm_description) | URDF/xacro 描述文件 | 用于 ROS2/仿真 |
| [openarm_hardware](https://github.com/enactic/openarm_hardware) | **CAD 全套**（STL + STEP + Fusion 360） | ⭐ **手搓必备** |
| [openarm_can](https://github.com/enactic/openarm_can) | CAN 总线控制库 | 真机控制 |
| [openarm_ros2](https://github.com/enactic/openarm_ros2) | ROS2 集成包 | 用于复杂管线 |
| [openarm_teleop](https://github.com/enactic/openarm_teleop) | 遥操作框架 | 人机协同核心 |
| [openarm_dataset](https://github.com/enactic/openarm_dataset) | 数据集录制/回放工具 | 模仿学习管道 |

官方文档站：[docs.openarm.dev](https://docs.openarm.dev)

---

## 三、"手搓一台"可行性分析

### 你需要什么

| 类别 | 需要的能力 | Josan 的专业背景 |
|------|-----------|----------------|
| 机械设计 | 看懂 CAD，能 CNC 或 3D 打印 | 机械 ✅ |
| 电子/电路 | 接线、驱动 Damiao 电机、CAN 通信 | 硬件 ✅ |
| 软件/固件 | Python、C++、CAN 驱动 | 软件 ✅ |
| 调试 | 调 PID、坐标系校准、MT 联调 | 全栈 ✅ |

> 从你的背景看（机械+软件+硬件），**手搓一台完全可行**。

### BOM 成本估算

OpenArm 的 BOM 和购买链接全部公开在 `openarm_hardware` 仓库。根据已有信息估算：

| 组件 | 估算成本（USD） |
|------|---------------|
| Damiao 电机 ×7（4310 ×4 + 4340P ×2 + 8009P ×1） | ~$1,500-2,000 |
| CNC 铝结构件 + 钢轴 | ~$500-800 |
| CAN-FD 控制板 | ~$100-200 |
| 电源 + 线束 + 接插件 | ~$200-400 |
| 3D 打印外壳件 | ~$100-200 |
| 螺丝/轴承/小件 | ~$100-200 |
| **单臂材料总成本** | **~$2,500-3,800** |
| **双臂材料总成本** | **~$5,000-7,600** |

**对比**：
- 手搓双臂：~$5,000-7,600（材料费）+ 数周~数月工时
- 买成品双臂：$6,500（WowRobo 组装测试好）
- 买 DIY 套件双臂：约 $3,000（仅 ReBot 有此选项，OpenArm 暂无）

### 手搓 vs 购买对比

| 维度 | 手搓 | 买成品（WowRobo） |
|------|------|-----------------|
| 成本 | $5k-7.6k（材料费） | $6,500 |
| 时间 | 数周~数月 | 20-40 天 |
| 质量控制 | 取决于你的手艺 | 工厂测试过 |
| 技术理解 | 🔥 **极高** — 100% 吃透每个零件 | 中等 — 开箱即用 |
| 定制空间 | **无限制** — 想怎么改怎么改 | CAD 开源也能改 |
| 风险 | 画板子焊线可能烧 | 有保修 |
| 故障维修 | 自己能修，备件自己找 | 可能需送修 |
| 成就感 | 🏆 **手搓一台 7DOF 人形臂！** | 正常购买 |

### 建议路径

```
          时间段                      产出
    ┌──────────────────┐      ┌──────────────────┐
    │ 今天              │      │  MuJoCo 跑通      │
    │ 克隆 repo         │ ──→  │  看双臂模型        │
    │ 拖入 simulate     │      │  拖拽关节感受      │
    └──────────────────┘      └──────────────────┘
    
    ┌──────────────────┐      ┌──────────────────┐
    │ 本周              │      │  评估手搓可行性    │
    │ 看 CAD 和 BOM     │ ──→  │  算是否值得自己搞   │
    │ 逛 Discord 社区   │      │  摸清难度          │
    └──────────────────┘      └──────────────────┘

         选择 A  ▼                     选择 B  ▼
    ┌──────────────────┐      ┌──────────────────┐
    │ 手搓双臂          │      │ 下单 WowRobo V2   │
    │ $5k-7.6k + 时间  │      │  $6,500 + 20-40天 │
    │ 100% 吃透       │      │  开箱即用          │
    └──────────────────┘      └──────────────────┘
          ↓                            ↓
    ┌──────────────────────────────────────────────┐
    │  殊途同归 — 最后都在 MuJoCo 上跑 RL 训练        │
    │  都在 Discord 社区里跟其他开发者交流              │
    │  都给我们的实验台搬砖 🤖🧪                       │
    └──────────────────────────────────────────────┘
```

### 关键的决策问题

问自己这几个问题后就能做决定：

1. **你的时间值多少钱？** 手搓省 1-2k 美元，但要投入几十上百小时
2. **你想学这个吗？** 如果手搓过程本身就是你想要的（学习 Damiao 电机、CAN 总线、URDF 建模），那这笔账就不能只看钱
3. **你准备用到什么程度？** 如果你后续会频繁拆改，手搓反而比买成品更适合——你已经知道每颗螺丝在哪

### 我作为首席 Agent 的建议

1. **今天先跑 MuJoCo 仿真** — 0 成本，5 分钟内看到双臂在屏幕上动
2. **逛一下 Discord 社区** — 和已经手搓过的人聊聊，真实经验比什么都值钱
3. **如果追求快速出成果** → 买成品（$6,500），省下的时间用来跑 IMU+MediaPipe+RL
4. **如果享受动手过程** → 手搓一台，完成后你比任何人都懂这台机器
5. **折中方案** → 买一套单臂成品 + 自己搓另一条臂，一边学习一边干活两不误

---

## 四、更新后的项目计划（结合手搓可能性）

### 并行工作线（更新版）

```
本周 ──── 立即做 ──────────────────────────────────
  ├── 🖥️ 跑 OpenArm MuJoCo 仿真（Joshua 今天做）
  ├── 🎮 继续跑 ALOHA RL 训练（Claude Code）
  └── 💰 买普通 USB 摄像头（¥100）

本周 ──── 评估决策 ────────────────────────────────
  ├── 逛 Discord，看手搓经验
  ├── 下载 CAD 看结构复杂度
  ├── 算 BOM 成本 + 采购时间线
  └── 决定：手搓 / 买成品 / 折中

下周 ──── 执行 ────────────────────────────────────
  ├── 如果手搓：下单 Damiao 电机 + CNC 结构件
  ├── 如果买：下 WowRobo 单（20-40 天到货）
  └── 如果折中：买单臂 + 手搓另一条臂

并行（不依赖硬件）：
  ├── IMU→MuJoCo 联动（Pipeline Prompt 3）
  ├── 触觉手套缝制（等成品测试）
  └── RL 训练持续优化
```
