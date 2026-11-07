# AeroPredict - Project Specification

## 1. Project Identity
- **Project Title:** AeroPredict – AI-Powered Aircraft Engine Health Monitoring and Predictive Maintenance System
- **Academic Context:** MCA College Mini-Project (Educational Predictive-Maintenance Prototype)
- **Domain:** Aviation Asset Management, Internet of Things (IoT) Sensor Monitoring, Machine Learning
- **Target Dataset:** NASA C-MAPSS (Commercial Modular Aero-Propulsion System Simulation) Turbofan Engine Degradation Dataset - Subset FD001

---

## 2. Executive Summary & Objective
AeroPredict is designed as an interactive web-based engineering dashboard and predictive maintenance platform. In modern aviation, unplanned engine downtime causes severe financial loss and safety hazards. By applying Machine Learning to multi-sensor time-series degradation telemetry, AeroPredict predicts an engine's **Remaining Useful Life (RUL)** in operational cycles, categorizes failure risk, and recommends proactive maintenance actions.

> [!NOTE]
> This system is an educational prototype and academic demonstration tool. It does not replace certified FAA/EASA airworthiness engineering systems.

---

## 3. Technology Stack & Environment

| Layer | Technology | Version / Specifics | Role |
| :--- | :--- | :--- | :--- |
| **Frontend** | React.js with Vite | Node v24+, React 18+ | High-performance SPA user interface |
| | Bootstrap 5 | Standard responsive CSS | Clean, consistent layout and components |
| | Axios | Latest | HTTP client for backend REST API calls |
| | React Router DOM | v6+ | Client-side routing between modules |
| | Recharts | Latest | Interactive sensor trend and degradation charts |
| | Lucide React | Latest | Modern icon set for aviation metrics |
| **Backend** | Python Flask | Python 3.13+, Flask 3+ | Lightweight RESTful microservice API |
| | Flask-CORS | Latest | Cross-Origin Resource Sharing handling |
| **Database** | MySQL | MySQL Server 8.0+ | Relational persistence for fleet, telemetry & tasks |
| | mysql-connector-python | Latest | Native Python MySQL driver with connection pooling |
| **Machine Learning**| Scikit-learn | Latest | Random Forest Regressor and preprocessing |
| | Pandas & NumPy | Latest | Sensor feature extraction & matrix math |
| | Joblib | Latest | Model serialization and artifact persistence |
| **Data Source** | NASA C-MAPSS FD001 | Text-based space-delimited | Simulated turbofan run-to-failure telemetry |

---

## 4. NASA C-MAPSS FD001 Dataset Details

### Operational Conditions & Fault Modes
- **Data subset:** FD001
- **Operating Conditions:** Sea Level (Single condition: Altitude 0 ft, Mach 0.0, etc.)
- **Fault Mode:** High-Pressure Compressor (HPC) Degradation
- **Engines in Training Set:** 100 units (run to failure)
- **Engines in Test Set:** 100 units (time-series truncated prior to failure)
- **Ground Truth Test RUL:** Provided in `RUL_FD001.txt`

### Data Columns (26 Columns Total)
1. `unit_number`: Engine identifier (Integer: 1 to 100)
2. `time_in_cycles`: Operational flight cycles (Integer: 1, 2, ...)
3. `setting_1`: Operational Setting 1
4. `setting_2`: Operational Setting 2
5. `setting_3`: Operational Setting 3
6. `sensor_1` to `sensor_21`: 21 continuous sensor measurements:
   - `sensor_1` (T2): Total temperature at fan inlet (°R)
   - `sensor_2` (T24): Total temperature at LPC outlet (°R)
   - `sensor_3` (T30): Total temperature at HPC outlet (°R)
   - `sensor_4` (T50): Total temperature at LPT outlet (°R)
   - `sensor_5` (P2): Pressure at fan inlet (psia)
   - `sensor_6` (P15): Total pressure in bypass-duct (psia)
   - `sensor_7` (P30): Total pressure at HPC outlet (psia)
   - `sensor_8` (Nf): Physical fan speed (rpm)
   - `sensor_9` (Nc): Physical core speed (rpm)
   - `sensor_10` (epr): Engine pressure ratio (P50/P2)
   - `sensor_11` (Ps30): Static pressure at HPC outlet (psia)
   - `sensor_12` (phi): Ratio of fuel flow to Ps30 (pps/psia)
   - `sensor_13` (NRf): Corrected fan speed (rpm)
   - `sensor_14` (NRc): Corrected core speed (rpm)
   - `sensor_15` (BPR): Bypass Ratio
   - `sensor_16` (farB): Burner fuel-air ratio
   - `sensor_17` (htBleed): Bleed Enthalpy
   - `sensor_18` (Nf_dmd): Demanded fan speed (rpm)
   - `sensor_19` (PCNfR_dmd): Demanded corrected fan speed (rpm)
   - `sensor_20` (W31): HPT coolant bleed (lbm/s)
   - `sensor_21` (W32): LPT coolant bleed (lbm/s)

---

## 5. Required Functional Modules

### Module 1: Executive Dashboard
- **Fleet Summary KPI Cards:** Total Aircraft, Operational, Under Maintenance, Attention Required.
- **Engine Health Overview:** Distribution of fleet health scores and RUL brackets.
- **Active Critical Alerts:** Real-time alert list for aircraft with RUL below threshold (< 30 cycles).
- **Quick Actions:** Shortcuts to add aircraft, record maintenance, or inspect sensors.

### Module 2: Aircraft Fleet Management
- **Add Aircraft:** Tail number, aircraft model, manufacturer, engine type, assigned C-MAPSS engine unit ID, current cycles, operational status.
- **View Fleet Table:** Searchable and filterable table with status badges and quick view links.
- **Update Aircraft:** Edit operational status, engine type, or assigned unit.
- **Delete Aircraft:** Cascade deletion safeguards with confirmation modal.
- **Search & Filter:** Instant search by tail number or model; filter by operational status.

### Module 3: Engine Health Monitoring
- **Real-Time / Simulated Telemetry Viewer:** Displays current cycle and active sensor parameters.
- **Telemetry Ingestion / Simulation:** Button or trigger to advance flight cycle and simulate incoming sensor data from C-MAPSS dataset.
- **Multi-Sensor Historical Trend Charts:** Interactive line charts (via Recharts) displaying key degradation indicators (e.g., T30, P30, Nc, BPR) over elapsed cycles.
- **Health Index Gauges:** Visual indicators of engine condition based on deviation from baseline nominal readings.

### Module 4: Predictive Maintenance & RUL Inference
- **Machine Learning Inference:** Random Forest Regressor predicts remaining flight cycles before failure threshold.
- **Risk Classification:**
  - **Low Risk (Normal):** Predicted RUL > 75 cycles (Green)
  - **Medium Risk (Watchlist):** Predicted RUL 31–75 cycles (Yellow)
  - **High Risk (Maintenance Due):** Predicted RUL 11–30 cycles (Orange)
  - **Critical Risk (Immediate Action):** Predicted RUL ≤ 10 cycles (Red)
- **Automated Recommendations:** Contextual recommendations generated dynamically (e.g., "Schedule B-Check inspection", "Inspect HPC compressor blades", "Grounded immediately").
- **Historical Prediction Log:** Track how predicted RUL changes as operational cycles accumulate.

### Module 5: Maintenance Management
- **Work Order Creation:** Log scheduled or unscheduled maintenance tasks tied to a specific aircraft.
- **Work Order Tracking:** Priority (Low, Medium, High, Critical), Status (Scheduled, In Progress, Completed, Cancelled).
- **Technician Notes & Date Logging:** Scheduled date, completion date, and work performed log.
- **Maintenance History View:** Complete audit log of past maintenance per aircraft.

---

## 6. Non-Functional & Quality Standards
- **Separation of Concerns:** Strict decoupling between UI (React), API/Business Logic (Flask), and Storage (MySQL).
- **Data Integrity:** Foreign keys on all relational tables, input validation on both client and server sides.
- **ML Rigor:** Engine-level group splitting for cross-validation to prevent temporal data leakage. No synthetic mock data substituting NASA C-MAPSS.
- **Maintainability:** Modular file structure with clean comments and readable function names suitable for an MCA capstone presentation.
