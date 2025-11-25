# Screen Recorder

[← Back to Main README](../README.md)  

This is a lightweight Python screen recorder that captures your display using `mss` and saves recordings in segmented MP4 files using `imageio` + ffmpeg (H.264). It supports automatic file rotation, FPS control, safe shutdown on Ctrl+C, and resolution downscaling.

---

## ✨ Features

- Full-screen recording using **mss**
- Saves videos as **MP4 (H.264)**  
- Automatic **segment rotation** (creates a new file every X seconds)
- Adjustable **FPS**, **resolution**, and **segment duration**
- Handles **Ctrl+C** gracefully (no corrupted video files)
- Cross-platform: Windows, macOS, Linux

---

## 📦 Requirements

Install dependencies manually:

```bash
pip install mss numpy Pillow imageio
