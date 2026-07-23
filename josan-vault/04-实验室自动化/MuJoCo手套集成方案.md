# MuJoCo 手套数据融合验证计划

## 现状
- ✅ LabVLA MuJoCo 场景：Franka Panda + 桌面 + 烧杯试管 + 3路RGB相机
- ✅ Phase 2 闭环验证通过（模型输出 action → MuJoCo 物理步进）
- ✅ 手套 124 压力点，JSON @15fps，USB串口
- ✅ 网格映射代码已写好（glove_grid_mapper.py）

## 下一步：在已有 MuJoCo 场景里验证手套数据接入

---

## Step 1：在 MuJoCo 中模拟手套压力数据（不需要真手套）

在 `run_phase2.py`（你已有的闭环脚本）里，在采集观测数据时加入**模拟手套数据**：

```python
# 在现有观测采集代码中
def get_observation(env, glove_data=None):
    """MuJoCo环境观测，增加手套数据通道"""
    # 原有观测
    rgb = env.render_cameras()          # 3×224×224 RGB
    joints = env.get_joint_states()      # robot proprioception
    
    # 新增：模拟或真实手套数据
    if glove_data is not None:
        tactile = glove_data             # 124维向量
    else:
        # 模拟：根据末端力和夹爪状态生成逼真压力
        gripper_force = env.get_gripper_force()        # [0, 1]
        contact = env.get_contact_info()               # 哪些部分有接触
        
        tactile = generate_simulated_tactile(
            gripper_force, contact, env.grasp_object
        )
    
    # 组合观测
    obs = {
        "images": rgb,
        "proprioception": joints,
        "tactile": tactile,              # ← 新增！
    }
    return obs
```

### 模拟压力生成函数

```python
def generate_simulated_tactile(gripper_force, contact_info, object_type):
    """
    根据MuJoCo物理状态模拟合理的压力分布
    让模型学"握瓶子时手指根部压力大、掌心有包裹感"这种规律
    """
    tactile = np.zeros(124)
    
    if gripper_force > 0.01:  # 正在抓取
        # 拇指 + 食指/中指 用力（捏取模式）
        if object_type == "beaker":  # 烧杯
            # 全手包裹模式：拇指+掌心大面积接触
            tactile[0:12] = 0.3  # 拇指
            tactile[12:24] = 0.2  # 食指
            tactile[24:36] = 0.2  # 中指
            tactile[64:128] = 0.15  # 掌心
        elif object_type == "spatula":  # 勺子
            # 拇指+食指捏模式
            tactile[0:6] = 0.6   # 拇指针尖
            tactile[12:18] = 0.5  # 食指针尖
        # ... 其他模式
    
    return tactile * gripper_force  # 按抓取力缩放
```

这个函数的目的是先让 LabVLA **能接收 124 维触觉输入并训练**，压力值逼不逼真不重要，重要的是**打通数据管线**。

---

## Step 2：改 LabVLA 观测编码器（加触觉通道）

在你的 LabVLA 代码中找到观测编码部分，加一个小MLP：

```python
# 在 observation_encoder.py 或类似文件中

class ObservationEncoder(nn.Module):
    def __init__(self):
        super().__init__()
        # ... 原有视觉编码器 ...
        self.vision_encoder = ...
        
        # 新增：触觉编码器
        self.tactile_encoder = nn.Sequential(
            nn.Linear(124, 256),
            nn.ReLU(),
            nn.Linear(256, 128),
            nn.LayerNorm(128)
        )
        
        # 融合投影
        self.fusion = nn.Linear(
            vision_dim + proprio_dim + 128,  # 加128维触觉特征
            model_dim
        )
    
    def forward(self, images, proprioception, tactile=None):
        vis_feat = self.vision_encoder(images)
        pro_feat = self.proprio_encoder(proprioception)
        
        if tactile is not None:
            tac_feat = self.tactile_encoder(tactile)  # (B, 128)
        else:
            tac_feat = torch.zeros(B, 128)  # 无手套时补零
        
        # 融合
        combined = torch.cat([vis_feat, pro_feat, tac_feat], dim=-1)
        return self.fusion(combined)
```

---

## Step 3：MuJoCo 测试对比

在 Phase 2 闭环上跑以下对比：

| 测试 | 配置 | 预期 |
|------|------|------|
| T1 | 无手套数据（原Phase 2） | 基线 |
| T2 | 有模拟手套（随机值） | 检查管线是否堵住 |
| T3 | 有模拟手套（物理合理值） | 看看是否提升抓取成功率 |

### 评估指标
- 抓取成功率
- 烧杯放置精度
- 任务完成率
- 推理延迟

---

## Step 4：接真实手套

MuJoCo 验证通过后，用真实手套数据替代模拟数据。

```
真实手套 (USB串口, JSON@15fps)
    ↓ serial.read()
    ↓ json.loads()
    ↓ glove_grid_mapper.process_frame()
    ↓ 124维特征向量
    ↓ 插值到30fps（和相机对齐）
    ↓ LabVLA观测编码器
```

### USB串口读取代码

```python
import serial
import json
import threading
from collections import deque
from glove_grid_mapper import GloveMapper

class GloveReader:
    def __init__(self, port="/dev/ttyUSB0", baud=115200):
        self.serial = serial.Serial(port, baud, timeout=0.1)
        self.mapper = GloveMapper()
        self.latest = None
        self.buffer = deque(maxlen=5)
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
    
    def _loop(self):
        while self.running:
            line = self.serial.readline().decode().strip()
            if not line:
                continue
            data = json.loads(line)
            pressure = data.get("pressure", [])
            ts = data.get("timestamp", 0)
            glove = self.mapper.process_frame(pressure, ts)
            self.latest = glove
            self.buffer.append(glove)
    
    def get_pressure_vector(self):
        """返回最近一帧的124维向量"""
        if self.latest is None:
            return np.zeros(124, dtype=np.float32)
        return self.latest.get_feature_vector()
    
    def close(self):
        self.running = False
        self.serial.close()
```

---

## 集成的最终调用方式

在你现有的 Phase 2 主循环中，只需要加几行：

```python
# === 现有 Phase 2 代码中 ===
from glove_grid_mapper import GloveMapper

# 可选：真手套
# glove = GloveReader("/dev/ttyUSB0")

for step in range(max_steps):
    # 1. 采集观测
    rgb = env.render()
    joints = env.get_joint_state()
    
    # 2. 手套数据（先模拟，后替换为真）
    tactile = generate_simulated_tactile(env)  
    # 将来替换为: tactile = glove.get_pressure_vector()
    
    # 3. 模型推理
    action = labvla_model.predict(rgb, joints, tactile)  # ← 新增tactile参数
    
    # 4. 执行
    env.step(action)
```

---

## 任务清单

- [ ] 复制 glove_grid_mapper.py 到 labvla-mujoco 项目目录
- [ ] 在 run_phase2.py 中加入 `generate_simulated_tactile()` 函数
- [ ] 修改观测编码器，增加 `tactile_encoder` MLP
- [ ] 跑 T1：验证原基线不变（tactile=None 时补零）
- [ ] 跑 T2：模拟压力随机值，验证管线通
- [ ] 跑 T3：物理合理压力，看收敛效果
- [ ] 通过后，写 glove_reader.py 接真实手套
