import signal
import mss
import numpy as np
import datetime
import os
from PIL import Image
import time
import imageio

# ---------------- Configuration ----------------
FPS = 10                     # frames per second
SEGMENT_DURATION = 60        # seconds per segment
RESOLUTION = (1280, 720)     # downscale to HD
OUTPUT_DIR = "recordings"    # folder to save recordings
# -----------------------------------------------

running = True
writer = None
segment_start_time = None

os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_filename():
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(OUTPUT_DIR, f"screen_{ts}.mp4")

def cleanup():
    global writer
    if writer is not None:
        writer.close()
        print("Segment saved safely.")

def handle_signal(sig, frame):
    global running
    print(f"\nSignal {sig} received. Stopping...")
    running = False

# Handle Ctrl+C and console close
signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)

def main():
    global running, writer, segment_start_time
    with mss.mss() as sct:
        monitor = sct.monitors[1]

        frame_interval = 1.0 / FPS
        next_frame_time = time.time()

        try:
            while running:
                # Capture screen
                img = sct.grab(monitor)
                frame = np.array(img)
                # Convert BGRA → RGB for imageio
                frame = frame[:, :, :3][:, :, ::-1]
                # Resize to target resolution
                frame = np.array(imageio.core.util.Array(frame))
                frame_pil = Image.fromarray(frame)
                frame_pil = frame_pil.resize(RESOLUTION, Image.BILINEAR)
                frame = np.array(frame_pil)

                # Start new segment if needed
                if writer is None:
                    filename = get_filename()
                    writer = imageio.get_writer(
                        filename,
                        fps=FPS,
                        codec='libx264',        # H.264
                        macro_block_size=None,  # avoid multiple-of-16 restriction
                        ffmpeg_params=['-pix_fmt', 'yuv420p']
                    )
                    segment_start_time = time.time()
                    print(f"Segment started: {filename}")

                writer.append_data(frame)

                # Rotate segment
                if SEGMENT_DURATION and (time.time() - segment_start_time) >= SEGMENT_DURATION:
                    writer.close()
                    print(f"Segment saved: {filename}")
                    writer = None
                    segment_start_time = None

                # Maintain FPS
                next_frame_time += frame_interval
                sleep_time = next_frame_time - time.time()
                if sleep_time > 0:
                    time.sleep(sleep_time)
                else:
                    next_frame_time = time.time()

        finally:
            cleanup()
            print("Recorder stopped.")

if __name__ == "__main__":
    main()
