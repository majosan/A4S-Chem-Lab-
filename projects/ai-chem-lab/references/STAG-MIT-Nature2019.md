# 论文分析：STAG Scalable Tactile Glove (MIT, Nature 2019)

## 基本信息
- **标题：** Learning the signatures of the human grasp using a scalable tactile glove
- **发表：** Nature 569, 698–702 (2019)
- **作者：** Subramanian Sundaram, Petr Kellnhofer, Yunzhu Li, Jun-Yan Zhu, Antonio Torralba, Wojciech Matusik
- **单位：** MIT CSAIL
- **项目主页：** stag.csail.mit.edu / humangrasp.io
- **代码：** github.com/geigerf/STAG_slim (PyTorch)
- **数据集：** 135,000帧，26种物体，非商用许可

## 技术要点
- 548个压阻传感器，针织手套，~$10成本
- 数据排列为32×32网格 → CNN分类/回归
- 两任务：物体识别(分类) + 重量估计(回归)

## 与"传感前锋"项目的关联
- ✅ 同样使用织物手套+CNN处理触觉压力数据
- ✅ 空间网格映射方法一致（32×32 vs 8×16）
- ✅ 验证了低成本织物传感+AI的技术路线
- 🔄 他们的数据集可用于预训练我们的触觉编码器
- ⬆️ 我们的项目是他们的延伸：从感知→执行、从单模态→多模态

## 可借用的资源
1. 公开触觉数据集 → 预训练VQ-VAE编码器
2. 网格映射方法论
3. 传感器数量-精度曲线结论
