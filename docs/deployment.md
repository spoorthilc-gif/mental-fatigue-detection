# Deployment Guide — FatigueAI

This document provides comprehensive guides to deploying the **FatigueAI** platform on cloud web service environments.

---

## 🚀 Render Deployment Setup

Render is the recommended hosting platform for FatigueAI as it reads standard python environments and deployment commands automatically.

### 1. Connect GitHub Repository
- Create a free account on [Render](https://render.com/).
- Click **New +** and select **Web Service**.
- Connect your GitHub repository.

### 2. Configure Service Settings
- **Name**: `fatigue-ai`
- **Region**: Select region closest to your traffic.
- **Branch**: `main`
- **Runtime**: `Python 3`
- **Build Command**:
  ```bash
  pip install -r requirements.txt
  ```
- **Start Command**:
  ```bash
  gunicorn app:app
  ```

### 3. Add Environment Variables
Navigate to the **Environment** tab inside your Render web service and add the following keys:
*   `SECRET_KEY`: `your_random_secret_production_key_string`
*   `FLASK_DEBUG`: `False` (Disables debugging modes)
*   `DATABASE_URL`: `sqlite:///database/fatigue_analytics.db` (Default database path)

---

## 🚂 Railway Deployment Setup

Railway serves as an excellent deployment alternative that automatically detects the `Procfile` at the repository root.

### 1. Start a New Project
- Create an account on [Railway](https://railway.app/).
- Click **New Project** and select **Deploy from GitHub repo**.
- Select the `mental-fatigue-detection` repository.

### 2. Configure Settings
- Railway automatically detects the Python environment and reads the `Procfile`:
  ```
  web: gunicorn app:app
  ```
- Navigate to the **Variables** tab and add the environment variables (`SECRET_KEY`, `FLASK_DEBUG`, and `DATABASE_URL`).

### 3. Deploy
- Railway builds and deploys your service. Click **Generate Domain** in the settings to expose the app online.
