# LabVLA → MuJoCo 环境搭建与测试指南

> 最后更新：2026-07-08 | 项目路径：`~/projects/labvla-mujoco/`
> 硬件：CPU 64GB RAM + NVIDIA RTX 4060 (8GB VRAM) | 环境：venv + Python 3.10

---

## 一、项目结构

```
~/projects/labvla-mujoco/          ← VSCode 项目根目录
├── .venv/                         ← Python 虚拟环境
├── LabVLA/                        ← 官方框架代码（git clone，不动源文件）
├── LabVLA-5B-Base/                ← 模型权重文件（~9.5GB，待下载）
└── scripts/                       ← 自定义脚本
    ├── download_model.sh          ← 模型下载脚本
    ├── infer_quantized.py         ← 4-bit 量化推理测试
    ├── test_client.py             ← WebSocket 测试客户端
    └── serve_labvla_4bit.py       ← 量化版部署服务
```

---

## 二、环境搭建步骤

### 2.1 创建 venv + 安装依赖

```bash
# 进项目目录
cd ~/projects/labvla-mujoco

# 创建 venv
python3.10 -m venv .venv
source .venv/bin/activate

# 确认 pip 是最新版
pip install --upgrade pip

# 1. 安装 PyTorch 2.7.1 + CUDA 12.6
pip install torch==2.7.1 torchvision==0.22.1 \
  --index-url https://download.pytorch.org/whl/cu126

# 2. 安装 FlashAttention（编译较慢，约 3-5 分钟）
pip install flash_attn==2.8.3 --no-build-isolation

# 3. 安装 LabVLA 其他依赖
cd LabVLA
pip install -r requirements.txt
cd ..

# 4. 安装 bitsandbytes（用于 4-bit 量化，关键！不然 8GB 显存不够）
pip install bitsandbytes

# 5. 安装 huggingface-cli（下载模型用）
pip install huggingface-hub

# 6. 验证 GPU 可用
python -c "import torch; print('CUDA:', torch.cuda.is_available(), '| VRAM:', round(torch.cuda.get_device_properties(0).total_memory/1e9, 1), 'GB')"
```

✅ **验证通过标志**：CUDA: True | VRAM: 8.0 GB

### 2.2 常见问题处理

| 问题 | 原因 | 解决 |
|------|------|------|
| `ModuleNotFoundError: No module named 'torch._six'` | PyTorch 2.7 移除了 `_six` | `pip install --upgrade torch` 或忽略（LabVLA 最新版已修复） |
| FlashAttention 编译报错 `g++ not found` | 缺少 C++ 编译器 | `sudo apt install build-essential` |
| `CUDA out of memory` | 8GB 显存放不下 FP16 模型 | 必须用 4-bit 量化，检查 BitsAndBytesConfig 配置 |
| `bitsandbytes` 导入报错 | 版本不匹配 | `pip install bitsandbytes --upgrade` |
| huggingface 下载慢或断掉 | 网络问题 | 加 `--resume-download` 参数续传 |

---

## 三、下载模型

```bash
# 激活环境后执行
source .venv/bin/activate
cd ~/projects/labvla-mujoco

# 创建模型目录
mkdir -p LabVLA-5B-Base

# 下载（约 9.5GB，需要 30 分钟 - 1 小时看网速）
huggingface-cli download zjunlp/LabVLA-5B-Base \
  --local-dir LabVLA-5B-Base \
  --resume-download
```

---

## 四、量化推理测试

### 4.1 推理脚本逻辑（`scripts/infer_quantized.py`）

```
加载模型:
  1. BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=float16, 
     bnb_4bit_use_double_quant=True, bnb_4bit_quant_type="nf4")
  2. transformers.AutoModelForCausalLM.from_pretrained(..., quantization_config=...)
  3. AutoProcessor.from_pretrained(...)

构造输入:
  1. 随机 224x224 图片 → PIL Image
  2. 文本: "pick up the beaker on the table"

推理:
  1. processor 处理图片+文本
  2. model.generate(...)
  3. processor.decode() 输出

显存检查:
  1. torch.cuda.max_memory_allocated()
  2. 预期 ~5-6 GB / 8 GB
```

✅ **成功标志**：推理输出有合理的 token 序列，显存占用 < 7.5 GB

### 4.2 WebSocket 客户端逻辑（`scripts/test_client.py`）

```
1. 连接到 ws://localhost:8000
2. 接收 metadata（msgpack 解码）
3. 循环:
   a. 发送观测字典（msgpack 编码，含 numpy 序列化）:
      - camera_1_rgb: (224,224,3) uint8 随机图像
      - camera_2_rgb: (224,224,3) uint8 随机图像
      - camera_3_rgb: (224,224,3) uint8 随机图像
      - state: (8,) float32 零向量
      - prompt: "pick up the beaker"
   b. 接收 action 回复
   c. 打印 action.shape 和数值范围
```

✅ **成功标志**：收到 action 回复，形状为 (action_dim, chunk_size)

---

## 五、部署服务启动

```bash
# 启动量化版部署服务（4-bit 加载）
source .venv/bin/activate
cd ~/projects/labvla-mujoco
python scripts/serve_labvla_4bit.py \
  --pretrained_path ./LabVLA-5B-Base \
  --vlm_path Qwen/Qwen3-VL-4B-Instruct \
  --port 8000 --device cuda

# 另开终端，启动测试客户端
source .venv/bin/activate
cd ~/projects/labvla-mujoco
python scripts/test_client.py --port 8000
```

⚠️ 首次启动模型加载约 10-30 秒，耐心等待。

---

## 六、后续阶段快速参考

### 阶段 2：MuJoCo 场景 + WebSocket 客户端
- Claude Code 提示词方向：
  1. 建 MuJoCo 场景（Franka + 桌面 + 烧杯 + 试管）
  2. 写 muJoco_client.py（渲染摄像头 + 读关节状态 + WebSocket 通信）

### 阶段 3：原子技能 + 数据生成
- 需要实现：pick / pour / press 三个技能
- 数据导出 LeRobot 格式
- 可用公开数据集（DROID, Open X-Embodiment）做预训练替换

### 阶段 4：微调
- 5B 全参微调需要 A100 80GB
- 可选 LoRA 微调，最低需要 24GB 显存
- 推荐方案：云 GPU 或 AutoDL 按量付费

---

## 七、关键术语对照

| 术语 | 含义 | 备注 |
|------|------|------|
| 5B | 50亿参数 | LabVLA-5B-Base 模型参数总量 |
| 4-bit 量化 | 每个参数用 4-bit 存储 | 5B×0.5B = 2.5GB 模型权重 |
| FlashAttention | 加速长序列注意力计算 | Qwen3-VL 必须依赖 |
| bitsandbytes | HuggingFace 量化工具库 | 关键依赖 |
| msgpack | 二进制序列化协议 | LabVLA WebSocket 数据格式 |
| LeRobot | HuggingFace 机器人数据标准 | 训练数据格式 |
| VLA | Vision-Language-Action | 视觉-语言-动作模型 |
| DiT | Diffusion Transformer | 动作为动作生成的扩散模型 |
| Flow Matching | 连续动作生成方法 | LabVLA 的后训练方法 |
| Knowledge Isolation | 知识隔离 | VLM 和动作专家之间的梯度阻断 |
