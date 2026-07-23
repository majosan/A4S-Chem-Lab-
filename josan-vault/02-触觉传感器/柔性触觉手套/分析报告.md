# Tactile Glove Sensor Data Analysis

Analysis scripts for the tactile-glove validation test suite.
Processes exported JSON sensor data and produces a self-contained HTML report.

---

## Directory layout

```
analysis/
├── analyze.py                  # Main entry point — run this
├── load_data.py                # JSON loading & format detection
├── visualize.py                # Heatmaps, curves, bar charts
├── report.py                   # HTML report generation
├── module1_baseline.py         # Test 1.1 — Empty-hand baseline stability
├── module2_response_curve.py   # Test 1.2 — Single-point pressure response
├── module3_repeatability.py    # Test 1.3 — Repeated-placement consistency
├── module4_cross_point.py      # Test 2.1 — Cross-point variation (record only)
├── module5_grasp.py            # Tests 3.1/3.2/3.3 — Grasp action analysis
├── module6_flex_interference.py# Test 3.5 — Flex interference (false positives)
├── requirements.txt
└── output/                     # Auto-created; charts + report written here
```

---

## Setup

```bash
# Create and activate a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r analysis/requirements.txt
```

---

## Quick start

```bash
python analysis/analyze.py <data_dir> --sample A
```

| Argument | Default | Description |
|---|---|---|
| `data_dir` | *(required)* | Folder with all exported test JSON files |
| `--sample` | `A` | Glove sample identifier (`A` or `B`) |
| `--output` | `output/` | Destination for charts and the HTML report |

The script auto-discovers which test files are present.
Missing data causes the corresponding module to be skipped (`N/A`) — no errors.

---

## Data file naming convention

Follow the convention from `test-protocol-v1.md §0.2`:

```
[sample]_[test_type]_[parameters].json

Examples:
  A_baseline_emptyhand.json
  A_singlepoint_P3_50g_r1.json
  A_grasp_bottle_r1.json
  A_flex_bendtest.json
```

---

## JSON formats supported

**Format A — single frame**
```json
{
  "points": {"P1": 0, "P2": 15, "P3": 42, ...},
  "timestamp": 1720000000000
}
```

**Format B — multi-frame (time series)**
```json
{
  "frames": [
    {"timestamp": 1720000000000, "points": {"P1": 0, "P2": 15, ...}},
    {"timestamp": 1720000100000, "points": {"P1": 2, "P2": 18, ...}}
  ]
}
```

The loader auto-detects and normalises both.  124 sensor points expected
(keys `P1`–`P124`; exact naming confirmed from real data on first run).

---

## Analysis modules

| Module | Test | Judgement |
|---|---|---|
| `module1_baseline` | 1.1 — Baseline stability | 🟢 ≥110 stable pts · ⚠️ 90–109 · ❌ <90 |
| `module2_response_curve` | 1.2 — Pressure response | 🟢 8/8 monotone, CV≤15%, range≥150 |
| `module3_repeatability` | 1.3 — Repeated placement | 🟢 CV≤10% · ⚠️ 10–15% · ❌ >15% |
| `module4_cross_point` | 2.1 — Cross-point variation | Record only — no pass/fail |
| `module5_grasp` | 3.1/3.2/3.3 — Grasp | 🟢 discrimination≥15 |
| `module6_flex_interference` | 3.5 — Flex interference | 🟢 ≤10 false-pos pts · ⚠️ 10–25 · ❌ >25 |

All thresholds are defined as module-level constants; edit them there if
you need to adjust them before real data arrives.

---

## Output

The script writes to `output/` (or the directory you pass with `--output`):

```
output/
├── report.html           # Self-contained report (open in any browser)
├── baseline_heatmap.png
├── response_curves.png
├── repeatability_P2.png
├── repeatability_P7.png
├── grasp_bottle_heatmap.png
├── grasp_beaker_heatmap.png
├── grasp_tube_heatmap.png
└── flex_fp_heatmap.png
```

---

## Implementation status

All module files currently contain **function signatures and docstrings only**.
The analysis logic (`raise NotImplementedError`) will be filled in once the
first real JSON export is available and the point-to-anatomy mapping is
confirmed.

Steps to fill in the logic:
1. Export a real JSON file and inspect point key names.
2. Update `visualize.get_hand_layout()` with the actual P-label grid.
3. Implement `load_data.py` parsers.
4. Implement each module's core functions in dependency order:
   `load_data` → `visualize` → `module1` … `module6` → `report` → `analyze`.
