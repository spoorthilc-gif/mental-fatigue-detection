import os
import joblib
import numpy as np

# Resolve base directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, 'ml_model', 'trained_models', 'random_forest_multimodal_validated.joblib')
ENCODER_PATH = os.path.join(BASE_DIR, 'ml_model', 'trained_models', 'label_encoder_multimodal_validated.joblib')

# Global references for loaded model/encoder
model = None
le = None

try:
    if os.path.exists(MODEL_PATH) and os.path.exists(ENCODER_PATH):
        model = joblib.load(MODEL_PATH)
        le = joblib.load(ENCODER_PATH)
        print(f"[ML] Loaded validated Random Forest model from {MODEL_PATH}")
    else:
        print(f"[ML WARNING] Validation binaries not found. Prediction utility will return default mock values.")
except Exception as e:
    print(f"[ML ERROR] Failed to load validation models: {e}")

def run_ml_inference(wpm, errors, session_duration, eye_aperture=None, mouth_stretch=None, face_active=None):
    """Run real-time inference using the Random Forest Ensemble model.
    Uses real physical indicators from the webcam tracker or browser metrics if available, otherwise simulates them.
    Returns: (fatigue_level, confidence, reasoning, eye_aperture, mouth_stretch)
    """
    if face_active is None:
        face_active = False
        
    if eye_aperture is None or mouth_stretch is None:
        eye_aperture = 10.0
        mouth_stretch = 16.0
        try:
            from tracker.webcam_tracker import tracker
            metrics = tracker.get_metrics()
            if metrics.get("is_active") and metrics.get("face_detected"):
                eye_aperture = metrics.get("eye_aperture", 10.0)
                mouth_stretch = metrics.get("mouth_stretch", 16.0)
                face_active = True
        except Exception as e:
            print(f"[ML INFERENCE ERROR] Failed to fetch metrics from webcam: {e}")

    if not face_active:
        # Simulated physical coordinates matching KSS distributions as fallback
        is_high = (wpm < 30 or errors > 5)
        is_medium = (wpm < 40 and not is_high)
        
        if is_high:
            eye_aperture = round(max(1.0, np.random.normal(8.8, 0.5)), 2)
            mouth_stretch = round(max(1.0, np.random.normal(16.5, 1.0)), 2)
        elif is_medium:
            eye_aperture = round(max(1.0, np.random.normal(9.9, 0.4)), 2)
            mouth_stretch = round(max(1.0, np.random.normal(17.0, 0.8)), 2)
        else:
            eye_aperture = round(max(1.0, np.random.normal(10.4, 0.4)), 2)
            mouth_stretch = round(max(1.0, np.random.normal(18.0, 0.8)), 2)
        
    if model is None or le is None:
        # Fallback to rules if model is absent
        is_high_fb = (wpm < 30 or errors > 5)
        is_medium_fb = (wpm < 40 and not is_high_fb)
        fallback_level = "HIGH" if is_high_fb else "MEDIUM" if is_medium_fb else "LOW"
        reasoning_fallback = ["Model binaries not found, using rule fallback"]
        if face_active:
            reasoning_fallback.append("Live gaze tracking active via webcam")
        else:
            reasoning_fallback.append("Webcam inactive/no face detected; using simulated physical fallback")
        return fallback_level, 0.90, reasoning_fallback, eye_aperture, mouth_stretch
        
    # Model expects feature columns in order: ['wpm', 'errors', 'session_duration', 'eye_aperture', 'mouth_stretch']
    features = np.array([[wpm, errors, session_duration, eye_aperture, mouth_stretch]])
    
    try:
        # Predict label
        pred_encoded = model.predict(features)[0]
        pred_label = le.inverse_transform([pred_encoded])[0]
        
        # Predict confidence score
        probs = model.predict_proba(features)[0]
        confidence = float(probs[pred_encoded])
        
        # Explainable reasoning points
        reasoning = []
        if face_active:
            reasoning.append("Live gaze tracking active via webcam")
        else:
            reasoning.append("Webcam inactive/no face detected; using simulated physical fallback")
            
        if wpm < 30:
            reasoning.append(f"Typing speed is slow ({round(wpm)} WPM)")
        elif wpm < 45:
            reasoning.append(f"Typing speed is moderate ({round(wpm)} WPM)")
        else:
            reasoning.append(f"Typing speed is active ({round(wpm)} WPM)")
            
        if errors > 5:
            reasoning.append(f"Correction rate is high ({errors} backspaces)")
            
        if eye_aperture < 9.5:
            reasoning.append(f"Eye aperture is narrow ({eye_aperture}) - indicators of drowsiness")
        else:
            reasoning.append(f"Eye aperture is wide ({eye_aperture}) - active gaze")
            
        if mouth_stretch > 22 or mouth_stretch < 14:
            reasoning.append(f"Mouth movement shows potential yawn activity ({mouth_stretch})")
            
        if session_duration > 600:
            reasoning.append("Continuous keyboard session exceeds 10 minutes")
            
        return pred_label.upper(), round(confidence, 2), reasoning, eye_aperture, mouth_stretch
    except Exception as e:
        print(f"[ML INFERENCE ERROR] Failed to run prediction: {e}")
        is_high_fb = (wpm < 30 or errors > 5)
        is_medium_fb = (wpm < 40 and not is_high_fb)
        fallback_level = "HIGH" if is_high_fb else "MEDIUM" if is_medium_fb else "LOW"
        return fallback_level, 0.50, [f"Inference error: {e}"], eye_aperture, mouth_stretch
