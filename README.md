# Windows Power / Wattage Meter

Lightweight system tray utility that shows current NVIDIA GPU power draw (watts).

- Dial icon colored by power level (green <100W, yellow <200W, red otherwise).
- Tooltip: current W (and limit if available), estimated hourly Wh, cumulative Wh since start/reset (estimate from samples).
- Right-click: refresh rate toggle (1s/2s), reset counter, quit.
- Low resource (~1-2s refresh).

## Requirements
- Windows
- NVIDIA GPU + driver (NVML)
- Python 3.10+ (installer handles 3.12 if missing)

## Quick Install
1. Download the zip and extract.
2. Run `install-power.bat` (as normal user).
3. It installs Python if needed, deps, and creates a Startup shortcut (pythonw, no console).

## Manual
```
pip install pystray Pillow nvidia-ml-py
pythonw power_meter.py
```

## Notes
- Tracks GPU power via nvidia-ml-py (primary high-draw component). Full system power (CPU+board) is not reliably available without additional sensors/tools/admin rights.
- Cumulative Wh is an estimate (trapezoidal integration of samples). Label as estimate.
- Matches style of windows-ram-meter / gpu_meter.

See install-power.bat for the full silent Python + Startup flow.
