import os
import sqlite3
import cv2
import sys
import importlib.metadata
from utils.analytics import DB_PATH

def check_model_file():
    model_path = os.path.join('ml_model', 'trained_models', 'random_forest_multimodal_validated.joblib')
    if os.path.exists(model_path):
        return True, f"Multimodal Random Forest model verified at {model_path}"
    return False, "Random Forest model binary missing! System will fall back to typing heuristics."

def check_webcam_availability():
    if os.getenv('RENDER') == 'true':
        return False, "Webcam capture bypassed in cloud deployment environment."
    # Attempt to open default camera (index 0)
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(0)  # Fallback to default backend
        
    if cap.isOpened():
        ret, frame = cap.read()
        cap.release()
        if ret:
            return True, "Webcam is active and successfully capturing frames."
        else:
            return False, "Webcam interface opened but failed to capture a test frame (possibly locked)."
    return False, "No active webcam detected on video index 0."

def check_database_schema():
    if not os.path.exists(DB_PATH):
        return True, "Database file does not exist yet (will be created automatically)."
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='session_logs'")
        if not cursor.fetchone():
            conn.close()
            return True, "session_logs table does not exist yet (will be initialized)."
        
        cursor.execute("PRAGMA table_info(session_logs)")
        columns = [row[1] for row in cursor.fetchall()]
        conn.close()
        
        required_cols = [
            'wpm', 'errors', 'session_duration', 'fatigue_score', 'fatigue_level',
            'productivity_score', 'blink_count', 'yawn_count', 'predict_level',
            'predict_confidence', 'concentration_score'
        ]
        
        missing = [col for col in required_cols if col not in columns]
        if missing:
            return False, f"Database schema is outdated. Missing columns: {', '.join(missing)}"
        return True, "Database schema verified successfully (11 columns present)."
    except Exception as e:
        return False, f"Database validation error: {e}"

def check_environment_packages():
    # Standard dependencies key-value mapping to verify
    packages = {
        "Flask": "flask",
        "joblib": "joblib",
        "numpy": "numpy",
        "pandas": "pandas",
        "scikit-learn": "sklearn",
        "opencv-python": "cv2",
        "mediapipe": "mediapipe"
    }
    
    missing_packages = []
    
    for display_name, import_name in packages.items():
        try:
            # First try direct import as absolute validation
            __import__(import_name)
        except ImportError:
            # Check metadata version as fallback check
            try:
                importlib.metadata.version(display_name)
            except importlib.metadata.PackageNotFoundError:
                missing_packages.append(display_name)
                
    if missing_packages:
        return False, f"Missing dependencies in Python environment: {', '.join(missing_packages)}"
    return True, "All critical libraries (Flask, NumPy, Pandas, Scikit-Learn, OpenCV, MediaPipe) are installed."

def run_all_checks():
    model_ok, model_msg = check_model_file()
    webcam_ok, webcam_msg = check_webcam_availability()
    db_ok, db_msg = check_database_schema()
    env_ok, env_msg = check_environment_packages()
    
    # Render Console ASCII diagnostics status card
    print("=" * 70)
    print("                  FATIGUEAI STARTUP SYSTEM DIAGNOSTICS               ")
    print("=" * 70)
    
    def print_row(status, text):
        indicator = "  [OK] " if status else "  [WARN]"
        print(f" {indicator:<8} {text:<58} ")

    print_row(model_ok, "ML Classifier Model Binary Verification")
    print_row(webcam_ok, "Webcam Hardware Capture Verification")
    print_row(db_ok, "SQLite Database Analytics Schema Verification")
    print_row(env_ok, "Active Virtual Environment Package Verification")
    
    print("-" * 70)
    if not model_ok:
        print(f" WARNING: {model_msg}")
    if not webcam_ok:
        print(f" WARNING: {webcam_msg}")
    if not db_ok:
        print(f" WARNING: {db_msg}")
    if not env_ok:
        print(f" WARNING: {env_msg}")
        
    if model_ok and webcam_ok and db_ok and env_ok:
        print(" SUCCESS: All core services loaded. Running in standard multi-modal mode.")
    else:
        print(" STATUS: Operational with fallbacks active. Ready for client dashboard query.")
    print("=" * 70)
    
    return {
        "model_ok": model_ok,
        "webcam_ok": webcam_ok,
        "database_ok": db_ok,
        "environment_ok": env_ok,
        "details": {
            "model": model_msg,
            "webcam": webcam_msg,
            "database": db_msg,
            "environment": env_msg
        }
    }
