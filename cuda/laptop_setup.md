### 🔧 Fix: Headless NVIDIA Drivers (Lazy Loading)

**Context:**
On Ubuntu/Pop!_OS, NVIDIA drivers often "lazy load"—they only initialize when a monitor is connected or a graphical session requests them. In a **headless** or **compute-only** setup (where the dGPU handles CUDA but not the display), the OS ignores the card at boot, causing PyTorch to report `CUDA not available` or `device not found`.

**The Fix:**
Add this to the root crontab (`sudo crontab -e`) to force the drivers to initialize immediately at boot.

```bash
@reboot /usr/bin/nvidia-modprobe -u -c=0
```

**Breakdown:**
* `@reboot`: Run this command once every system startup.
* `nvidia-modprobe`: Manually loads the NVIDIA kernel modules (bypassing the "lazy" check).
* `-u`: Loads the **Unified Memory (UVM)** module.
    * *Why:* Essential for modern CUDA applications (PyTorch/TensorFlow) to manage memory pointers between CPU and GPU.
* `-c=0`: Manually creates the device node for **Card 0**.
    * *Why:* Ensures the file `/dev/nvidia0` exists instantly so your code can find the hardware without needing a "wake up" event.
