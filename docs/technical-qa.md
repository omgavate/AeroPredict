# AeroPredict - Technical Q&A & Architectural Defense Guide

This guide provides technical explanations and answers to complex architectural, machine learning, and database design questions regarding the **AeroPredict** system.

---

## 1. Executive System Summary (30–60 Seconds)

> *"AeroPredict is an AI-powered predictive maintenance and real-time engine health monitoring system for commercial aircraft fleets. In aviation, unscheduled engine breakdowns cause massive financial loss and safety hazards. AeroPredict ingests multi-sensor thermodynamic telemetry from the NASA C-MAPSS turbofan dataset and uses an ensemble Random Forest Regressor to predict an engine's Remaining Useful Life (RUL) in flight cycles. Based on predicted RUL, it categorizes failure risk into four tiers, prescribes maintenance actions, and enables engineers to create and track work orders through an interactive React dashboard backed by Flask and MySQL."*

---

## 2. Comprehensive Module Walkthrough

### Module 1: Executive Fleet Dashboard
- **What it does:** Provides a high-level operational overview for fleet directors and powerplant engineers.
- **Key Features:**
  - 6 KPI metric cards (Total Aircraft, Operational, Under Maintenance, Attention Required, Pending Maintenance, Active Alerts).
  - Recharts Donut chart showing fleet airworthiness distribution.
  - Recharts Bar chart showing work order backlog by status.
  - Turbofan Health Matrix tracking per-aircraft health percentages and wear degradation bars.
  - Quick action to trigger RUL prediction for high-cycle aircraft.

### Module 2: Aircraft Fleet Management
- **What it does:** Complete fleet inventory management for airframes and engines.
- **Key Features:**
  - Full CRUD operations with client-side and server-side validation.
  - Detailed airframe profiles: Tail Number, Model, Manufacturer, Engine Type, NASA C-MAPSS Unit Mapping (1–100), Accumulated Operating Cycles, Flight Hours, and Operational Status (`OPERATIONAL`, `UNDER_MAINTENANCE`, `ATTENTION_REQUIRED`, `RETIRED`).
  - Search, filter by status, and pagination.

### Module 3: Engine Health Monitoring
- **What it does:** Real-time thermodynamic and mechanical telemetry ingestion and visualization.
- **Key Features:**
  - 21-channel physical sensor matrix (T2, T24, T30, T50, P2, P15, P30, Nf, Nc, Ps30, BPR, bleed flows).
  - 4 interactive degradation trend line charts powered by Recharts.
  - Cycle progression simulator advancing engines through NASA C-MAPSS wear cycles.
  - Diagnostic breakdown across 7 critical engine subsystems (Fan, LPC, HPC, Combustor, LPT, Bypass, Cooling).

### Module 4: Predictive Maintenance & Prognostics
- **What it does:** High-precision Remaining Useful Life (RUL) calculation and automated maintenance prescriptions.
- **Key Features:**
  - Instantaneous machine learning inference using a pre-trained Random Forest Regressor ($< 30$ ms latency).
  - 4-tier risk classification: Low ($> 75$ cycles), Medium (50–75 cycles), High (25–50 cycles), Critical ($\le 25$ cycles).
  - Contextual maintenance prescriptions (e.g. HPC borescope inspection, turbine blade overhaul, AOG grounding).
  - Chronological prediction audit trail persisted in MySQL.

### Module 5: Maintenance Management
- **What it does:** End-to-end work order tracking from initial alert to resolution.
- **Key Features:**
  - Full work order backlog with status lifecycle (`PENDING` $\rightarrow$ `IN_PROGRESS` $\rightarrow$ `COMPLETED`).
  - Priority triage (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
  - Technician remarks and sign-off logging.
  - Complete historical maintenance records linked to individual aircraft assets.

---

## 3. Technology Stack Justification

### Why React 18 + Vite for the Frontend?
- **Component Reusability:** The dashboard, sensor tables, and KPI cards share common layout and status tokens.
- **Fast Development & Build:** Vite provides instant Hot Module Replacement (HMR) and optimized Rollup tree-shaking for small production bundles.
- **Data Visualization:** Recharts integrates natively with React's virtual DOM, delivering smooth 60fps animations for thermodynamic wear curves.

### Why Python Flask for the Backend?
- **Direct ML Ecosystem Integration:** Python is the native environment for scikit-learn, joblib, pandas, and numpy, allowing seamless in-memory model inference without cross-language serialization bottlenecks.
- **Lightweight & Modular:** Flask Blueprints provide a clean, decoupled REST architecture without the heavy boilerplate of Django.

### Why MySQL Server?
- **Relational Integrity:** Aircraft, sensor logs, work orders, and predictions have strict parent-child relationships requiring Foreign Keys and ACID transaction safety.
- **High Ingestion Performance:** InnoDB connection pooling handles high-throughput time-series sensor ingestion efficiently.

### Why Random Forest Regressor over Deep Learning (LSTM / CNN)?
1. **No Overfitting on Moderate Data:** FD001 has 100 training engines. Random Forest ensemble bagging prevents overfitting far better than deep neural networks without requiring massive GPU infrastructure.
2. **Interpretability:** Feature importance allows engineers to verify that thermodynamic degradation in HPC outlet temperature ($T_{30}$) and core speed ($N_c$) actually drives the RUL prediction.
3. **Ultra-Low Latency Inference:** Random Forest evaluates decision trees in $< 30$ ms on standard CPU hardware without GPU acceleration.
4. **Empirically Superior Accuracy:** Achieved a verified test set MAE of **12.70 cycles** and $R^2$ of **0.8044** on the held-out NASA C-MAPSS benchmark.

---

## 4. Machine Learning & Data Pipeline Details

### Q1: What dataset does AeroPredict use?
**Answer:** The benchmark **NASA C-MAPSS (Commercial Modular Aero-Propulsion System Simulation) FD001** dataset. It simulates a 90,000-lb thrust class turbofan engine at sea-level operating conditions with high-pressure compressor degradation.
- **Training Set:** 100 engines run to complete failure (20,631 total cycle snapshots).
- **Test Set:** 100 engines truncated at arbitrary points prior to failure (13,096 cycles).
- **Ground Truth:** True remaining life cycles for all 100 test engines at their last cycle.

### Q2: Why did you cap the RUL target at 125 cycles?
**Answer:** In early operational cycles, an engine operates normally without measurable mechanical wear. Capping RUL at 125 cycles converts the problem into a **piecewise linear degradation model** (established in NASA prognostics literature by Heimes, 2008). This prevents the regressor from wasting split capacity trying to distinguish between an engine with 300 cycles left vs 250 cycles left when both are in identical nominal conditions.

### Q3: What features did you engineer?
**Answer:**
1. Dropped 7 invariant sensors with zero variance (`sensor_1`, `sensor_5`, `sensor_6`, `sensor_10`, `sensor_16`, `sensor_18`, `sensor_19`).
2. Retained 14 dynamic sensors and 3 operational settings.
3. Calculated **5-cycle backward-looking rolling mean and rolling standard deviation** for all 14 dynamic sensors.
4. Total feature vector: **45 numerical features**.

### Q4: How did you ensure zero data leakage during Cross-Validation?
**Answer:** We used **5-Fold GroupKFold cross-validation**, where the splits are grouped strictly by engine unit ID. Data from the same engine is never split across training and validation folds simultaneously.

---

## 5. Database Architecture & Integrity

### Q1: What tables exist in MySQL?
**Answer:** Five normalized relational tables:
1. `aircraft`: Core fleet assets with tail numbers, engine types, cycles, and status.
2. `sensor_readings`: Time-series thermodynamic telemetry across 21 sensor channels.
3. `rul_predictions`: Inferred RUL, risk levels, and automated maintenance prescriptions.
4. `maintenance_records`: Work orders with status lifecycle (`PENDING`, `IN_PROGRESS`, `COMPLETED`).
5. `engine_health_summary`: Aggregated subsystem health snapshots for high-speed dashboard analytics.

### Q2: What happens when an aircraft is deleted?
**Answer:** We configured `ON DELETE CASCADE` on all foreign key constraints. Deleting an aircraft cleanly and automatically removes all associated sensor readings, predictions, and work orders, preventing orphan records.

### Q3: How do you prevent SQL injection?
**Answer:** All database operations use **parameterized queries** with `%s` tuple substitution (`cursor.execute(sql, (param1, param2))`). User inputs are never directly concatenated into SQL strings.

---

## 6. Architecture & Scalability Considerations

### Q: "How does the prediction service maintain sub-30ms latency under high load?"
**Answer:** We follow a singleton pattern where the Random Forest model and MinMaxScaler are loaded into memory once when the Flask server initializes. During a `POST /api/predict` request, the model only executes inference (`model.predict()`), which takes under 30 milliseconds. We never retrain the model inside an HTTP request.

### Q: "How would this system scale in a commercial airline cloud environment?"
**Answer:** The architecture is decoupled and container-ready:
1. The Flask REST API can be packaged as a lightweight Docker container and deployed across AWS ECS / Kubernetes behind an Application Load Balancer.
2. The MySQL database maps directly to AWS RDS Aurora with read replicas for analytics queries.
3. The React/Vite single-page application is compiled into static assets and distributed globally via Amazon CloudFront CDN and S3.
4. Real-time telemetry can be ingested via Apache Kafka or AWS Kinesis to handle telemetry streams from hundreds of concurrent aircraft in flight.
