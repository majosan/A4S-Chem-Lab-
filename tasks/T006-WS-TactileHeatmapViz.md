# T006-WS-TactileHeatmapVisualization

- Status: PENDING
- Assignee: Company Desktop (WSL)
- Priority: HIGH
- Project: labvla / a4s
- Dependencies: T005 (tactile data injection verified)

## Description

在 MuJoCo Phase 2 闭环运行时，旁边打开一个实时 matplotlib 热力图窗口，显示 12×12 触觉压力网格。夹爪抓物体时热力图同步变化，让触觉数据"看得见"。

## Background

- T005 已验证触觉数据可从 MuJoCo 状态生成并通过 WebSocket 发送
- 目前 LabVLA 是夹爪式，与手套的手指标不符，视觉上无法直接对应
- 热力图在旁边开一个独立窗口，muJoCo 主窗口不受影响
- 目标是：运行 Phase 2 时能实时看到触觉分布变化

## Environment

```
~/projects/labvla-mujoco/     # LabVLA + MuJoCo 项目
~/A4S-Chem-Lab-/              # 主项目仓库
```

Conda: `labvla-cu124`

现有文件：
- `scripts/mujoco_client.py` — Phase 2 客户端（基线）
- `scripts/mujoco_client_tactile.py` — T005 补丁版（生成 + 发送 tactile）
- `scripts/tactile_sim.py` — 模拟压力生成器
- `scripts/glove_grid_mapper.py` — 124 点 → 12×12 网格映射

## Task Steps

### Step 1: Create visualizer module

Create `scripts/heatmap_viz.py` — 独立的热力图可视化模块。

```python
"""heatmap_viz.py — 实时 12×12 触觉热力图显示"""

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from collections import deque


class TactileHeatmap:
    """实时显示 12×12 触觉压力热力图（非阻塞）"""

    def __init__(self, title="触觉压力分布 (12×12)", history_len=50):
        plt.ion()  # 交互模式，非阻塞
        self.fig, self.ax = plt.subplots(figsize=(5, 5))
        self.fig.canvas.manager.set_window_title(title)

        # 初始网格（全零）
        self.grid = np.zeros((12, 12), dtype=np.float32)
        self.im = self.ax.imshow(
            self.grid, cmap="hot", vmin=0, vmax=1.0,
            interpolation="nearest", aspect="equal"
        )
        self.colorbar = self.fig.colorbar(self.im, ax=self.ax, label="Pressure")

        # 标签
        self.ax.set_xticks(range(12))
        self.ax.set_yticks(range(12))
        labels = ["", "食指", "", "中指", "", "无名", "", "小指", "", "", "拇指", ""]
        self.ax.set_xticklabels(labels, fontsize=7)
        self.ax.set_yticklabels(range(12), fontsize=7)
        self.ax.set_xlabel("Finger / Palm Region")
        self.ax.set_ylabel("Tip → Base (row)")
        self.ax.set_title(title)

        # 日志
        self.max_history = history_len
        self.energy_log = deque(maxlen=history_len)
        self.frame_count = 0

    def update(self, grid_12x12: np.ndarray):
        """更新热力图。在主循环每帧调用。"""
        assert grid_12x12.shape == (12, 12), f"Expected (12,12), got {grid_12x12.shape}"

        self.grid = grid_12x12
        self.im.set_data(grid_12x12)
        self.im.set_clim(vmin=0, vmax=max(1.0, grid_12x12.max()))

        # 窗口标题显示总能量
        energy = grid_12x12.sum()
        self.frame_count += 1
        self.energy_log.append(energy)
        avg = np.mean(self.energy_log) if self.energy_log else 0
        self.fig.suptitle(
            f"Frame {self.frame_count} | Energy: {energy:.1f} | Avg: {avg:.1f}"
        )

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        plt.pause(0.001)  # 极小延迟，让 GUI 事件循环有机会处理

    def close(self):
        plt.ioff()
        plt.close(self.fig)


if __name__ == "__main__":
    # 快速测试 — 模拟 50 帧随机数据
    import time

    viz = TactileHeatmap()
    try:
        for i in range(50):
            # 模拟一个移动的亮点
            grid = np.zeros((12, 12), dtype=np.float32)
            rx, ry = 3 + int(i / 5) % 6, 2 + int(i / 3) % 8
            grid[rx, ry] = 0.8
            grid[rx + 1, ry - 1: ry + 2] = 0.3  # 扩散
            viz.update(grid)
            time.sleep(0.1)
    finally:
        viz.close()
    print("✅ heatmap_viz test PASSED")
```

**不依赖 LabVLA 服务** — 本模块独立可测。

---

### Step 2: Patch Phase 2 client with heatmap

创建 `scripts/mujoco_client_heatmap.py` — 基于 T005 的 tactile 客户端，加上热力图显示。

从 `scripts/mujoco_client_tactile.py` 复制并修改：

```python
from heatmap_viz import TactileHeatmap
from glove_grid_mapper import GloveMapper

# 在 main 函数开始时初始化
mapper = GloveMapper()
viz = TactileHeatmap()

try:
    # 在每帧循环中，收到 tactile 后：
    # 1. 用 mapper 把 124 维转换成 12×12 网格
    # 2. 热力图更新
    # ...
    # 关键改动：
    tactical_124 = generate_simulated_tactile(
        gripper_force=gripper_force,
        object_type=args.object_type
    )
    grid_12x12 = mapper.process_frame(tactical_124)
    viz.update(grid_12x12)            # ← 新增：更新热力图
    payload["tactile"] = tactical_124  # 继续发 WebSocket
    # ...
finally:
    viz.close()
```

**特别注意：**
- matplotlib 使用 `plt.ion()` 非阻塞模式，muJoCo 主循环不受影响
- 如果绘图导致 Phase 2 变慢，降低热力图刷新率（每 N 帧更新一次）
- `glove_grid_mapper.process_frame()` 接受 124 维输入，需确认输入格式

**需要添加命令行参数：**
```python
parser.add_argument("--no-viz", action="store_true",
                    help="Disable heatmap visualization (headless mode)")
```

---

### Step 3: Create automation script

创建 `scripts/run_phase2_heatmap.sh` — 同 run_phase2_tactile.sh 但用 heatmap 客户端：

```bash
cp scripts/run_phase2_tactile.sh scripts/run_phase2_heatmap.sh
# 修改其中的 CLIENT 和 LOG 变量指向 heatmap 版本
```

**注意：** WS 是通过 WSL 运行的。matplotlib 图形窗口会显示在 Windows 桌面吗？可能需要在 WSL 中确认：
```bash
echo $DISPLAY
# 如果为空 → WSLG (WSL GUI) 不需要 DISPLAY
# 如果是 :0 或 :1 → 需确认 WSLG 是否启用
```

如果 WSL 中没有图形显示能力，可选方案：
- **方案 B**：保存每一帧的 PNG 到 `output/heatmap_frames/`，运行后合成 GIF/视频
- **方案 C**：用 OpenCV 窗口代替 matplotlib 窗口（更轻量）

---

### Step 4: Run validation

```bash
cd ~/projects/labvla-mujoco
bash scripts/run_phase2_heatmap.sh 2>&1 | tee phase2_t3_heatmap.log
```

**期望结果：**
- LabVLA 服务加载（~3 分钟）
- MuJoCo 窗口打开
- 旁边弹出热力图窗口，显示 12×12 彩色网格
- 夹爪动作时热力图同步变化（抓→热力值升高，放→降低）
- 记录热力图数据到日志

**验证指标：**
| 检查项 | 预期 |
|-------|------|
| 热力图窗口正常弹出 | 每帧更新 |
| 压力与夹爪状态同步 | 夹爪闭合时热力升高 |
| 不同物体类型有区别 | beaker vs spatula 热力分布不同 |
| Phase 2 不受影响 | RTT 变化 < 10% |

---

### Step 5: Documentation

更新 `PHASE2-TACTILE-REPORT.md`，追加 T3 热力图结果（在 Step 8 原始报告中追加即可）。

---

### Step 6: Commit & Push

```bash
cd ~/projects/labvla-mujoco
git add scripts/heatmap_viz.py scripts/mujoco_client_heatmap.py scripts/run_phase2_heatmap.sh
git commit -m "T006: Add tactile heatmap visualization alongside MuJoCo"
git push origin main

# 同步到 A4S
cp PHASE2-TACTILE-REPORT.md ~/A4S-Chem-Lab-/projects/lab-automation/
cd ~/A4S-Chem-Lab-
git add projects/lab-automation/PHASE2-TACTILE-REPORT.md
git commit -m "T006: heatmap visualization complete - add report"
git push origin master
```

## Troubleshooting

### Matplotlib 不显示窗口（WSL GUI 问题）
- WSL2 默认支持 WSLG，不需要额外配置
- 检查方法：运行 `python -c "import matplotlib.pyplot as plt; plt.figure(); plt.plot([1,2,3]); plt.show()"` 看是否有窗口弹出
- 如果不行：安装 `sudo apt install python3-tk`

### 热力图拖慢主循环
- 每 N 帧才更新一次热力图：`if frame % viz_interval == 0: viz.update(grid)`
- 或者在 `--no-viz` 模式下关闭热力图只做数据注入

## After Completion

Update this task with execution summary:

```markdown
## Execution Summary

| Step | Result | Notes |
|------|--------|-------|
| 1. Create heatmap_viz.py | ✅/❌ | |
| 2. Patch Phase 2 client | ✅/❌ | |
| 3. Automation script | ✅/❌ | |
| 4. Run validation | ✅/❌ | RTT impact: |
| 5. Documentation | ✅/❌ | |
| 6. Commit + push | ✅/❌ | |

**Key findings:**
- WSL GUI works? Y/N
- Latency impact with/without viz:
- Any issues:
