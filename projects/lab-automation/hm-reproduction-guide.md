# HM 复现指南 — T005 + T006 全流程

> 目标：在家里台式电脑（HM）上复现今天 WS 上全部跑通的内容。
> 这些步骤已包含所有踩过的坑的修复，HM 的 Claude Code 可直接按此执行。
> 状态：🚀 READY

---

## 0. 先决条件确认

HM 上必备条件（2026-07-18 已验证通过）：

| 条件 | 确认命令 |
|------|---------|
| Conda 环境 | `conda activate labvla-cu124 && python -c "import torch; print(torch.cuda.is_available())"` → True |
| labvla-mujoco 仓库 | `cd ~/projects/labvla-mujoco && git status` |
| A4S 仓库 | `cd ~/A4S-Chem-Lab- && git pull origin master` |
| 模型权重 | `ls ~/projects/labvla-mujoco/LabVLA-5B-Base/` → 非空 |
| MuJoCo menagerie | `find ~ -name "franka_emika_panda" -type d 2>/dev/null` |
| WSLg 图形 | `echo $DISPLAY` → 应为 `:0` |

**路径兼容性检查（HM 专属）：**
```bash
# 检查 scene.xml 引用的路径是否存在
grep "panda.xml" ~/projects/labvla-mujoco/scripts/mujoco_scene.xml 2>/dev/null

# 如果引用的是 ~/ai-chem-lab/... 但实际在 ~/venv/ai-chem-lab/...
# 创建符号链接（仅需一次）：
ln -sf ~/venv/ai-chem-lab ~/ai-chem-lab
```

---

## 1. 拉取最新代码

```bash
cd ~/A4S-Chem-Lab-
git pull origin master

cd ~/projects/labvla-mujoco
git pull origin main
```

---

## 2. Step 1 — 复制 mapper + 测试

```bash
cd ~/projects/labvla-mujoco

# 从 A4S 拷贝 mapper
cp ~/A4S-Chem-Lab-/projects/lab-automation/glove_grid_mapper.py scripts/glove_grid_mapper.py

# 创建 mapper 测试脚本
cat > scripts/test_mapper.py << 'PYEOF'
"""Quick test: verify glove_grid_mapper standalone"""
import sys
sys.path.insert(0, 'scripts')
from glove_grid_mapper import GloveMapper
import numpy as np

mapper = GloveMapper()
fake_pressure = np.random.rand(124).astype(np.float32) * 255
grid = mapper.process_frame(fake_pressure)

print(f"Input: 124 floats")
print(f"Output shape: {grid.shape}")
print(f"Output dtype: {grid.dtype}")
print(f"Value range: {grid.min():.2f} - {grid.max():.2f}")
print(f"Non-zero cells: {np.count_nonzero(grid)} / 144")
assert grid.shape == (12, 12), f"Expected (12,12), got {grid.shape}"
print("✅ Mapper test PASSED")
PYEOF

python scripts/test_mapper.py
```

---

## 3. Step 2 — 创建 tactile_sim.py（索引已修正版）

```bash
cat > scripts/tactile_sim.py << 'PYEOF'
"""tactile_sim.py — Generate simulated tactile data from MuJoCo state.

Produces physically plausible 124-dim pressure vectors based on
gripper state and contact info.

⚠️ 124维索引映射规则（对应 glove_grid_mapper.py 的 _map_124_directly）：
   手指区 [0-59]: 6行 × 每行10个 (小→无名→中→食→拇, 各2列)
   手掌区 [60-123]: 8行 × 8列
"""

import numpy as np

FINGER_124_IDX = {
    "pinky":  [0,1, 10,11, 20,21, 30,31, 40,41, 50,51],
    "ring":   [2,3, 12,13, 22,23, 32,33, 42,43, 52,53],
    "middle": [4,5, 14,15, 24,25, 34,35, 44,45, 54,55],
    "index":  [6,7, 16,17, 26,27, 36,37, 46,47, 56,57],
    "thumb":  [8,9, 18,19, 28,29, 38,39, 48,49, 58,59],
}
PALM_124_IDX = list(range(60, 124))


def generate_simulated_tactile(
    gripper_force: float = 0.0,
    object_type: str = "beaker"
) -> np.ndarray:
    """Generate tactile pressure vector based on gripper state."""
    tactile = np.zeros(124, dtype=np.float32)
    
    if gripper_force < 0.01:
        return tactile
    
    force = float(gripper_force)
    noise = np.random.randn(124).astype(np.float32) * 0.02 * force
    
    if object_type == "beaker":
        for fname, idx_list in FINGER_124_IDX.items():
            for i, pos in enumerate(idx_list):
                row_progress = i // 2
                pressure = np.interp(row_progress, [0, 5], [0.25, 0.45]) * force
                tactile[pos] = pressure
        for i, pos in enumerate(PALM_124_IDX):
            row = i // 8
            pressure = np.interp(row, [0, 7], [0.2, 0.08]) * force
            tactile[pos] = pressure
        
    elif object_type == "spatula":
        for pos in FINGER_124_IDX["thumb"][:2]:
            tactile[pos] = 0.6 * force
        for pos in FINGER_124_IDX["index"][:2]:
            tactile[pos] = 0.5 * force
        for pos in PALM_124_IDX:
            tactile[pos] = 0.01 * force
        
    elif object_type == "bottle":
        for fname, idx_list in FINGER_124_IDX.items():
            for i, pos in enumerate(idx_list):
                row_progress = i // 2
                pressure = np.interp(row_progress, [0, 5], [0.3, 0.5]) * force
                tactile[pos] = pressure
        for pos in PALM_124_IDX[:24]:
            tactile[pos] = 0.05 * force
    else:
        tactile = noise * 0.3
    
    tactile = np.clip(tactile + noise, 0.0, 1.0)
    return tactile.astype(np.float32)


if __name__ == "__main__":
    for obj in ["beaker", "spatula", "bottle", "none"]:
        p = generate_simulated_tactile(0.7, object_type=obj)
        nz = np.count_nonzero(p)
        print(f"tactile_sim({obj}): shape={p.shape}, "
              f"range=[{p.min():.3f}, {p.max():.3f}], "
              f"nonzero={nz}/124")
        # 零力测试
        p_zero = generate_simulated_tactile(0.0, object_type=obj)
        assert p_zero.sum() == 0, f"zero-force should be all-zero, got sum={p_zero.sum()}"
    print("✅ tactile_sim test PASSED")
PYEOF

python scripts/tactile_sim.py
```

---

## 4. Step 3 — T1 基线测试 + T2 触觉注入

**关键优化（从 WS 经验总结）：** T1 和 T2 共享同一个 LabVLA 服务进程，避免 5 分钟冷启动等待。

### 4a. 先跑 T1 基线

```bash
cd ~/projects/labvla-mujoco

# 检查 Phase 2 客户端是否存在（T003 产物）
ls scripts/mujoco_client.py || echo "Phase 2 not set up — run T003 first"

# 启动 Phase 2 闭环（包含 LabVLA 服务 + MuJoCo 客户端）
# 如果已有 run_phase2.sh：
bash scripts/run_phase2.sh 2>&1 | tee phase2_t1_baseline.log

# 预期结果（HM RTX 4060 Ti / 16GB）：
# - 模型加载 ~90s（vs WS 208s）
# - 首帧 RTT ~740ms（vs WS ~10s）
# - 后续帧 RTT ~194ms（vs WS ~2840ms）
# - HM 16GB VRAM 无需 CPU offload
```

### 4b. 创建 tactile 注入版客户端

```bash
# 复制 tactile 客户端（如果 A4S 仓库同步了）
cp scripts/mujoco_client.py scripts/mujoco_client_tactile.py
```

编辑 `scripts/mujoco_client_tactile.py`，在观测采集处加入：
```python
from tactile_sim import generate_simulated_tactile

# 在帧循环中，获取 gripper 状态后：
gripper_force = 1.0 - (gripper_ctrl / 255.0)
tactile = generate_simulated_tactile(
    gripper_force=gripper_force,
    object_type="beaker"
)
obs["tactile"] = tactile
```

### 4c. 创建 T2 自动化脚本

```bash
cp scripts/run_phase2.sh scripts/run_phase2_tactile.sh
```

编辑 `scripts/run_phase2_tactile.sh`：
- 将 `mujoco_client.py` → `mujoco_client_tactile.py`
- 日志文件名改为 `phase2_t2_tactile.log`

### 4d. 运行 T2（等待 T1 服务还热着的时候尽快启动）

```bash
bash scripts/run_phase2_tactile.sh 2>&1 | tee phase2_t2_tactile.log
```

**关键指标验证（HM 预期 vs WS 对比）：**
| 指标 | WS (4060 8GB) | HM (4060 Ti 16GB) | 检查 |
|------|:------------:|:-----------------:|:----:|
| T1 加载时间 | 230s | ~90s | |
| T1 首帧 RTT | ~10.8s | ~740ms | |
| T1 后续 RTT | ~2840ms | ~194ms | |
| T2 后续 RTT | ~2892ms | ~240ms（预期） | 加触觉后看有无明显增加 |
| 触觉注入 | ✅ | ✅ | 服务不应报错 |

---

## 5. Step 4 — 热力图可视化（T006）

### 5a. 创建 heatmap_viz.py

```bash
cat > scripts/heatmap_viz.py << 'PYEOF'
"""heatmap_viz.py — 实时 12×12 触觉热力图显示"""

import matplotlib.pyplot as plt
import numpy as np
from collections import deque


class TactileHeatmap:
    """实时显示 12×12 触觉压力热力图（非阻塞）"""

    def __init__(self, title="Tactile Pressure (12×12)", history_len=50):
        plt.ion()
        self.fig, self.ax = plt.subplots(figsize=(5, 5))
        self.fig.canvas.manager.set_window_title(title)

        self.grid = np.zeros((12, 12), dtype=np.float32)
        self.im = self.ax.imshow(
            self.grid, cmap="hot", vmin=0, vmax=1.0,
            interpolation="nearest", aspect="equal"
        )
        self.fig.colorbar(self.im, ax=self.ax, label="Pressure")

        # 使用英文标签避免中文字体警告
        labels = ["", "Idx", "", "Mid", "", "Ring", "", "Pinky", "", "", "Thumb", ""]
        self.ax.set_xticks(range(12))
        self.ax.set_yticks(range(12))
        self.ax.set_xticklabels(labels, fontsize=7)
        self.ax.set_yticklabels(range(12), fontsize=7)
        self.ax.set_xlabel("Finger / Palm")
        self.ax.set_ylabel("Tip → Base")
        self.ax.set_title(title)

        self.max_history = history_len
        self.energy_log = deque(maxlen=history_len)
        self.frame_count = 0

    def update(self, grid_12x12):
        assert grid_12x12.shape == (12, 12), f"Expected (12,12), got {grid_12x12.shape}"
        self.grid = grid_12x12
        self.im.set_data(grid_12x12)
        self.im.set_clim(vmin=0, vmax=max(1.0, grid_12x12.max()))

        energy = grid_12x12.sum()
        self.frame_count += 1
        self.energy_log.append(energy)
        avg = np.mean(self.energy_log) if self.energy_log else 0
        self.fig.suptitle(f"Frame {self.frame_count} | Energy: {energy:.1f} | Avg: {avg:.1f}")

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        plt.pause(0.001)

    def close(self):
        plt.ioff()
        plt.close(self.fig)


if __name__ == "__main__":
    import time
    viz = TactileHeatmap()
    try:
        for i in range(50):
            grid = np.zeros((12, 12), dtype=np.float32)
            rx, ry = 3 + int(i / 5) % 6, 2 + int(i / 3) % 8
            grid[rx, ry] = 0.8
            grid[rx + 1, ry - 1: ry + 2] = 0.3
            viz.update(grid)
            time.sleep(0.1)
    finally:
        viz.close()
    print("✅ heatmap_viz test PASSED")
PYEOF

python scripts/heatmap_viz.py
```

**HM 特殊提示：** HM 也是 WSL2 + WSLg，matplotlib 应自动用 Qt5Agg 后端。如果看不到窗口：
```bash
# 确认 WSLg 启用
echo $DISPLAY  # 应输出 :0

# 如果不行：
pip install matplotlib
python -c "import matplotlib; print(matplotlib.get_backend())"
# 应输出 Qt5Agg 或 TkAgg
```

### 5b. 创建 heatmap 版客户端

```bash
cp scripts/mujoco_client_tactile.py scripts/mujoco_client_heatmap.py
```

在 `scripts/mujoco_client_heatmap.py` 开头加入：
```python
from heatmap_viz import TactileHeatmap
from glove_grid_mapper import GloveMapper

# 在 main 中，连接 WebSocket 之后、帧循环之前：
mapper = GloveMapper()
viz = TactileHeatmap()

# 在帧循环中，生成 tactile 之后：
grid_12x12 = mapper.process_frame(tactile)
viz.update(grid_12x12)

# 在 finally 块中关闭：
viz.close()

# 添加命令行参数：
# parser.add_argument("--no-viz", action="store_true")
```

### 5c. 运行 T3 热力图测试

```bash
cp scripts/run_phase2_tactile.sh scripts/run_phase2_heatmap.sh
# 修改客户端脚本指向 heatmap 版本
bash scripts/run_phase2_heatmap.sh 2>&1 | tee phase2_t3_heatmap.log
```

**预期：** MuJoCo 窗口 + 热力图窗口同时弹出。夹爪抓→热力图亮，张开→全黑。

---

## 6. 验证汇总

运行以下代码输出汇总表：

```bash
cat > scripts/report_summary.py << 'PYEOF'
"""打印 HM 对比 WS 的结果汇总"""
print("=" * 68)
print("HM 复现验证 — 结果汇总")
print("=" * 68)
print()
print(f"{'测试项':<30} {'WS (4060 8GB)':>14} {'HM (4060 Ti 16GB)':>18}")
print("-" * 68)
# 从日志中提取 RTT 的脚本（简化版）
print(f"{'T1 模型加载':<30} {'230s':>14} {'':>18}")
print(f"{'T1 首帧 RTT':<30} {'~10.8s':>14} {'':>18}")
print(f"{'T1 后续帧 RTT':<30} {'~2840ms':>14} {'':>18}")
print(f"{'T2 触觉注入 RTT':<30} {'~2892ms':>14} {'':>18}")
print(f"{'T3 热力图 RTT':<30} {'~1631ms':>14} {'':>18}")
print(f"{'触觉数据发送':<30} {'✅':>14} {'':>18}")
print(f"{'热力图显示':<30} {'✅':>14} {'':>18}")
print()
print("⚠️  把实际 HM 数值填入上方空列后截图")
PYEOF

python scripts/report_summary.py
```

---

## 7. 提交结果

```bash
cd ~/projects/labvla-mujoco
git add scripts/glove_grid_mapper.py scripts/test_mapper.py
git add scripts/tactile_sim.py scripts/heatmap_viz.py
git add scripts/mujoco_client_tactile.py scripts/mujoco_client_heatmap.py
git add scripts/run_phase2_tactile.sh scripts/run_phase2_heatmap.sh
git add phase2_*.log
git commit -m "HM: T005+T006 full pipeline re-run"
git push origin main

# 同步报告到 A4S
cp PHASE2-TACTILE-REPORT.md ~/A4S-Chem-Lab-/projects/lab-automation/PHASE2-TACTILE-REPORT-HM.md
cd ~/A4S-Chem-Lab-
git add projects/lab-automation/PHASE2-TACTILE-REPORT-HM.md
git commit -m "HM: add re-run report"
git push origin master
```

---

## 附录：踩坑记录（WS → HM 迁移注意事项）

| 坑 | HM 检查 |
|----|---------|
| conda 环境名 | 确认 `labvla-cu124` 存在 |
| muJoCo menagerie 路径 | `find ~ -name "franka_emika_panda"` |
| scene.xml 引用路径 | `grep panda.xml scripts/mujoco_scene.xml` |
| WSLg 图形 | `echo $DISPLAY` 应为 `:0` |
| SSH key 权限 | `repo write` 权限确认 |
| 模型权重 | `ls LabVLA-5B-Base/` 非空 |
| environment.yml 修复 | torchaudio + setuptools + flash-attn（见 7/18 记录） |
