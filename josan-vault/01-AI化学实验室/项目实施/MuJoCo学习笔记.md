# MuJoCo 学习笔记

> 学习记录：2026-05-28 ~ 2026-05-29
> 场景：AI 化学实验室项目
> 关键发现：mujoco_menagerie、模型导入、viewer 操作

---

## 一、MuJoCo Menagerie — 高质量机器人模型库

### 是什么
Google DeepMind 官方维护的高质量 MuJoCo 模型合集，包含数十种主流机器人。

### 下载方式
```bash
# 克隆整个仓库（约 1.2GB）
git clone https://github.com/google-deepmind/mujoco_menagerie.git

# 也可以只下载你需要的子目录（比如只下载 aloha）
# 手动到 GitHub 把 aloha/ 文件夹下载下来即可
```

### 已下载到项目的模型
- **ALOHA 2** → `data/simulation/mujoco_menagerie/aloha/`
  - 双 ViperX 300 6DOF 机械臂 + 桌面 + 铝型材框架
  - 4 个摄像头（参数匹配 RealSense D405）
  - 16 DOF，BSD-3-Clause 开源协议
- 其他可选参考：Shadow Hand（五指+触觉sensor）、Franka Panda、Leap Hand

### 仓库结构
```
mujoco_menagerie/
├── aloha/           ← 双臂协作场景（已下载）
├── shadow_hand/     ← 五指灵巧手（含 touch sensor）
├── franka_emika_panda/  ← 单臂
├── leap_hand/       ← 低成本灵巧手
├── robotiq_2f85/    ← 二指夹爪
├── realsense_d435i/ ← 深度相机模型
└── ... (60+ 模型)
```

### 场景文件说明（以 ALOHA 为例）
| 文件 | 作用 |
|------|------|
| `scene.xml` | 主场景（桌子+框架+相机+灯光） |
| `aloha.xml` | 双臂机器人本体 |
| `filtered_cartesian_actuators.xml` | 笛卡尔空间滤波控制器 |
| `joint_position_actuators.xml` | 关节位置控制器 |
| `assets/` | 3D 模型文件（STL/OBJ） |
| `mjx_scene.patch` | MJX 场景适配补丁 |

---

## 二、模型格式支持

### ✅ MuJoCo 原生支持

| 格式 | 后缀 | 用法 | 说明 |
|------|------|------|------|
| **Wavefront OBJ** | `.obj` | `<mesh file="model.obj"/>` | **最推荐**，兼容性好，附带 `.mtl` 材质 |
| **Collada DAE** | `.dae` | `<mesh file="model.dae"/>` | 保留颜色/UV/贴图，效果最好 |
| **STL** | `.stl` | `<mesh file="model.stl"/>` | 仅三角网格，无颜色，适合碰撞体 |
| **GLTF/GLB** | `.gltf` / `.glb` | `<mesh file="model.glb"/>` | MuJoCo 3.0+ 新增支持 |

### ❌ MuJoCo 不支持的格式
| 格式 | 原因 | 解决方案 |
|------|------|----------|
| **FBX** | 私有格式，MuJoCo 无解析器 | Blender 打开 → Export → OBJ 或 DAE |
| **BLEND** | Blender 工程文件，不是交换格式 | Blender 打开 → Export → OBJ 或 DAE |
| **3DS/MAX/C4D** | 商业软件专有格式 | 同上，导出为 OBJ |

### 从建模软件到 MuJoCo 的推荐流程

**SolidWorks 最佳路径：**
```
SolidWorks → 另存为 OBJ 或 STL → 放到 assets/ → XML 中引用
```
注意：SolidWorks 导出的 DAE 有时会出问题，OBJ 最稳。

**Blender 最佳路径：**
```
Blender → File → Export → Collada (.dae)  ✅ 带颜色和UV
Blender → File → Export → Wavefront (.obj) ✅ 最兼容
Blender → File → Export → STL              ✅ 轻量碰撞体
```

---

## 三、外部模型导入 MuJoCo（三步法）

### Step 1：把模型文件放到场景目录
```
mujoco_menagerie/aloha/
├── assets/                    ← 放 .obj/.stl/.dae 文件
│   ├── my_beaker.obj
│   ├── my_beaker.mtl          ← OBJ 材质文件（如果有）
│   └── my_testtube_rack.obj
├── scene.xml                  ← 编辑这个文件
└── ...
```

### Step 2：在 XML 中声明并放置模型

```xml
<!-- scene.xml 的 <asset> 部分添加 -->
<asset>
    <!-- ...原有模型... -->
    <mesh file="my_beaker.obj" name="beaker"/>
    <mesh file="my_testtube_rack.obj" name="rack"/>
</asset>

<!-- <worldbody> 部分添加物体 -->
<worldbody>
    <!-- ...原有场景... -->

    <!-- 烧杯放在桌面中央 -->
    <body name="beaker" pos="0.15 -0.1 0.75">
        <!-- 视觉层（group=1，不参与物理） -->
        <geom type="mesh" mesh="beaker" group="1" rgba="0.7 0.85 1 0.4"/>
        <!-- 碰撞层（简化为圆柱，提高仿真速度） -->
        <geom type="cylinder" size="0.025 0.06" rgba="0 0 0 0" condim="3"/>
        <!-- 自由关节（可被抓取/移动） -->
        <freejoint/>
    </body>
</worldbody>
```

### 关键参数说明
- `group="1"` — 仅视觉渲染，不参与物理碰撞
- `group="0"`（默认）— 参与物理碰撞
- `rgba="r g b a"` — 颜色，最后一位是透明度（0=全透，1=不透明）
- `condim="3"` — 摩擦维度（3=有摩擦力），刚性物体用 3
- `contype` / `conaffinity` — 碰撞过滤器（0=不碰撞，1=默认碰撞）
- `<freejoint/>` — 自由关节，物体可被推/抓/捡起
- 碰撞体尽量用圆柱/球/方块近似，不要用高精度 mesh，否则仿真极慢

### 更整洁的做法：独立 labware.xml

把实验室器皿单独放一个 XML，用 `<include>` 引入主场景：

```xml
<!-- labware.xml -->
<mujoco>
  <asset>
    <mesh file="beaker.obj" name="beaker"/>
    <mesh file="testtube_rack.obj" name="rack"/>
    <mesh file="graduated_cylinder.obj" name="cylinder"/>
    <mesh file="flask.obj" name="flask"/>
  </asset>

  <worldbody>
    <body name="beaker_1" pos="0.15 -0.1 0.75"><freejoint/>
      <geom type="mesh" mesh="beaker" group="1"/>
      <geom type="cylinder" size="0.025 0.06" condim="3"/>
    </body>
    <body name="beaker_2" pos="-0.15 -0.1 0.75"><freejoint/>
      <geom type="mesh" mesh="beaker" group="1"/>
      <geom type="cylinder" size="0.025 0.06" condim="3"/>
    </body>
    <body name="testtube_rack" pos="0 0.15 0.75"><freejoint/>
      <geom type="mesh" mesh="rack" group="1"/>
      <geom type="box" size="0.04 0.03 0.02" condim="3"/>
    </body>
  </worldbody>
</mujoco>
```

然后在 `scene.xml` 中加入：
```xml
<mujoco>
  <include file="scene.xml"/>      <!-- ALOHA 场景 -->
  <include file="labware.xml"/>    <!-- 实验室器皿 -->
</mujoco>
```

### 快速定位物体位置的技巧

```python
import mujoco.viewer

m = mujoco.MjModel.from_xml_path("scene.xml")
d = mujoco.MjData(m)

with mujoco.viewer.launch_passive(m, d) as viewer:
    while viewer.is_running():
        mujoco.mj_step(m, d)
        viewer.sync()
        # 在 Terminal 打印物体位置（运行中按 Ctrl+C 中断可输出）
        # print("烧杯位置:", d.body("beaker").xpos)
```

用 viewer 拖拽物体到想要的位置，然后在 terminal 中打印当前位置坐标。

---

## 四、Viewer 界面操作

### 启动 viewer
```python
import mujoco.viewer
m = mujoco.MjModel.from_xml_path("scene.xml")
d = mujoco.MjData(m)

with mujoco.viewer.launch_passive(m, d) as viewer:
    while viewer.is_running():
        mujoco.mj_step(m, d)
        viewer.sync()
```

### 快捷键

| 快捷键 | 功能 |
|--------|------|
| **Ctrl+Right** | 调出/隐藏 **Tree 面板**（场景树） |
| **Ctrl+Left** | 调出/隐藏 **Info 面板**（属性信息） |
| **Ctrl+Space** | 暂停/恢复物理仿真 |
| **F** | 视角聚焦到选中的物体 |
| **ESC** | 退出 viewer |
| 鼠标左键拖拽 | 旋转视角 |
| 鼠标滚轮 | 缩放 |
| 鼠标右键拖拽 | 平移视角 |

### Tree 面板能做什么
- 按 body 层级展开场景中所有物体
- 点击任意 body/geom → 3D 视图中该物体**高亮框选**
- Info 面板同步显示该物体的名称、位置、尺寸、质量等

### 统计信息
在 viewer 菜单或标题栏右键 → **Statistics**，可以看到：
- `nbody` — 场景中 body 总数
- `ngeom` — geom 总数
- `nmesh` — mesh 总数
- `njoint` — 关节总数
- `ndof` — 自由度总数
- `nsensor` — 传感器总数

也可以直接在 Python 中读取：
```python
print(f"Bodies: {m.nbody}")
print(f"Geoms: {m.ngeom}")
print(f"Joints: {m.njqpos}")   # 关节位置维度
print(f"DOFs: {m.nv}")        # 自由度
```

### 显示模式
```python
# 代码中设置
viewer.opt.frame = mujoco.mjtFrame.mjFRAME_GEOM    # 显示物体框线
viewer.opt.frame = mujoco.mjtFrame.mjFRAME_BODY    # 显示 body 坐标轴
viewer.opt.frame = mujoco.mjtFrame.mjFRAME_NONE    # 不显示（默认）
```

---

## 五、场景文件快速搭建 — 用几何体替代 mesh

不需要下载模型，MuJoCo 原生几何体可以快速搭建实验室场景：

```xml
<!-- 烧杯 -->
<body name="beaker" pos="0.2 -0.1 0.75"><freejoint/>
  <geom type="cylinder" size="0.025 0.06" mass="0.05" rgba="0.7 0.85 1 0.4"/>
</body>

<!-- 试管（小圆柱） -->
<body name="testtube" pos="-0.2 -0.1 0.75"><freejoint/>
  <geom type="cylinder" size="0.005 0.05" mass="0.01" rgba="0.8 0.9 1 0.5"/>
</body>

<!-- 底座（方块） -->
<body name="base" pos="0 0 0.75" euler="0 0 0">
  <geom type="box" size="0.1 0.08 0.01" rgba="0.3 0.3 0.3 1"/>
</body>

<!-- 目标标记（球体） -->
<body name="target" pos="0.3 0.2 0.75" euler="0 0 0">
  <geom type="sphere" size="0.015" rgba="0 1 0 0.6"/>
</body>
```

### MuJoCo 支持的 geom 类型
| 类型 | 代码 | 适用场景 |
|------|------|----------|
| `plane` | `<geom type="plane"/>` | 地面、桌面 |
| `box` | `<geom type="box"/>` | 底座、托盘、支架 |
| `sphere` | `<geom type="sphere"/>` | 球体标记、搅拌子 |
| `cylinder` | `<geom type="cylinder"/>` | 烧杯、试管、量筒 |
| `capsule` | `<geom type="capsule"/>` | 机械臂连杆 |
| `mesh` | `<geom type="mesh"/>` | 导入的外部模型 |

---

## 六、模型资源下载

| 资源 | 地址 | 说明 |
|------|------|------|
| MuJoCo Menagerie | [GitHub](https://github.com/google-deepmind/mujoco_menagerie) | 60+ 官方高质量机器人模型 |
| CGTrader 免费实验室包 | [CGTrader](https://www.cgtrader.com/free-3d-models/science/laboratory/3d-laboratory-equipment-pack) | 烧杯/试管/量筒/锥形瓶，含 OBJ/DAE/STL |
| Sketchfab | [sketchfab.com](https://sketchfab.com/) | 搜 "laboratory/beaker/chemistry"，免费模型选 OBJ |
| TurboSquid | [turbosquid.com](https://www.turbosquid.com/) | 免费区搜 "lab equipment" |
| Free3D | [free3d.com](https://free3d.com/) | 276 个化学实验室模型 |

**推荐：** CGTrader 那个免费实验室包直接下载，33 个 DAE 文件 + 17 个 OBJ 文件，格式全对，不用转换。

---

## 七、典型问题排查

### 模型加载后不显示
- 检查 `meshdir` 路径是否正确（相对于 XML 文件的路径）
- 检查文件名大小写（Linux 区分大小写）

### 物体穿过桌子掉下去
- 检查是否加了 `freejoint`（可被推动）
- 检查桌面 `geom` 是否设了 `contype`/`conaffinity`（默认=1，可碰撞）

### 模型加载慢
- 碰撞体用几何体近似（`geom type="cylinder"` vs `type="mesh"`），不要用高精度 mesh

### FBX/BLEND 格式报错
- 这两个格式 MuJoCo 不支持，需导出为 OBJ 或 DAE
