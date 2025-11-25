import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import cv2
import pyvirtualcam
from pyvirtualcam import PixelFormat
import os
import ctypes
import numpy as np
import math
from PIL import Image, ImageTk 

# Make the app DPI aware on Windows
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

class FakeCamApp:
    # Set fixed 16:9 Landscape dimensions for the virtual camera output
    FIXED_WIDTH = 1280
    FIXED_HEIGHT = 720

    def __init__(self, root):
        self.root = root
        self.root.title("Fake Cam")
        self.root.configure(bg="#2c2c2c")
        
        # Use fixed dimensions
        self.width = self.FIXED_WIDTH
        self.height = self.FIXED_HEIGHT
        
        self.file_path = None
        self.source_image = None
        self.cap = None
        
        # State: [center_x, center_y, width, height] - Initialized to full frame
        self.box_cx = self.width / 2
        self.box_cy = self.height / 2
        self.box_w = 0 # Will be set on upload to fit the new frame
        self.box_h = 0
        
        self.rotation = 0.0 
        self.mirror = False
        
        # Configuration
        self.SNAP_EDGE_DIST = 25   
        self.ROTATION_ZONE_DIST = 120 
        
        # Interaction State
        self.active_handle = None 
        self.drag_start_pos = (0,0)
        self.start_state = {} 
        
        self.is_broadcasting = False
        self.cam = None

        self.create_ui()
        self.update_loop()

    def create_ui(self):
        style = ttk.Style()
        style.theme_use('clam') 
        style.configure('TFrame', background='#3a3a3a')
        style.configure('TButton', background='#5a5a5a', foreground='white', borderwidth=0, relief='flat', font=('Arial', 10, 'bold'))
        style.map('TButton', background=[('active', '#6a6a6a')])
        style.configure('Broadcast.TButton', background='#cc3333', foreground='white', font=('Arial', 10, 'bold'))
        style.map('Broadcast.TButton', background=[('active', '#e64d4d')])
        
        toolbar = ttk.Frame(self.root, style='TFrame')
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=0, pady=0)
        
        ttk.Button(toolbar, text="📂 Upload Media", command=self.upload_file).pack(side=tk.LEFT, padx=10, pady=8)
        
        self.mirror_btn = ttk.Button(toolbar, text="↔ Mirror: OFF", command=self.toggle_mirror)
        self.mirror_btn.pack(side=tk.LEFT, padx=5, pady=8)
        
        self.broadcast_btn = ttk.Button(toolbar, text="📡 Start Broadcast", command=self.toggle_broadcast, 
                                       style='Broadcast.TButton')
        self.broadcast_btn.pack(side=tk.RIGHT, padx=10, pady=8)

        self.canvas_frame = tk.Frame(self.root, bg="#1a1a1a")
        self.canvas_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        # Canvas dimensions set to fixed 16:9 resolution
        self.canvas = tk.Canvas(self.canvas_frame, width=self.width, height=self.height, 
                                bg="#1a1a1a", highlightthickness=0)
        self.canvas.pack(anchor=tk.CENTER, padx=5, pady=5)

        self.vid_container = self.canvas.create_image(0, 0, anchor=tk.NW)

        self.ui_items = {}
        self.ui_items['outline'] = self.canvas.create_polygon(0,0,0,0, outline="#00e5ff", fill="", width=2, dash=(4, 4))
        self.ui_items['rot_line'] = self.canvas.create_line(0,0,0,0, fill="#cccccc", width=2)
        
        for h in ['nw', 'n', 'ne', 'e', 'se', 's', 'sw', 'w', 'rot']:
            color = "#ffcc00" if h == 'rot' else ("#00e5ff" if len(h) == 2 else "#ffffff")
            if h == 'rot':
                shp = self.canvas.create_oval(0,0,0,0, fill=color, outline="#2c2c2c")
            else:
                shp = self.canvas.create_rectangle(0,0,0,0, fill=color, outline="#2c2c2c")
            self.ui_items[h] = shp

        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.canvas.bind("<Motion>", self.update_cursor)

    # --- MATH HELPERS (Unchanged) ---

    def rotate_point(self, x, y, cx, cy, angle_deg):
        rad = math.radians(angle_deg)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)
        dx, dy = x - cx, y - cy
        return (cx + dx * cos_a - dy * sin_a, cy + dx * sin_a + dy * cos_a)

    def get_corners(self, cx, cy, w, h, angle):
        hw, hh = w/2, h/2
        pts = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
        rotated_pts = []
        for px, py in pts:
            rx, ry = self.rotate_point(cx + px, cy + py, cx, cy, angle)
            rotated_pts.append((rx, ry))
        return rotated_pts

    def get_handle_pos(self, h_name, cx, cy, w, h, angle):
        hw, hh = w/2, h/2
        offsets = {
            'nw': (-hw, -hh), 'n': (0, -hh), 'ne': (hw, -hh),
            'e': (hw, 0), 'se': (hw, hh), 's': (0, hh),
            'sw': (-hw, hh), 'w': (-hw, 0),
            'rot': (0, -hh - 30) 
        }
        ox, oy = offsets[h_name]
        return self.rotate_point(cx + ox, cy + oy, cx, cy, angle)

    # --- INPUT LOGIC (Unchanged) ---

    def hit_test(self, mx, my):
        HANDLE_TOLERANCE = 15 
        
        rot_x, rot_y = self.get_handle_pos('rot', self.box_cx, self.box_cy, self.box_w, self.box_h, self.rotation)
        if math.hypot(mx - rot_x, my - rot_y) < HANDLE_TOLERANCE: return 'rot'

        rmx, rmy = self.rotate_point(mx, my, self.box_cx, self.box_cy, -self.rotation)
        hw, hh = self.box_w/2, self.box_h/2
        
        handles = {
            'nw': (-hw, -hh), 'n': (0, -hh), 'ne': (hw, -hh),
            'e': (hw, 0), 'se': (hw, hh), 's': (0, hh),
            'sw': (-hw, hh), 'w': (-hw, 0)
        }
        
        for name, (ox, oy) in handles.items():
            tx, ty = self.box_cx + ox, self.box_cy + oy
            if abs(rmx - tx) < HANDLE_TOLERANCE and abs(rmy - ty) < HANDLE_TOLERANCE:
                return name
                
        if (self.box_cx - hw) < rmx < (self.box_cx + hw) and \
           (self.box_cy - hh) < rmy < (self.box_cy + hh):
            return 'move'
            
        return None

    def on_mouse_down(self, event):
        self.active_handle = self.hit_test(event.x, event.y)
        self.drag_start_pos = (event.x, event.y)
        self.start_state = {
            "cx": self.box_cx, "cy": self.box_cy,
            "w": self.box_w, "h": self.box_h,
            "rot": self.rotation
        }

    def on_mouse_drag(self, event):
        if not self.active_handle: return

        st = self.start_state
        mx, my = event.x, event.y
        
        # --- ROTATION LOGIC (Unchanged) ---
        if self.active_handle == 'rot':
            dx = mx - st["cx"]
            dy = my - st["cy"]
            raw_angle = math.degrees(math.atan2(dy, dx)) + 90
            dist = math.hypot(dx, dy)
            
            if dist < self.ROTATION_ZONE_DIST:
                nearest_90 = round(raw_angle / 90) * 90
                if abs(raw_angle - nearest_90) < 15: angle = nearest_90
                else: angle = raw_angle 
            else:
                angle = round(raw_angle / 5.0) * 5.0
            self.rotation = angle % 360
            return

        # --- MOVEMENT LOGIC (Unchanged) ---
        if self.active_handle == 'move':
            dx = mx - self.drag_start_pos[0]
            dy = my - self.drag_start_pos[1]
            
            prop_cx = st["cx"] + dx
            prop_cy = st["cy"] + dy
            
            corners = self.get_corners(prop_cx, prop_cy, st["w"], st["h"], st["rot"])
            xs = [c[0] for c in corners]
            ys = [c[1] for c in corners]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            
            snap_x = 0; snap_y = 0
            if abs(min_x - 0) < self.SNAP_EDGE_DIST: snap_x = -min_x 
            elif abs(max_x - self.width) < self.SNAP_EDGE_DIST: snap_x = self.width - max_x 
            if abs(min_y - 0) < self.SNAP_EDGE_DIST: snap_y = -min_y 
            elif abs(max_y - self.height) < self.SNAP_EDGE_DIST: snap_y = self.height - max_y 
            
            self.box_cx = prop_cx + snap_x
            self.box_cy = prop_cy + snap_y
            
        else:
            # --- ANCHOR RESIZING LOGIC (Unchanged) ---
            
            cur_x, cur_y = mx, my
            if abs(cur_x - 0) < self.SNAP_EDGE_DIST: cur_x = 0
            elif abs(cur_x - self.width) < self.SNAP_EDGE_DIST: cur_x = self.width
            if abs(cur_y - 0) < self.SNAP_EDGE_DIST: cur_y = 0
            elif abs(cur_y - self.height) < self.SNAP_EDGE_DIST: cur_y = self.height
            
            dx = cur_x - self.drag_start_pos[0]
            dy = cur_y - self.drag_start_pos[1]

            rad = math.radians(-st["rot"])
            rdx = dx * math.cos(rad) - dy * math.sin(rad)
            rdy = dx * math.sin(rad) + dy * math.cos(rad)
            
            nw, nh = st["w"], st["h"]
            if 'e' in self.active_handle: nw = st["w"] + rdx
            if 'w' in self.active_handle: nw = st["w"] - rdx
            if 's' in self.active_handle: nh = st["h"] + rdy
            if 'n' in self.active_handle: nh = st["h"] - rdy
            
            if len(self.active_handle) == 2:
                ratio = st["w"] / st["h"]
                if ratio > 1.0: nh = nw / ratio
                else: nw = nh * ratio

            nw = max(20, nw)
            nh = max(20, nh)
            
            actual_dw = nw - st["w"]
            actual_dh = nh - st["h"]

            lcx_shift = 0
            lcy_shift = 0
            if 'e' in self.active_handle: lcx_shift = actual_dw / 2.0
            if 'w' in self.active_handle: lcx_shift = -actual_dw / 2.0
            if 's' in self.active_handle: lcy_shift = actual_dh / 2.0
            if 'n' in self.active_handle: lcy_shift = -actual_dh / 2.0
            
            rad_fwd = math.radians(st["rot"])
            wcx_shift = lcx_shift * math.cos(rad_fwd) - lcy_shift * math.sin(rad_fwd)
            wcy_shift = lcx_shift * math.sin(rad_fwd) + lcy_shift * math.cos(rad_fwd)

            self.box_w = nw
            self.box_h = nh
            self.box_cx = st["cx"] + wcx_shift
            self.box_cy = st["cy"] + wcy_shift

    def on_mouse_up(self, event):
        self.active_handle = None

    def update_cursor(self, event):
        hit = self.hit_test(event.x, event.y)
        if hit == 'move': self.canvas.config(cursor="fleur")
        elif hit == 'rot': self.canvas.config(cursor="exchange")
        elif hit:
            base_angles = { 'n': 0, 's': 0, 'e': 90, 'w': 90, 'nw': 45, 'se': 45, 'ne': 135, 'sw': 135 }
            if hit in base_angles:
                total_angle = (base_angles[hit] + self.rotation) % 180
                if 22.5 <= total_angle < 67.5: self.canvas.config(cursor="size_nw_se")
                elif 67.5 <= total_angle < 112.5: self.canvas.config(cursor="sb_h_double_arrow")
                elif 112.5 <= total_angle < 157.5: self.canvas.config(cursor="size_ne_sw")
                else: self.canvas.config(cursor="sb_v_double_arrow")
        else:
            self.canvas.config(cursor="arrow")

    # --- PROCESSING: UPDATED UPLOAD LOGIC ---

    def upload_file(self):
        path = filedialog.askopenfilename(filetypes=[("Media", "*.png;*.jpg;*.jpeg;*.mp4;*.avi;*.mov")])
        if path:
            self.file_path = path
            
            if self.is_broadcasting:
                 self.toggle_broadcast() 

            if self.cap: self.cap.release()
            self.cap = None
            self.source_image = None
            
            if self.file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                self.source_image = cv2.imread(self.file_path)
            else:
                self.cap = cv2.VideoCapture(self.file_path)
                if self.cap.isOpened():
                    ret, _ = self.cap.read()
                    if ret:
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    else:
                        messagebox.showerror("Error", "Could not read video stream.")
                        self.cap = None
            
            self.rotation = 0
            self.mirror = False
            self.mirror_btn.config(text="↔ Mirror: OFF")
            
            # 1. Get Source Dimensions
            source_w, source_h = 0, 0
            if self.source_image is not None: 
                source_h, source_w = self.source_image.shape[:2]
            elif self.cap is not None and self.cap.isOpened():
                source_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                source_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # 2. Set Canvas/Camera to FIXED Landscape (16:9) Dimensions
            self.width = self.FIXED_WIDTH
            self.height = self.FIXED_HEIGHT

            # 3. Fit Source Media Box within the FIXED 16:9 Frame
            if source_w > 0:
                
                # Calculate the scale factor to fit the source within the fixed frame
                scale_w = self.width / source_w
                scale_h = self.height / source_h
                scale = min(scale_w, scale_h) # Use the smaller scale factor to ensure it fits entirely (pillarbox/letterbox)

                self.box_w = source_w * scale
                self.box_h = source_h * scale

                self.canvas.config(width=self.width, height=self.height)
                self.canvas_frame.config(width=self.width, height=self.height)
                # Adjust root window size (toolbar + canvas + padding)
                self.root.geometry(f"{self.width + 20}x{self.height + 70}") 

                # Center the box
                self.box_cx = self.width / 2
                self.box_cy = self.height / 2

    def toggle_mirror(self):
        self.mirror = not self.mirror
        self.mirror_btn.config(text=f"↔ Mirror: {'ON' if self.mirror else 'OFF'}")

    def toggle_broadcast(self):
        if not self.is_broadcasting:
            if self.width <= 0 or self.height <= 0:
                messagebox.showerror("Error", "Invalid output dimensions.")
                return

            try:
                # Use the fixed width/height for the virtual cam
                self.cam = pyvirtualcam.Camera(width=self.width, height=self.height, fps=30, fmt=PixelFormat.BGR)
                self.is_broadcasting = True
                self.broadcast_btn.config(text="⏹ Stop Broadcast", style='Broadcast.TButton')
            except Exception as e:
                messagebox.showerror("Error", f"Failed to start virtual camera: {e}")
        else:
            self.is_broadcasting = False
            if self.cam: self.cam.close(); self.cam = None
            self.broadcast_btn.config(text="📡 Start Broadcast", style='Broadcast.TButton')

    def get_source_frame(self):
        frame = None
        if self.cap:
            if self.cap.isOpened():
                ret, frame = self.cap.read()
                if not ret:
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = self.cap.read()
        elif self.source_image is not None:
            frame = self.source_image.copy()
        return frame

    def update_loop(self):
        # The final frame is always the FIXED_WIDTH x FIXED_HEIGHT size, and starts black
        final = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        src = self.get_source_frame()
        
        if src is not None:
            if self.mirror: src = cv2.flip(src, 1)
            
            bw, bh = int(self.box_w), int(self.box_h)
            if bw > 0 and bh > 0:
                src_scaled = cv2.resize(src, (bw, bh))
                diag = int(math.hypot(bw, bh))
                
                # ... (Rest of image processing logic is unchanged) ...
                
                padded = cv2.copyMakeBorder(src_scaled, 
                                          (diag-bh)//2, (diag-bh)//2, 
                                          (diag-bw)//2, (diag-bw)//2, 
                                          cv2.BORDER_CONSTANT, value=(0,0,0))
                
                M = cv2.getRotationMatrix2D((diag//2, diag//2), -self.rotation, 1.0)
                rotated = cv2.warpAffine(padded, M, (diag, diag))
                
                tx = int(self.box_cx - diag//2)
                ty = int(self.box_cy - diag//2)
                h_rot, w_rot = rotated.shape[:2]
                
                x1, y1 = max(tx, 0), max(ty, 0)
                x2, y2 = min(tx + w_rot, self.width), min(ty + h_rot, self.height)
                
                ox1, oy1 = max(0, -tx), max(0, -ty)
                ox2, oy2 = ox1 + (x2 - x1), oy1 + (y2 - y1)
                
                if x2 > x1 and y2 > y1:
                    roi = final[y1:y2, x1:x2]
                    fg = rotated[oy1:oy2, ox1:ox2]
                    gray = cv2.cvtColor(fg, cv2.COLOR_BGR2GRAY)
                    _, mask = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
                    roi_bg = cv2.bitwise_and(roi, roi, mask=cv2.bitwise_not(mask))
                    fg_fg = cv2.bitwise_and(fg, fg, mask=mask)
                    final[y1:y2, x1:x2] = cv2.add(roi_bg, fg_fg)

        cv2image = cv2.cvtColor(final, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(cv2image)
        imgtk = ImageTk.PhotoImage(image=img)
        self.canvas.itemconfig(self.vid_container, image=imgtk)
        self.canvas.image = imgtk

        if src is not None:
            for item in self.ui_items.values():
                self.canvas.tag_raise(item)

            corners = self.get_corners(self.box_cx, self.box_cy, self.box_w, self.box_h, self.rotation)
            flat_corners = [c for pt in corners for c in pt]
            self.canvas.coords(self.ui_items['outline'], *flat_corners)
            
            rx, ry = self.get_handle_pos('rot', self.box_cx, self.box_cy, self.box_w, self.box_h, self.rotation)
            top_mid = self.get_handle_pos('n', self.box_cx, self.box_cy, self.box_w, self.box_h, self.rotation)
            self.canvas.coords(self.ui_items['rot_line'], top_mid[0], top_mid[1], rx, ry)
            
            HANDLE_SIZE = 8 
            for h_name in ['nw', 'n', 'ne', 'e', 'se', 's', 'sw', 'w', 'rot']:
                hx, hy = self.get_handle_pos(h_name, self.box_cx, self.box_cy, self.box_w, self.box_h, self.rotation)
                sz = HANDLE_SIZE
                self.canvas.coords(self.ui_items[h_name], hx-sz, hy-sz, hx+sz, hy+sz)
        else:
            for item in self.ui_items.values():
                self.canvas.coords(item, -20, -20, -10, -10)

        if self.is_broadcasting and self.cam:
            self.cam.send(final)
            self.cam.sleep_until_next_frame()

        self.root.after(30, self.update_loop)

if __name__ == "__main__":
    root = tk.Tk()
    app = FakeCamApp(root)
    root.mainloop()