# 环境验证项目

## 目标
验证 WSL2 + MuJoCo + MJX + GPU 加速已正确安装，并跑通一个完整的仿真管道。

## 包含的测试

| 文件 | 测试内容 | 预期结果 |
|------|---------|---------|
| `test_01_basic.py` | MuJoCo 基本加载 + 步进 | 仿真跑通，无报错 |
| `test_02_mjx_gpu.py` | MJX GPU 批量仿真 | 输出 GPU 设备信息，1k 批量仿真 |
| `test_03_render.py` | MuJoCo viewer 可视化 | 弹窗显示机器人/物体 |
| `test_04_tactile_sim.py` | 触觉传感器仿真 | 读取接触力数据 |

## 使用方式

```bash
cd projects/ai-chem-lab/verification
python3 test_01_basic.py
python3 test_02_mjx_gpu.py
python3 test_03_render.py      # WSLg 需要正常
python3 test_04_tactile_sim.py
```
