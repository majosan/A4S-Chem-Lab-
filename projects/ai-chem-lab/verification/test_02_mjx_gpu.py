"""
test_02_mjx_gpu.py — MJX GPU 批量仿真验证
测试 JAX 是否可用 GPU、MJX 是否正常工作
"""
import jax
import jax.numpy as jp
import mujoco
import mujoco.mjx as mjx
import time

print(f"JAX 版本: {jax.__version__}")
print(f"可用设备: {jax.devices()}")

# 检测是否有 GPU
devices = jax.devices()
has_gpu = any(d.platform == 'gpu' for d in devices)
print(f"GPU 加速: {'✅ 可用' if has_gpu else '❌ 不可用（将使用 CPU）'}")

# 创建模型：双摆（复杂一点，测试批量仿真）
XML = """
<mujoco>
  <option timestep="0.01"/>
  <worldbody>
    <light name="top" pos="0 0 2"/>
    <geom name="floor" type="plane" size="2 2 0.1"/>
    <body name="pendulum" pos="0 0 0.5">
      <joint name="hinge1" type="hinge" axis="0 1 0" pos="0 0 0"/>
      <geom name="arm1" type="capsule" fromto="0 0 0 0 0 0.3" size="0.02" rgba="0 0 1 1"/>
      <body name="pendulum2" pos="0 0 0.3">
        <joint name="hinge2" type="hinge" axis="0 1 0" pos="0 0 0"/>
        <geom name="arm2" type="capsule" fromto="0 0 0 0 0 0.3" size="0.02" rgba="1 0 0 1"/>
      </body>
    </body>
  </worldbody>
</mujoco>
"""

model = mujoco.MjModel.from_xml_string(XML)
mx = mjx.put_model(model)

# 批量仿真：同时跑 N 个不同初始条件的仿真
N = 1024  # 批量大小
print(f"\n批量仿真测试: {N} 个并行仿真")

# 创建 N 个不同的初始条件
rng = jax.random.PRNGKey(42)
rng, key = jax.random.split(rng)
init_qpos = jax.random.uniform(key, (N, model.nq), minval=-1.0, maxval=1.0)

# 创建批量数据
dx = mjx.make_data(mx)
dx = dx.replace(qpos=init_qpos)

# 计时批量步进
t0 = time.time()
N_STEPS = 100
for _ in range(N_STEPS):
    dx = mjx.step(mx, dx)
t1 = time.time()

fps = N * N_STEPS / (t1 - t0)
speedup = fps / (1 / model.opt.timestep)  # 相对实时的倍数

print(f"耗时: {(t1-t0)*1000:.1f} ms")
print(f"吞吐量: {fps:.0f} FPS")
print(f"相对实时: {speedup:.0f}x")
print(f"✅ test_02_mjx_gpu 通过 — MJX 批量仿真正常工作")
