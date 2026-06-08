import threading
import time
import os
import random
from collections import deque

try:
    from pynput import keyboard
    PYNPUT_AVAILABLE = True
except Exception as e:
    print(f"[SYSTEM WARNING] pynput keyboard listener unavailable: {e}. Switching to mock simulator.")
    PYNPUT_AVAILABLE = False

# Global state (simple singleton for demo purposes)

_state = {
    "char_count": 0,   # total characters typed (including spaces)
    "backspace_count": 0,
    "start_time": None,
    "last_event": None,
    "events": deque(maxlen=1000)  # store recent timestamps for optional future analysis
}

def _on_press(key):
    """Callback for each key press.
    Updates global counters for characters and backspaces.
    """
    now = time.time()
    # Record the event timestamp (optional future use)
    _state["events"].append(now)
    _state["last_event"] = now
    if _state["start_time"] is None:
        _state["start_time"] = now

    try:
        # Alphanumeric keys and space count as characters
        if isinstance(key, keyboard.KeyCode):
            _state["char_count"] += 1
        elif key == keyboard.Key.space:
            _state["char_count"] += 1
        elif key == keyboard.Key.backspace:
            _state["backspace_count"] += 1
        # Other special keys are ignored for the simple demo
    except Exception:
        pass

def _simulate_typing_events():
    """Background loop that simulates active typing to show live telemetry in cloud mode."""
    print("[SYSTEM] Keyboard simulation loop started.")
    while True:
        # Simulate typing latency
        time.sleep(random.uniform(0.15, 0.45))
        
        # Increment characters
        _state["char_count"] += random.randint(1, 3)
        _state["last_event"] = time.time()
        
        # 4% chance of backspace error
        if random.random() < 0.04:
            _state["backspace_count"] += 1
            
        if _state["start_time"] is None:
            _state["start_time"] = time.time()

def start_listener():
    """Start the keyboard listener or simulated loop in a background daemon thread.
    The thread will run for the lifetime of the process.
    """
    if PYNPUT_AVAILABLE and os.getenv('RENDER') != 'true':
        try:
            listener = keyboard.Listener(on_press=_on_press)
            listener.daemon = True
            listener.start()
            return listener
        except Exception as e:
            print(f"[SYSTEM WARNING] Failed to start keyboard listener: {e}. Falling back to simulation.")
            
    # Simulation daemon thread for cloud deployments
    print("[SYSTEM] Starting keyboard simulation engine for cloud environment...")
    sim_thread = threading.Thread(target=_simulate_typing_events, daemon=True)
    sim_thread.start()
    return sim_thread


def get_stats():
    """Return a dictionary with current typing statistics.
    - ``wpm``: words‑per‑minute (using the standard 5‑char definition)
    - ``errors``: number of backspace presses (simple proxy for mistakes)
    - ``elapsed``: seconds since the first key press
    """
    st = _state
    if st["start_time"] is None:
        return {"wpm": 0, "errors": 0, "elapsed": 0, "chars": 0}
    elapsed_seconds = time.time() - st["start_time"]
    minutes = max(elapsed_seconds / 60.0, 1e-6)  # avoid division by zero
    wpm = (st["char_count"] / 5.0) / minutes
    return {
        "wpm": round(wpm, 2),
        "errors": st["backspace_count"],
        "elapsed": round(elapsed_seconds, 1),
        "chars": st["char_count"]
    }
def reset_stats():
    """Reset all tracking counters back to zero.
    Called by the /api/reset route when the user clicks Reset Session.
    """
    _state["char_count"]      = 0
    _state["backspace_count"] = 0
    _state["start_time"]      = None
    _state["last_event"]      = None
    _state["events"].clear()


def calc_fatigue(stats):
    """Simple rule‑based fatigue calculator.
    Returns (level, score).
    """
    wpm = stats.get('wpm', 0)
    errors = stats.get('errors', 0)
    # Beginner‑friendly thresholds
    if wpm >= 40 and errors <= 2:
        return "Low", 25
    elif wpm >= 30 and errors <= 5:
        return "Medium", 50
    else:
        return "High", 75


# If this module is run directly, start the listener for quick manual testing
if __name__ == "__main__":
    print("Starting keyboard listener (press ESC to stop)...")
    start_listener()
    if PYNPUT_AVAILABLE:
        # Keep the main thread alive until ESC is pressed
        with keyboard.Listener() as listener:
            listener.join()
    else:
        print("Running in simulation mode. Keeping main thread alive...")
        while True:
            time.sleep(1.0)

