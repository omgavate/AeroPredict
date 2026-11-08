# AeroPredict - Installation & Deployment Guide

This guide provides step-by-step setup instructions to run the **AeroPredict** platform locally on Windows, macOS, or Linux.

---

## 1. Required Software & Prerequisites

Before beginning, ensure the following software packages are installed on your machine:

| Software | Minimum Version | Recommended Version | Download / Check Command |
| :--- | :--- | :--- | :--- |
| **Node.js & npm** | Node v18.0.0+ | Node v24 LTS | `node -v` & `npm -v` |
| **Python** | Python 3.10+ | Python 3.13 | `python --version` |
| **MySQL Server** | MySQL 8.0+ | MySQL 8.0.45+ | `mysql --version` |
| **Git** | v2.30+ | Latest | `git --version` |

---

## 2. Repository & Dataset Verification

### 2.1 Verify Repository Structure
Ensure the project is cloned/located in your working directory (e.g. `d:\Aeropredict`):
```powershell
cd d:\Aeropredict
```

### 2.2 Dataset Location
The NASA C-MAPSS FD001 dataset files must reside inside the `dataset/` directory:
- `dataset/train_FD001.txt` (20,631 records, 100 engines run to failure)
- `dataset/test_FD001.txt` (13,096 records, 100 engines truncated)
- `dataset/RUL_FD001.txt` (100 ground-truth remaining life cycles)

Verify dataset presence via PowerShell:
```powershell
Get-ChildItem -Path d:\Aeropredict\dataset
```

---

## 3. MySQL Database Setup

### 3.1 Create Database
Start MySQL Server (service `MySQL80` or via MySQL Workbench) and create the database:
```sql
CREATE DATABASE IF NOT EXISTS aeropredict_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

### 3.2 Automated Schema & Seed Ingestion
The backend automatically creates all required tables and seeds initial fleet assets and work orders on first startup. Alternatively, you can inspect the full DDL script in [`DATABASE_SCHEMA.md`](file:///d:/Aeropredict/DATABASE_SCHEMA.md).

---

## 4. Backend Setup & Configuration

### 4.1 Create & Activate Virtual Environment
```powershell
cd d:\Aeropredict\backend

# Create virtual environment
python -m venv venv

# Activate on Windows PowerShell:
.\venv\Scripts\Activate.ps1

# (On Linux / macOS: source venv/bin/activate)
```

### 4.2 Install Python Dependencies
```powershell
pip install -r requirements.txt
```

### 4.3 Configure Environment Variables
Create a `.env` file inside the `backend/` directory (`backend/.env`):
```ini
# Flask Environment
FLASK_APP=app.py
FLASK_ENV=development
FLASK_DEBUG=1
PORT=5000

# MySQL Database Connection
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password_here
DB_NAME=aeropredict_db
DB_POOL_NAME=aeropredict_pool
DB_POOL_SIZE=5

# CORS Whitelist (Optional)
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000
```

---

## 5. Machine Learning Model Artifacts

Pre-trained production artifacts are saved inside `ml_model/artifacts/`:
- `random_forest_rul_model.joblib`: Trained Random Forest regressor (100 estimators).
- `scaler.joblib`: Pre-fitted StandardScaler.
- `feature_names.joblib`: Serialized list of 45 causal rolling features.
- `model_metadata.json`: Model hyperparameters and verified metrics.

### Optional: Retrain Model from Scratch
If you wish to retrain the model on the C-MAPSS dataset:
```powershell
cd d:\Aeropredict
backend\venv\Scripts\python ml_model/train.py
```
This executes the 5-fold GroupKFold cross-validation, evaluates test engines, and writes updated artifacts into `ml_model/artifacts/`.

---

## 6. Frontend Setup & Configuration

### 6.1 Install Node Dependencies
```powershell
cd d:\Aeropredict\frontend
npm install
```

### 6.2 Frontend Environment Variables (Optional)
By default, the frontend connects to `http://localhost:5000/api`. To customize, create `frontend/.env`:
```ini
VITE_API_URL=http://localhost:5000/api
```

---

## 7. Starting the Application

To run the complete system, launch the backend and frontend in separate terminals:

### Terminal 1: Start Backend API Server
```powershell
cd d:\Aeropredict\backend
.\venv\Scripts\Activate.ps1
python app.py
```
*Output: `✈️ Starting AeroPredict API Server on http://localhost:5000`*

### Terminal 2: Start Frontend Vite Client
```powershell
cd d:\Aeropredict\frontend
npm run dev
```
*Output: `VITE v6.1.0 ready in 250 ms ➜ Local: http://localhost:5173/`*

Open your browser and navigate to **`http://localhost:5173/`**.

---

## 8. Verification & Running Test Suites

### Run Automated Backend Tests (50 Tests)
```powershell
cd d:\Aeropredict
backend\venv\Scripts\python -m unittest discover -s backend/tests -p "test_*.py" -v
```
*Expected: `Ran 50 tests in ~2.3s ... OK (100% passing)`*

### Run Technical Audits
```powershell
# Run Database Schema Audit
backend\venv\Scripts\python backend/tests/db_audit.py

# Run Machine Learning Empirical Audit
backend\venv\Scripts\python ml_model/audit_ml.py

# Run E2E Lifecycle Workflow Test
backend\venv\Scripts\python backend/tests/test_e2e_workflow.py
```

### Run Frontend Production Build
```powershell
npm run build --prefix frontend
```
*Expected: `✓ built in ~3.8s with 0 errors`*

---

## 9. Troubleshooting Common Issues

1. **MySQL Connection Refused (`Error 2003`):**
   - Ensure the MySQL service is running: Open Windows Services (`services.msc`) and verify `MySQL80` is running.
   - Verify credentials in `backend/.env`.
2. **Port 5000 in Use:**
   - Change `PORT=5001` in `backend/.env` and update `VITE_API_URL=http://localhost:5001/api` in `frontend/.env`.
3. **PowerShell Execution Policy Error:**
   - If virtual environment activation is blocked, execute:
     `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
4. **Vite Offline Fallback Mode:**
   - If the backend is not yet started, the frontend displays a yellow badge: `Local Cached Dataset`. Once Flask is running, click **Sync** to switch to `Database Connected`.
