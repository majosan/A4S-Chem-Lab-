# 仿真技术栈全景图

> 2026-05-24 决策记录

## 整体架构

```
采集层 ───▶ 仿真层 ───▶ 训练层 ───▶ 真机层
               │            │
               ▼            ▼
           MuJoCo MJX    PyTorch
           (域随机化)     (策略网络)
```

## 选型决策

| 选项 | 结论 | 原因 |
|------|------|------|
| **仿真引擎** | MuJoCo + MJX | 免费开源Apache2.0，触觉sensor原生支持，MJX GPU批量训练，Sim-to-Real行业标准 |
| **备选关注** | Genesis v0.3.0 | 流体/变形原生支持、速度快，但才1.5岁，触觉sensor待完善，等2027年评估 |
| **已排除** | PyBullet | 开发停滞、接触精度不如MuJoCo、无GPU加速 |
| **RL接口** | Gymnasium | 行业标准，兼容MuJoCo |
| **模型框架** | PyTorch | 主流，灵活 |
| **GPU加速** | CUDA + JAX (MJX) | WSL2 原生支持 |
| **操作系统** | WSL2 (Ubuntu 22.04) | GPU直通、VS Code集成、USB usbipd转发 |

## 发展阶段

### Phase 1：仿真环境搭建（当前 ~ 手套缝好）
- [ ] WSL2 环境配置（GPU + USB 串口）
- [ ] 安装 MuJoCo + MJX
- [ ] 创建实验室基础场景 XML（实验台 + 器皿）
- [ ] 触觉手套 124 点数据接入仿真
- [ ] IMU 数据接入仿真
- [ ] MuJoCo viewer 可视化验证

### Phase 2：动作识别管道
- [ ] 6类化学实验动作的场景定义
- [ ] 数据流管道：真实数据 → 虚拟手驱动
- [ ] Gymnasium env 封装
- [ ] 域随机化管道搭建

### Phase 3：Sim-to-Real
- [ ] 策略在 MJX 中批量训练
- [ ] 域随机化参数调优
- [ ] 迁移到真机验证

## 参考链接
- MuJoCo: https://mujoco.org/
- MJX: https://mujoco.readthedocs.io/en/stable/mjx.html
- Genesis: https://github.com/Genesis-Embodied-AI/genesis-world
- Gymnasium: https://gymnasium.farama.org/
- usbipd-win: https://github.com/dorssel/usbipd-win
