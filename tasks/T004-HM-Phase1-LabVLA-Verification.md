# T004-HM-Phase1-LabVLA-Verification

- Status: PENDING
- Assignee: Home Desktop (HM)
- Priority: HIGH
- Project: labvla

## Description

Run Phase 1 verification on this Home Desktop to confirm the `labvla-cu124` environment works end-to-end with LabVLA inference.

## Context

The `labvla-cu124` conda environment was set up in T003. The `LabVLA-5B-Base/` model weights (8.9GB) are expected at `~/labvla-mujoco/LabVLA-5B-Base/`.

The company desktop (WS) already passed Phase 1:
- 4-bit quantized inference: ✅ action output [50, 8] float32
- WebSocket service: ✅ round-trip confirmed
- Peak GPU memory: ~18.2 GB (CPU offloading heavily used on 8GB VRAM card)

This machine has **RTX 4060 Ti / 16GB VRAM** — better than company desktop's 8GB, but still needs 4-bit quantization.

## Steps

### Step 1: Environment Verification

```bash
conda activate labvla-cu124
python -c "
import torch
print('CUDA available:', torch.cuda.is_available())
print('GPU:', torch.cuda.get_device_name(0))
print('VRAM (MiB):', torch.cuda.get_device_properties(0).total_memory / 1024 / 1024)
print('Torch:', torch.__version__)
print('CUDA version:', torch.version.cuda)
"
```

Also verify key dependencies:
```bash
python -c "
import transformers, accelerate, bitsandbytes, flash_attn, websockets, msgpack
print('All key deps OK')
"
```

### Step 2: Run Local 4-bit Inference

Run the quantized inference script:

```bash
cd ~/labvla-mujoco
conda activate labvla-cu124
PYTHONPATH="/home/josan/labvla-mujoco/LabVLA" python scripts/infer_quantized.py --pretrained_path /home/josan/labvla-mujoco/LabVLA-5B-Base --vlm_path Qwen/Qwen3-VL-4B-Instruct --device cuda
```

This will:
1. Load the LabVLA-5B-Base model with 4-bit quantization (~3 min)
2. Generate a random test image
3. Run one inference pass
4. Report: load time, inference time, peak GPU memory, action shape/dtype/range

❗ This will use a lot of VRAM — watch for OOM. If it crashes, try adding `--use_cpu_offload`

### Step 3: Run WebSocket Test

Start the inference server in one terminal:

```bash
cd ~/labvla-mujoco
conda activate labvla-cu124
PYTHONPATH="/home/josan/labvla-mujoco/LabVLA" python LabVLA/deployment/serve_labvla.py --pretrained_path /home/josan/labvla-mujoco/LabVLA-5B-Base --vlm_path Qwen/Qwen3-VL-4B-Instruct --device cuda --port 8000
```

In another terminal, run the test client:

```bash
cd ~/labvla-mujoco
conda activate labvla-cu124
python scripts/test_client.py --host 127.0.0.1 --port 8000
```

Record the round-trip time and action output format.

### Step 4: Generate PHASE1-REPORT.md

Create `~/labvla-mujoco/PHASE1-REPORT-HM.md` with the results.

## Deliverables

- Update this task file with the full output of each step
- Create `PHASE1-REPORT-HM.md` with structured results

## Notes

- Environment: `labvla-cu124` (Python 3.10, torch 2.7.1, CUDA 12.4)
- Hardware: RTX 4060 Ti / 16GB VRAM, driver 591.86
- Scripts are at `~/labvla-mujoco/scripts/`
- If `scripts/infer_quantized.py` doesn't exist, check `scripts/` listing
- If `LabVLA/deployment/serve_labvla.py` doesn't exist, check `LabVLA/deployment/` listing
