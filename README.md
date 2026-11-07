# AeroPredict ✈️
### AI-Powered Aircraft Engine Health Monitoring and Predictive Maintenance System

AeroPredict is an educational predictive-maintenance platform designed for an MCA college mini-project. It simulates turbofan engine sensor telemetry, monitors real-time degradation trends, predicts Remaining Useful Life (RUL) using machine learning, and manages maintenance work orders.

---

## 🛠️ Technology Stack

- **Frontend:** React.js, Vite, Bootstrap 5, Axios, React Router, Recharts, Lucide React (UI tokens from 21st.dev Harbor Blue theme)
- **Backend:** Python Flask, Flask-CORS
- **Database:** MySQL Server 8.0, `mysql-connector-python` (with connection pooling)
- **Machine Learning:** Scikit-learn (Random Forest Regressor), Pandas, NumPy, Joblib
- **Dataset:** NASA C-MAPSS FD001 Turbofan Engine Degradation Simulation

---

## 📂 Project Directory Structure

```
d:/Aeropredict/
│
├── dataset/                     # NASA C-MAPSS FD001 telemetry files
│   ├── train_FD001.txt          # 20,631 run-to-failure cycles (100 engines)
│   ├── test_FD001.txt           # 13,096 cycles (100 engines prior to failure)
│   └── RUL_FD001.txt            # 100 ground-truth remaining life cycles
│
├── frontend/                    # React + Vite client SPA
├── backend/                     # Flask REST API service
├── ml_model/                    # Training pipeline, evaluators & serialized artifacts
│   └── artifacts/               # Joblib serialized models and scalers
└── documentation/               # Project diagrams & submission reports
```

---

## 📚 Documentation Index

- [MASTER_INSTRUCTIONS.md](file:///d:/Aeropredict/MASTER_INSTRUCTIONS.md): Guiding rules, constraints, and requirements.
- [PROJECT_SPEC.md](file:///d:/Aeropredict/PROJECT_SPEC.md): Complete project specifications, sensor definitions, and risk tiers.
- [ARCHITECTURE.md](file:///d:/Aeropredict/ARCHITECTURE.md): System architecture, component models, and Mermaid sequence diagrams.
- [DATABASE_SCHEMA.md](file:///d:/Aeropredict/DATABASE_SCHEMA.md): Relational MySQL schema DDL, constraints, indexes, and ER diagram.
- [IMPLEMENTATION_PLAN.md](file:///d:/Aeropredict/IMPLEMENTATION_PLAN.md): API contract and phased milestone breakdown.
- [PROGRESS.md](file:///d:/Aeropredict/PROGRESS.md): Live project milestone tracker and changelog.

---

## 🚦 Current Status
- **Phase 1 (Milestone 0):** Planning, Architecture & Dataset Integrity Verification – **Completed & Verified**
- **Next Phase:** Phase 2 – React Frontend Development
