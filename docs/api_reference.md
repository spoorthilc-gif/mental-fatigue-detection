# API Reference — FatigueAI

This document outlines the API endpoints exposed by the **FatigueAI** Flask backend. All routes (except `/` and `/login`/`/register`) require an active user session.

---

## 🔐 Authentication APIs

### 1. Register Account
*   **Endpoint**: `/register`
*   **Method**: `POST`
*   **Request Parameters**:
    - `username` (string, length >= 3)
    - `email` (string, regex verified)
    - `password` (string, length >= 6)
    - `confirm_password` (string, matching password)
*   **Response**: Redirects to `/login` on success, or renders form with error messages.

### 2. Standard Login
*   **Endpoint**: `/login`
*   **Method**: `POST`
*   **Request Parameters**:
    - `username_or_email` (string)
    - `password` (string)
    - `remember` (checkbox boolean)
*   **Response**: Redirects to `/dashboard` on success.

### 3. Recruiter Demo Login
*   **Endpoint**: `/demo-login`
*   **Method**: `GET`
*   **Description**: Authenticates directly as user `demo` and redirects to the dashboard.

---

## 📊 Telemetry & Data APIs

### 1. Get Live Typing Heuristics
*   **Endpoint**: `/api/stats`
*   **Method**: `GET`
*   **Response Format**: `JSON`
*   **Sample Output**:
    ```json
    {
      "wpm": 68.4,
      "errors": 12,
      "elapsed": 120.0,
      "chars": 570
    }
    ```

### 2. Calculate Fatigue Level
*   **Endpoint**: `/api/fatigue`
*   **Method**: `GET`
*   **Description**: Evaluates rule-based calculations and triggers log writes to SQLite and CSV.
*   **Sample Output**:
    ```json
    {
      "fatigue": "Low",
      "score": 15
    }
    ```

### 3. Machine Learning Inference
*   **Endpoint**: `/api/predict-fatigue`
*   **Method**: `GET`
*   **Description**: Runs live Random Forest inference using physical (EAR, MAR, yawn, blinks) and typing telemetry.
*   **Sample Output**:
    ```json
    {
      "fatigue_level": "LOW",
      "confidence": 0.94,
      "reasoning": [
        "Typing speed is stable",
        "Blink frequency is normal"
      ]
    }
    ```

### 4. Webcam Status
*   **Endpoint**: `/api/webcam-status`
*   **Method**: `GET`
*   **Sample Output**:
    ```json
    {
      "is_active": true,
      "face_detected": true,
      "fps": 28,
      "blink_count": 8,
      "yawn_count": 0,
      "eye_aperture": 0.26,
      "mouth_stretch": 0.12
    }
    ```

### 5. Research Statistical Summary
*   **Endpoint**: `/api/research-report`
*   **Method**: `GET`
*   **Sample Output**:
    ```json
    {
      "total_records": 120,
      "avg_wpm": 64.2,
      "avg_errors": 8,
      "total_blinks": 45,
      "total_yawns": 2,
      "correlations": {
        "wpm_vs_fatigue": -0.425,
        "blinks_vs_fatigue": 0.612
      },
      "fatigue_distribution": {
        "LOW": 70.0,
        "MEDIUM": 20.0,
        "HIGH": 10.0
      }
    }
    ```

### 6. Export Dataset
*   **Endpoint**: `/api/export-csv`
*   **Method**: `GET`
*   **Description**: Streams and downloads the complete user log database as a formatted CSV file.
