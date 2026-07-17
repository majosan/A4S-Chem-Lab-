# Prompt 1 — IMU 数据读取 + 手腕四元数

## 状态
- 时间：2026-05-25（最后更新 2026-05-28）
- 交付物：`run_imu.py`
- 前置条件：IMU 已通过 USB-UART 转接板接上 PC

## 提示词

请帮我写一个 Python 脚本，在 WSL2 (Ubuntu 22.04) 下读取 9-DOF IMU 传感器数据。

硬件连接方式：
- IMU 通过 UART 模式（115200 波特率）连接到 USB-UART 转换板，插在电脑 USB 口
- 在 Linux 下显示为 /dev/ttyUSB0 或 /dev/ttyACM0

需求：
1. 自动检测 IMU 所在的串口设备（扫描 /dev/ttyUSB* 和 /dev/ttyACM*）
2. 读取原始 9 轴数据：加速度 (ax,ay,az)，陀螺仪 (gx,gy,gz)，地磁 (mx,my,mz)
3. 直接用 IMU 芯片内置的融合算法读出绝对欧拉角（roll/pitch/yaw）或四元数
4. 以大约 30-50Hz 的稳定频率输出数据
5. 数据格式：一行一个 JSON，包含 timestamp 和四元数
6. 可通过 Ctrl+C 优雅退出

依赖：pyserial（根据具体 IMU 型号可能需要额外驱动库）

输出范例：
{"t": 1234.56, "quat": [0.707, 0.0, 0.707, 0.0], "accel": [0.1, -0.2, 9.8]}

请提供一份可以直接 python run_imu.py 运行的脚本。

## 验证标准
- [ ] `python run_imu.py` 能打印出四元数 JSON
- [ ] 转动 IMU 板，四元数值实时变化
- [ ] Ctrl+C 优雅退出

## 下一步
跑通后执行：prompt-02-camera.md
