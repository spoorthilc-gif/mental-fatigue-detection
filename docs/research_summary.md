# Research Summary — FatigueAI

FatigueAI integrates behavioral human-computer interaction (HCI) metrics with computer vision physiological telemetry. Below is the scientific methodology and mathematical descriptions of the calculations.

---

## 👁️ Physiological Computations (Webcam)

We employ MediaPipe FaceMesh landmarks to compute structural indicators of drowsiness and physical fatigue:

### 1. Eye Aperture Ratio (EAR)
Tracks eye closure levels by calculating the ratio between the vertical eyelid distance and horizontal eye width:
$$\text{EAR} = \frac{||p_2 - p_6|| + ||p_3 - p_5||}{2 ||p_1 - p_4||}$$
*   EAR drops below `0.22` during a blink. If sustained, it indicates eye closures or micro-sleeps.

### 2. Mouth Stretch Ratio (MAR)
Tracks mouth expansion to detect yawns:
$$\text{MAR} = \frac{||p_{top} - p_{bottom}||}{||p_{left} - p_{right}||}$$
*   MAR increases significantly (exceeding `0.6`) during yawning events.

---

## ⌨️ Typing Heuristics (Behavioral)

We calculate fatigue level scoring by combining WPM decline rates with correction multipliers:

1.  **Speed Decay**: Calculates the percentage drop of current WPM against the user's historical average.
2.  **Error Accumulation**: Multiplies the WPM decay by an error penalty:
    $$\text{Penalty} = 1 + \left(\frac{\text{Corrections}}{\text{Characters Typed}} \times 10\right)$$
3.  **Fatigue Score**: Standardized onto a $0 - 100$ scale.
    - **Score <= 35**: LOW Fatigue
    - **Score <= 65**: MEDIUM Fatigue
    - **Score > 65**: HIGH Fatigue (Triggers the Break Alert Modal overlay)

---

## 📈 Statistical Analysis Methods

### 1. Pearson Correlation Coefficient ($r$)
Evaluates linear relationships between behavioral speed/physiological telemetry and the calculated fatigue score.
$$r = \frac{n \sum xy - (\sum x)(\sum y)}{\sqrt{[n \sum x^2 - (\sum x)^2][n \sum y^2 - (\sum y)^2]}}$$
- An $r$ approaching $-1$ for WPM vs. Fatigue confirms typing speed decays as fatigue levels rise.
- An $r$ approaching $+1$ for Blinks vs. Fatigue indicates a correlation between eye blinking rates and physical drowsiness.

### 2. Random Forest Ensemble
- **Architecture**: A bag of decision tree classifiers co-trained on keystroke WPM, corrective errors, EAR, MAR, yawn counts, and blink counts.
- **Robustness**: The ensemble is trained to resist sensor failure (e.g., if the webcam is inactive or locked, typing heuristics maintain classification accuracy, and vice-versa).
