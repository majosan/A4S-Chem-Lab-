# LabVLA: Grounding Vision-Language-Action Models in Scientific Laboratories

- **作者**: Baochang Ren, Xinjie Liu, Ningyu Zhang, Huajun Chen 等（浙江大学 + 上海AI Lab）
- **链接**: https://arxiv.org/abs/2606.13578
- **项目主页**: https://zjunlp.github.io/LabVLA/
- **代码**: https://github.com/zjunlp/LabVLA
- **模型权重**: https://huggingface.co/zjunlp/LabVLA

## 核心贡献

### 1. LabVLA 模型
- 视觉语言骨干：Qwen3-VL-4B-Instruct
- 动作专家：DiT（Diffusion Transformer）+ Flow Matching
- 知识隔离（Knowledge Isolation）：VLM与动作专家间stop-gradient
- 两阶段训练：FAST action token预训练 → Flow Matching后训练
- 三阶段微调：预训练→后训练→任务微调

### 2. RoboGenesis（非模型，数据引擎）
- 知识增强的仿真数据引擎
- 11种原子技能（状态机控制器）
- 工作流编排引擎（YAML配置）
- 自动随机化（位置/光照/颜色/参数）
- 输出LabEmbodied-Data结构化数据

### 3. LabUtopia 基准
- 六类实验室任务
- ID: 71.1% OOD: 70.0%（泛化差距仅1.1%）
- Franka真机验证通过

### 4. 11种原子技能
pick(7阶段)/place(6)/pour(6)/stir(5)/shake(10)/press(3)/pressZ(3-4)/open(8)/close(3)/move/navigate
