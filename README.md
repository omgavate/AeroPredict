# AeroPredict ✈️
### AI-Powered Aircraft Engine Health Monitoring and Predictive Maintenance System

[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1+-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![React](https://img.shields.io/badge/React-18.3+-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-6.1+-646CFF?logo=vite&logoColor=white)](https://vitejs.dev/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-4479A1?logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.6+-F7931E?logo=scikitlearn&logoColor=white)](https://scikit-learn.org/)
[![Build Status](https://img.shields.io/badge/Build-Passing-10B981)](#-automated-testing--verification)
[![Test Suite](https://img.shields.io/badge/Tests-50%2F50%20Passing-10B981)](#-automated-testing--verification)

AeroPredict is a full-stack, AI-powered predictive maintenance and real-time engine health monitoring platform developed as an **MCA Capstone Mini-Project**. The system ingests multi-sensor turbofan degradation time-series from the **NASA C-MAPSS (Commercial Modular Aero-Propulsion System Simulation) FD001 dataset**, predicts Remaining Useful Life (RUL) in flight cycles via a verified **Random Forest Regressor**, classifies thermodynamic failure risk, issues automated maintenance prescriptions, and manages complete maintenance work orders through a relational MySQL database.

---

## 🛠️ Technology Stack & System Components

| Layer | Technology | Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Frontend UI** | React.js (SPA) | `^18.3.1` | High-performance reactive aviation management interface |
| **Build Tool** | Vite | `^6.1.0` | Ultra-fast HMR and optimized production rollup bundler |
| **Styling & Icons** | Bootstrap 5, Lucide React | `^5.3.3`, `^0.475.0` | Aviation Harbor Blue design system (`#194391`, `#0F172A`) |
| **Telemetry Charts** | Recharts | `^2.15.1` | Multi-channel degradation curves, availability donuts & bar charts |
| **HTTP Client** | Axios | `^1.7.9` | Interceptor-based asynchronous REST API communication |
| **Backend API** | Python Flask | `^3.1.0` | Modular RESTful microservice with blueprint routing |
| **CORS Middleware**| Flask-CORS | `^5.0.0` | Cross-Origin Resource Sharing handling for React clients |
| **Database** | MySQL Server | `8.0+` | ACID-compliant relational persistence for assets & logs |
| **DB Driver** | mysql-connector-python | `^9.2.0` | Native connection pool with transaction management |
| **ML Engine** | Scikit-learn, Pandas, NumPy | `^1.6.1`, `^2.2.3` | Random Forest Regressor, rolling feature engine & scaling |
| **Model Persistence**| Joblib | `^1.4.2` | Production model artifact serialization and zero-retrain inference |
| **Dataset** | NASA C-MAPSS FD001 | 20,631 records | Run-to-failure turbofan sensor matrix (Sea Level, HPC degradation) |

---

## 📂 Project Directory Structure

```
d:/Aeropredict/
│
├── dataset/                           # NASA C-MAPSS FD001 dataset (Local)
│   ├── train_FD001.txt                # 20,631 run-to-failure cycles (100 units)
│   ├── test_FD001.txt                 # 13,096 cycles (100 units truncated)
│   └── RUL_FD001.txt                  # 100 ground-truth remaining life cycles
│
├── ml_model/                          # Machine learning pipeline
│   ├── data_loader.py                 # C-MAPSS ingestion & column mapping
│   ├── feature_engineering.py         # 45 causal rolling features extraction
│   ├── preprocess.py                  # Piecewise RUL capping (125) & scaling
│   ├── train.py                       # GroupKFold CV trainer & model exporter
│   ├── evaluate.py                    # Independent test evaluation script
│   ├── audit_ml.py                    # Empirical metrics audit & verification
│   └── artifacts/                     # Serialized production models
│       ├── random_forest_rul_model.joblib # Trained Random Forest model (100 estimators)
│       ├── scaler.joblib              # StandardScaler artifact
│       ├── feature_names.joblib       # 45 feature column list
│       └── model_metadata.json        # Hyperparameters & verified metrics
│
├── backend/                           # Flask REST API server
│   ├── app.py                         # Application factory, CORS & error handlers
│   ├── config/
│   │   └── database.py                # MySQL pool connection & schema initializer
│   ├── routes/                        # REST Blueprints
│   │   ├── health_routes.py           # GET /api/health
│   │   ├── aircraft_routes.py         # /api/aircraft CRUD
│   │   ├── engine_routes.py           # /api/aircraft/<id>/sensors & /api/engine
│   │   ├── prediction_routes.py       # POST /api/predict & history
│   │   ├── maintenance_routes.py      # /api/maintenance work orders
│   │   └── dashboard_routes.py        # GET /api/dashboard & KPI aggregations
│   ├── services/                      # Decoupled business logic
│   │   ├── aircraft_service.py
│   │   ├── engine_service.py
│   │   ├── prediction_service.py
│   │   ├── maintenance_service.py
│   │   └── dashboard_service.py
│   └── tests/                         # Automated unit & integration test suite (50 tests)
│       ├── test_health.py
│       ├── test_aircraft_api.py
│       ├── test_engine_api.py
│       ├── test_prediction_api.py
│       ├── test_maintenance_api.py
│       ├── test_dashboard_api.py
│       └── test_e2e_workflow.py
│
├── frontend/                          # React + Vite Single Page Application
│   ├── src/
│   │   ├── api/                       # API clients with fallback support
│   │   ├── components/                # Reusable UI widgets (MetricCard, AlertCard, RulGauge, etc.)
│   │   ├── pages/                     # 5 Module Views (Dashboard, Fleet, Monitoring, Prognostics, Orders)
│   │   ├── data/                      # Local cached offline fallback datasets
│   │   ├── App.jsx                    # Routing & navigation layout
│   │   └── index.css                  # Aviation Harbor Blue styling tokens
│   ├── package.json
│   └── vite.config.js
│
└── documentation/                     # Academic deliverables
    ├── PROJECT_REPORT.md              # Complete 23-section MCA mini-project report
    ├── INSTALLATION_GUIDE.md          # Step-by-step environment & execution setup
    └── VIVA_PREPARATION.md            # Comprehensive viva questions & defense guide
```

---

## ✈️ Core Functional Modules

### Module 1: Executive Fleet Dashboard
- **Real-Time KPIs:** 6 responsive metric cards displaying Total Aircraft, Operational Rate, Under Maintenance count, Attention Required, Pending Work Orders, and Active Alerts.
- **Visual Analytics:** Interactive Recharts Donut (`PieChart`) for fleet airworthiness availability and Bar Chart (`BarChart`) for maintenance work order status distribution.
- **Turbofan Health Matrix:** Fleet mean health percentage, mean estimated RUL, risk tiering, and individual per-aircraft degradation progress bars.
- **Triage & Activity:** Active maintenance alerts with real-time acknowledge/resolve action and an operational timeline combining work orders, alerts, and inferences.

### Module 2: Aircraft Fleet Management
- **Airframe Registry:** Comprehensive fleet inventory recording Tail Number, Model, Manufacturer, Engine Type, NASA C-MAPSS Unit Mapping, Operating Cycles, Flight Hours, and Operational Status.
- **CRUD Operations:** Complete registration modal form with client/server validation, edit capabilities, search filtering, and safe cascade deletion.

### Module 3: Engine Health Monitoring
- **21-Channel Sensor Matrix:** Live thermodynamic telemetry including T2, T24, T30, T50, P2, P15, P30, Nf, Nc, Ps30, BPR, and bleed flows.
- **Degradation Trend Curves:** 4 multi-sensor Recharts line graphs plotting sensor wear over elapsed operating cycles.
- **Interactive Cycle Simulation:** Step-by-step cycle advance feature simulating real wear data ingested from NASA C-MAPSS.
- **Subsystem Health Status:** Diagnostic health breakdown across 7 critical engine subsystems (Fan, LPC, HPC, Combustor, LPT, Bypass/Bleed, Cooling).

### Module 4: Predictive Maintenance & Prognostics
- **Random Forest RUL Inference:** Zero-retrain ML inference predicting Remaining Useful Life in operational flight cycles with sub-30ms latency.
- **Tone-Coded Risk Classification:**
  - 🟢 **Low Risk (Nominal):** $\text{RUL} > 75$ cycles
  - 🟡 **Medium Risk (Watchlist):** $\text{RUL} \in [31, 75]$ cycles
  - 🟠 **High Risk (Maintenance Due):** $\text{RUL} \in [11, 30]$ cycles
  - 🔴 **Critical Risk (Immediate Action):** $\text{RUL} \le 10$ cycles
- **Contextual Prescriptions:** Automated maintenance recommendations (e.g. HPC borescope inspection, blade tip clearance check, grounding).
- **Prognostic Audit Log:** MySQL-persisted prediction history logging RUL trends across flight cycles.

### Module 5: Maintenance Management
- **Work Order Backlog:** Complete work order lifecycle tracking (`PENDING`, `SCHEDULED`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`).
- **Priority Triage:** Work orders categorized by urgency (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
- **Relational History:** Full audit log of completed, active, and scheduled shop interventions linked to airframes.

---

## 📊 Machine Learning Performance Metrics

AeroPredict was evaluated on the **NASA C-MAPSS FD001** benchmark dataset:

| Evaluation Stage | Methodology | MAE (Cycles) | RMSE (Cycles) | $R^2$ Score | NASA Penalty Score |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **5-Fold Cross-Validation** | Zero-leakage GroupKFold by Engine ID (20,631 train rows) | **11.17** | **16.57** | **0.8419** | 129,694.6 |
| **Held-Out Test Set** | 100 unseen test engines at final cycle (Piecewise Capped $\le 125$) | **12.70** | **17.72** | **0.8044** | **564.5** |
| **Held-Out Test Set** | 100 unseen test engines at final cycle (Raw Uncapped) | **13.77** | **18.88** | **0.7936** | 632.4 |

> [!NOTE]
> All metrics are empirically verified through [`audit_ml.py`](file:///d:/Aeropredict/ml_model/audit_ml.py) against ground-truth labels in `RUL_FD001.txt`. No simulated or fabricated scores are used.

---

## 🚀 Quick Start Guide

### Prerequisites
- **Node.js:** v18.0 or higher (v24 LTS recommended)
- **Python:** v3.10 to v3.13
- **MySQL Server:** v8.0 or higher running locally on port `3306`

### 1. Database Setup
Log in to MySQL and ensure the database user has permissions:
```sql
CREATE DATABASE IF NOT EXISTS aeropredict_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. Backend Installation & Startup
```powershell
# Navigate to backend directory
cd d:\Aeropredict\backend

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Configure environment variables (create backend/.env from .env.example)
# DB_HOST=localhost, DB_PORT=3306, DB_USER=root, DB_PASSWORD=your_password, DB_NAME=aeropredict_db

# Run API Server
python app.py
```
*API Server starts at `http://localhost:5000`.*

### 3. Frontend Installation & Startup
```powershell
# In a new terminal, navigate to frontend
cd d:\Aeropredict\frontend

# Install dependencies
npm install

# Start Vite Development Server
npm run dev
```
*Web application opens at `http://localhost:5173`.*

---

## 🧪 Automated Testing & Verification

AeroPredict includes a 50-test automated verification suite covering API endpoints, input validation, database integrity, and end-to-end operational workflows:

```powershell
# Execute complete backend test suite
cd d:\Aeropredict
backend\venv\Scripts\python -m unittest discover -s backend/tests -p "test_*.py" -v
```
**Result:** `Ran 50 tests in 2.29s ... 100% OK`.

```powershell
# Execute Vite production build
npm run build --prefix frontend
```
**Result:** `✓ built in 3.88s ... 0 errors, 0 warnings`.

---

## 📄 Academic Documentation Index

Detailed documentation for MCA evaluation is available in the [`documentation/`](file:///d:/Aeropredict/documentation) folder:
- [PROJECT_REPORT.md](file:///d:/Aeropredict/documentation/PROJECT_REPORT.md): Complete 23-chapter academic project report.
- [INSTALLATION_GUIDE.md](file:///d:/Aeropredict/documentation/INSTALLATION_GUIDE.md): Setup instructions, troubleshooting, and production deployment guide.
- [VIVA_PREPARATION.md](file:///d:/Aeropredict/documentation/VIVA_PREPARATION.md): Comprehensive viva defense questions, examiner scenarios, and model explanations.
- [ARCHITECTURE.md](file:///d:/Aeropredict/ARCHITECTURE.md): Multi-tier architectural specifications and sequence diagrams.
- [DATABASE_SCHEMA.md](file:///d:/Aeropredict/DATABASE_SCHEMA.md): Relational MySQL schema DDL, constraints, and ER diagrams.
- [PROJECT_SPEC.md](file:///d:/Aeropredict/PROJECT_SPEC.md): Full technical specification and sensor definitions.
- [PROGRESS.md](file:///d:/Aeropredict/PROGRESS.md): 13-phase roadmap and milestone changelog.
