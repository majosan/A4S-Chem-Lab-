"""
test_01_basic.py — MuJoCo 基本安装验证
加载一个简单的摆钟模型，跑 1000 步，验证安装正确
"""
import mujoco
import numpy as np

# 创建一个最简单的 MuJoCo 模型：一个自由落体的球
XML = """
<mujoco>
  <worldbody>
    <light name="top" pos="0 0 2"/>
    <geom name="floor" type="plane" size="1 1 0.1" rgba="0.8 0.8 0.8 1"/>
    <body name="ball" pos="0 0 1">
      <freejoint/>
      <geom name="sphere" type="sphere" size="0.1" rgba="1 0 0 1"/>
    </body>
  </worldbody>
</mujoco>
"""

# 加载模型
model = mujoco.MjModel.from_xml_string(XML)
data = mujoco.MjData(model)

print(f"MuJoCo 版本: {mujoco.__version__}")
print(f"模型加载成功: {model.ngeom} 个几何体, {model.nbody} 个刚体")
print(f"开始仿真 1000 步...")

# 仿真 1000 步
for i in range(1000):
    mujoco.mj_step(model, data)
    
    if i == 0:
        print(f"初始位置: z={data.qpos[2]:.4f}")
    if i == 500:
        print(f"500步后位置: z={data.qpos[2]:.4f}")
    if i == 999:
        print(f"1000步后位置: z={data.qpos[2]:.4f}")

# 验证球确实下落了
assert data.qpos[2] < 0.9, "球没有正常下落，物理引擎可能有问题"
print("✅ test_01_basic 通过 — MuJoCo 安装正确，物理引擎正常工作")
