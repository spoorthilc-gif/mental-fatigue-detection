import os
from datetime import datetime

LOG_FILE = os.path.join('database', 'tracker.log')

def log_event(level, message):
    """Write a timestamped diagnostic message to database/tracker.log."""
    try:
        os.makedirs('database', exist_ok=True)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_line = f"[{timestamp}] [{level.upper()}] {message}\n"
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_line)
    except Exception as e:
        print(f"[LOGGER ERROR] Failed to write log: {e}")
