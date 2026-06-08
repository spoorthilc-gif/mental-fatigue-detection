# Production Deployment QA Checklist — FatigueAI

This document provides structured quality assurance procedures for validating deployed instances of **FatigueAI** (Render / Railway).

---

## 🛠️ Verification Protocols

### 1. SSL/TLS Verification
*   **Action**: Navigate to the HTTPS version of the deployed app domain (e.g. `https://fatigue-ai.onrender.com`).
*   **Checks**:
    - Verify that the browser indicates a secure connection (valid SSL certificate).
    - Ensure any attempts to access `http://` redirect automatically to `https://`.

### 2. Startup Log Inspection
*   **Action**: Open the Render/Railway service deployment dashboard and inspect the runtime startup logs.
*   **Checks**:
    - Verify the system validation status table prints cleanly to the log terminal.
    - Confirm the Random Forest Ensemble joblib file loaded successfully:
      `[ML] Loaded validated Random Forest model from...`
    - Verify that no ImportError or package resolution warnings are present.
    - If camera hardware is not available on the cloud container (normal behavior), verify the system falls back gracefully to typing heuristics without exiting:
      `[SYSTEM WARNING] Webcam offline or locked. Bypassing webcam tracker thread startup.`

### 3. Recruiter Demonstration Bypass
*   **Action**: Open the landing page and click the **🎯 Recruiter Demo Access** CTA.
*   **Checks**:
    - Verify that you are directly authenticated as user `demo` without credentials prompting.
    - Ensure a glassmorphic success toast alert displays: `"Successfully logged in as demo user!"`.
    - Verify that user profile displays `demo` in the navbar.

### 4. Telemetry Endpoint Status Codes
*   **Action**: While logged in, open browser dev tools (network tab) and verify response status codes.
*   **Checks**:
    - `/api/stats` -> `200 OK`
    - `/api/fatigue` -> `200 OK`
    - `/api/predict-fatigue` -> `200 OK`
    - `/api/explain` -> `200 OK`
    - `/api/logs` -> `200 OK`
    - `/api/webcam-status` -> `200 OK` (Should return `is_active: false` indicating webcam is offline on cloud, which triggers the premium webcam offline card overlay).

### 5. CSV Telemetry Exporting
*   **Action**: Navigate to the dashboard and click the **📥 Export Dataset** button in the navbar.
*   **Checks**:
    - Verify that a file download triggers immediately (`fatigue_session_dataset.csv`).
    - Verify that the downloaded file contains the correct 12 headers and reflects logs recorded during the active session.

### 6. Session Purges
*   **Action**: Click the **Reset Session** button in the navbar, then confirm the prompt.
*   **Checks**:
    - Verify a toast notification confirms: `"Session analytics reset successfully"`.
    - Verify that stats cards reset to `0`, graphs clear, and the logs table displays the custom empty-state placeholder.
