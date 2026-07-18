# T003-HM-SetupLabVLAEnv

- Status: PENDING
- Assignee: Home Desktop (HM)
- Priority: HIGH
- Project: labvla

## Description

Set up the `labvla-cu124` conda environment on this machine (Home Desktop, HM).

## Context

The `labvla-mujoco` repo is already cloned at `~/labvla-mujoco/`.
The `LabVLA-5B-Base/` model weights (8.9GB) has been copied into that directory.
The `environment.yml` is already in the repo but has a few hardcoded version pins that need fixing.

## Steps

### 1. Fix environment.yml

Edit `~/labvla-mujoco/environment.yml` to fix these issues:

- **torchaudio** line: change `torchaudio==2.7.1+cu126` → `torchaudio==2.7.1` (the `+cu126` suffix is a PyTorch repo convention, not available on regular PyPI)
- **setuptools** line: change `setuptools==82.0.1` → `setuptools==80.0.0` (82 is too new, conflicts with lerobot dependency)
- **Remove** `flash-attn==2.8.3` from the pip section (it needs torch to be installed first, but pip installs alphabetically, so the build fails)

### 2. Set faster pip mirror

```bash
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3. Clean previous attempts

```bash
conda env remove -n labvla-cu124 -y
conda clean -a -y
pip cache purge
```

### 4. Create the environment

```bash
cd ~/labvla-mujoco
conda env create -f environment.yml
```

This will take a while (~10-20 min depending on network). Be patient.

### 5. Install flash-attn after env is ready

Once the conda environment is created successfully:

```bash
conda activate labvla-cu124
pip install flash-attn==2.8.3
```

### 6. Verify torch + CUDA

```bash
conda activate labvla-cu124
python -c "import torch; print('CUDA available:', torch.cuda.is_available()); print('CUDA version:', torch.version.cuda); print('Torch version:', torch.__version__)"
```

Expected output:
```
CUDA available: True
CUDA version: 12.4
Torch version: 2.7.1
```

### 7. Verify model weights

```bash
cd ~/labvla-mujoco/LabVLA-5B-Base/
ls -lh | head -5
```

You should see model weight files (safetensors, config.json, etc.).

## Deliverables

- Update this task file by adding the output of each verification step below
- If any step fails, paste the error message here so we can troubleshoot

## Notes

- This machine has RTX 4060 Ti (16GB VRAM), driver 591.86, CUDA 13.1 (backward compatible with CUDA 12.4)
- WSL root partition has 33GB free after cleaning cache - should be enough
- If disk space runs out: `conda clean -a -y` to free up cache space
