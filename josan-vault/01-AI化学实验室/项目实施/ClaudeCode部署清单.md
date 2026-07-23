# LabVLA 环境跑通 Checklist — 交给 Claude Code 执行

> **任务性质**：验证 LabVLA-5B-Base 能在本地部署并完成一次完整的推理+通信闭环
> **执行环境**：`~/projects/labvla-mujoco/` | Python 3.10 venv | RTX 4060 (8GB VRAM)
> **交付物**：每个步骤输出明确的 ✅/❌ 标志 + 相关关键信息截图/日志
> **验收目标**：传感前锋（我）根据结果判断是否可以进入 Phase 2

---

## ⚡ 对 Claude Code 的提示词模板

以下是 Josan 可以直接喂给 Claude Code 的完整任务描述：

---

## 一、任务概述

我已经在 `~/projects/labvla-mujoco/` 创建了项目目录和 Python 3.10 venv，安装好了所有依赖（PyTorch 2.7.1 + CUDA 12.6、FlashAttention、bitsandbytes、LabVLA requirements）。现在需要你完成以下步骤来验证整个环境能否跑通。

## 二、项目结构（当前状态）

```
~/projects/labvla-mujoco/
├── .venv/                     ← venv 环境（已装好依赖）
├── LabVLA/                    ← 官方框架（已 clone）
├── LabVLA-5B-Base/            ← 空目录（待下载）
└── scripts/                   ← 空目录（待创建）
```

## 三、需要做的事

### 📦 Step 0：前置验证

在开始前，先验证基础环境是否正常。

```bash
cd ~/projects/labvla-mujoco
source .venv/bin/activate
```

运行：

```python
import torch, sys
print(f"Python: {sys.version_info.major}.{sys.version_info.minor}")
print(f"PyTorch: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA version: {torch.version.cuda}")
print(f"VRAM: {round(torch.cuda.get_device_properties(0).total_memory/1e9, 1)} GB")
print(f"GPU name: {torch.cuda.get_device_properties(0).name}")
```

**预期输出**：
- Python 3.10
- CUDA available: True
- VRAM: 8.0 GB
- GPU name: NVIDIA GeForce RTX 4060

### 📥 Step 1：下载模型

创建 `scripts/download_model.sh`：

```bash
#!/bin/bash
set -e
cd ~/projects/labvla-mujoco
source .venv/bin/activate

mkdir -p LabVLA-5B-Base

huggingface-cli download zjunlp/LabVLA-5B-Base \
  --local-dir LabVLA-5B-Base \
  --resume-download

echo "✅ 下载完成"
echo "文件大小："
du -sh LabVLA-5B-Base/
```

**执行后确认**：
- 下载成功，目录大小约 ~9.5GB
- 关键文件存在：`config.json`, `model-00001-of-00015.safetensors` 等分片文件
- 记录下载耗时（供后续参考）

### 🔍 Step 2：量化推理测试（核心验证！）

创建 `scripts/infer_quantized.py`：

> 逻辑参考 LabVLA 官方推理代码 + 4-bit 量化配置，实现以下功能：
> 1. 加载模型（with BitsAndBytes 量化）
> 2. 构造一张随机图片 + 文本指令
> 3. 运行一次推理
> 4. 报告显存占用

```python
#!/usr/bin/env python3
"""LabVLA-5B 4-bit 量化推理测试"""
import torch
import time
import numpy as np
from PIL import Image
from transformers import (
    AutoModelForCausalLM, 
    AutoProcessor,
    BitsAndBytesConfig
)

# ── 量化配置 ──
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
)

device = "cuda" if torch.cuda.is_available() else "cpu"
model_path = "./LabVLA-5B-Base"  # 从本地加载

# ── Step 1: 加载模型 ──
print("[1/4] 加载模型...")
t0 = time.time()
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True,
)
processor = AutoProcessor.from_pretrained(
    model_path,
    trust_remote_code=True,
)
t1 = time.time()
print(f"     加载耗时: {t1-t0:.1f}s")
print(f"     模型参数: {sum(p.numel() for p in model.parameters())/1e6:.0f}M")

# ── Step 2: 构造输入 ──
print("[2/4] 构造输入...")
image = Image.fromarray(np.random.randint(0, 256, (224, 224, 3), dtype=np.uint8))
prompt = "pick up the beaker on the table"

# ── Step 3: 推理 ──
print("[3/4] 运行推理...")
torch.cuda.reset_peak_memory_stats()
t2 = time.time()
inputs = processor(text=prompt, images=image, return_tensors="pt").to(device)
with torch.no_grad():
    output_ids = model.generate(
        **inputs,
        max_new_tokens=256,
        do_sample=False,
    )
t3 = time.time()
output_text = processor.decode(output_ids[0], skip_special_tokens=True)

# ── Step 4: 报告 ──
print("[4/4] 结果报告")
print(f"     推理耗时: {t3-t2:.2f}s")
print(f"     输出 token 数: {output_ids.shape[1]}")
print(f"     输出文本: {output_text[:200]}")
peak_mem = torch.cuda.max_memory_allocated() / 1e9
print(f"     峰值显存: {peak_mem:.2f} GB / 8 GB")
print(f"     显存余量: {8 - peak_mem:.2f} GB")

if peak_mem < 7.5:
    print("✅ 量化推理成功！显存足够，可以部署服务。")
else:
    print("❌ 显存不足！需调整量化参数或模型配置。")
```

**运行**：
```bash
cd ~/projects/labvla-mujoco
source .venv/bin/activate
python scripts/infer_quantized.py
```

**验收标准**：
- ✅ 模型加载成功，无报错
- ✅ 推理输出了合理的 token 序列
- ✅ 峰值显存 < 7.5 GB
- ❌ 如果 OOM，需检查量化配置或减 batch_size

### 🔌 Step 3：WebSocket 服务部署 + 测试客户端

创建 `scripts/serve_labvla_4bit.py`（部署服务）和 `scripts/test_client.py`（测试客户端）。

**服务端 serve_labvla_4bit.py**：

```python
#!/usr/bin/env python3
"""LabVLA 4-bit 量化 WebSocket 推理服务"""
import argparse
import asyncio
import json
import msgpack
import numpy as np
import torch
from PIL import Image
from transformers import (
    AutoModelForCausalLM,
    AutoProcessor,
    BitsAndBytesConfig,
)
import websockets

parser = argparse.ArgumentParser()
parser.add_argument("--pretrained_path", default="./LabVLA-5B-Base")
parser.add_argument("--port", type=int, default=8000)
parser.add_argument("--device", default="cuda")
args = parser.parse_args()

# ── 加载模型 ──
print(f"[加载模型] {args.pretrained_path}")
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
)
model = AutoModelForCausalLM.from_pretrained(
    args.pretrained_path,
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True,
)
processor = AutoProcessor.from_pretrained(
    args.pretrained_path,
    trust_remote_code=True,
)
print(f"  模型加载完成 | 设备: {model.device}")

# ── 消息处理 ──
async def handle_message(websocket):
    print(f"[连接] 客户端已连接")
    # 发送元数据
    meta = {"action_dim": 8, "chunk_size": 16}
    await websocket.send(msgpack.packb(meta))

    async for raw in websocket:
        data = msgpack.unpackb(raw)

        # 解析观测
        image_np = data.get("camera_1_rgb", np.zeros((224,224,3), dtype=np.uint8))
        prompt = data.get("prompt", "pick up the beaker")
        image = Image.fromarray(image_np)

        # 推理
        inputs = processor(text=prompt, images=image, return_tensors="pt").to(model.device)
        with torch.no_grad():
            output_ids = model.generate(**inputs, max_new_tokens=256, do_sample=False)

        # 解析动作（简化版：取 embedding 的前 action_dim x chunk_size 作为动作输出）
        # 实际应按 LabVLA 官方动作头输出格式解析
        action = np.random.randn(8, 16).astype(np.float32)  # 占位
        await websocket.send(msgpack.packb({"action": action.tobytes(), "shape": list(action.shape)}))

        print(f"  [推理] 输出动作 shape={action.shape}")

asyncio.run(websockets.serve(handle_message, "0.0.0.0", args.port))
print(f"[服务] WebSocket 运行在 ws://0.0.0.0:{args.port}")
```

**客户端 test_client.py**：

```python
#!/usr/bin/env python3
"""LabVLA WebSocket 测试客户端"""
import argparse
import asyncio
import msgpack
import numpy as np
import websockets

parser = argparse.ArgumentParser()
parser.add_argument("--port", type=int, default=8000)
args = parser.parse_args()

async def test():
    uri = f"ws://localhost:{args.port}"
    print(f"[客户端] 连接至 {uri}")
    async with websockets.connect(uri) as ws:
        # 接收 metadata
        meta_raw = await ws.recv()
        meta = msgpack.unpackb(meta_raw)
        print(f"  [元数据] {meta}")
        action_dim = meta.get("action_dim", 8)
        chunk_size = meta.get("chunk_size", 16)

        # 发送 5 轮观测
        for i in range(5):
            obs = {
                "camera_1_rgb": np.random.randint(0, 256, (224, 224, 3), dtype=np.uint8),
                "camera_2_rgb": np.random.randint(0, 256, (224, 224, 3), dtype=np.uint8),
                "camera_3_rgb": np.random.randint(0, 256, (224, 224, 3), dtype=np.uint8),
                "state": np.zeros(8, dtype=np.float32),
                "prompt": f"pick up the beaker (step {i+1})",
            }
            await ws.send(msgpack.packb(obs))
            print(f"  [发送] step {i+1}")

            # 接收动作回复
            raw = await ws.recv()
            reply = msgpack.unpackb(raw)
            action = np.frombuffer(reply["action"], dtype=np.float32).reshape(reply["shape"])
            print(f"  [接收] action shape={action.shape}, min={action.min():.4f}, max={action.max():.4f}")

        print("✅ 客户端测试完成！")

asyncio.run(test())
```

**测试步骤**：
```bash
# 终端 1：启动服务
cd ~/projects/labvla-mujoco
source .venv/bin/activate
python scripts/serve_labvla_4bit.py \
  --pretrained_path ./LabVLA-5B-Base \
  --port 8000 --device cuda

# 终端 2：启动客户端（等模型加载完再运行）
cd ~/projects/labvla-mujoco
source .venv/bin/activate
python scripts/test_client.py --port 8000
```

**验收标准**：
- ✅ 服务启动成功，模型加载无报错（约 10-30 秒）
- ✅ 客户端连接成功，收到 metadata
- ✅ 至少成功完成 1 次完整的观测→推理→动作回复的往返
- ✅ 动作回复包含合理的 float32 数组
- ❌ 如果 OOM 或连接失败，排查原因

### 🎯 Step 4：环境完整性报告

运行以下汇总脚本，输出一份完整的验证报告：

```bash
#!/bin/bash
# scripts/verify_all.sh
set -e
cd ~/projects/labvla-mujoco
source .venv/bin/activate

echo "═══════════════════════════════════════"
echo "  LabVLA 环境验收报告"
echo "═══════════════════════════════════════"
echo ""
echo "[系统]"
echo "  Python:   $(python --version 2>&1)"
echo "  PyTorch:  $(python -c 'import torch; print(torch.__version__)')"
echo "  CUDA:     $(python -c 'import torch; print(torch.version.cuda)')"
echo "  GPU:      $(python -c "
import torch
p = torch.cuda.get_device_properties(0)
print(f'{p.name} | VRAM: {round(p.total_memory/1e9,1)}GB')
")"
echo ""
echo "[目录结构]"
ls -la
echo ""
echo "[模型文件]"
ls LabVLA-5B-Base/ | head -20
echo "  总大小: $(du -sh LabVLA-5B-Base/ | cut -f1)"
echo ""
echo "[关键依赖检查]"
python -c "
import importlib
pkgs = ['torch', 'transformers', 'bitsandbytes', 'flash_attn', 'PIL', 'msgpack', 'websockets', 'numpy']
for p in pkgs:
    try:
        importlib.import_module(p)
        print(f'  ✅ {p}')
    except:
        print(f'  ❌ {p} MISSING')
"
echo ""
echo "[显存负载测试]"
python -c "
import torch, gc
x = torch.randn(1, 1024, 1024, device='cuda')
del x
gc.collect()
torch.cuda.empty_cache()
print('  ✅ 显存基本功能正常')
"
echo ""
echo "═══════════════════════════════════════"
```

---

## 四、验收标准汇总

| # | 检查项 | 必须？ | 验收条件 |
|---|--------|--------|---------|
| 0 | 基础环境 | ✅ | CUDA True, Python 3.10 |
| 1 | 模型下载 | ✅ | ~9.5GB, 文件完整 |
| 2 | 量化推理 | ✅ | 峰值显存 < 7.5 GB, 输出正常 |
| 3a | WS 服务启动 | ✅ | 模型加载成功，端口监听正常 |
| 3b | WS 客户端通信 | ✅ | 至少 1 次完整观测→动作往返 |
| 4 | 汇总报告 | ✅ | 输出完整验证报告 |

---

## 五、常见问题处理指引

### 模型加载失败
```
Error: The model weights are not in the correct format
```
→ 检查 `--pretrained_path` 路径是否正确
→ 检查 `LabVLA-5B-Base/` 下是否有 `config.json` 和 shard 文件

### OOM（Out of Memory）
```
CUDA out of memory. Tried to allocate ... GiB
```
→ 确认使用了 4-bit 量化配置
→ 检查 `bnb_4bit_compute_dtype` 设为 `float16` 而非 `float32`
→ 尝试减少 `max_new_tokens`

### WebSocket 连接失败
```
Connection refused
```
→ 确认服务端已启动并正在监听
→ 确认端口号一致
→ 防火墙检查

### msgpack 序列化错误
```
msgpack.exceptions.UnpackException
```
→ 确认服务端/客户端使用相同的序列化方式
→ 检查 numpy 数组的 `.tobytes()` / `np.frombuffer()` 方向正确

---

## 六、产出物要求

Claude Code 在完成上述步骤后，应输出一个摘要文件 `CLAUDE-CODE-REPORT.md`，包含：

```markdown
# LabVLA 环境验证报告

**执行日期**：2026-07-XX
**执行者**：Claude Code

## 验证结果汇总

| Step | 状态 | 备注 |
|------|------|------|
| 0 基础环境 | ✅ | ... |
| 1 模型下载 | ✅ | ... |
| 2 量化推理 | ✅ | ... |
| 3 WebSocket | ✅ | ... |

## 关键数据

- 模型加载时间：XX 秒
- 推理耗时：XX 秒
- 峰值显存：X.X GB
- WS 往返次数：X

## 异常记录

（如有任何错误或异常，在此记录）

## 结论

✅/❌ 环境就绪，可以进入 Phase 2
```

---

## 七、验收后交接

1. Claude Code 将 `CLAUDE-CODE-REPORT.md` 放至 `~/projects/labvla-mujoco/`
2. Josan 将报告内容分享给我（传感前锋）
3. 我根据报告判断是否可以进入 Phase 2（MuJoCo 场景搭建）
