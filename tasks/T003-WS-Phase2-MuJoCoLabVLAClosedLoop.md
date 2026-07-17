# T003-WS-Phase2-MuJoCoLabVLAClosedLoop

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

### Step 4: End-to-End Validation

**Setup (terminal 1 — LabVLA service):**
```bash
cd ~/projects/labvla-mujoco
source /home/josan/miniforge3/etc/profile.d/conda.sh
conda activate labvla-cu124
PYTHONPATH="/home/josan/projects/labvla-mujoco/LabVLA" \
  python LabVLA/deployment/serve_labvla.py \
  --pretrained_path /home/josan/projects/labvla-mujoco/LabVLA-5B-Base \
  --vlm_path Qwen/Qwen3-VL-4B-Instruct \
  --device cuda --port 8000
```

**Run (terminal 2):**
```bash
cd ~/projects/labvla-mujoco
source /home/josan/miniforge3/etc/profile.d/conda.sh
conda activate labvla-cu124
PYTHONPATH="/home/josan/projects/labvla-mujoco/LabVLA" \
  python scripts/mujoco_client.py --host 127.0.0.1 --port 8000 \
  --prompt "pick up the beaker" --num_steps 5
```

**Requirements:**
- Wait for LabVLA service to fully load (2-3 min, look for "Listening on port 8000")
- Run client in a second terminal
- Let it run ≥5 frames
- Expect ~2s/frame

**Troubleshooting:**
- OOM? → add `torch.cuda.empty_cache()` calls, or reduce render resolution
- WebSocket timeout? → increase timeout
- If `mujoco.viewer` blocks the loop, use `mujoco.MjModel.from_xml_path()` with offscreen rendering
- If `cv2` not available, use `PIL` for image saving

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
