# AeroPredict - Viva Voce & Oral Defense Preparation Guide

This guide is designed to help an **MCA student** confidently defend the **AeroPredict** project during external viva voce examinations.

---

## 1. Quick Project Elevator Pitch (30–60 Seconds)

> *"AeroPredict is an AI-powered predictive maintenance and real-time engine health monitoring system for commercial aircraft fleets. In aviation, unscheduled engine breakdowns cause massive financial loss and safety hazards. AeroPredict ingests multi-sensor thermodynamic telemetry from the NASA C-MAPSS turbofan dataset and uses an ensemble Random Forest Regressor to predict an engine's Remaining Useful Life (RUL) in flight cycles. Based on predicted RUL, it categorizes failure risk into four tiers, prescribes maintenance actions, and enables engineers to create and track work orders through an interactive React dashboard backed by Flask and MySQL."*

---

## 2. Comprehensive Module Walkthrough

### Module 1: Executive Fleet Dashboard
- **What it does:** Provides a high-level operational quick-scan for fleet directors and chief engineers.
- **Key Features:**
  - 6 KPI metric cards (Total Aircraft, Operational, Under Maintenance, Attention Required, Pending Maintenance, Active Alerts).
  - Recharts Donut chart showing fleet airworthiness distribution.
  - Recharts Bar chart showing work order backlog by status.
  - Turbofan health degradation progress bars for individual airframes.
  - Active alert feed with instant "Acknowledge / Resolve" action.

### Module 2: Aircraft Fleet Management
- **What it does:** Serves as the central airframe registry.
- **Key Features:**
  - Full CRUD operations (Add, View, Edit, Delete aircraft).
  - Stores Tail Number, Model, Manufacturer, Engine Type, NASA C-MAPSS Unit Mapping, Operating Cycles, and Status.
  - Real-time search and status filtering with cascade delete protection.

### Module 3: Engine Health Monitoring & Telemetry
- **What it does:** Provides real-time condition monitoring of turbofan components.
- **Key Features:**
  - 21-channel physical sensor matrix (inlet/outlet temperatures, pressures, spool speeds, bypass ratios).
  - 4 interactive Recharts degradation curves plotting sensor trends across elapsed flight cycles.
  - "Advance Cycle" simulation feature to demonstrate wear progression cycle-by-cycle.
  - Diagnostic health status across 7 critical engine subsystems (Fan, LPC, HPC, Combustor, LPT, Bypass/Bleed, Cooling).

### Module 4: Predictive Maintenance & Prognostics
- **What it does:** The core AI prognostic engine.
- **Key Features:**
  - Evaluates live telemetry using the trained Random Forest model in $<30\text{ ms}$.
  - Visual RUL circular gauge displaying remaining safe flight cycles.
  - 4-tier risk classification (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
  - Contextual maintenance prescriptions (e.g. HPC borescope inspection, turbine seal overhaul).
  - Prediction history table persisted in MySQL.

### Module 5: Maintenance Management
- **What it does:** Manages maintenance work orders and technician dispatch.
- **Key Features:**
  - Create work orders tied to specific airframes with priority (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
  - Status lifecycle tracking (`PENDING` $\rightarrow$ `SCHEDULED` $\rightarrow$ `IN_PROGRESS` $\rightarrow$ `COMPLETED`).
  - Automatically updates aircraft status (e.g., switches to `ATTENTION_REQUIRED` or `UNDER_MAINTENANCE`).
  - Detailed modal view with technician notes and completion logs.

---

## 3. Technology Choices Justification

| Question | Recommended Answer |
| :--- | :--- |
| **Why React + Vite instead of plain HTML/JS or Django templates?** | React's component-based virtual DOM allows dynamic re-rendering of live sensor telemetry and charts without reloading the page. Vite provides ultra-fast Hot Module Replacement (HMR) and optimized Rollup tree-shaking for quick production bundling. |
| **Why Flask instead of Django?** | AeroPredict follows a decoupled microservice architecture. Flask is lightweight, unopinionated, and imposes zero unnecessary ORM bloat, allowing direct control over API route blueprints, SQL connection pooling, and low-latency ML inference. |
| **Why MySQL over MongoDB / NoSQL?** | Aviation asset management requires strict ACID compliance and relational integrity. An airframe has strict 1-to-many relationships with sensor readings, alerts, and work orders. MySQL's foreign key constraints ensure 0 orphan records. |
| **Why Random Forest instead of Deep Learning (LSTM/CNN)?** | Random Forest Regressor provides superior tabular feature handling, resistance to overfitting, deterministic training, and natural feature importance ranking. For tabular time-series features with rolling statistics, Random Forest trains in 14 seconds while delivering an $R^2$ of 0.8044 and MAE under 13 cycles. |

---

## 4. NASA C-MAPSS Dataset Questions

### Q1: What is the C-MAPSS dataset?
**Answer:** C-MAPSS stands for **Commercial Modular Aero-Propulsion System Simulation**, created by NASA Glenn Research Center and Pratt & Whitney. It is a benchmark simulation tool that models realistic turbofan engine degradation under varying operating cycles, capturing thermodynamic wear across temperatures, pressures, and rotational speeds until functional failure.

### Q2: Which sub-dataset did you use?
**Answer:** We used **FD001**.
- **Operating Conditions:** Single condition (Sea Level: Altitude 0 ft, Mach 0.0).
- **Fault Mode:** High-Pressure Compressor (HPC) degradation.
- **Training Set:** 100 engines run to failure (20,631 cycles).
- **Test Set:** 100 engines truncated prior to failure (13,096 cycles).
- **Ground Truth:** `RUL_FD001.txt` containing the actual remaining cycles for each test engine.

### Q3: Why are there 21 sensors and why did you drop 7 of them?
**Answer:** The dataset logs 21 physical sensor measurements. Statistical variance analysis revealed that 7 sensors (`sensor_1`, `sensor_5`, `sensor_6`, `sensor_10`, `sensor_16`, `sensor_18`, `sensor_19`) have a standard deviation of **0.0000** across all 20,631 rows. Because they do not vary, they carry zero degradation signal and would only add computational noise. We dropped them, leaving **14 informative sensors**.

---

## 5. Machine Learning Concepts & RUL Explanation

### Q1: What is RUL (Remaining Useful Life)?
**Answer:** RUL is the number of operational flight cycles an engine can safely continue to fly before component degradation exceeds the allowable physical safety threshold. 
- Example: If an engine is at cycle 192 and failure occurs at cycle 198, its true RUL is $198 - 192 = 6\text{ cycles}$.

### Q2: What is Piecewise Linear RUL Capping and why is it used?
**Answer:** In physical turbofan engines, negligible wear occurs during the early cycles of operation; the engine operates in a nominal "as-new" state. If we assume linear degradation from cycle 1, the model tries to learn degradation where none exists. By applying a piecewise linear cap at **125 cycles**, we treat all early cycles as having an RUL of 125, allowing the model to focus learning on the inflection point where wear actually begins.

### Q3: What features did you engineer? (Explain the 45 features)
**Answer:** We formulated 45 causal features:
1. `time_in_cycles` (1 feature): Current operating cycle.
2. Operational settings (2 features): `setting_1` and `setting_2`.
3. Informative sensors (14 features): Raw sensor values for the 14 active sensors.
4. Rolling Means (14 features): 5-cycle backward moving average ($\mu_5$) for each active sensor.
5. Rolling Standard Deviations (14 features): 5-cycle backward moving standard deviation ($\sigma_5$) capturing wear volatility.
Total: $1 + 2 + 14 + 14 + 14 = 45\text{ features}$.

### Q4: What is data leakage and how did you prevent it?
**Answer:** In time-series ML, data leakage occurs if:
1. **Lookahead Leakage:** Features use future data (e.g., centered rolling windows). We prevented this by using strictly backward-looking windows ($t-4$ to $t$).
2. **Cross-Validation Leakage:** Cycles from the same engine appear in both training and test folds. Standard $K$-Fold would leak temporal patterns. We used **GroupKFold** grouped strictly by `unit_number`, ensuring an engine's complete lifecycle is either entirely in the training split or entirely in the validation split.

---

## 6. Model Evaluation: MAE, RMSE & $R^2$ Explanation

### Q1: What are your actual model metrics?
**Answer:**
- **5-Fold Cross-Validation:** $\text{MAE} = 11.17\text{ cycles}$, $\text{RMSE} = 16.57\text{ cycles}$, $R^2 = 0.8419$.
- **Held-Out Test Set (100 engines):** $\text{MAE} = 12.70\text{ cycles}$, $\text{RMSE} = 17.72\text{ cycles}$, $R^2 = 0.8044$.
- **NASA Asymmetric Loss:** $564.5$ on test set.

### Q2: What is the difference between MAE and RMSE?
**Answer:**
- **Mean Absolute Error (MAE):** Average magnitude of errors without considering direction:
  $$\text{MAE} = \frac{1}{N} \sum |y - \hat{y}|$$
  Our MAE of 12.70 means our predictions are off by an average of ~12.7 flight cycles.
- **Root Mean Squared Error (RMSE):** Squares errors before averaging, heavily penalizing large outliers:
  $$\text{RMSE} = \sqrt{\frac{1}{N} \sum (y - \hat{y})^2}$$
  Our RMSE is 17.72. The closeness between MAE (12.7) and RMSE (17.7) confirms our model has very few severe outlier errors.

### Q3: What is the NASA Asymmetric Scoring Function?
**Answer:** In aviation maintenance, an **early prediction** ($\hat{y} < y$, predicting failure before it happens) causes minor premature maintenance, whereas a **late prediction** ($\hat{y} > y$, predicting an engine has life when it is about to fail) is catastrophic. The NASA scoring function penalizes late predictions exponentially:
- $d = \hat{y} - y$
- If $d < 0$ (early): $S = e^{-d/13} - 1$
- If $d \ge 0$ (late): $S = e^{d/10} - 1$

---

## 7. Database & System Architecture Questions

### Q1: Explain your MySQL database schema.
**Answer:** We have 5 normalized tables in `aeropredict_db`:
1. `aircraft`: Master fleet assets table (Primary key: `id`, unique `tail_number`).
2. `sensor_readings`: 21-sensor time series telemetry (Foreign key: `aircraft_id`).
3. `rul_predictions`: Model prediction log with RUL and risk tier (Foreign key: `aircraft_id`).
4. `maintenance_alerts`: Active alerts triggered by critical RUL or sensor anomalies (Foreign key: `aircraft_id`).
5. `maintenance_records`: Work orders with status lifecycle (`PENDING`, `SCHEDULED`, `IN_PROGRESS`, `COMPLETED`) (Foreign key: `aircraft_id`).

### Q2: What happens when an aircraft is deleted?
**Answer:** We configured `ON DELETE CASCADE` on all foreign key constraints. Deleting an aircraft cleanly and automatically removes all associated sensor readings, predictions, alerts, and work orders, preventing orphan records.

### Q3: How do you prevent SQL injection?
**Answer:** All database operations in our Python service layer use **parameterized queries** with `%s` tuple substitution (`cursor.execute(sql, (param1, param2))`). User inputs are never directly concatenated into SQL strings.

---

## 8. Potential Tough Examiner Questions & Model Answers

### Examiner: "Why didn't you deploy this to AWS or Azure cloud?"
**Answer:** *"For this MCA capstone project, our priority was developing a self-contained, reproducible, locally verifiable system with an isolated virtual environment and automated test suite. However, the system is fully container-ready: the Flask backend can be containerized into a Docker container and deployed to AWS Elastic Beanstalk or ECS, the MySQL database can map to AWS RDS, and the Vite frontend can be served via AWS S3 and CloudFront."*

### Examiner: "Can this system be used on a real Airbus or Boeing aircraft today?"
**Answer:** *"AeroPredict is an educational software prototype developed for academic demonstration. While it utilizes the genuine NASA C-MAPSS benchmark dataset, commercial aviation deployment requires Level-A DO-178C software certification, FAA/EASA airworthiness approvals, and hardware integration with onboard ARINC 429 / 629 avionics data buses."*

### Examiner: "How does the prediction service stay fast if you have hundreds of requests?"
**Answer:** *"We follow a singleton pattern where the Random Forest model and StandardScaler are loaded into memory once when the Flask server starts. During a `POST /api/predict` request, the model only executes inference (`model.predict()`), which takes under 30 milliseconds. We never retrain the model inside an HTTP request."*
