# T002-LP-Sample-LabVLATest

- Status: PENDING
- Assignee: Laptop
- Priority: MEDIUM
- Project: labvla

## Description

Switch to the `labvla-mujoco` project and run the existing inference script as a quick smoke test.

Steps:
1. `cd ~/projects/labvla-mujoco`
2. Activate the virtual environment: `source .venv/bin/activate` (or `conda activate labvla` if using conda)
3. Run: `python scripts/infer_quantized.py` and check if it starts without errors
4. Capture the first 20 lines of output

## Deliverables

- Update this task file with the test results and any errors encountered
- If it works, note the command used and output summary

## Notes

- This is just a connectivity/readiness check, not a full validation
- If it fails, note the error message so we can troubleshoot
