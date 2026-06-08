# Recruiter Demonstration Script — FatigueAI

This script guides you through demonstrating **FatigueAI** to recruiters, showcasing its premium UI, real-time biometrics tracking, machine learning models, and production-grade features.

---

## 🎬 Act 1: The Landing Page & Authentication
1.  **Welcome Landing Page**:
    *   *Action*: Navigate to the root URL `/`.
    *   *Talking Point*: *"Welcome to FatigueAI. The entry page is a premium, glassmorphic marketing landing page designed to explain the project architecture, features, and tech stack. It features custom typing animations and dynamic scroll reveals."*
2.  **Authentication & Recruiter Login**:
    *   *Action*: Hover over the buttons. Click **🎯 Recruiter Demo Access**.
    *   *Talking Point*: *"Instead of forcing recruiters to fill out sign-up forms, I built a direct Recruiter Demo Access route. Clicking this button automatically signs us in as the pre-seeded recruiter demo account (`demo`/`demo123`), triggers a success toast, and routes us to the protected dashboard."*

---

## 🎬 Act 2: Real-Time Telemetry & The Dashboard
3.  **Real-Time Statistics**:
    *   *Action*: Point to the numeric cards (Typing Speed, Backspace Errors, Session Time, Characters Typed).
    *   *Talking Point*: *"The dashboard updates at 1-second intervals. As I begin typing in any window, the background pynput hook registers key events and updates WPM speed and error rates using smooth sliding numbers."*
4.  **Threaded Webcam Physiological Tracking**:
    *   *Action*: Show the Live Webcam Feed card. Yawn or blink to trigger the counters.
    *   *Talking Point*: *"We run a dedicated, lock-protected computer vision thread that uses MediaPipe FaceMesh to extract 468 facial landmark coordinates. It calculates vertical eyelid aperture (EAR) and mouth stretch (MAR) ratios to track blinks and yawns. If the webcam is offline or locked, it displays a premium offline overlay without blocking the rest of the application."*

---

## 🎬 Act 3: Explainable AI & Machine Learning
5.  **Multi-Class Ensemble Model**:
    *   *Action*: Point to the ML Fatigue Prediction Card.
    *   *Talking Point*: *"On the right is our Random Forest Classifier. It co-trains keystroke variables with webcam landmarks to predict fatigue states (LOW/MEDIUM/HIGH). It calculates classification confidence and explains the physical triggers under ML Reasoning."*
6.  **Explainable AI (XAI)**:
    *   *Action*: Point to the XAI panel.
    *   *Talking Point*: *"The rules-based Explainable AI system computes concentration ratios and productivity indexes. It outputs clear verbal diagnostics explaining the physical and behavioral indicators of fatigue."*

---

## 🎬 Act 4: Advanced Reports & Exporters
7.  **Research-Grade Analytics**:
    *   *Action*: Click the **🔬 Research Report** button in the navbar.
    *   *Talking Point*: *"Clicking the Research Report opens a detailed data analysis modal. Here, the system calculates Pearson Correlation Coefficients ($r$) in real time to prove correlations between typing speeds or blink rates and fatigue levels. It also displays percentages of dataset fatigue distributions."*
8.  **Standard Dataset Exporter**:
    *   *Action*: Click **Download CSV Dataset**.
    *   *Talking Point*: *"We can export the user's isolated logs as a standard CSV format dataset. This downloads the complete, serialized telemetry history, ready for ML training notebooks."*

---

## 🎬 Act 5: Recruiter Presentation Mode
9.  **Presentation View**:
    *   *Action*: Click **📺 Presentation Mode** in the navbar.
    *   *Talking Point*: *"Finally, to optimize presentation layout for large displays or mobile devices, I built a Recruiter Presentation Mode. Clicking this hides debugging logs, expands line charts to full width, stretches camera video streams, and refits Chart.js layouts."*
10. **Clean Sign-Out**:
    *   *Action*: Click **🚪 Logout**.
    *   *Talking Point*: *"Logging out safely destroys the session and redirects back to the login page."*
