# AeroPredict - System Architecture Document

## 1. High-Level Architecture Overview

AeroPredict follows an enterprise-grade, decoupled three-tier service-oriented architecture:

1. **Client Presentation Tier (Frontend):** Modern Single Page Application (SPA) built with React 18, Vite, Bootstrap 5, Recharts, and Lucide React icons following the Harbor Blue aviation design language.
2. **Application & Analytics Tier (Backend & ML Engine):** Python Flask REST API server paired with a standalone Scikit-learn Machine Learning Prediction Service.
3. **Data Persistence Tier (Database):** MySQL Server 8.0 relational database storing airframe configurations, continuous 21-sensor C-MAPSS telemetry, RUL predictions, active alerts, and work orders.

```mermaid
flowchart TD
    subgraph Client["Presentation Tier (React 18 SPA)"]
        UI["React 18 Component Tree"]
        RTR["React Router (7 Core Routes)"]
        RC["Recharts Visual Analytics"]
        AX["Axios API Client Layer"]
        UI --> RTR
        UI --> RC
        UI --> AX
    end

    subgraph Server["Application Tier (Flask REST API Server)"]
        FL["Flask Application Factory (Port 5000)"]
        CORS["Flask-CORS Middleware"]
        VLD["Request Validation Layer"]
        SVC["Service Layer"]
        
        FL --> CORS
        FL --> VLD
        VLD --> SVC
        
        subgraph Services["Core Business Services"]
            ACS["Aircraft Service"]
            ENS["Engine & Sensor Service"]
            PRS["Prediction Service"]
            MTS["Maintenance Service"]
            DBS["Dashboard Service"]
        end
        
        SVC --> ACS
        SVC --> ENS
        SVC --> PRS
        SVC --> MTS
        SVC --> DBS
    end

    subgraph MLTier["Machine Learning Prognostic Pipeline"]
        CMAPSS["NASA C-MAPSS FD001 Dataset (20,631 Train Rows)"]
        FE["Causal Rolling Feature Extractor (45 Features)"]
        TRN["Random Forest Trainer (100 Trees, GroupKFold CV)"]
        MDL["Serialized Joblib Artifacts (.joblib)"]
        
        CMAPSS --> FE
        FE --> TRN
        TRN --> MDL
        MDL --> PRS
    end

    subgraph DataTier["Persistence Tier (MySQL Server 8.0)"]
        DBC["Connection Pool (mysql-connector-python)"]
        TBL1[("aircraft")]
        TBL2[("sensor_readings")]
        TBL3[("rul_predictions")]
        TBL4[("maintenance_alerts")]
        TBL5[("maintenance_records")]
        
        DBC --> TBL1
        DBC --> TBL2
        DBC --> TBL3
        DBC --> TBL4
        DBC --> TBL5
    end

    AX <-->|JSON over HTTP / REST| FL
    ACS & ENS & PRS & MTS & DBS <--> DBC
```

---

## 2. Component Architecture Details

### 2.1 Frontend Architecture (`frontend/src/`)
Constructed as a modular, responsive Single Page Application (SPA) with clear separation between state, views, and network transports:

- **Client-Side Routing (`App.jsx`):**
  - `/`: Executive Fleet Dashboard (KPIs, availability donut, maintenance distribution, health overview, active alerts)
  - `/aircraft`: Fleet Inventory Management (List, search, filter, status toggles)
  - `/aircraft/add`: Aircraft Registration Form with full field validations
  - `/aircraft/:id`: Aircraft Diagnostics Profile & Edit Form
  - `/monitoring`: Engine Health Monitoring & Sensor Analytics (`?unit=X&tail=Y`)
  - `/predictive`: Predictive Maintenance & RUL Inference (`?id=X&tail=Y`)
  - `/maintenance`: Maintenance Work Order Management & Backlog (`?aircraft_id=X`)
- **API Client Layer (`src/api/`):**
  - `apiClient.js`: Central Axios instance with base URL `http://localhost:5000/api`, 8000ms timeout, and error response unpacker.
  - `aircraftApi.js`, `engineApi.js`, `predictionApi.js`, `maintenanceApi.js`, `dashboardApi.js`: Individual domain clients with seamless fallback to cached local datasets if backend is offline.
- **Visual Analytics (`Recharts`):**
  - Multi-sensor wear degradation curves (T30, T50, P30, Nc, BPR)
  - Fleet Operational Availability Donut Chart (`PieChart`, `Pie`, `Cell`)
  - Maintenance Work Order Distribution Bar Chart (`BarChart`, `Bar`)
- **UI Components (`src/components/`):**
  - `Navbar.jsx`, `Sidebar.jsx`, `MetricCard.jsx`, `StatusBadge.jsx`, `AlertCard.jsx`, `RulGauge.jsx`, `LoadingSpinner.jsx`.

---

### 2.2 Backend Architecture (`backend/`)
Follows Flask's application factory pattern with blueprint modularity and business logic isolation:

- **Application Factory (`app.py`):** Configures app settings, registers all blueprints with centralized URL prefixes, configures CORS, and handles centralized HTTP error codes (400, 404, 405, 500).
- **Database Configuration (`config/database.py`):** Initializes MySQL connection pool (`mysql.connector.pooling.MySQLConnectionPool`) with pool size of 5, providing thread-safe connection reuse, automatic schema creation, and health check utilities.
- **REST Blueprints (`routes/`):**
  - `health_routes.py`: System diagnostic health check (`GET /api/health`).
  - `aircraft_routes.py`: Airframe CRUD operations (`/api/aircraft`).
  - `engine_routes.py`: NASA C-MAPSS sensor readings, historical curves, cycle advancement (`/api/aircraft/<id>/sensors`, `/api/engine`).
  - `prediction_routes.py`: Random Forest RUL inference (`POST /api/predict`), prediction history, model metadata.
  - `maintenance_routes.py`: Work order lifecycle management (`/api/maintenance`).
  - `dashboard_routes.py`: Aggregated executive metrics (`GET /api/dashboard`).
- **Service Layer (`services/`):**
  - `aircraft_service.py`: Fleet asset logic, validations, cascade deletes.
  - `engine_service.py`: Sensor history extraction, cycle advance wear simulation, 7 subsystem diagnostic scoring.
  - `prediction_service.py`: Singleton ML inference engine, physical sensor boundary validation, 45 rolling feature vector construction, RUL inference, risk tiering, recommendation mapping, MySQL alert creation.
  - `maintenance_service.py`: Work order creation, status lifecycle transitions (`PENDING` $\rightarrow$ `IN_PROGRESS` $\rightarrow$ `COMPLETED`), automatic airframe status realignment.
  - `dashboard_service.py`: Aggregated KPI calculations, fleet health scoring, alert feeds.

---

### 2.3 Machine Learning Architecture (`ml_model/`)

```mermaid
flowchart LR
    A["Raw C-MAPSS Data\n(train_FD001.txt)"] --> B["Drop 7 Invariant Sensors\n(std = 0)"]
    B --> C["Piecewise RUL Capping\n(Max RUL = 125 cycles)"]
    C --> D["Feature Engineering\n(45 Causal Rolling Features)"]
    D --> E["StandardScaler\n(Zero Data Leakage)"]
    E --> F["5-Fold GroupKFold CV\n(Split by Engine Unit ID)"]
    F --> G["Random Forest Regressor\n(100 Trees, Depth 18)"]
    G --> H["Evaluate Test Set\n(100 Engines, RUL_FD001.txt)"]
    H --> I["Export Serialized Artifacts\n(.joblib & .json)"]
```

- **Data Ingestion:** Reads space-delimited NASA C-MAPSS FD001 matrix (100 training engines, 100 test engines).
- **Variance Filtering:** Drops 7 invariant sensor channels with zero variance across all cycles (`sensor_1`, `sensor_5`, `sensor_6`, `sensor_10`, `sensor_16`, `sensor_18`, `sensor_19`).
- **Piecewise Linear Target Formulation:** Caps Remaining Useful Life at 125 cycles during early operating stages to reflect negligible thermodynamic degradation before initial micro-wear onset.
- **Causal Feature Engineering:** Generates 45 features including elapsed cycles, operational settings, 14 active sensors, 14 rolling means (window $W=5$), and 14 rolling standard deviations (window $W=5$).
- **Zero-Leakage GroupKFold CV:** Splits training set into 5 folds strictly grouped by `unit_number` so an engine's earlier cycles never appear in both training and validation splits.
- **Model Training:** `RandomForestRegressor(n_estimators=100, max_depth=18, min_samples_split=5, min_samples_leaf=2, max_features=0.7, random_state=42)`.
- **Inference Runtime:** Pre-loads serialized model and scaler once on startup. Evaluates RUL in $<30\text{ ms}$ without retraining during requests.

---

## 3. End-to-End Prediction & Maintenance Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor Tech as Aircraft Engineer / Technician
    participant UI as React UI (Dashboard / Prognostics)
    participant API as Flask REST API Server
    participant Pred as Prediction Service (Random Forest)
    participant DB as MySQL Database (aeropredict_db)

    Tech->>UI: Select Aircraft (e.g. N101AP) & Request RUL
    UI->>API: POST /api/predict {aircraft_id: 1, cycle: 192, telemetry: {...}}
    API->>Pred: validate_telemetry_payload(data)
    Pred->>DB: Verify aircraft exists & fetch baseline cycles
    DB-->>Pred: Aircraft Record (ID #1, Unit #1)
    Pred->>Pred: Construct 45-feature causal vector
    Pred->>Pred: Standardize features via scaler.joblib
    Pred->>Pred: Predict RUL via random_forest_rul_model.joblib
    Note over Pred: Result: RUL = 6.2 cycles (CRITICAL Risk)
    Pred->>Pred: Map actionable recommendations
    Pred->>DB: INSERT INTO rul_predictions (aircraft_id, cycle, rul, risk, rec)
    Pred->>DB: INSERT INTO maintenance_alerts (aircraft_id, RUL_CRITICAL, severity: CRITICAL)
    Pred-->>API: Structured Prediction Payload
    API-->>UI: 200 OK {predicted_rul: 6.2, risk_level: "CRITICAL", alert_created: true}
    UI->>Tech: Display RUL Gauge (6.2 cycles), Alert Banner & Actionable Card
    Tech->>UI: Click "Schedule Maintenance"
    UI->>API: POST /api/maintenance {aircraft_id: 1, title: "HPC Blade Replacement", priority: "CRITICAL"}
    API->>DB: INSERT INTO maintenance_records & UPDATE aircraft status = 'ATTENTION_REQUIRED'
    DB-->>API: 201 Created (Work Order #1)
    API-->>UI: Work Order Confirmed
    UI->>Tech: Display Updated Maintenance Backlog & Dashboard Status
```
