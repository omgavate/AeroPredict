# AeroPredict - Installation & Deployment Guide

This guide provides step-by-step instructions to set up, configure, and execute the **AeroPredict** platform on Windows, macOS, or Linux.

---

## 1. Prerequisites

Ensure the following tools are installed on your workstation:

| Component | Minimum Version | Verified Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Node.js & npm** | Node v18+ | Node v20 / v22+ | Frontend runtime & package manager |
| **Python** | Python 3.10+ | Python 3.11 / 3.12 / 3.13 | Backend API & Machine Learning engine |
| **MySQL Server** | MySQL 8.0+ | MySQL 8.0 / 8.4 / MariaDB 10.6+ | Relational persistence & telemetry storage |
| **Git** | Git 2.30+ | Git 2.40+ | Version control |

---

## 2. Repository & Dataset Structure

Verify the repository contents after cloning:

```bash
git clone https://github.com/omgavate/AeroPredict.git
cd AeroPredict
```

The repository includes:
- `backend/` - Flask REST API with PyMySQL pooling and service layers.
- `frontend/` - React 18 single-page application with Vite and Tailwind CSS.
- `ml_model/` - Training scripts, validation tests, and pre-trained Random Forest model artifacts in `ml_model/artifacts/`.
- `dataset/` - NASA C-MAPSS FD001 dataset text files (`train_FD001.txt`, `test_FD001.txt`, `RUL_FD001.txt`).

---

## 3. Database Setup

### 3.1 Create Database
Open your MySQL terminal or MySQL Workbench and create the database:
```sql
CREATE DATABASE IF NOT EXISTS aeropredict_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

### 3.2 Configure Environment Variables
Inside the `backend/` folder, copy `.env.example` to `.env`:

On Windows PowerShell:
```powershell
Copy-Item backend\.env.example backend\.env
```
On Linux / macOS:
```bash
cp backend/.env.example backend/.env
```

Open `backend/.env` in your text editor and set your MySQL credentials:
```ini
# Database Connection Parameters
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_actual_mysql_password
DB_NAME=aeropredict_db
DB_POOL_NAME=aeropredict_pool
DB_POOL_SIZE=5

# Flask API Configuration
PORT=5000
FLASK_DEBUG=1
SECRET_KEY=aeropredict-secret-key-2026
```

### 3.3 Automated Schema & Demonstration Fleet Seeding
Run the seeder script to initialize all 5 tables and seed demonstration aircraft, telemetry, and work orders in a single step:

```bash
cd backend
python db/seed_data.py
```
*Output confirmation:*
```text
Step 1: Initializing database schema...
Schema: Schema successfully initialized in database 'aeropredict_db'
Step 2: Seeding initial aircraft fleet...
Aircraft registered: 6 aircraft in fleet.
Step 3: Seeding sample maintenance work orders...
Maintenance records in DB: 4
Step 4: Ensuring C-MAPSS telemetry is seeded for demonstration fleet...
  - N101AP (ID 1): 213 sensor cycles available.
  - N204AP (ID 2): 125 sensor cycles available.
  - N308AP (ID 3): 179 sensor cycles available.
  - N412AP (ID 4): 88 sensor cycles available.
  - VT-AER (ID 5): 210 sensor cycles available.
  - VT-BLR (ID 6): 64 sensor cycles available.

Database initialization and seeding complete! AeroPredict is ready.
```

---

## 4. Backend Service Startup

### 4.1 Python Virtual Environment
Inside the `backend/` directory:

On Windows:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

On Linux / macOS:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4.2 Start Flask Server
```bash
python app.py
```
The backend API is now running at `http://localhost:5000`. You can verify health via:
```bash
curl http://localhost:5000/api/health
```
*Expected response:*
```json
{
  "status": "healthy",
  "database": {
    "connected": true,
    "database": "aeropredict_db"
  },
  "model": {
    "loaded": true,
    "model_type": "RandomForestRegressor"
  }
}
```

---

## 5. Frontend Application Startup

Open a second terminal window:

```bash
cd frontend
npm install
npm run dev
```

The Vite development server will start at:
```text
  VITE v6.1.0  ready in 240 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

---

## 6. Accessing the Application

Open your browser and navigate to:
**`http://localhost:5173`**

You will see the executive dashboard immediately populated with:
1. Fleet metrics (total aircraft, active maintenance, health distribution).
2. Aircraft Fleet Management table with search and filtering.
3. Engine health monitoring with 21 sensor channels and cycle timelines.
4. Remaining Useful Life (RUL) prognostic prediction calculator.
5. Maintenance work order lifecycle management.

---

## 7. Running Automated Test Suites

### Backend Tests (50 Test Cases):
```powershell
cd backend
python -m unittest discover -s tests -p "test_*.py"
```

### Machine Learning Validation Tests:
```powershell
python ml_model/test_model.py
python ml_model/test_preprocessing.py
python ml_model/audit_ml.py
```

### Frontend Build Verification:
```powershell
cd frontend
npm run build
```
