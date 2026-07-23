# MuJoCo 一周入门计划

> 地点：WSL2 (Ubuntu 22.04) + VS Code + Claude Code
> 目标：7天从零到能搭建一个完整的仿真闭环

---

## Day 1：基础概念 + 第一个仿真

**学习目标**：理解 MuJoCo 最核心的三个概念，跑通第一个仿真。

### 三个核心概念
| 概念 | 类比 | 作用 |
|------|------|------|
| **Model** | 模具 | 定义场景里有什么（几何体、关节、传感器） |
| **Data** | 面团 | 当前状态（位置、速度、力） |
| **mj_step** | 擀一下 | 物理引擎向前推进一步 |

### 任务
1. 进 WSL2，跑验证项目的第一个测试：
```bash
cd ~
mkdir -p ai-chem-lab
python3 ~/venv/chem-lab/bin/python3 projects/ai-chem-lab/verification/test_01_basic.py
```
2. 看代码，理解 model/data/step 的关系
3. 改参数（改球的半径、颜色、初始高度），观察变化

### 输出
- 理解 MuJoCo 的基本工作流程
- 能在 Python 里创建最简单的场景

---

## Day 2：MJCF 场景语言

**学习目标**：学会用 XML 描述一个物理世界。

### 任务
创建一个 `scene_arm.xml`，包含：
- 一个底座 + 两段机械臂（肩关节 + 肘关节）
- 一个目标方块
- 关节限制（不能转过头）

```xml
<!-- 参考框架 -->
<mujoco>
  <worldbody>
    <body name="base">
      <joint name="shoulder" type="hinge" axis="0 1 0"/>
      <geom type="cylinder" size="0.1 0.05"/>
      <body name="upper_arm">
        <joint name="elbow" type="hinge" axis="0 1 0"/>
        <geom type="capsule" fromto="0 0 0 0 0 0.3" size="0.03"/>
        <body name="forearm">
          ...
        </body>
      </body>
    </body>
  </worldbody>
</mujoco>
```

### 要掌握的元素
- `geom` — 几何体（box, sphere, cylinder, capsule, mesh）
- `body` — 刚体（可以嵌套）
- `joint` — 关节（hinge 旋转, slide 滑动, free 自由）
- `site` — 标记点（传感器位置）
- `actuator` — 驱动器（电机）

### 资料
- 官方 MJCF 参考：https://mujoco.readthedocs.io/en/stable/XMLreference.html
- 或者直接问 AI："帮我写一个 MJCF 场景，两关节机械臂 + 目标物体"

---

## Day 3：传感器 + 控制

**学习目标**：让机械臂动起来，并读取数据。

### 任务
1. 在 Day 2 的机械臂上添加位置电机（position actuator）
2. 写 Python 代码让机械臂做正弦运动
3. 添加触觉传感器，模拟触碰目标

```python
# 控制循环框架
model = mujoco.MjModel.from_xml_path("scene_arm.xml")
data = mujoco.MjData(model)

for t in range(1000):
    # 发出控制指令
    data.ctrl[0] = 0.5 * math.sin(t * 0.05)  # 肩关节
    data.ctrl[1] = -0.8 + 0.3 * math.sin(t * 0.03)  # 肘关节
    
    mujoco.mj_step(model, data)
    
    # 读取传感器
    touch_data = data.sensor("touch_sensor").data.copy()
```

### 要掌握的概念
- `data.ctrl` — 控制信号输入
- `data.qpos` — 关节位置
- `data.sensor()` — 传感器数据
- `mj_step` 的时序理解

---

## Day 4：导入外部模型 (URDF)

**学习目标**：学会导入现成的机器人模型，而不是自己从头搭。

### 任务
1. 下载一个 Franka Emika Panda 机械臂 URDF
2. 用 MuJoCo 加载并查看
3. 找一个烧杯/试管模型（STL），导入场景

```python
# 加载 URDF
model = mujoco.MjModel.from_xml_path("franka/panda.xml")
data = mujoco.MjData(model)

# 也可以把 URDF 合并到 MJCF 场景里
# 通过 <include> 或 <body> 引用
```

### 资源
- 现成 URDF：https://github.com/ros-industrial/franka_description
- 简单 3D 模型：Thingiverse / Printables 搜 "beaker" "test tube"
- 或者 AI 直接生成 STL（文字生成 3D 模型）

---

## Day 5：可视化 + 交互

**学习目标**：学会用 MujoCo viewer 调试场景。

### 任务
1. 用 `mujoco.viewer` 打开你的机械臂场景
2. 在 viewer 里拖动视角、切换显示模式
3. 尝试 `launch_passive`（代码控制 + 手动查看）
4. 在 viewer 里添加标记（显示目标位置）

```python
# 基本 viewer 用法
with mujoco.viewer.launch_passive(model, data) as viewer:
    while viewer.is_running():
        # 你的控制逻辑
        mujoco.mj_step(model, data)
        viewer.sync()
```

### 要掌握的操作
- 鼠标左键旋转视角
- 鼠标滚轮缩放
- 右键平移
- 按 ESC 退出

---

## Day 6：Gymnasium 环境封装

**学习目标**：把自己搭的场景包装成标准的 RL 训练环境。

### 任务
创建一个简单的 reaching task 环境：
- 状态：关节角度 + 末端位置
- 动作：关节力矩/位置
- 奖励：末端越接近目标越好

```python
import gymnasium as gym
from gymnasium import spaces

class ChemLabEnv(gym.Env):
    def __init__(self):
        self.model = mujoco.MjModel.from_xml_path("scene_arm.xml")
        self.data = mujoco.MjData(self.model)
        
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(6,))
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(2,))
    
    def step(self, action):
        self.data.ctrl[:] = action
        mujoco.mj_step(self.model, self.data)
        obs = self._get_obs()
        reward = self._compute_reward(obs)
        return obs, reward, False, False, {}
    
    def reset(self, seed=None):
        mujoco.mj_resetData(self.model, self.data)
        return self._get_obs(), {}
```

### 输出
一个可被任何 RL 算法调用的标准环境接口。

---

## Day 7：综合项目 — 闭环仿真

**学习目标**：把所有知识串起来，完成一个完整的仿真闭环。

### 任务
搭建一个"**机械臂伸向烧杯**"的场景：

| 需求 | 实现 |
|------|------|
| 场景 | 实验台 + 机械臂 + 烧杯 |
| 传感器 | 触觉（接触力） |
| 控制 | 位置控制 → 到达目标 |
| 闭环 | 当末端接近烧杯时停止 |
| 可视化 | viewer 实时显示 |

### 验收标准
- 场景能成功加载并显示
- 机械臂能受控运动到目标位置
- 触碰到烧杯时传感器有读数
- 代码结构清晰，可复用

---

## 学习建议

### 遇到不会的怎么办
直接问 AI。例如：
> "帮我写一个 MuJoCo 场景，两关节机械臂 + 目标物体，用 MJCF XML 格式"

### 要不要记笔记
建议在 `~/ai-chem-lab/` 下建 `notes/` 目录，每天建一个 markdown 文件记心得。Claude Code 也可以帮你整理。

### 第一天就先做一件事
进入 WSL2，VS Code 打开 `~/ai-chem-lab/`，跑通 test_01_basic.py，然后再改着玩。其他的慢慢来。
