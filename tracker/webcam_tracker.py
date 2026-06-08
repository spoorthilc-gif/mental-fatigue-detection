import cv2
import threading
import time
import os
import urllib.request
import numpy as np
import mediapipe as mp
from utils.tracker_logger import log_event

class WebcamTracker:
    def __init__(self, device_id=0):
        self.device_id = device_id
        self.cap = None
        self.running = False
        self.is_active = False
        self.latest_frame = None
        self.lock = threading.Lock()
        self.thread = None
        
        # MediaPipe model paths
        self.model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'face_landmarker.task')
        self.model_url = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
        self.detector = None
        
        # State metrics
        self.face_detected = False
        self.eye_aperture = 10.0
        self.mouth_stretch = 16.0
        self.blink_count = 0
        self.yawn_count = 0
        self.fps = 0.0
        self.drowsy_duration = 0.0
        
        # Blink & Yawn tracking algorithm variables
        self.blink_state = False
        self.blink_start_time = 0.0
        self.yawn_state = False
        self.yawn_start_time = 0.0
        
        # FPS estimation states
        self.frame_count = 0
        self.start_time = 0.0
        
        # Optimization and cache states
        self.last_landmarks = None
        self.process_counter = 0
        
    def start(self):
        """Start the webcam capture loop in a background thread."""
        with self.lock:
            if self.running:
                return
            
            if os.getenv('RENDER') == 'true':
                log_event("info", "Render cloud environment detected. Bypassing physical webcam capture thread.")
                self.is_active = False
                return
            
            # Download model if not present locally
            if not os.path.exists(self.model_path):
                log_event("info", f"Downloading MediaPipe Face Landmarker model from {self.model_url}...")
                try:
                    urllib.request.urlretrieve(self.model_url, self.model_path)
                    log_event("info", "Model downloaded successfully.")
                except Exception as e:
                    log_event("error", f"Failed to download Face Landmarker model: {e}")
                    self.is_active = False
                    return
            
            log_event("info", f"Initializing capture device {self.device_id}...")
            self.cap = cv2.VideoCapture(self.device_id)
            if not self.cap.isOpened():
                log_event("error", f"Could not open device {self.device_id} (permission or connection failure)")
                self.is_active = False
                return
                
            # Perform a test read to confirm stream permissions
            ret, frame = self.cap.read()
            if not ret or frame is None:
                log_event("error", f"Permission granted but failed to read initial frame from device {self.device_id}")
                self.cap.release()
                self.cap = None
                self.is_active = False
                return
                
            # Initialize MediaPipe Tasks FaceLandmarker model
            try:
                from mediapipe.tasks import python
                from mediapipe.tasks.python import vision
                
                base_options = python.BaseOptions(model_asset_path=self.model_path)
                options = vision.FaceLandmarkerOptions(
                    base_options=base_options,
                    running_mode=vision.RunningMode.IMAGE,
                    num_faces=1
                )
                self.detector = vision.FaceLandmarker.create_from_options(options)
                log_event("info", "MediaPipe FaceLandmarker loaded successfully.")
            except Exception as e:
                log_event("error", f"Failed to initialize FaceLandmarker: {e}")
                self.cap.release()
                self.cap = None
                self.is_active = False
                return
            
            self.is_active = True
            self.running = True
            self.latest_frame = frame.copy()
            self.start_time = time.time()
            self.frame_count = 0
            self.thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.thread.start()
            log_event("info", "Background FaceMesh capture loop started successfully.")
            
    def _capture_loop(self):
        """Background frame grabbing and MediaPipe FaceMesh processing thread loop."""
        consecutive_failures = 0
        
        while self.running:
            with self.lock:
                if self.cap is None:
                    cap_ref = None
                else:
                    cap_ref = self.cap
                    
            if cap_ref is None:
                time.sleep(1.0)
                continue
                
            ret, frame = cap_ref.read()
            if not ret or frame is None:
                consecutive_failures += 1
                log_event("warning", f"Grabbing frame failed ({consecutive_failures}/5). Re-initializing camera source...")
                
                with self.lock:
                    if self.cap:
                        self.cap.release()
                        self.cap = None
                    self.is_active = False
                    self.face_detected = False
                
                if consecutive_failures >= 5:
                    log_event("error", "Webcam disconnected. Entering slow recovery retry loop (checking every 5 seconds)...")
                    time.sleep(5.0)
                else:
                    time.sleep(1.0)
                    
                with self.lock:
                    if self.running:
                        self.cap = cv2.VideoCapture(self.device_id)
                continue
            else:
                consecutive_failures = 0
                
            h, w, c = frame.shape
            
            # Optimization: Resize frame to 320x240 for fast MediaPipe FaceMesh inference
            inference_w, inference_h = 320, 240
            resized_frame = cv2.resize(frame, (inference_w, inference_h))
            rgb_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            
            # Skip redundant processing: run inference on every 2nd frame
            self.process_counter += 1
            run_inference = (self.process_counter % 2 == 0 or self.last_landmarks is None)
            
            if run_inference:
                try:
                    results = self.detector.detect(mp_image)
                    if results.face_landmarks:
                        self.last_landmarks = results.face_landmarks[0]
                    else:
                        if self.last_landmarks is not None:
                            log_event("info", "Face tracking lost.")
                        self.last_landmarks = None
                except Exception as e:
                    log_event("error", f"MediaPipe detection failed: {e}")
                    self.last_landmarks = None
                    
            face_landmarks = self.last_landmarks
            
            if face_landmarks:
                # Coordinate extraction helper
                def get_pt(idx):
                    pt = face_landmarks[idx]
                    return np.array([pt.x, pt.y])
                
                # ── EAR left eye calculation ──
                p160 = get_pt(160)
                p144 = get_pt(144)
                p158 = get_pt(158)
                p153 = get_pt(153)
                p33 = get_pt(33)
                p133 = get_pt(133)
                ear_left = (np.linalg.norm(p160 - p144) + np.linalg.norm(p158 - p153)) / (2.0 * np.linalg.norm(p33 - p133))
                
                # ── EAR right eye calculation ──
                p385 = get_pt(385)
                p380 = get_pt(380)
                p387 = get_pt(387)
                p373 = get_pt(373)
                p362 = get_pt(362)
                p263 = get_pt(263)
                ear_right = (np.linalg.norm(p385 - p380) + np.linalg.norm(p387 - p373)) / (2.0 * np.linalg.norm(p362 - p263))
                
                ear = (ear_left + ear_right) / 2.0
                
                # ── Pixel-scaled eye aperture (matching JzZJUT coordinates height scale) ──
                y159 = face_landmarks[159].y
                y145 = face_landmarks[145].y
                y386 = face_landmarks[386].y
                y374 = face_landmarks[374].y
                eye_height_left = max(0.0, y145 - y159) * h
                eye_height_right = max(0.0, y374 - y386) * h
                computed_eye_aperture = round(eye_height_left + eye_height_right, 2)
                
                # ── MAR mouth aspect ratio calculation ──
                p13 = get_pt(13)
                p14 = get_pt(14)
                p61 = get_pt(61)
                p291 = get_pt(291)
                mar = np.linalg.norm(p13 - p14) / np.linalg.norm(p61 - p291)
                
                # ── Pixel-scaled mouth stretch (matching JzZJUT height scale) ──
                y0 = face_landmarks[0].y
                y17 = face_landmarks[17].y
                computed_mouth_stretch = round(max(0.0, y17 - y0) * h, 2)
                
                # Draw landmarks on the frame copy (using coordinates scaled to original resolution)
                drawn_frame = frame.copy()
                # Left eye (Green)
                for idx in [33, 133, 160, 144, 158, 153, 159, 145]:
                    pt = face_landmarks[idx]
                    cx, cy = int(pt.x * w), int(pt.y * h)
                    cv2.circle(drawn_frame, (cx, cy), 2, (160, 229, 0), -1)
                # Right eye (Green)
                for idx in [263, 362, 385, 380, 387, 373, 386, 374]:
                    pt = face_landmarks[idx]
                    cx, cy = int(pt.x * w), int(pt.y * h)
                    cv2.circle(drawn_frame, (cx, cy), 2, (160, 229, 0), -1)
                # Mouth (Cyan)
                for idx in [13, 14, 0, 17, 61, 291]:
                    pt = face_landmarks[idx]
                    cx, cy = int(pt.x * w), int(pt.y * h)
                    cv2.circle(drawn_frame, (cx, cy), 2, (255, 212, 0), -1)
                
                # Save processed frames and landmarks status
                with self.lock:
                    self.latest_frame = drawn_frame
                    self.is_active = True
                    self.face_detected = True
                    self.eye_aperture = computed_eye_aperture
                    self.mouth_stretch = computed_mouth_stretch
                    
                    # ── State Blink Tracking Logic ──
                    now = time.time()
                    if ear < 0.20:
                        if not self.blink_state:
                            self.blink_state = True
                            self.blink_start_time = now
                        else:
                            # Track prolonged closed eyes (drowsiness indicator)
                            self.drowsy_duration = round(now - self.blink_start_time, 2)
                    else:
                        if self.blink_state:
                            self.blink_state = False
                            duration = now - self.blink_start_time
                            if duration < 1.0:  # A fast closure count
                                self.blink_count += 1
                            self.drowsy_duration = 0.0
                            
                    # ── State Yawn Tracking Logic ──
                    if mar > 0.50:
                        if not self.yawn_state:
                            self.yawn_state = True
                            self.yawn_start_time = now
                    else:
                        if self.yawn_state:
                            self.yawn_state = False
                            duration = now - self.yawn_start_time
                            if duration >= 1.5:  # Yawn duration
                                self.yawn_count += 1
            else:
                with self.lock:
                    self.latest_frame = frame.copy()
                    self.is_active = True
                    self.face_detected = False
                    self.drowsy_duration = 0.0
                
            # Update FPS tracking
            self.frame_count += 1
            now = time.time()
            elapsed = now - self.start_time
            if elapsed >= 2.0:
                self.fps = self.frame_count / elapsed
                self.frame_count = 0
                self.start_time = now
                
            # Limit loop latency to approx 30 FPS
            time.sleep(0.033)
            
    def get_frame(self):
        """Retrieve the latest captured camera frame in a thread-safe manner."""
        with self.lock:
            if self.latest_frame is None:
                return None
            return self.latest_frame.copy()
            
    def get_metrics(self):
        """Retrieve current physiological features and status metrics."""
        with self.lock:
            return {
                "is_active": self.is_active,
                "face_detected": self.face_detected,
                "eye_aperture": self.eye_aperture,
                "mouth_stretch": self.mouth_stretch,
                "blink_count": self.blink_count,
                "yawn_count": self.yawn_count,
                "drowsy_duration": self.drowsy_duration,
                "fps": round(self.fps, 1)
            }
            
    def reset_counts(self):
        """Reset the blink and yawn counters to zero."""
        with self.lock:
            self.blink_count = 0
            self.yawn_count = 0
            self.drowsy_duration = 0.0
            self.blink_state = False
            self.yawn_state = False
            print("[WEBCAM] Counters reset successfully.")
            
    def stop(self):
        """Safely release webcam device capture resources and terminate background threads."""
        with self.lock:
            self.running = False
            self.is_active = False
            self.face_detected = False
            
        if self.thread:
            self.thread.join(timeout=1.0)
            
        with self.lock:
            if self.cap:
                self.cap.release()
                self.cap = None
            if self.detector:
                self.detector.close()
                self.detector = None
            self.latest_frame = None
            print("[WEBCAM] Camera capture and FaceLandmarker closed.")

# Global Singleton instance
tracker = WebcamTracker(device_id=0)
