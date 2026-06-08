# System Architecture — FatigueAI

This document provides a detailed description of the design patterns, processing pipelines, and threading logic inside **FatigueAI**.

---

## 🏗️ Design Overview

FatigueAI is built on a decoupled, multimodal telemetry architecture where physical biometrics and behavioral keystrokes are co-trained and tracked via separate pipelines. The Flask backend processes API requests from the dynamic HTML dashboard while running background hardware capture hooks.

```
                      +-------------------+
                      |   User Interface  |
                      +---------+---------+
                                |
             +------------------+------------------+
             | (1s telemetry poll)                 | (2s pipeline logs)
    +--------v--------+                   +--------v--------+
    |  /api/stats     |                   |  /api/fatigue   |
    |  (keystrokes)   |                   |  /api/predict   |
    +--------+--------+                   +--------+--------+
             |                                     |
    +--------v--------+                   +--------v--------+
    | Keyboard Hook   |                   | Threaded Webcam |
    | (Active Listener|                   | (FaceMesh EAR/  |
    |  pynput thread) |                   |  MAR extract)   |
    +-----------------+                   +-----------------+
```

---

## 🧵 Active Telemetry Pipelines

### 1. Keyboard Behavioral Hook
*   **Module**: `tracker/keyboard_listener.py`
*   **Pipeline**:
    - Uses a non-blocking background keyboard hook thread (`pynput.keyboard.Listener`).
    - Captures the exact timestamp of key presses and releases.
    - Increments character counts (`chars`) and backspace errors (`errors`).
    - Calculates words-per-minute (`WPM`) speed over moving 10-second averages:
      $$\text{WPM} = \frac{\text{chars typed}}{5} \times \frac{60}{\text{elapsed seconds}}$$
    - The hook runs continuously in a dedicated thread separated from the main Flask worker to avoid blocking web traffic.

### 2. Threaded Physiological Webcam Tracker
*   **Module**: `tracker/webcam_tracker.py`
*   **Pipeline**:
    - Spawns a dedicated camera frame grabbing thread (`threading.Thread`) on server startup.
    - Captures raw video frames from the webcam (`cv2.VideoCapture`).
    - Feeds video frames to Google's MediaPipe FaceMesh solutions.
    - Extracts 468 3D facial mesh coordinate coordinates.
    - Calculates:
      - **Eye Aperture Ratio (EAR)**: Monitors eye closure (distance between vertical lid landmarks divided by horizontal width).
      - **Mouth Stretch Ratio (MAR)**: Monitors mouth expansion (vertical lip opening landmarks divided by horizontal width).
      - Registers a blink if EAR drops below `0.22` for more than 2 frames.
      - Registers a yawn if MAR stretches past `0.6` for more than 30 frames (1.5 seconds).
    - Writes metrics to shared variables protected by thread locks (`threading.Lock`) to avoid race conditions during Flask polling queries.

---

## 🗄️ Database & Storage Design
*   **Module**: `utils/analytics.py`
*   **Design**:
    - Exposes `log_behavior()` to save a snapshot of 11 variables every 10 seconds during typing active sessions to a local SQLite database (`database/fatigue_analytics.db`) under table `session_logs`.
    - Automatically replicates SQL database telemetry records to a user-specific CSV dataset file (`dataset/behavioral_data/live_behavior_dataset_user_{id}.csv`) to ensure recruiters see data serialization outputs.
    - Employs foreign keys linked to the `users` credentials table, ensuring multi-user telemetry isolation.
