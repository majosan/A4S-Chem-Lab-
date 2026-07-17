# T-Rex: Tactile-Reactive Dexterous Manipulation

- **作者**: Dantong Niu, Zhuoyang Liu, Li Fei-Fei, Jim Fan, Danfei Xu 等（UC Berkeley, NVIDIA, Stanford, Panasonic）
- **链接**: https://arxiv.org/abs/2606.17055
- **项目主页**: https://tactile-rex.github.io/

## 核心贡献

### 1. Mixture-of-Transformer-Experts (MoT) 架构
- Latent Expert：视觉+语言处理，5Hz低频
- Action Expert：粗粒度动作规划，流匹配去噪，5Hz
- Tactile Expert：触觉实时修正，20Hz高频
- 级联去噪：Action Expert前N步→Tactile Expert后M步

### 2. 时空触觉编码器
- 时间通道：VQ-VAE将16帧6D力向量压缩为离散token
- 空间通道：轻量CNN提取指尖形变图特征
- 目的：抗传感器漂移 + 压缩数据量

### 3. 关键发现
- 不加处理的触觉融合：成功率从17%降至6%
- MoT架构+触觉：平均65% vs 基线35%，领先30个百分点
- 消融实验：去掉触觉→降23pp，去掉异步执行→降5pp

### 4. 数据集
- 100小时双臂灵巧手遥操作数据
- 200+日常物品 × 22种运动基元
- 7,700+轨迹，含RGB+机器人状态+动作+触觉力+形变图
