# Pro Fake Cam

A small GUI tool (Tkinter + OpenCV) for broadcasting an image or video as a virtual camera feed using pyvirtualcam. The main application file is `main.py`.

## Features
- Upload an image or video file
- Position, scale, rotate, mirror the source
- Stream to a virtual camera using `pyvirtualcam`

## Requirements
- Python 3.8+ (recommended)
- Windows (tested)

Fake Cam works with the following virtual camera backends:
- **OBS Studio (includes Virtual Camera)**
  - Download: https://obsproject.com/download

- **UnityCapture**
  - Download: https://github.com/schellingb/UnityCapture/releases
  
Dependencies are listed in `requirements.txt`.

## Quick start
1. Create and activate a virtual environment (recommended):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

3. Run the app:

```powershell
python main.py
```

Notes:
- On Windows you might need to install a virtual camera driver or enable a virtual camera provider (OBS Virtual Camera can be used as the receiving device).
- `tkinter` is included with the standard Python installer on Windows.

## Next steps
- Connect this local repo to a remote (GitHub/GitLab) if you'd like to push and share the project.
- Add tests, packaging or a GUI installer if you plan to distribute the app.

---

If you'd like I can also create a GitHub remote, add CI or update README to include screenshots and usage examples — tell me what you'd prefer.
