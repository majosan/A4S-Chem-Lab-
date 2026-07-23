# RoboGenesis — 知识增强的仿真数据引擎

- **维护方**: 浙江大学（LabVLA同一团队，Ylr9933）
- **仓库**: https://github.com/Ylr9933/RoboGenesis
- **文档**: https://lxj-kai.github.io/robogenesis/v0.5/zh/

## 本质
❌ **不是模型**，是数据引擎/数据工厂。基于MuJoCo的仿真数据自动生成工具。

## 核心能力
- 自然语言→YAML工作流配置→原子技能状态机执行→结构化HDF5训练数据
- 自动随机化：位置/光照/颜色/技能参数
- 输出：LabEmbodied-Data格式，直接兼容LabVLA训练管线

## 11种原子技能
| 技能 | 阶段数 | 用途 | 状态机 |
|------|--------|------|--------|
| pick | 7 | 抓取物体 | 移动→修正→下降→稳定→闭合→抬升→完成 |
| place | 6 | 放置物体 | 接近→下探→稳定→释放→后撤→完成 |
| pour | 6 | 容器间倒液 | 移动→精调→倾倒→保持→回正→结束 |
| stir | 5 | 容器内搅拌 | 抬高→水平移动→下降→圆周搅拌→抬起 |
| shake | 10 | 容器摇晃 | 中心→Y轴往返4次→返回→完成 |
| press | 3 | 水平按压 | 移动→闭合夹爪→向前按压 |
| pressZ | 3-4 | 竖直按压 | 接近→闭合→下压→(可选回撤) |
| open | 8 | 开门/开盖 | 接近→微调→抓住→弧线拉→稳定→释放→后撤 |
| close | 3 | 关门/关盖 | 接近→弧线推→后撤 |
| move | 无固定 | 末端移动 | 单目标/多航点/两段式 |
| navigate | 无固定 | 底盘导航 | A*路径规划 |

## 关键技术细节
- **状态机推进**: events_dt[i]控制每帧推进速度，累积到1.0进入下一阶段
- **参数合并优先级**: YAML params > 机器人覆盖 > 全局默认值
- **夹爪适配层**: GripperAdapter兼容prismatic和revolute两类夹爪
- **腕关节控制**: pour的Phase2切换速度模式，不依赖位置控制
- **Virtual Attach**: 不适用物理夹持时启用虚拟附着

## 工作流配置示例
```yaml
name: workflow_pick_pour
task_type: "workflow"
controller_type: "workflow"
mode: "collect"
workflow:
  language_instruction: "Pick the source beaker and pour into the target beaker"
  scene_objects:
    - name: "source_beaker"
      path: "/World/beaker_2"
      position_range:
        x: [0.20, 0.28]
        y: [0.05, 0.12]
        z: [0.06, 0.065]
  steps:
    - skill: "pick"
      target_object: "source_beaker"
    - skill: "pour"
      target_object: "target_beaker"
```
