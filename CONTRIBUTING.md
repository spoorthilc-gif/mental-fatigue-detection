# Contributing to FatigueAI

First off, thank you for considering contributing to FatigueAI! It is people like you who make FatigueAI such a premium open-source tool.

---

## 🛠️ Local Development Setup

To contribute to this project, follow the setup instructions below to prepare your developer workspace:

1.  **Fork and Clone**:
    Clone the repository to your local system:
    ```bash
    git clone https://github.com/your-username/mental-fatigue-detection.git
    cd mental-fatigue-detection
    ```

2.  **Environment Settings**:
    *   Initialize a virtual environment (`python -m venv venv`) and activate it.
    *   Install dependencies: `pip install -r requirements.txt`.
    *   Create a local configuration `.env` file from the example configuration:
        ```bash
        cp .env.example .env
        ```

3.  **Local Startup checks**:
    Run the validation diagnostics before coding:
    ```bash
    python app.py
    ```

---

## 📝 Contribution Workflow

To make code changes:

1.  **Create a Feature Branch**:
    Name branches descriptively based on your edits:
    ```bash
    git checkout -b feature/optimize-model-inference
    ```

2.  **Coding Standards**:
    *   Write clean, documented Python code adhering to PEP 8 standard constraints.
    *   Ensure any new client-side javascript handles animations, Glassmorphism colors, and Chart.js resizing rules appropriately.
    *   Keep template markups responsive across mobile and desktop viewport sizes.

3.  **Commit Messages**:
    Use structured, clear commit messages prefixing issues or feature scopes:
    ```bash
    git commit -m "feat(telemetry): optimized polling cache to bypass idle redraws"
    ```

4.  **Open a Pull Request**:
    Open a Pull Request against the `main` branch. Provide detailed descriptions of features modified, validation checklists, and attachments of any screenshot/recording UI transitions.
