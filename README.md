# AeroPredict ✈️
### AI-Powered Aircraft Engine Health Monitoring and Predictive Maintenance System

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![React](https://img.shields.io/badge/React-18.3+-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-6.1+-646CFF?logo=vite&logoColor=white)](https://vitejs.dev/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-4479A1?logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.4+-F7931E?logo=scikitlearn&logoColor=white)](https://scikit-learn.org/)
[![Tests](https://img.shields.io/badge/Tests-50%2F50%20Passing-10B981)](#-automated-testing--verification)
[![License](https://img.shields.io/badge/License-Academic-blue.svg)](#)

AeroPredict is a full-stack, AI-powered predictive maintenance and real-time engine health monitoring system developed as a Master of Computer Applications (**MCA**) capstone project. The system ingests multi-sensor turbofan degradation time-series from the **NASA Commercial Modular Aero-Propulsion System Simulation (C-MAPSS) FD001 dataset**, predicts Remaining Useful Life (**RUL**) in operating flight cycles via an empirically validated **Random Forest Regressor**, classifies thermodynamic failure risk, issues automated maintenance prescriptions, and manages complete maintenance work orders through an ACID-compliant MySQL relational database.

---

## 📑 Table of Contents

- [Key Highlights](#-key-highlights)
- [System Architecture](#-system-architecture)
- [Core Application Modules](#-core-application-modules)
- [Machine Learning Performance](#-machine-learning-performance)
- [Repository Structure](#-repository-structure)
- [Quick Start Guide](#-quick-start-guide)
- [Automated Testing & Verification](#-automated-testing--verification)
- [Academic Documentation & Diagrams](#-academic-documentation--diagrams)

---

## 🌟 Key Highlights

- **NASA C-MAPSS FD001 Turbofan Dataset:** Uses authentic turbofan engine degradation data (100 training engines run to complete failure; 100 test engines with ground truth RUL).
- **Zero-Retrain Turnkey Deployment:** Pre-trained Random Forest model and scaler artifacts are committed directly in the repository—inference works immediately upon installation.
- **High-Precision Prognostics:** Empirically verified test set **MAE of 12.70 cycles** and **$R^2$ of 0.8044** across 100 unseen NASA test engines (no simulated or fabricated metrics).
- **Causal Feature Pipeline:** Computes backward-looking rolling statistics ($W=5$ cycles) across 14 dynamic sensors and 3 operational settings, generating a 45-dimensional feature space.
- **Relational Integrity & Connection Pooling:** Thread-safe PyMySQL pooling with full foreign key cascading across 5 normalized relational tables.
- **Aviation-Inspired Single-Page UI:** Built with React 18, Vite, Tailwind CSS, Lucide icons, and Recharts degradation curve visualizers.

---

## 🏛️ System Architecture

AeroPredict uses a decoupled, three-tier architecture:

```
[ React 18 SPA (Vite + Tailwind CSS) ]
                   │
         JSON over REST / HTTP
                   ▼
[ Python Flask API Server (Port 5000) ]
   ├── Blueprints: aircraft, engine, prediction, maintenance, dashboard
   ├── Service Layer: Business logic & schema initialization
   └── ML Pipeline: Random Forest Regressor (45 Rolling Features)
                   │
           PyMySQL Pool (ACID)
                   ▼
[ MySQL Relational Database (aeropredict_db) ]
```

Detailed architectural specifications and sequence interactions are documented in [docs/architecture.md](docs/architecture.md).

---

## ✈️ Core Application Modules

| Module | Interface | API Endpoint | Description |
| :--- | :--- | :--- | :--- |
| **Executive Dashboard** | `DashboardPage.jsx` | `GET /api/dashboard` | Fleet health KPIs, airworthiness distribution charts, active work orders, and high-priority maintenance alerts. |
| **Aircraft Fleet Management** | `AircraftListPage.jsx`<br>`AddAircraftPage.jsx` | `GET/POST /api/aircraft`<br>`GET /api/aircraft/<id>` | Full fleet asset inventory, tail number registration, flight hours, cycle tracking, and operational status transitions. |
| **Engine Health Monitoring** | `EngineMonitoringPage.jsx` | `GET /api/engine/readings/<id>`<br>`POST /api/engine/readings` | Real-time multi-sensor telemetry matrix across 21 channels (temperatures, pressures, core speeds) and Recharts wear curves. |
| **Predictive Maintenance** | `PredictiveMaintenancePage.jsx` | `POST /api/predict`<br>`GET /api/predict/history/<id>` | Instantaneous RUL estimation in flight cycles, risk classification (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), and prescribed actions. |
| **Maintenance Work Orders** | `MaintenancePage.jsx` | `GET/POST /api/maintenance`<br>`PUT/DELETE /api/maintenance/<id>` | Complete work order backlog management (`PENDING` $\rightarrow$ `IN_PROGRESS` $\rightarrow$ `COMPLETED`), priority triage, and technician logs. |

---

## 📊 Machine Learning Performance

The predictive model was trained on the **NASA C-MAPSS FD001** benchmark dataset (20,631 operational cycle records) using a **Random Forest Regressor** with a piecewise linear RUL target capped at 125 cycles.

All metrics below are empirically verified via [`ml_model/audit_ml.py`](file:///d:/Aeropredict/ml_model/audit_ml.py) against official NASA test labels (`RUL_FD001.txt`):

| Evaluation Stage | Evaluation Split | MAE (Cycles) | RMSE (Cycles) | $R^2$ Score |
| :--- | :--- | :---: | :---: | :---: |
| **5-Fold Cross-Validation** | Zero-leakage GroupKFold by Unit (Train Set) | **11.17** | **16.57** | **0.8419** |
| **Held-Out Test Set** | 100 Unseen NASA Engines (Capped Target $\le 125$) | **12.70** | **17.72** | **0.8044** |
| **Held-Out Test Set** | 100 Unseen NASA Engines (Uncapped Target) | **18.73** | **23.16** | **0.6865** |

For the complete feature selection breakdown and hyperparameter details, see [docs/ml-pipeline.md](docs/ml-pipeline.md).

---

## 📂 Repository Structure

```
AeroPredict/
├── README.md                             # Project overview and quick start guide
├── docs/                                 # Academic documentation and technical guides
│   ├── architecture.md                   # System architecture and design patterns
│   ├── database-design.md                # Relational schema, DDL, and data dictionary
│   ├── ml-pipeline.md                    # C-MAPSS dataset, features, and model metrics
│   ├── api-reference.md                  # Complete REST API specification
│   ├── installation-guide.md             # Comprehensive deployment instructions
│   ├── diagrams.md                       # Mermaid architecture, ER, and sequence diagrams
│   ├── project-report.md                 # Complete 23-section MCA mini-project report
│   └── viva-preparation.md               # Viva voce defense questions & answers
│
├── dataset/                              # NASA C-MAPSS FD001 dataset
│   ├── train_FD001.txt                   # 20,631 run-to-failure cycles (100 engines)
│   ├── test_FD001.txt                    # 13,096 cycles prior to failure (100 engines)
│   └── RUL_FD001.txt                     # 100 ground-truth remaining life cycles
│
├── backend/                              # Flask REST API server
│   ├── app.py                            # Application factory, CORS & blueprint registration
│   ├── requirements.txt                  # Pinned Python dependencies
│   ├── .env.example                      # Template environment variables
│   ├── config/
│   │   └── database.py                   # PyMySQL pool & automatic schema initializer
│   ├── db/
│   │   ├── schema.sql                    # Production DDL schema
│   │   └── seed_data.py                  # One-command schema creator & fleet seeder
│   ├── routes/                           # Modular API blueprints
│   │   ├── health_routes.py              # GET /api/health
│   │   ├── aircraft_routes.py            # /api/aircraft CRUD
│   │   ├── engine_routes.py              # /api/engine telemetry endpoints
│   │   ├── prediction_routes.py          # /api/predict RUL inference
│   │   ├── maintenance_routes.py         # /api/maintenance work orders
│   │   └── dashboard_routes.py           # /api/dashboard analytics
│   ├── services/                         # Decoupled business logic & database queries
│   │   ├── aircraft_service.py
│   │   ├── dashboard_service.py
│   │   ├── engine_service.py
│   │   ├── maintenance_service.py
│   │   └── prediction_service.py
│   └── tests/                            # Automated test suite (50 tests)
│       ├── db_audit.py                   # Referential integrity validator
│       ├── sql_safety_audit.py           # SQL parameterization scanner
│       ├── test_aircraft.py
│       ├── test_dashboard.py
│       ├── test_engine.py
│       ├── test_maintenance.py
│       └── test_prediction.py
│
├── frontend/                             # React 18 Single-Page Application
│   ├── index.html                        # Application entry point
│   ├── package.json                      # Dependencies (React, Vite, Recharts, Lucide)
│   ├── vite.config.js                    # Vite bundler & reverse proxy configuration
│   ├── tailwind.config.js                # Aviation theme palette and styling tokens
│   └── src/
│       ├── App.jsx                       # Main application router and layout
│       ├── api/                          # Axios API clients with uniform error handlers
│       ├── components/                   # Shared UI components (MetricCard, Header, Sidebar)
│       └── pages/                        # Module view containers (Dashboard, Fleet, Prognostics)
│
└── ml_model/                             # Machine learning training & inference pipeline
    ├── data_loader.py                    # C-MAPSS parser and column assigner
    ├── feature_engineering.py            # 45 rolling mean/std features extractor
    ├── preprocess.py                     # Data cleaning and MinMaxScaler
    ├── train.py                          # Random Forest trainer with GroupKFold CV
    ├── predict.py                        # Standalone RULPredictor inference class
    ├── audit_ml.py                       # Empirical validation script for model metrics
    ├── test_model.py                     # Unit tests for inference pipeline
    ├── test_preprocessing.py             # Unit tests for feature extraction
    └── artifacts/                        # Serialized model artifacts
        ├── random_forest_rul_model.joblib
        ├── scaler.joblib
        ├── feature_names.joblib
        ├── model_config.joblib
        └── model_metadata.json
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Python:** 3.10+ installed
- **Node.js:** 18.0+ installed
- **MySQL Server:** 8.0+ running on port `3306`

### 2. Database Initialization
Create the database and copy the environment template:
```sql
CREATE DATABASE IF NOT EXISTS aeropredict_db;
```

```bash
# Copy environment configuration:
cp backend/.env.example backend/.env
# Open backend/.env and enter your MySQL password (DB_PASSWORD=...)

# One-command schema creation, fleet seeding, and telemetry ingestion:
cd backend
python db/seed_data.py
```

### 3. Start Backend API
```bash
cd backend
python -m venv venv
source venv/bin/activate       # On Windows: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```
*(Backend runs at `http://localhost:5000`)*

### 4. Start React Frontend
In a separate terminal:
```bash
cd frontend
npm install
npm run dev
```
*(Frontend runs at `http://localhost:5173`)*

Open your browser at **`http://localhost:5173`** to access the complete AeroPredict platform.

---

## 🧪 Automated Testing & Verification

AeroPredict includes a comprehensive automated test suite covering all tiers:

```bash
# 1. Run all 50 Backend Integration & Unit Tests:
cd backend
python -m unittest discover -s tests -p "test_*.py"

# 2. Run Database Integrity & Security Audits:
python tests/db_audit.py
python tests/sql_safety_audit.py

# 3. Run Machine Learning Pipeline & Metric Audits:
python ml_model/test_model.py
python ml_model/test_preprocessing.py
python ml_model/audit_ml.py

# 4. Verify Frontend Production Build:
cd frontend
npm run build
```

---

## 📚 Academic Documentation & Diagrams

Complete documentation prepared for MCA academic submission and viva voce examination:

- 📘 [MCA Project Report](docs/project-report.md) — Complete 23-section academic report (Certificate, Abstract, Literature Review, Methodology, Results).
- 📐 [Architectural Diagrams](docs/diagrams.md) — Mermaid UML diagrams (System Architecture, ER Diagram, Data Flow, Sequence, Use Case, ML Workflow).
- 🗄️ [Database Design & Schema](docs/database-design.md) — Comprehensive data dictionary, constraints, and production SQL DDL.
- ⚙️ [Machine Learning Methodology](docs/ml-pipeline.md) — In-depth mathematical formulation, feature engineering, and cross-validation methodology.
- 🔌 [REST API Reference](docs/api-reference.md) — Full API endpoint contracts, schemas, and payload examples.
- 🎓 [Viva Voce Defense Guide](docs/viva-preparation.md) — Frequently asked questions, examiner defenses, and architectural justification.
- 🛠️ [Installation Guide](docs/installation-guide.md) — Step-by-step developer deployment guide.
