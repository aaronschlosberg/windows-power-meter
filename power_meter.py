#!/usr/bin/env python3
"""
Power / Wattage Meter - System Tray Utility
Shows current NVIDIA GPU power draw (W) in the system tray with a dial-like icon.
Tooltip: current W, estimated hourly (current * 1h), cumulative energy (Wh) since start/reset.
Right-click: quit, reset counter, refresh toggle.

Requires: pip install pystray Pillow nvidia-ml-py
NVIDIA driver must be installed (provides NVML).
Note: System-wide power (CPU+board) is not reliably available without extra tools/admin; this tracks GPU power (primary high-draw component). Cumulative Wh is an estimate from integrated samples.
"""

import pystray
from PIL import Image, ImageDraw
import threading
import time

try:
    from pynvml import (
        nvmlInit, nvmlShutdown, nvmlDeviceGetCount,
        nvmlDeviceGetHandleByIndex, nvmlDeviceGetName,
        nvmlDeviceGetPowerUsage, nvmlDeviceGetPowerManagementLimit,
        NVMLError
    )
    NVML_AVAILABLE = True
except ImportError:
    NVML_AVAILABLE = False

# Defaults
REFRESH_INTERVAL = 2.0
THRESHOLDS = (100, 200)  # green <100W, yellow <200W, red otherwise (adjust for your GPU)
GPU_INDEX = 0  # primary GPU

# Energy tracking (estimate)
cumulative_wh = 0.0
last_sample_time = None
last_power_w = 0.0

def create_image(watts):
    image = Image.new('RGB', (64, 64), color=(30, 30, 30))
    draw = ImageDraw.Draw(image)
    
    draw.ellipse((4, 4, 60, 60), outline=(100, 100, 100), width=2)
    
    # Color by absolute watts thresholds
    color = (0, 255, 0) if watts < THRESHOLDS[0] else (255, 165, 0) if watts < THRESHOLDS[1] else (255, 0, 0)
    # Dial as % of 300W max for visual (or use power limit if known; fixed for simplicity)
    max_visual = 300.0
    pct = max(0, min(100, (watts / max_visual) * 100))
    angle = int(360 * pct / 100)
    draw.arc((8, 8, 56, 56), start=-90, end=-90 + angle, fill=color, width=6)
    
    text = f"{int(watts)}W"
    # rough centering
    x = 16 if watts < 10 else 12 if watts < 100 else 8
    draw.text((x, 24), text, fill=(255, 255, 255))
    
    return image

def get_power_info():
    if not NVML_AVAILABLE:
        return None
    try:
        handle = nvmlDeviceGetHandleByIndex(GPU_INDEX)
        name = nvmlDeviceGetName(handle)
        if isinstance(name, bytes):
            name = name.decode('utf-8', errors='ignore').strip()
        else:
            name = str(name).strip()
        
        try:
            power_mw = nvmlDeviceGetPowerUsage(handle)
            power_w = power_mw / 1000.0 if power_mw is not None else 0.0
        except (NVMLError, Exception):
            power_w = 0.0
        
        try:
            limit_mw = nvmlDeviceGetPowerManagementLimit(handle)
            limit_w = limit_mw / 1000.0 if limit_mw else None
        except (NVMLError, Exception):
            limit_w = None
        
        return {
            'power_w': power_w,
            'limit_w': limit_w,
            'name': name
        }
    except (NVMLError, Exception):
        return None

def update_icon(icon):
    global REFRESH_INTERVAL, cumulative_wh, last_sample_time, last_power_w
    while True:
        now = time.time()
        info = get_power_info()
        if info:
            watts = info['power_w']
            icon.icon = create_image(watts)
            
            # Integrate energy (Wh estimate)
            if last_sample_time is not None:
                dt_h = (now - last_sample_time) / 3600.0
                # trapezoid with previous
                avg_w = (last_power_w + watts) / 2.0
                cumulative_wh += avg_w * dt_h
            last_sample_time = now
            last_power_w = watts
            
            hourly_est = watts  # current rate * 1h
            limit_str = f" / {info['limit_w']:.0f}W" if info['limit_w'] else ""
            icon.title = (
                f"GPU Power: {watts:.0f}W{limit_str} | "
                f"Est. hourly: {hourly_est:.0f} Wh | "
                f"Cumul: {cumulative_wh:.2f} Wh (est) | {info['name']}"
            )
        else:
            icon.icon = create_image(0)
            icon.title = "Power: No NVIDIA GPU detected / NVML unavailable"
        time.sleep(REFRESH_INTERVAL)

def on_quit(icon, item):
    try:
        if NVML_AVAILABLE:
            nvmlShutdown()
    except Exception:
        pass
    icon.stop()

def on_reset(icon, item):
    global cumulative_wh, last_sample_time
    cumulative_wh = 0.0
    last_sample_time = None

def on_toggle_refresh(icon, item):
    global REFRESH_INTERVAL
    REFRESH_INTERVAL = 1.0 if REFRESH_INTERVAL > 1.0 else 2.0
    item.text = f"Refresh: {REFRESH_INTERVAL:.1f}s"

def make_menu():
    return pystray.Menu(
        pystray.MenuItem(f"Refresh: {REFRESH_INTERVAL:.1f}s", on_toggle_refresh),
        pystray.MenuItem("Reset counter", on_reset),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", on_quit)
    )

def setup(icon):
    icon.visible = True
    if NVML_AVAILABLE:
        try:
            nvmlInit()
            count = nvmlDeviceGetCount()
            if count == 0:
                icon.title = "Power: No NVIDIA GPUs found"
        except Exception as e:
            icon.title = f"Power: NVML init failed ({e})"
    else:
        icon.title = "Power: nvidia-ml-py not installed"
    icon.menu = make_menu()
    threading.Thread(target=update_icon, args=(icon,), daemon=True).start()

if __name__ == "__main__":
    icon = pystray.Icon("Power Meter", create_image(0), "Power Meter", make_menu())
    icon.run(setup)
