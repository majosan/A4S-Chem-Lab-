# 传感数据 → MuJoCo 仿真管线

> 最后更新：2026-05-25
> 创建人：Josan / AI 工作伙伴
> 目标：打通"真实传感器 → 虚拟人手同步"的数据回路，为后续 Sim-to-Real 训练奠定基础

---

## 一、项目现状（2026-05-25）

### 已有资产

| 资产 | 状态 | 备注 |
|------|------|------|
| WSL2 + MuJoCo/MJX 环境 | ✅ 已完成 | Ubuntu 22.04, Python 3.11, CUDA 12.6 |
| 桌面两臂机器人 | ⏳ 选型完成（待采购） | 推荐 OpenArm 2.0（见 data/hardware/robot-selection.md） |
| 灵巧手 | ❌ 待评估 | 机器人自带夹爪，先评估是否需要灵巧手 |
| 9-DOF IMU | ✅ 调试成功 | 新 IMU 传感器数据已成功接收（2026-06-08） |
| 触觉手套（布片） | ✅ 数据采集可用 | 已委托专业人士缝制，等待成品测试 |
| 烧杯/量筒/绿球 | ✅ 已购入 | 物理实验道具 + lab_equipment 3D 模型 |
| USB 摄像头 | ⏳ 待购买 | 推荐先买普通 USB 摄像头（¥100），后续再 D435 |

### 技术架构决策

```
                PC (WSL2 Ubuntu 22.04)
                ┌────────────────────────────┐
USB 摄像头 ─────┤  cv2 + MediaPipe           │
                │    → 手腕 3D 坐标 + 手指点   │
                │                            │
IMU (UART/USB) ─┤  pyserial                  │
                │    → 四元数（手腕旋转）     │
                │                            │
触觉手套 (USB) ─┤  pyserial                   │
                │    → 手指角度 + 掌心压力     │
                │                            │
                └─────────┬──────────────────┘
                          │ (data fusion)
                          ▼
                ┌────────────────────────────┐
                │  MuJoCo 仿真场景            │
                │  - 虚拟人手（四元数+指关节）  │
                │  - 桌面 + 烧杯/量筒/球       │
                │  - 接收实时传感器数据流       │
                └────────────────────────────┘
```

### 硬件连接说明

- **IMU → PC**：不需要额外 MCU。IMU 通过 UART 或 USB 连接 PC，显示为 `/dev/ttyUSB0`。芯片自带融合算法直接输出四元数。
- **摄像头 → PC**：普通 USB 摄像头，直接插。MediaPipe 在 PC 上跑手部检测，不需要外置驱动板。
- **触觉手套 → PC**：已有串口通信管线。
- **未来机器人**：通过 USB/以太网连接 PC 独立控制器。

---

## 二、实施路线图（4 阶段）

### Phase 1：传感器裸数据跑通（1-3 天）

目标：每个传感器独立工作在 PC 上读出稳定数据流。

#### Step 1.1 — IMU 读写
- 连接 IMU（UART 模式）到 PC
- Python 脚本通过 pyserial 读取，输出四元数 JSON 流
- 验证：手转动 IMU 板，数据实时变化
- **提示词文件**：`prompts/prompt-01-imu.md`

#### Step 1.2 — 摄像头手部追踪
- USB 摄像头连接 PC，MediaPipe 检测手部 21 个关键点
- 输出手腕 3D 坐标 + 全部指节坐标 JSON 流
- 验证：摄像头前挥手，坐标实时变化
- **提示词文件**：`prompts/prompt-02-camera.md`

#### Step 1.3 — 触觉手套串口数据（已有）
- 验证现有管线能稳定输出 136 点传感数据
- 格式化为手指角度映射

### Phase 2：MuJoCo 仿真场景搭建（1 周）

目标：和真实物理世界对应的数字孪生场景渲染出来。

#### Step 2.1 — 场景模型
- 桌面 + 烧杯 + 量筒 + 绿球（基础几何体）
- MJCF XML 格式

#### Step 2.2 — 虚拟人手模型
- 19 自由度人手骨骼树（手腕球关节 4 + 五指 15 关节）
- 指尖加 touch sensor

#### Step 2.3 — Python 加载脚本
- 接收 JSON 传感器帧 → 驱动 qpos → mj_forward 刷新渲染
- **提示词文件**：`prompts/prompt-03-mujoco-scene.md`

### Phase 3：数据融合同步（3-5 天）

目标：真实手和虚拟手实时同步运动。

#### Step 3.1 — 三合一主控脚本
- 多线程 + 队列：IMU 线程 + 摄像头线程 + MuJoCo 渲染主线程
- 统一时间戳对齐
- 按键录制数据到 `recordings/`
- **提示词文件**：`prompts/prompt-04-main-pipeline.md`

#### Step 3.2 — 数据同步验证
- 肉眼观察虚拟手是否跟随真实手运动
- 延迟 < 50ms 达标

#### Step 3.3 — 录制第一组实验数据
- 执行一个简单动作（伸手→拿烧杯）
- 保存含 IMU + 视觉 + 关节角的完整数据包

### Phase 4（后续）：仿真训练 + 机器人选型

待 Phase 3 跑通后规划。

---

## 三、Prompt 链（提示词索引）

所有 prompt 保存在 `prompts/` 目录下，按顺序执行：

| 提示词 | 文件 | 交付物 | 前置条件 |
|--------|------|--------|---------|
| Prompt 1 | `prompts/prompt-01-imu.md` | `run_imu.py` | IMU 硬件就绪 |
| Prompt 2 | `prompts/prompt-02-camera.md` | `run_camera.py` | USB 摄像头就绪 |
| Prompt 3 | `prompts/prompt-03-mujoco-scene.md` | `scene.xml` + `load_scene.py` | Phase 1 完成 |
| Prompt 4 | `prompts/prompt-04-main-pipeline.md` | `main_pipeline.py` | Phase 2 完成 |

### 验证标准

每跑通一个，在下面打勾：

- [ ] Phase 1.1：`python run_imu.py` 输出稳定四元数 JSON（IMU 硬件已工作 ✅）
- [ ] Phase 1.2：`python run_camera.py` 显示实时手部追踪（摄像头待购入）
- [ ] Phase 2：`python load_scene.py` 渲染 MuJoCo 场景（需搭建虚拟手场景）
- [ ] Phase 3：`python main_pipeline.py` 真实手驱动虚拟手（需 Phase 1+2 就绪）

---

## 四、硬件清单

### 已购入
- [x] 9-DOF IMU（BNO055 调试失败已退货 → 新 IMU 已调通并成功接收数据 ✅）
- [x] USB-UART 转接板
- [x] 触觉手套（含串口采集硬件，已委托专业人士缝制中 ⏳）
- [x] 烧杯、量筒、绿色球（物理实验道具）
- [x] lab_equipment 3D 模型（用于 MuJoCo 仿真）

### 待购入
- [ ] Intel RealSense D435（手部追踪，¥2,000-2,500，详见 `hardware/camera-selection.md`）
  - ⚠️ 可先用普通 USB 摄像头（¥100）跑通流程，之后再升级
- [ ] 普通 USB 摄像头（推荐先行，¥100 跑 MediaPipe 手指跟踪）

### 非必需（Phase 4 前不需要）
- [ ] 桌面机器人臂（选型建议：OpenArm 2.0，详见 `../hardware/robot-selection.md`）
- [ ] 灵巧手（如有需要再评估）

---

## 五、技术要点备忘

### IMU → 手腕旋转
- IMU 芯片自带 9 轴融合算法，直接读四元数即可
- 不需要自己写 Madgwick / Mahony 滤波
- UART 模式 115200 波特率，一帧约 100 bytes，理论 1000Hz+
- 实际输出稳定在 30-50Hz（够用）

### 摄像头 → 手腕位置
- MediaPipe 检测 21 个手部关键点，landmark 0 是手腕
- 归一化坐标 (0-1) 需要映射到真实桌面尺度（可调参数）
- 单凭摄像头 z 轴精度有限（单目深度不准），但做 demo 够用
- 未来可升级为双目 / RealSense

### 手套 → 手指角度
- 124/136 个传感点 → 需要映射为 15 个关节角度
- 每根手指 3 个弯曲自由度（MCP/PIP/DIP）
- 映射方式：最大值滤波 → 归一化 → linear mapping 到关节角度范围
- 精确校准需要做"全开/全握"标定

### MuJoCo 同步
- 使用 `mj_forward()`（纯向前运动学），不跑动力学
- 不必用 `mj_step()`（会触发物理引擎，没必要且降低帧率）
- 帧率目标：30fps+（人眼感知流畅）

---

## 六、技术选型记录

| 决策点 | 选择 | 理由 | 日期 |
|--------|------|------|------|
| 仿真引擎 | MuJoCo + MJX | 免费开源，原生触觉 sensor，GPU 批量训练 | 2026-05-24 |
| 备选 | Genesis | 流体/变形原生，v0.3.0 关注，2027 年再评估 | 2026-05-24 |
| 排除 | PyBullet | 开发停滞，无 GPU 加速 | 2026-05-24 |
| 人手位置方案 | IMU 旋转 + 摄像头位置 | 纯 IMU 位置漂移严重，加摄像头补 | 2026-05-25 |
| 操作系统方案 | WSL2 (Ubuntu 22.04) | GPU 直通，VS Code 集成，USB 串口 usbipd-win | 2026-05-24 |
| IMU 接口 | UART 模式 | 直连 USB-UART 转接板，Linux 识别为串口设备 | 2026-05-25 |
| 手部追踪库 | MediaPipe | 无需 GPU，USB 摄像头即用 | 2026-05-25 |
| 是否需额外 MCU | 不需要 | IMU + 摄像头 + 手套皆可 PC 直连 | 2026-05-25 |
