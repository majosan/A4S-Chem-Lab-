﻿# T003-WS-Phase2-MuJoCoLabVLAClosedLoop

- Status: PENDING
- Assignee: Company Desktop (WSL)
- Priority: HIGH
- Project: labvla

## Description

Execute Phase 2 of the LabVLA project: build a MuJoCo simulation closed loop with Franka Panda + 3 cameras, connect to the LabVLA WebSocket inference service, and validate end-to-end.

## Background

Phase 1 is complete (see `PHASE1-REPORT.md`). LabVLA-5B-Base runs as a 4-bit quantized WebSocket service on ws://localhost:8000, outputting (50×8) float32 delta action chunks.

Phase 2 target: MuJoCo renders 3 camera views → sends via WebSocket to LabVLA → LabVLA returns actions → MuJoCo drives the Franka arm.

## Environment

### Project directory
```
~/projects/labvla-mujoco/
```

### Python/conda
- Conda env: `labvla-cu124` (actual CUDA is cu126, env name is legacy)
- Python: `/home/josan/miniforge3/envs/labvla-cu124/bin/python`
- GPU: RTX 4060 (8GB VRAM)

### Known mujoco_menagerie location (probe first)
```bash
find ~ -name "franka_emika_panda" -type d 2>/dev/null
```
Likely at: `/home/josan/venv/ai-chem-lab/mujoco_menagerie/`

If not found, clone:
```bash
cd ~/projects
git clone --depth 1 https://github.com/google-deepmind/mujoco_menagerie.git
```

### LabVLA service
- Model: `~/projects/labvla-mujoco/LabVLA-5B-Base/` (already downloaded)
- Service script: `LabVLA/deployment/serve_labvla.py`
- Schema: `scripts/labvla_schema.json`
- Port: 8000

### Key data formats (from Phase 1)
- Camera keys: `["camera_1_rgb", "camera_2_rgb", "camera_3_rgb"]`
- State keys: `["state", "observation/state"]`
- Action shape: (50, 8), float32, delta mode
- Protocol: msgpack with ndarray encoding
- Text prompt: `"pick up the beaker"`
- Obs: 3 images (uint8, 224x224x3) + 8-dim state vector

## Task Steps

### Step 1: MuJoCo Scene Setup (Franka Panda)

**Requirements:**
1. Locate the mujoco_menagerie (probe `~/venv/ai-chem-lab/`, `~/projects/`)
2. Copy `franka_emika_panda/` scene as base, or reference it from the menagerie path
3. Create a custom scene XML at `scripts/mujoco_scene.xml` that includes:
   - Franka Panda arm (7-DOF + gripper) on a table
   - 1-2 lab objects on the table (beaker, test tube — simple boxes/cylinders OK)
   - Proper lighting and collision meshes
4. If `mujoco` Python package is not installed, install it:
   ```bash
   /home/josan/miniforge3/envs/labvla-cu124/bin/pip install mujoco
   ```

**Verification:**
- Write a test script `scripts/test_scene.py` that loads the scene and prints:
  - Number of bodies, joints, cameras
  - Camera sensor names
  - Robot DOF count
- Run it and confirm no errors

---

### Step 2: Camera Configuration (3× 224×224 RGB)

**Requirements:**
1. Add 3 camera sensors to the scene XML, outputting 224×224 RGB
2. Position cameras:
   - `camera_1_rgb`: Front-top, looking down at workspace
   - `camera_2_rgb`: Side-left, 45-degree angle
   - `camera_3_rgb`: Side-right, 45-degree angle
3. Each camera should clearly see the Franka arm and the tabletop objects

**Verification:**
- Write `scripts/test_cameras.py`:
  - Load scene
  - Render all 3 cameras
  - Check image shape: (224, 224, 3), dtype: uint8
  - Save sample images as `scripts/camera_1_test.png`, etc.
  - Print image min/max/mean for each camera

---

### Step 3: WebSocket Client Integration

**Requirements:**
1. Write `scripts/mujoco_client.py` — the main closed-loop client
2. The client loop (per frame):
   a. Read Franka current joint angles (7 joints + gripper = 8-dim state)
   b. Render 3 camera images (224×224×3 uint8)
   c. Encode observation as msgpack with ndarray format matching `labvla_schema.json`
   d. Send via WebSocket to ws://localhost:8000
   e. Receive action chunk (50×8 float32)
   f. Decode delta: `new_joint_pos = current_joint_pos + action[0, :7]` (first step of chunk)
   g. Set gripper: `gripper_pos = action[0, 7]` (clamp to valid range)
   h. Apply to MuJoCo and step simulation
   i. Log round-trip time, action stats
3. Save `labvla_schema.json` from `scripts/labvla_schema.json` for reference

**Critical constraints:**
- LabVLA service uses ~7.9GB VRAM. MuJoCo should use CPU rendering (glfw, not EGL/GPU)
- First inference (CUDA warmup) takes ~10-15s, subsequent ~2.2s
- The WebSocket protocol: first message is metadata (read it first), then send observation
- Use msgpack encoding for ndarray (not plain JSON)

**Code structure for `scripts/mujoco_client.py`:**
```python
# Main entry point
# 1. Parse args: --host, --port, --prompt, --num_steps
# 2. Connect WebSocket
# 3. Read metadata frame
# 4. Loop for num_steps:
#    a. Get obs from MuJoCo (state + 3 camera images)
#    b. Build msgpack payload
#    c. Send, receive action
#    d. Apply delta to MuJoCo
#    e. Log timing / action stats
#    f. Check for OOM or errors
```

---

### Step 4: End-to-End Validation (Fully Automated)

All in one terminal — Claude Code handles starting the service and running the client.

**Create `scripts/run_phase2.sh` — the one-shot automation script:**
```bash
#!/bin/bash
# Phase 2 automated runner
# Starts LabVLA service in background, waits for ready, runs MuJoCo client, cleans up

set -e

PROJECT_DIR=~/projects/labvla-mujoco
CONDA_BASE=/home/josan/miniforge3
ENV_NAME=labvla-cu124
LOG_FILE=$PROJECT_DIR/phase2_run.log
SERVICE_LOG=$PROJECT_DIR/phase2_service.log

cd "$PROJECT_DIR"

# Activate conda
source "$CONDA_BASE/etc/profile.d/conda.sh"
conda activate "$ENV_NAME"

echo "[Phase2] Starting LabVLA inference service (background)..." | tee -a "$LOG_FILE"

# Start service in background, redirect output
PYTHONPATH="$PROJECT_DIR/LabVLA" \
  nohup python LabVLA/deployment/serve_labvla.py \
  --pretrained_path "$PROJECT_DIR/LabVLA-5B-Base" \
  --vlm_path Qwen/Qwen3-VL-4B-Instruct \
  --device cuda --port 8000 \
  > "$SERVICE_LOG" 2>&1 &
SERVICE_PID=$!
echo "[Phase2] Service PID: $SERVICE_PID" | tee -a "$LOG_FILE"

# Poll for service readiness (port 8000)
echo "[Phase2] Waiting for service to be ready (this may take 2-3 minutes)..." | tee -a "$LOG_FILE"
MAX_WAIT=300  # 5 minutes max
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health 2>/dev/null | grep -q 200; then
        echo "[Phase2] Service is ready! (after ${WAITED}s)" | tee -a "$LOG_FILE"
        break
    fi
    # Also check for "Listening on port" in log as fallback
    if grep -q "Listening on port" "$SERVICE_LOG" 2>/dev/null; then
        echo "[Phase2] Service log says ready! (after ${WAITED}s)" | tee -a "$LOG_FILE"
        break
    fi
    sleep 5
    WAITED=$((WAITED + 5))
done

if [ $WAITED -ge $MAX_WAIT ]; then
    echo "[Phase2] ERROR: Service did not start within ${MAX_WAIT}s" | tee -a "$LOG_FILE"
    tail -30 "$SERVICE_LOG" >> "$LOG_FILE"
    kill $SERVICE_PID 2>/dev/null
    exit 1
fi

# Give it a few more seconds for WebSocket to bind
sleep 3

# Run the MuJoCo client
echo "[Phase2] Running MuJoCo client ($NUM_STEPS frames)..." | tee -a "$LOG_FILE"
PYTHONPATH="$PROJECT_DIR/LabVLA" \
  python scripts/mujoco_client.py \
  --host 127.0.0.1 --port 8000 \
  --prompt "pick up the beaker" \
  --num_steps 5 \
  2>&1 | tee -a "$LOG_FILE"

CLIENT_EXIT=${PIPESTATUS[0]}

# Cleanup
echo "[Phase2] Cleaning up service (PID $SERVICE_PID)..." | tee -a "$LOG_FILE"
kill $SERVICE_PID 2>/dev/null
wait $SERVICE_PID 2>/dev/null || true

if [ $CLIENT_EXIT -eq 0 ]; then
    echo "[Phase2] ✅ Closed-loop validation complete!" | tee -a "$LOG_FILE"
else
    echo "[Phase2] ❌ Client exited with code $CLIENT_EXIT" | tee -a "$LOG_FILE"
fi
```

**After creating the script**, run it:
```bash
cd ~/projects/labvla-mujoco
chmod +x scripts/run_phase2.sh
bash scripts/run_phase2.sh 2>&1 | tee phase2_console.log
```

**What will happen:**
1. Script starts LabVLA service in background (2-3 min load time)
2. Auto-polls port 8000 until ready
3. Runs MuJoCo client for 5 frames
4. Kills the service when done
5. Everything logged to `phase2_run.log` + `phase2_console.log`

**Troubleshooting (if `run_phase2.sh` fails):**
- OOM? → Edit `mujoco_client.py` to render at lower res (128x128) or reduce to 1 camera
- `curl` not available? → Use Python-based health check instead: `python -c "import socket; s=socket.socket(); s.settimeout(2); s.connect(('127.0.0.1',8000)); s.close()"`
- Service log not showing "Listening"? → Check `phase2_service.log` for errors
- The `PYTHONPATH` in the service command may need to be adjusted for LabVLA imports  
- If `mujoco.viewer` blocks, use offscreen rendering only (no viewer window)

---

### Step 5: Report (PHASE2-REPORT.md)

At project root (`~/projects/labvla-mujoco/`), create `PHASE2-REPORT.md`:

```markdown
# Phase 2 Technical Validation Report

## 1. Scene Configuration
- Franka model source path
- Objects placed on table
- Initial joint positions
- Camera positions (xyz coordinates for each)

## 2. Camera Test Results
- Image shape / dtype / value range per camera
- Any rendering artifacts

## 3. Closed-Loop Test Results
- Total frames run
- Average RTT (ms)
- Action range per dimension (min/max/mean)
- Mechanical arm behavior description (smooth? jittery? reasonable direction?)

## 4. Problems Encountered
- Any OOM, freeze, connection errors
- How they were resolved (or if unresolved)

## 5. Conclusion
✅ MuJoCo closed-loop validated, proceed to Phase 3
or
❌ Blocking issues requiring discussion

## 6. Logs (Appendices)
- Full console output from both terminals
- Debugging notes
```

## After Completion

1. Commit everything to the labvla-mujoco repo:
   ```bash
   cd ~/projects/labvla-mujoco
   git add -A
   git commit -m "Phase 2: MuJoCo closed-loop setup"
   git push origin main
   ```

2. Copy a summary status back here (into this task file, under a `## Execution Summary` section) with:
   - ✅/❌ for each step
   - Link to key findings
   - Any blockers

## Notes

- **Do not modify** `LabVLA/` framework source code
- **Do not modify** `mujoco_menagerie/` model files
- All new code goes in `scripts/`
- If the conda env is missing mujoco/websocket-client, install them with pip (not conda)
- Use `HF_ENDPOINT=https://hf-mirror.com` if huggingface.co is unreachable
