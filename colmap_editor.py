import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw
import sqlite3
import numpy as np
import os
import sys

def array_to_blob(array):
    return array.astype(np.float32).tobytes()

def blob_to_array(blob, dtype, shape):
    return np.frombuffer(blob, dtype=dtype).reshape(shape)

class ColmapFeatureViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("COLMAP Feature Viewer")
        self.geometry("1200x900")

        # --- Control panel (fixed) ---
        ctrl_frame = tk.Frame(self)
        ctrl_frame.pack(side=tk.TOP, fill=tk.X)

        self.db_path_btn = tk.Button(ctrl_frame, text="Select COLMAP .db File", command=self.select_db_file)
        self.db_path_btn.pack(side=tk.LEFT, padx=5)
        self.img_dir_btn = tk.Button(ctrl_frame, text="Select Images Folder", command=self.select_images_folder)
        self.img_dir_btn.pack(side=tk.LEFT, padx=5)
        self.load_btn = tk.Button(ctrl_frame, text="Load Data", command=self.load_data, state=tk.DISABLED)
        self.load_btn.pack(side=tk.LEFT, padx=5)
        self.prev_btn = tk.Button(ctrl_frame, text="<< Previous", command=self.prev_image, state=tk.DISABLED)
        self.prev_btn.pack(side=tk.LEFT, padx=10)
        self.next_btn = tk.Button(ctrl_frame, text="Next >>", command=self.next_image, state=tk.DISABLED)
        self.next_btn.pack(side=tk.LEFT, padx=10)
        self.save_btn = tk.Button(ctrl_frame, text="Save Matches", command=self.save_session_and_reset)
        self.save_btn.pack(side=tk.LEFT, padx=10)
        self.clear_btn = tk.Button(ctrl_frame, text="Clear Queue", command=self.clear_session)
        self.clear_btn.pack(side=tk.LEFT, padx=10)

        # --- Scrollable/zoomable canvas ---
        canvas_frame = tk.Frame(self)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg='black')
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.hbar = tk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.hbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.vbar = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.vbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.config(xscrollcommand=self.hbar.set, yscrollcommand=self.vbar.set)

        # --- Internal state ---
        self.db_path = None
        self.images_dir = None
        self.conn = None
        self.cursor = None
        self.images = []
        self.keypoints = {}
        self.matches = {}
        self.current_index = 0
        self.original_pil_img = None
        self.current_pil_img = None
        self.tk_img = None
        self.zoom_level = 1.0
        self.added_features = []
        self.match_session_active = False
        self.session_start_index = None
        self.session_features = []  # list of (image_id, kp_idx)
        self.session_matches = {}   # dict: (id1, id2) -> np.array of matches
        # --- Bindings ---
        self.canvas.bind("<Configure>", self.redraw_image)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)        # Windows, MacOS
        self.canvas.bind("<Button-1>", self.on_left_click)  # Left click to add feature
        self.canvas.bind("<Button-3>", self.on_right_click) # Right click to cancel
        # self.enable_feature_addition()

    # def enable_feature_addition(self):
    #     self.canvas.bind("<Button-1>", self.on_canvas_click)
        
    def on_left_click(self, event):
        # Start session if not active
        if not self.match_session_active:
            self.match_session_active = True
            self.session_start_index = self.current_index
            self.session_features = []
            self.session_matches = {}

        # Add feature at click location
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        img_x = canvas_x / self.zoom_level
        img_y = canvas_y / self.zoom_level

        image_id, _ = self.images[self.current_index]
        if image_id in self.keypoints:
            kps = self.keypoints[image_id]
            new_kps = np.vstack([kps, np.array([[img_x, img_y]], dtype=np.float32)])
            new_kp_index = len(kps)
        else:
            new_kps = np.array([[img_x, img_y]], dtype=np.float32)
            new_kp_index = 0
        self.keypoints[image_id] = new_kps
        self.update_keypoints_in_db(image_id, new_kps)

        # Add to session features
        self.session_features.append((image_id, new_kp_index))

        # Add matches to all previous features in this session
        if len(self.session_features) > 1:
            current_img_id, current_kp_idx = self.session_features[-1]
            for prev_img_id, prev_kp_idx in self.session_features[:-1]:
                id1, id2 = sorted((prev_img_id, current_img_id))
                if (id1, id2) not in self.session_matches:
                    self.session_matches[(id1, id2)] = np.empty((0, 2), dtype=np.uint32)
                # Determine match direction
                if id1 == prev_img_id:
                    new_match = np.array([[prev_kp_idx, current_kp_idx]], dtype=np.uint32)
                else:
                    new_match = np.array([[current_kp_idx, prev_kp_idx]], dtype=np.uint32)
                self.session_matches[(id1, id2)] = np.vstack([self.session_matches[(id1, id2)], new_match])

        # Advance to next image
        self.current_index = (self.current_index + 1) % len(self.images)
        self.display_image_with_features(self.current_index)

        # If we've looped back to the starting image, end session and save matches
        # if self.match_session_active and self.current_index == self.session_start_index:
        #     print("matches were saved")
        #     self.save_session_matches()
        #     self.match_session_active = False
        #     self.session_features = []
        #     self.session_matches = {}

    def on_right_click(self, event):
        # Skip adding a feature and stay on the current image
        pass

    def save_session_matches(self):
        # Save all matches from this session to the database
        # You can append to the matches table or overwrite, as needed
        # Here, we append (recommended if you want to keep all matches)
        try:
            self.cursor.execute("CREATE TABLE IF NOT EXISTS matches (pair_id INTEGER PRIMARY KEY, rows INTEGER, cols INTEGER, data BLOB)")
        except Exception:
            pass
        for (id1, id2), arr in self.session_matches.items():
            print("match was saved")
            pair_id = id1 + (id2 << 32)
            blob = arr.astype(np.uint32).tobytes()
            rows, cols = arr.shape
            # Insert or append matches for this pair
            # Check if pair already exists
            self.cursor.execute("SELECT data, rows, cols FROM matches WHERE pair_id=?", (pair_id,))
            result = self.cursor.fetchone()
            if result:
                # Append to existing matches
                old_blob, old_rows, old_cols = result
                old_arr = np.frombuffer(old_blob, dtype=np.uint32).reshape((old_rows, old_cols))
                arr = np.vstack([old_arr, arr])
            self.cursor.execute("INSERT OR REPLACE INTO matches (pair_id, rows, cols, data) VALUES (?, ?, ?, ?)",
                                (pair_id, arr.shape[0], arr.shape[1], arr.astype(np.uint32).tobytes()))
        self.conn.commit()

    # def on_canvas_click(self, event):
    #     # Convert canvas click to image coords
    #     canvas_x = self.canvas.canvasx(event.x)
    #     canvas_y = self.canvas.canvasy(event.y)
    #     img_x = canvas_x / self.zoom_level
    #     img_y = canvas_y / self.zoom_level

    #     image_id, _ = self.images[self.current_index]
    #     if image_id in self.keypoints:
    #         kps = self.keypoints[image_id]
    #         new_kps = np.vstack([kps, np.array([[img_x, img_y]], dtype=np.float32)])
    #     else:
    #         new_kps = np.array([[img_x, img_y]], dtype=np.float32)
    #     self.keypoints[image_id] = new_kps

    #     # Update DB
    #     self.update_keypoints_in_db(image_id, new_kps)

    #     # Redraw image with new feature visible
    #     self.redraw_image()


    def update_keypoints_in_db(self, image_id, keypoints):
        blob = array_to_blob(keypoints)
        rows, cols = keypoints.shape
        self.cursor.execute("DELETE FROM keypoints WHERE image_id=?", (image_id,))
        self.cursor.execute(
            "INSERT INTO keypoints (image_id, rows, cols, data) VALUES (?, ?, ?, ?)",
            (image_id, rows, cols, blob)
        )
        self.conn.commit()

    def save_matches(self):
        # Save all matches to the database
        try:
            self.cursor.execute("DELETE FROM matches")
        except sqlite3.OperationalError:
            self.cursor.execute("CREATE TABLE matches (pair_id INTEGER PRIMARY KEY, rows INTEGER, cols INTEGER, data BLOB)")
        for (id1, id2), arr in self.matches.items():
            # print("SAVED ONE MATCH")
            pair_id = id1 + (id2 << 32)
            blob = arr.astype(np.uint32).tobytes()
            rows, cols = arr.shape
            self.cursor.execute("INSERT OR REPLACE INTO matches (pair_id, rows, cols, data) VALUES (?, ?, ?, ?)",
                                (pair_id, rows, cols, blob))
        self.conn.commit()

    def select_db_file(self):
        path = filedialog.askopenfilename(
            title="Select COLMAP database file",
            filetypes=[("SQLite DB files", "*.db"), ("All files", "*.*")]
        )
        if path:
            self.db_path = path
            self.db_path_btn.config(text=os.path.basename(path))
            self.check_ready_to_load()

    def select_images_folder(self):
        path = filedialog.askdirectory(title="Select folder containing images")
        if path:
            self.images_dir = path
            self.img_dir_btn.config(text=os.path.basename(path))
            self.check_ready_to_load()

    def check_ready_to_load(self):
        if self.db_path and self.images_dir:
            self.load_btn.config(state=tk.NORMAL)
        else:
            self.load_btn.config(state=tk.DISABLED)

    def load_data(self):
        if self.conn:
            self.conn.close()
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            self.images = self.load_images()
            self.keypoints = self.load_keypoints()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load database: {e}")
            return
        if not self.images:
            messagebox.showinfo("Info", "No images found in database.")
            return
        self.current_index = 0
        self.zoom_level = 1.0
        self.display_image_with_features(self.current_index)
        self.prev_btn.config(state=tk.NORMAL)
        self.next_btn.config(state=tk.NORMAL)

    def load_images(self):
        self.cursor.execute("SELECT image_id, name FROM images ORDER BY image_id")
        return self.cursor.fetchall()

    def load_keypoints(self):
        self.cursor.execute("SELECT image_id, data FROM keypoints")
        keypoints = {}
        for image_id, blob in self.cursor.fetchall():
            arr = blob_to_array(blob, np.float32, (-1, 2))
            keypoints[image_id] = arr
        return keypoints

    def display_image_with_features(self, index):
        image_id, image_name = self.images[index]
        image_path = os.path.join(self.images_dir, image_name)
        if not os.path.exists(image_path):
            messagebox.showwarning("Warning", f"Image file not found:\n{image_path}")
            return
        pil_img = Image.open(image_path).convert("RGB")
        # draw = ImageDraw.Draw(pil_img)
        # if image_id in self.keypoints:
        #     pts = self.keypoints[image_id]
        #     valid = np.isfinite(pts).all(axis=1) & ~np.all(pts == 0, axis=1)
        #     for (x, y) in pts[valid]:
        #         cx, cy = x * self.zoom_level, y * self.zoom_level
        #         r = 5
        #         draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline="red", width=2)
        self.original_pil_img = pil_img
        # DO NOT reset self.zoom_level here!
        self.redraw_image()

    def save_session_and_reset(self):
        if self.match_session_active:
            self.save_session_matches()
            self.match_session_active = False
            self.session_features = []
            self.session_matches = {}
            self.display_image_with_features(self.current_index)

    def clear_session(self):
        # Remove features and matches from the current session only
        for img_id, kp_idx in reversed(self.session_features):
            kps = self.keypoints[img_id]
            if 0 <= kp_idx < len(kps):
                kps = np.delete(kps, kp_idx, axis=0)
                self.keypoints[img_id] = kps
                self.update_keypoints_in_db(img_id, kps)
        self.match_session_active = False
        self.session_features = []
        self.session_matches = {}
        self.display_image_with_features(self.current_index)

    def redraw_image(self, event=None):
        if self.original_pil_img is None:
            return
        w, h = self.original_pil_img.size
        new_w = int(w * self.zoom_level)
        new_h = int(h * self.zoom_level)
        if new_w < 1 or new_h < 1:
            return
        try:
            resample = Image.Resampling.LANCZOS
        except AttributeError:
            resample = Image.LANCZOS
        self.current_pil_img = self.original_pil_img.resize((new_w, new_h), resample)
        draw = ImageDraw.Draw(self.current_pil_img)
        image_id, _ = self.images[self.current_index]
        if image_id in self.keypoints:
            pts = self.keypoints[image_id]
            valid = np.isfinite(pts).all(axis=1) & ~np.all(pts == 0, axis=1)
            # Get indices of features in current session for this image
            session_kp_indices = {kp_idx for img_id, kp_idx in getattr(self, 'session_features', []) if img_id == image_id}
            for idx, (x, y) in enumerate(pts[valid]):
                cx, cy = x * self.zoom_level, y * self.zoom_level
                r = 5
                color = "green" if idx in session_kp_indices else "red"
                draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=color, width=2)
        self.tk_img = ImageTk.PhotoImage(self.current_pil_img)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_img)
        self.canvas.config(scrollregion=(0, 0, new_w, new_h))


    def on_mousewheel(self, event):
        # Zoom if Ctrl is held, otherwise scroll
        if (event.state & 0x0004) != 0 or (event.state & 0x0008) != 0:  # Ctrl or Alt held
            if event.delta > 0 or getattr(event, 'num', None) == 4:
                self.zoom_level *= 1.1
            elif event.delta < 0 or getattr(event, 'num', None) == 5:
                self.zoom_level /= 1.1
            self.zoom_level = max(0.1, min(self.zoom_level, 10))
            self.canvas.delete("all")
            self.redraw_image()
        else:
            # Scroll normally
            if event.delta:
                self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            elif getattr(event, 'num', None) == 4:
                self.canvas.yview_scroll(-3, "units")
            elif getattr(event, 'num', None) == 5:
                self.canvas.yview_scroll(3, "units")

    def prev_image(self):
        if not self.images:
            return
        self.current_index = (self.current_index - 1) % len(self.images)
        self.display_image_with_features(self.current_index)

    def next_image(self):
        if not self.images:
            return
        self.current_index = (self.current_index + 1) % len(self.images)
        self.display_image_with_features(self.current_index)

    def on_close(self):
        if self.conn:
            self.conn.close()
        self.destroy()

if __name__ == "__main__":
    app = ColmapFeatureViewer()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
