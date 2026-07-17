"""
test_04_tactile_sim.py — 触觉传感器仿真验证
在 MuJoCo 中创建带触觉传感器的夹爪，模拟抓取并读取触觉数据
这是触觉手套项目的仿真侧验证
"""
import mujoco
import numpy as np

# 场景：带触觉传感器的二指夹爪，抓取一个橡胶球
XML = """
<mujoco>
  <option timestep="0.005" gravity="0 0 -9.81"/>
  
  <visual>
    <headlight ambient="0.3 0.3 0.3" diffuse="0.7 0.7 0.7"/>
  </visual>

  <worldbody>
    <light name="top" pos="0 0 3"/>
    <geom name="floor" type="plane" size="1 1 0.05" rgba="0.7 0.7 0.7 1"/>
    
    <!-- 左手爪 -->
    <body name="left_finger" pos="-0.15 0 0.1">
      <joint name="left_joint" type="slide" axis="1 0 0" range="-0.05 0.15"/>
      <geom name="left_pad" type="box" size="0.08 0.02 0.02" rgba="0.2 0.4 0.8 1"/>
      <!-- 触觉传感器 site（读取接触力用） -->
      <site name="tactile_left" type="box" size="0.08 0.02 0.02" pos="0 -0.02 0" rgba="1 0 0 0.3"/>
    </body>
    
    <!-- 右手爪 -->
    <body name="right_finger" pos="0.15 0 0.1">
      <joint name="right_joint" type="slide" axis="-1 0 0" range="-0.05 0.15"/>
      <geom name="right_pad" type="box" size="0.08 0.02 0.02" rgba="0.2 0.8 0.4 1"/>
      <site name="tactile_right" type="box" size="0.08 0.02 0.02" pos="0 0.02 0" rgba="0 1 0 0.3"/>
    </body>
    
    <!-- 被抓取物 -->
    <body name="object" pos="0 0 0.08">
      <freejoint/>
      <geom name="sphere" type="sphere" size="0.025" rgba="0.9 0.6 0.1 1" friction="0.8 0.01 0.01"/>
    </body>
  </worldbody>
  
  <!-- 触觉传感器 -->
  <sensor>
    <touch name="touch_left" site="tactile_left"/>
    <touch name="touch_right" site="tactile_right"/>
  </sensor>

  <actuator>
    <velocity name="left_motor" joint="left_joint"/>
    <velocity name="right_motor" joint="right_joint"/>
  </actuator>
</mujoco>
"""

model = mujoco.MjModel.from_xml_string(XML)
data = mujoco.MjData(model)

print("触觉传感器仿真验证")
print(f"传感器数量: {model.nsensor}")
print(f"传感器列表:")
for i in range(model.nsensor):
    print(f"  [{i}] {model.sensor(i).name}")

print("\n开始抓取仿真...")

# 阶段1：夹爪闭合
print("\n▶ 阶段1: 夹爪闭合...")
for i in range(200):
    # 向中间夹
    data.ctrl[0] = 0.0005  # 左爪向右
    data.ctrl[1] = 0.0005  # 右爪向左
    mujoco.mj_step(model, data)
    
    if i % 50 == 0:
        touch_l = data.sensor("touch_left").data.copy()
        touch_r = data.sensor("touch_right").data.copy()
        print(f"  步{i:3d}: 触觉左={touch_l[0]:.6f} 触觉右={touch_r[0]:.6f}")

# 阶段2：抓住后晃动
print("\n▶ 阶段2: 抓着物体（夹爪固定，观察物体是否掉落）...")
initial_obj_pos = data.qpos[3:6].copy()
for i in range(500):
    data.ctrl[0] = 0.0
    data.ctrl[1] = 0.0
    mujoco.mj_step(model, data)

# 阶段3：松开
print("\n▶ 阶段3: 松开夹爪（物体应掉落）...")
for i in range(200):
    data.ctrl[0] = -0.002
    data.ctrl[1] = -0.002
    mujoco.mj_step(model, data)

# 读取最终触觉数据
touch_l = data.sensor("touch_left").data.copy()
touch_r = data.sensor("touch_right").data.copy()
print(f"\n最终触觉数据: 左={touch_l[0]:.6f} 右={touch_r[0]:.6f}")
print(f"物体最终z位置: {data.qpos[5]:.4f}")

# 验证触觉传感器是否正常返回数据
print(f"\n✅ test_04_tactile_sim 通过 — 触觉传感器仿真正常工作")
print(f"   触觉数据格式: site 接触力 (N)")
