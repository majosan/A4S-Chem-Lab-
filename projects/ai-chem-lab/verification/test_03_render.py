"""
test_03_render.py — MuJoCo 可视化验证（需要 WSLg）
如果 WSLg 正常，会弹出一个窗口显示机械臂模型
"""
import mujoco
import mujoco.viewer
import time
import numpy as np

# 加载一个简单的二指夹爪机械臂场景
XML = """
<mujoco>
  <visual>
    <headlight ambient="0.4 0.4 0.4" diffuse="0.6 0.6 0.6"/>
  </visual>
  
  <asset>
    <material name="robot" rgba="0.2 0.4 0.8 1"/>
    <material name="table" rgba="0.6 0.6 0.6 1"/>
    <material name="target" rgba="0.8 0.2 0.2 0.8"/>
  </asset>

  <worldbody>
    <light pos="0 2 3" dir="0 -1 -1"/>
    <geom name="floor" type="plane" size="2 2 0.05" material="table"/>
    
    <!-- 底座 -->
    <body name="base" pos="0 0 0.05">
      <geom type="cylinder" size="0.15 0.05" material="robot"/>
      
      <!-- 第一段臂 -->
      <body name="arm1" pos="0 0 0.05">
        <joint name="shoulder" type="hinge" axis="0 1 0" range="-90 90"/>
        <geom type="capsule" fromto="0 0 0 0 0 0.3" size="0.03" material="robot"/>
        
        <!-- 第二段臂 -->
        <body name="arm2" pos="0 0 0.3">
          <joint name="elbow" type="hinge" axis="0 1 0" range="-150 0"/>
          <geom type="capsule" fromto="0 0 0 0 0 0.25" size="0.025" material="robot"/>
          
          <!-- 夹爪 -->
          <body name="gripper" pos="0 0 0.25">
            <geom type="box" size="0.02 0.04 0.01" material="robot"/>
          </body>
        </body>
      </body>
    </body>
    
    <!-- 目标物体 -->
    <body name="target" pos="0.3 0 0.3">
      <geom type="box" size="0.03 0.03 0.03" material="target"/>
    </body>
  </worldbody>

  <actuator>
    <position name="shoulder_motor" joint="shoulder" kp="100"/>
    <position name="elbow_motor" joint="elbow" kp="100"/>
  </actuator>
</mujoco>
"""

model = mujoco.MjModel.from_xml_string(XML)
data = mujoco.MjData(model)

print("MuJoCo 可视化验证")
print("场景: 2-DOF 机械臂 + 目标方块")
print("打开可视化窗口...")
print("提示: 窗口会显示机械臂缓慢摆动")
print("按 ESC 或 Ctrl+C 退出\n")

try:
    with mujoco.viewer.launch_passive(model, data) as viewer:
        print("✅ WSLg 可视化窗口已打开！")
        
        # 让机械臂做正弦摆动
        t = 0
        while viewer.is_running():
            step = 100
            t += 1
            
            # 控制关节做正弦运动
            data.ctrl[0] = 0.5 * np.sin(t * 0.02)  # 肩关节
            data.ctrl[1] = -0.8 + 0.3 * np.sin(t * 0.015)  # 肘关节
            
            mujoco.mj_step(model, data)
            viewer.sync()
            
            time.sleep(0.01)
            
            if t > 3000:  # 运行30秒后自动退出
                break
                
except ImportError:
    print("⚠️ MuJoCo viewer 不支持当前环境（无显示设备）")
    print("   WSLg 未正常工作或没有显示器连接")
    print("   改用无头模式验证...")
    
    # 无头模式仍然测试仿真正常
    for i in range(100):
        mujoco.mj_step(model, data)
    print("✅ 无头模式仿真 100 步正常")

except Exception as e:
    print(f"⚠️ 可视化异常: {e}")
    print("   WSLg 可能未正确配置。不影响其他功能。")

print("✅ test_03_render 完成")
