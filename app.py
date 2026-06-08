import os
import time
import atexit
from flask import Flask, render_template, jsonify, Response
from flask_login import login_required, current_user
from auth import auth as auth_blueprint, init_login_manager
from tracker.keyboard_listener import start_listener, get_stats, calc_fatigue, reset_stats
from utils.analytics import init_storage, log_behavior, get_recent_logs, run_explainable_ai, clear_logs, generate_statistical_report
from utils.predict import run_ml_inference
from tracker.webcam_tracker import tracker as webcam_tracker

from utils.startup_checks import run_all_checks
from dotenv import load_dotenv

load_dotenv()

# Create Flask app instance
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'fatigueai_secure_secret_key_production_2026')

# Initialize Login Manager and register Blueprint
init_login_manager(app)
app.register_blueprint(auth_blueprint)

# Run system validation checks at startup
startup_diagnostics = run_all_checks()

# Start keyboard listener once when the app loads
start_listener()

# Start background webcam capture device loop only if webcam check succeeds
if startup_diagnostics.get("webcam_ok"):
    webcam_tracker.start()
else:
    print("[SYSTEM WARNING] Webcam offline or locked. Bypassing webcam tracker thread startup.")

# Register safe webcam release on shutdown
atexit.register(webcam_tracker.stop)

# Initialize SQLite and CSV storage
init_storage()

# Ensure the instance folder exists
os.makedirs(os.path.join(app.instance_path, 'config'), exist_ok=True)

# Tracking state for periodic logging
_last_log_time = 0
_last_logged_char_count = -1


@app.route('/')
def welcome():
    return render_template('welcome.html')


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('index.html')


@app.route('/api/diagnostics')
@login_required
def api_diagnostics():
    """Return startup checks and active diagnostics metrics."""
    webcam_metrics = {}
    try:
        webcam_metrics = webcam_tracker.get_metrics()
    except Exception as e:
        webcam_metrics = {"error": str(e)}
        
    return jsonify({
        "status": "ok",
        "startup_validation": startup_diagnostics,
        "runtime_diagnostics": {
            "webcam_active": webcam_tracker.is_active,
            "webcam_metrics": webcam_metrics,
            "pid": os.getpid(),
            "timestamp": time.time()
        }
    })


@app.route('/api/stats')
@login_required
def api_stats():
    """Return live typing statistics as JSON."""
    return jsonify(get_stats())


@app.route('/api/fatigue')
@login_required
def api_fatigue():
    """Return fatigue level based on current stats."""
    global _last_log_time, _last_logged_char_count
    stats = get_stats()
    level, score = calc_fatigue(stats)

    # ── Auto behavioral logging (every 10s if active key events occur) ──
    now = time.time()
    char_count = stats.get('chars', 0)
    if now - _last_log_time >= 10.0:
        if char_count != _last_logged_char_count or _last_logged_char_count == -1:
            recent_logs = get_recent_logs(limit=5, user_id=current_user.id)
            wpm = stats.get('wpm', 0.0)
            errors = stats.get('errors', 0)
            duration = stats.get('elapsed', 0.0)

            xai_data = run_explainable_ai(wpm, errors, duration, score, level, recent_logs)
            prod_score = xai_data["productivity_score"]
            conc_score = xai_data["concentration_score"]

            # Run ML inference to get predicted level and confidence
            ml_level, ml_conf, ml_reasons, eye_ap, mouth_st = run_ml_inference(wpm, errors, duration)

            # Get webcam metrics
            webcam_metrics = webcam_tracker.get_metrics()
            blinks = webcam_metrics.get("blink_count", 0)
            yawns = webcam_metrics.get("yawn_count", 0)

            # Save full behavioral snapshot
            log_behavior(
                wpm=wpm,
                errors=errors,
                duration=duration,
                fatigue_score=score,
                fatigue_level=level,
                productivity_score=prod_score,
                blink_count=blinks,
                yawn_count=yawns,
                predict_level=ml_level,
                predict_confidence=ml_conf,
                concentration_score=conc_score,
                user_id=current_user.id
            )
            _last_log_time = now
            _last_logged_char_count = char_count

    return jsonify({"fatigue": level, "score": score})


@app.route('/api/predict-fatigue')
@login_required
def api_predict_fatigue():
    """Predict fatigue level in real-time using the trained ML model."""
    stats = get_stats()
    wpm = stats.get('wpm', 0.0)
    errors = stats.get('errors', 0)
    duration = stats.get('elapsed', 0.0)
    
    level, confidence, reasoning, eye_aperture, mouth_stretch = run_ml_inference(wpm, errors, duration)
    
    return jsonify({
        "fatigue_level": level,
        "confidence": confidence,
        "reasoning": reasoning,
        "eye_aperture": eye_aperture,
        "mouth_stretch": mouth_stretch
    })


@app.route('/api/webcam-status')
@login_required
def api_webcam_status():
    """Return status and active metrics of the webcam tracker."""
    return jsonify(webcam_tracker.get_metrics())


@app.route('/video_feed')
@login_required
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    import cv2
    import numpy as np
    
    def gen_frames():
        while True:
            frame = webcam_tracker.get_frame()
            if frame is None:
                # 640x480 black image with a message
                blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(blank_frame, "Camera Stream Off", (160, 240),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (122, 131, 153), 2)
                ret, buffer = cv2.imencode('.jpg', blank_frame)
                frame_bytes = buffer.tobytes()
            else:
                ret, buffer = cv2.imencode('.jpg', frame)
                frame_bytes = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.04)
            
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/api/logs')
@login_required
def api_logs():
    """Return the recent session logs from SQLite."""
    return jsonify(get_recent_logs(limit=50, user_id=current_user.id))


@app.route('/api/explain')
@login_required
def api_explain():
    """Calculate and return Explainable AI fatigue reasoning."""
    stats = get_stats()
    level, score = calc_fatigue(stats)
    wpm = stats.get('wpm', 0.0)
    errors = stats.get('errors', 0)
    duration = stats.get('elapsed', 0.0)

    recent_logs = get_recent_logs(limit=50, user_id=current_user.id)
    xai_data = run_explainable_ai(wpm, errors, duration, score, level, recent_logs)
    return jsonify(xai_data)


@app.route('/api/research-report')
@login_required
def api_research_report():
    """Return research-grade statistical analysis calculations in JSON."""
    report = generate_statistical_report(user_id=current_user.id)
    return jsonify(report)


@app.route('/api/export-csv')
@login_required
def api_export_csv():
    """Stream all recorded session logs from SQLite as a downloadable CSV file."""
    import sqlite3
    import io
    import csv
    
    def generate():
        headers = [
            'timestamp',
            'wpm',
            'errors',
            'session_duration',
            'fatigue_score',
            'fatigue_level',
            'productivity_score',
            'blink_count',
            'yawn_count',
            'predict_level',
            'predict_confidence',
            'concentration_score'
        ]
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)
        
        from utils.analytics import DB_PATH
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT timestamp, wpm, errors, session_duration, fatigue_score, fatigue_level, productivity_score, blink_count, yawn_count, predict_level, predict_confidence, concentration_score FROM session_logs WHERE user_id = ? ORDER BY id ASC", (current_user.id,))
        
        while True:
            rows = cursor.fetchmany(100)
            if not rows:
                break
            for row in rows:
                row_dict = dict(row)
                writer.writerow([
                    row_dict.get('timestamp', ''),
                    row_dict.get('wpm', 0.0),
                    row_dict.get('errors', 0),
                    row_dict.get('session_duration', 0.0),
                    row_dict.get('fatigue_score', 0),
                    row_dict.get('fatigue_level', 'LOW'),
                    row_dict.get('productivity_score', 100.0),
                    row_dict.get('blink_count', 0),
                    row_dict.get('yawn_count', 0),
                    row_dict.get('predict_level', 'LOW'),
                    row_dict.get('predict_confidence', 1.0),
                    row_dict.get('concentration_score', 100.0)
                ])
                yield output.getvalue()
                output.seek(0)
                output.truncate(0)
                
        conn.close()

    response = Response(generate(), mimetype='text/csv')
    response.headers.set("Content-Disposition", "attachment", filename="fatigue_session_dataset.csv")
    return response


@app.route('/api/reset', methods=['POST'])
@login_required
def api_reset():
    """Reset all typing stats to zero.
    Called by the frontend Reset Session button.
    Returns a confirmation JSON so the JS can clear charts too.
    """
    global _last_log_time, _last_logged_char_count
    reset_stats()
    _last_log_time = 0
    _last_logged_char_count = -1
    clear_logs(user_id=current_user.id)
    # Reset webcam tracker counters
    try:
        webcam_tracker.reset_counts()
    except Exception as e:
        print(f"[RESET ERROR] Failed to reset webcam counters: {e}")
    return jsonify({"status": "ok", "message": "Session reset successfully"})


if __name__ == '__main__':
    debug_val = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    print(f"Starting Flask server at http://127.0.0.1:5000 (debug={debug_val})")
    app.run(host='127.0.0.1', port=5000, debug=debug_val)
