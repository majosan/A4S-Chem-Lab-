# Prompt 4 — 三合一主控：数据同步驱动 MuJoCo 虚拟手

## 状态
- 时间：2026-05-25
- 交付物：`main_pipeline.py`
- 前置条件：Phase 2 完成（IMU + 摄像头 + MuJoCo 场景各自独立跑通）

## 提示词

请帮我写一个主控脚本 main_pipeline.py，将以下三个模块整合成一个完整的数据采集与可视化同步系统。

依赖模块（假设已存在）：
- run_imu.py（输出 IMU 四元数 JSON 流）
- run_camera.py（输出手腕坐标 JSON 流 + 手部关键点）
- load_scene.py（加载 MuJoCo 场景并接收关节角度更新）

需求：
1. 启动三个子进程（IMU、摄像头、MuJoCo 渲染）
2. 从 IMU 进程读取四元数 → 写入 MuJoCo 手腕旋转（qpos[0:4]）
3. 从摄像头进程读取手腕 3D 坐标 → 写入 MuJoCo 手腕位置（qpos 平移部分）
4. 从摄像头进程读取手指关键点（landmarks 1-20）→ 映射为 15 个手指关节弯曲角度 → 写入 MuJoCo（qpos[4:19]）
5. 所有数据打上统一时间戳对齐
6. 实时刷新 MuJoCo 渲染窗口，显示虚拟手与真实手同步运动
7. 按 'R' 键开始录制数据，按 'S' 键停止，录制的数据保存到 recordings/ 目录下（JSON 格式，包含 IMU + 视觉 + MuJoCo qpos）
8. 按 'Q' 键退出

数据同步精度要求：
- 延迟 < 50ms（人眼感知不明显）
- 使用多线程 + 队列，不阻塞主渲染循环

请提供一份完整的可直接运行的脚本，并附带 requirements.txt

## 验证标准
- [ ] `python main_pipeline.py` 启动后，MuJoCo 窗口中的虚拟手跟随真实手运动
- [ ] 手部旋转时虚拟手同步旋转
- [ ] 手指弯曲时虚拟手指对应弯曲
- [ ] R/S 键录制数据存到 recordings/
- [ ] Q 键优雅退出

## 完成标志
✅ 4 个 Phase 全部跑通，真实传感器驱动虚拟人手完成
