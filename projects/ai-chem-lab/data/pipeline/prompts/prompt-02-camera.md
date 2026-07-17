# Prompt 2 — USB 摄像头手部追踪 → 手腕 3D 坐标

## 状态
- 时间：2026-05-25
- 交付物：`run_camera.py`
- 前置条件：USB 摄像头已接上 PC

## 提示词

请帮我写一个 Python 脚本，读取 USB 摄像头的画面，通过 Google MediaPipe 实现左手/右手的手部关键点检测，输出手腕的 3D 空间坐标。

要求：
1. 打开 /dev/video0（或自动检测 USB 摄像头）
2. 使用 mediapipe.solutions.hands 库检测手部
3. 输出 21 个手部关键点的归一化坐标（x, y, z），重点是手腕关键点（landmark 0）
4. 将归一化坐标映射到真实空间尺度：
   - 假设桌面范围 1m × 0.6m，摄像头高于桌面约 0.8m
   - x: 0~1 → 桌面宽度 0~1m
   - y: 0~1 → 桌面深度 0~0.6m
   - z: 0~1 → 高度范围 桌面上 0~0.5m
   - 可调参数，方便后续标定
5. 同时输出每个关键点的检测置信度，低于 0.7 的丢弃
6. 稳定输出在 15-30Hz
7. 一行一个 JSON，包含 timestamp 和手腕坐标 (wx, wy, wz) + 全部 21 点坐标

依赖：opencv-python, mediapipe

输出范例：
{"t": 1234.56, "wrist": [0.35, 0.42, -0.05], "landmarks": [[0.35,0.42,-0.05], ...], "confidence": 0.95}

请提供一份可直接 python run_camera.py 运行的脚本。

## 验证标准
- [ ] `python run_camera.py` 打开摄像头窗口并显示手部追踪
- [ ] 挥手时手部关键点跟随
- [ ] JSON 输出包含手腕 3D 坐标
- [ ] 无手时置信度 < 0.7 的数据被过滤

## 下一步
跑通后执行：prompt-03-mujoco-scene.md
