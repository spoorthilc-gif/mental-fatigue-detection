# FatigueAI — Final QA Validation Checklist

This document details the quality assurance validation checklists designed to verify the deployment-ready, recruiter-grade components of the **FatigueAI** platform.

---

## 1. Authentication & Session Security Flow
- [ ] **Direct Welcome Navigation**:
  - Visit `/` in an unauthenticated session. Verify the premium glassmorphic intro loader runs and fades out cleanly.
  - Verify that the hero section typing animations and metrics card reveal slide-ins behave smoothly.
- [ ] **Recruiter Demo Access**:
  - Click the **🎯 Recruiter Demo Access** CTA on the Welcome page.
  - Verify that you are instantly redirected to `/dashboard` as the seeded `demo` account.
  - Verify that a glassmorphic success toast sliding up from the bottom right flashes: `"Successfully logged in as demo user!"`.
- [ ] **Manual Authentication**:
  - Access `/login`. Enter incorrect credentials; verify the sliding toast alert displays the corresponding auth errors.
  - Test registration at `/register`. Register a new account, check validation rules, and ensure successful redirects to `/login`.
- [ ] **Protected Routes**:
  - Log out and attempt to access `/dashboard` or `/api/stats` directly. Verify the middleware returns a `401 Unauthorized` redirect (or routes back to `/login` smoothly).

---

## 2. Real-Time Telemetry & Metric Polling
- [ ] **Keyboard Telemetry Tracking**:
  - Open a text editor (or click on the dashboard and type in other windows). Verify the keystroke listener logs character counts, elapsed seconds, WPM, and errors.
  - Verify that numerical counters (`statWpm`, `statErrors`, `statElapsed`, `statChars`) update using smooth scrolling numbers.
- [ ] **Physiological Webcam Tracking**:
  - Check the Live Webcam Feed. If a camera is present and permitted:
    - Verify face landmarks track landmarks (FPS badge lights up green).
    - Blink and yawn; verify numerical blink/yawn telemetry counters increment instantly.
  - If webcam is missing/locked:
    - Verify that the card displays the **Webcam Offline / Locked** empty-state overlay.
    - Check that the card badge shows a grey **Inactive** status.
    - Ensure a warning toast shows up on dashboard loading notifying that physiological biometrics are offline.

---

## 3. Machine Learning & Heuristics Pipelines
- [ ] **Explainable AI Heuristics**:
  - Verify the **Fatigue Level (Rule-Based)** ring score gauge shifts dynamically based on typing speed and correction rates.
  - Verify the XAI panel outputs descriptive explanations (e.g. *No fatigue indicators*, *Concentration is declining*).
- [ ] **Multimodal Random Forest predictions**:
  - Verify the **Fatigue Prediction (Machine Learning)** ring score tracks and shows confidence levels (e.g. *87%*).
  - Verify that ML reasoning logs physical/behavioral details (e.g. *High correction rate*, *Drowsiness indicators*).
- [ ] **History Charts & Dynamic Switching**:
  - Click on the glassmorphic tab selector on the Fatigue Score History card.
  - Verify switching between **Fatigue Score**, **Blinks & Yawns**, **ML Confidence**, and **Productivity & Concentration** charts renders and animations smoothly.
  - Verify connecting lines use HSL tailored color schemes corresponding to low/medium/high thresholds.

---

## 4. UI Polish, Modal Interactivity & Themes
- [ ] **Toast Notifications**:
  - Trigger resets or dataset exports. Verify alerts stack beautifully and auto-dismiss after 4 seconds.
- [ ] **Break Alert Interactivity**:
  - Simulate high fatigue or manually wait for a high-fatigue transition. Verify the red high fatigue modal displays.
  - Click **Snooze 5 Min**; verify it hides and does not re-display for 5 minutes.
  - Click **Got It!**; verify it dismisses.
- [ ] **Research Analytics Modal**:
  - Click the **🔬 Research Report** button in the navbar.
  - Verify that the modal displays total dataset samples, Pearson correlations, and ML classification distributions.
  - Verify the modal is responsive and closes cleanly using either the close button or clicking outside.
- [ ] **Theme Switching**:
  - Click the moon/sun theme toggle button.
  - Verify the dark-theme and light-theme classes propagate across all charts, tables, cards, and modal components.
  - Ensure that canvas backgrounds and gridlines reload cleanly without layout breaks.

---

## 5. Recruiter Presentation Mode
- [ ] **Presentation View Layout**:
  - Click **📺 Presentation Mode** in the navbar.
  - Verify the debug panels (logs table, XAI logs list) collapse cleanly.
  - Verify the webcam card, ML prediction ring, and line charts dynamically expand and scale to fill the screen.
  - Click **Exit Presentation** to verify the restoration of the multi-modal analytics layout.

---

## 6. Build & Deployment Optimization
- [ ] **Environment Seeding**:
  - Verify that `.env` is loaded by looking at Flask logs on boot.
  - Verify `gunicorn` starts production processes when executing `Procfile`.
- [ ] **Diagnostic Checks**:
  - Call `/api/diagnostics`. Verify standard startup checks are running and outputting complete hardware, model, and database operational specs.
