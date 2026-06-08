import os
import sqlite3
import csv
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv('DATABASE_URL', os.path.join('database', 'fatigue_analytics.db'))
CSV_DIR = os.path.join('dataset', 'behavioral_data')
CSV_PATH = os.path.join(CSV_DIR, 'live_behavior_dataset.csv')

def init_storage():
    """Ensure database and CSV storage structures exist and are initialized."""
    # 1. Initialize SQLite Database
    os.makedirs('database', exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create users table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Check if session_logs table exists and verify schema columns
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='session_logs'")
    table_exists = cursor.fetchone()
    
    if table_exists:
        cursor.execute("PRAGMA table_info(session_logs)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'blink_count' not in columns:
            print("[DB] Outdated database schema detected. Dropping session_logs table to migrate...")
            cursor.execute("DROP TABLE session_logs")
            conn.commit()
        elif 'user_id' not in columns:
            print("[DB] Adding user_id foreign key column to session_logs...")
            cursor.execute("ALTER TABLE session_logs ADD COLUMN user_id INTEGER REFERENCES users(id)")
            conn.commit()
            
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS session_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            wpm REAL,
            errors INTEGER,
            session_duration REAL,
            fatigue_score INTEGER,
            fatigue_level TEXT,
            productivity_score REAL,
            blink_count INTEGER,
            yawn_count INTEGER,
            predict_level TEXT,
            predict_confidence REAL,
            concentration_score REAL,
            user_id INTEGER REFERENCES users(id)
        )
    ''')
    
    # Seed demo user dynamically
    cursor.execute("SELECT id FROM users WHERE username = 'demo'")
    if not cursor.fetchone():
        from werkzeug.security import generate_password_hash
        demo_pass_hash = generate_password_hash('demo123')
        try:
            cursor.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                ('demo', 'demo@fatigueai.ai', demo_pass_hash)
            )
            conn.commit()
            print("[DB] Seeded demo user account (demo / demo123)")
        except Exception as e:
            print(f"[DB ERROR] Failed to seed demo user: {e}")
            
    conn.close()

    # 2. Initialize Global CSV Dataset (as fallback)
    os.makedirs(CSV_DIR, exist_ok=True)
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
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
                'concentration_score',
                'user_id'
            ])


def get_user_csv_path(user_id):
    """Get the path to a user-specific behavioral CSV dataset, initializing it if needed."""
    user_csv = os.path.join(CSV_DIR, f'live_behavior_dataset_user_{user_id}.csv')
    os.makedirs(CSV_DIR, exist_ok=True)
    if not os.path.exists(user_csv):
        with open(user_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
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
                'concentration_score',
                'user_id'
            ])
    return user_csv

def log_behavior(wpm, errors, duration, fatigue_score, fatigue_level, productivity_score, 
                 blink_count=0, yawn_count=0, predict_level="LOW", predict_confidence=1.0, concentration_score=100.0, user_id=None):
    """Save a behavioral snapshot to both SQLite and the user-specific CSV dataset."""
    init_storage()  # Safeguard directories/files

    # 1. SQLite Logging
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO session_logs (
            wpm, errors, session_duration, fatigue_score, fatigue_level, productivity_score,
            blink_count, yawn_count, predict_level, predict_confidence, concentration_score, user_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (wpm, errors, duration, fatigue_score, fatigue_level, productivity_score,
          blink_count, yawn_count, predict_level, predict_confidence, concentration_score, user_id))
    conn.commit()
    conn.close()

    # 2. CSV Logging (SAFE APPEND to user CSV if user logged in)
    if user_id is not None:
        user_csv_path = get_user_csv_path(user_id)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(user_csv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp,
                wpm,
                errors,
                duration,
                fatigue_score,
                fatigue_level,
                productivity_score,
                blink_count,
                yawn_count,
                predict_level,
                predict_confidence,
                concentration_score,
                user_id
            ])

def get_recent_logs(limit=50, user_id=None):
    """Retrieve recent records from SQLite sorted newest first for a specific user."""
    init_storage()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if user_id is not None:
        cursor.execute('SELECT * FROM session_logs WHERE user_id = ? ORDER BY id DESC LIMIT ?', (user_id, limit))
    else:
        cursor.execute('SELECT * FROM session_logs ORDER BY id DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    conn.close()

    # Format timestamp nicely (e.g. 10:15:30 PM or YYYY-MM-DD HH:MM:SS)
    result = []
    for r in rows:
        row_dict = dict(r)
        result.append(row_dict)
    return result

def clear_logs(user_id=None):
    """Clear all records from database and truncate the user-specific CSV file back to header."""
    init_storage()
    # 1. SQLite truncate for specific user
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if user_id is not None:
        cursor.execute('DELETE FROM session_logs WHERE user_id = ?', (user_id,))
    else:
        cursor.execute('DELETE FROM session_logs')
    conn.commit()
    conn.close()

    # 2. Truncate CSV back to header for specific user
    if user_id is not None:
        user_csv_path = get_user_csv_path(user_id)
        with open(user_csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
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
                'concentration_score',
                'user_id'
            ])

def run_explainable_ai(wpm, errors, duration, fatigue_score, fatigue_level, recent_logs):
    """Analyze stats history to compute productivity, concentration, trends and reasoning text."""
    # Try to import and fetch live webcam metrics
    webcam_active = False
    blink_count = 0
    yawn_count = 0
    drowsy_duration = 0.0
    try:
        from tracker.webcam_tracker import tracker
        metrics = tracker.get_metrics()
        if metrics.get("is_active") and metrics.get("face_detected"):
            webcam_active = True
            blink_count = metrics.get("blink_count", 0)
            yawn_count = metrics.get("yawn_count", 0)
            drowsy_duration = metrics.get("drowsy_duration", 0.0)
    except Exception as e:
        print(f"[XAI ERROR] Failed to fetch metrics from webcam: {e}")

    # 1. Productivity Score calculation
    # Formula uses speed and penalizes backspace error rates. Bounded between 0 and 100.
    if duration < 5 and wpm == 0:
        productivity_score = 100.0
    else:
        # Base productivity is scaled by typing speed (WPM * 2.2), with error penalties
        productivity_score = max(0.0, min(100.0, (wpm * 2.2) - (errors * 3.5)))
        # Give a small boost for active keyboard time
        if wpm > 10:
            productivity_score = min(100.0, productivity_score + 10.0)

    # 2. Concentration Score calculation
    # Focuses on typing precision (errors vs WPM keystrokes estimate)
    if wpm == 0:
        concentration_score = 100.0
    else:
        error_ratio = errors / max(1.0, wpm * 5.0)  # estimate total chars typed
        concentration_score = max(0.0, min(100.0, 100.0 - (error_ratio * 250.0)))
        # Decline slightly if working for a long continuous session
        if duration > 900:  # 15 mins
            concentration_score = max(30.0, concentration_score - min(30.0, (duration - 900) / 120.0))

    # Integrate webcam feedback into the numerical scores
    if webcam_active:
        if yawn_count > 0:
            productivity_score = max(0.0, productivity_score - yawn_count * 5.0)
            concentration_score = max(0.0, concentration_score - yawn_count * 8.0)
        if drowsy_duration > 1.0:
            # Scale penalty with drowsiness duration
            drowsy_penalty = min(30.0, drowsy_duration * 10.0)
            productivity_score = max(0.0, productivity_score - drowsy_penalty)
            concentration_score = max(0.0, concentration_score - drowsy_penalty * 1.5)

    # 3. Fatigue Trend interpretation
    trend = "STABLE"
    if len(recent_logs) >= 3:
        # Check slope of scores over the last 5 readings
        scores = [log['fatigue_score'] for log in reversed(recent_logs[:5])]
        if len(scores) >= 2:
            diff = scores[-1] - scores[0]
            if diff > 5:
                trend = "RISING"
            elif diff < -5:
                trend = "FALLING"

    # 4. Generate human-readable reasons (Explainable AI reasoning engine)
    reasons = []

    # Webcam/Visual checks
    if webcam_active:
        if drowsy_duration > 1.0:
            reasons.append(f"Prolonged eye closure detected ({drowsy_duration}s) — active sign of drowsiness")
        if yawn_count > 0:
            reasons.append(f"Yawning activity detected ({yawn_count} yawns) — indicating physical tiredness")
        if blink_count > 25:
            reasons.append(f"High blink frequency ({blink_count} blinks) — potential visual fatigue or strain")
        
        if drowsy_duration <= 1.0 and yawn_count == 0 and blink_count <= 25:
            reasons.append("Webcam feed confirms active facial gaze and standard blink patterns")
    else:
        # Check if the webcam tracker is running at all (e.g. is_active is True but face_detected is False)
        cam_active_but_no_face = False
        try:
            from tracker.webcam_tracker import tracker
            if tracker.get_metrics().get("is_active"):
                cam_active_but_no_face = True
        except:
            pass
            
        if cam_active_but_no_face:
            reasons.append("Webcam active but no face detected in the frame")
        else:
            reasons.append("Webcam tracking offline — visual fatigue diagnostics inactive")

    # Speed checks
    if len(recent_logs) >= 4:
        wpms = [log['wpm'] for log in recent_logs]
        peak_wpm = max(wpms)
        if peak_wpm > 0:
            drop_percent = ((peak_wpm - wpm) / peak_wpm) * 100
            if drop_percent >= 25:
                reasons.append(f"Typing speed dropped by {round(drop_percent)}% from peak ({round(peak_wpm)} WPM)")
    
    if wpm < 30 and wpm > 0:
        reasons.append(f"Typing speed is low ({round(wpm)} WPM) — signs of visual or cognitive fatigue")
    elif wpm == 0:
        reasons.append("No active typing detected in the current interval")

    # Error checks
    if errors > 5:
        reasons.append(f"Frequent spelling corrections detected ({errors} backspaces) — indicating decreased typing accuracy")

    # Duration and breaks
    if duration > 120:  # for testing ease or long work hours
        reasons.append(f"Active keyboard session exceeded {round(duration)} seconds without a break")

    # Concentration indicator
    if concentration_score < 70 and wpm > 0:
        reasons.append("High correction density suggests lapses in concentration")

    # Fallback default reason
    if not reasons:
        reasons.append("All physical typing traits conform to standard baseline thresholds")

    # Productivity Level mapping
    if productivity_score >= 80:
        prod_level = "EXCELLENT"
    elif productivity_score >= 50:
        prod_level = "GOOD"
    else:
        prod_level = "NEEDS BREAK"

    return {
        "productivity_score": round(productivity_score, 1),
        "productivity_level": prod_level,
        "concentration_score": round(concentration_score, 1),
        "trend": trend,
        "reasons": reasons
    }


def generate_statistical_report(user_id=None):
    """
    Generate research-grade statistical analysis from session_logs for a specific user.
    Computes summary statistics and Pearson correlation coefficients.
    """
    init_storage()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if user_id is not None:
        cursor.execute("SELECT * FROM session_logs WHERE user_id = ?", (user_id,))
    else:
        cursor.execute("SELECT * FROM session_logs")
    rows = cursor.fetchall()
    conn.close()

    total_records = len(rows)
    if total_records == 0:
        return {
            "total_records": 0,
            "avg_wpm": 0.0,
            "avg_errors": 0.0,
            "total_blinks": 0,
            "total_yawns": 0,
            "fatigue_distribution": {"LOW": 0.0, "MEDIUM": 0.0, "HIGH": 0.0},
            "correlations": {
                "wpm_vs_fatigue": 0.0,
                "blinks_vs_fatigue": 0.0
            }
        }

    wpms = []
    errors_list = []
    blinks = []
    yawns = []
    fatigue_scores = []
    predict_levels = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}

    total_wpm = 0.0
    total_errors = 0
    total_blinks = 0
    total_yawns = 0

    for r in rows:
        w = r["wpm"] if r["wpm"] is not None else 0.0
        err = r["errors"] if r["errors"] is not None else 0
        blink = r["blink_count"] if r["blink_count"] is not None else 0
        yawn = r["yawn_count"] if r["yawn_count"] is not None else 0
        fatigue = r["fatigue_score"] if r["fatigue_score"] is not None else 0
        p_lvl = r["predict_level"] if r["predict_level"] is not None else "LOW"

        p_lvl = p_lvl.upper().strip()
        if p_lvl not in predict_levels:
            predict_levels[p_lvl] = 0
        predict_levels[p_lvl] += 1

        wpms.append(w)
        errors_list.append(err)
        blinks.append(blink)
        yawns.append(yawn)
        fatigue_scores.append(fatigue)

        total_wpm += w
        total_errors += err
        total_blinks += blink
        total_yawns += yawn

    avg_wpm = round(total_wpm / total_records, 2)
    avg_errors = round(total_errors / total_records, 2)

    distribution = {}
    for lvl, count in predict_levels.items():
        distribution[lvl] = round((count / total_records) * 100, 1)

    for k in ["LOW", "MEDIUM", "HIGH"]:
        if k not in distribution:
            distribution[k] = 0.0

    def pearson_correlation(x, y):
        n = len(x)
        if n < 2:
            return 0.0
        sum_x = sum(x)
        sum_y = sum(y)
        sum_x_sq = sum(val**2 for val in x)
        sum_y_sq = sum(val**2 for val in y)
        sum_xy = sum(val_x * val_y for val_x, val_y in zip(x, y))

        numerator = n * sum_xy - sum_x * sum_y
        denominator = ((n * sum_x_sq - sum_x**2) * (n * sum_y_sq - sum_y**2)) ** 0.5
        if denominator == 0:
            return 0.0
        return round(numerator / denominator, 3)

    wpm_vs_fatigue = pearson_correlation(wpms, fatigue_scores)
    blinks_vs_fatigue = pearson_correlation(blinks, fatigue_scores)

    return {
        "total_records": total_records,
        "avg_wpm": avg_wpm,
        "avg_errors": avg_errors,
        "total_blinks": total_blinks,
        "total_yawns": total_yawns,
        "fatigue_distribution": distribution,
        "correlations": {
            "wpm_vs_fatigue": wpm_vs_fatigue,
            "blinks_vs_fatigue": blinks_vs_fatigue
        }
    }

