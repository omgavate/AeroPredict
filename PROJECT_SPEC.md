# AeroPredict - Project Specification

## 1. Project Identity
- **Project Title:** AeroPredict – AI-Powered Aircraft Engine Health Monitoring and Predictive Maintenance System
- **Academic Context:** MCA Capstone Mini-Project (Predictive Maintenance & Asset Triage System)
- **Domain:** Aviation Asset Management, Internet of Things (IoT) Sensor Monitoring, Machine Learning
- **Target Dataset:** NASA C-MAPSS (Commercial Modular Aero-Propulsion System Simulation) Turbofan Engine Degradation Dataset – Subset FD001

---

## 2. Executive Summary & Objective
AeroPredict is a full-stack, enterprise-style web application and prognostic AI system designed to eliminate unscheduled aircraft groundings and optimize turbofan engine maintenance. By processing 21-channel physical degradation sensor telemetry from the **NASA C-MAPSS FD001** simulation dataset, AeroPredict:
1. Simulates continuous engine wear and tracks multi-sensor degradation trends.
2. Ingests and stores sensor readings in an ACID-compliant MySQL database.
3. Predicts Remaining Useful Life (RUL) in flight cycles using a trained **Random Forest Regressor** ($R^2 = 0.8044$, $\text{MAE} = 12.70\text{ cycles}$).
4. Categorizes failure risk into 4 tiers (**Low**, **Medium**, **High**, **Critical**).
5. Automatically generates contextual maintenance recommendations.
6. Manages the complete work order lifecycle from triage to completion.

---

## 3. Technology Stack & Specifications

| Layer | Technology | Version | Role in AeroPredict |
| :--- | :--- | :--- | :--- |
| **Frontend UI** | React.js (SPA) | `^18.3.1` | Reactive user interface with component-driven architecture |
| **Build System** | Vite | `^6.1.0` | Ultra-fast build pipeline with optimized production bundling |
| **CSS Framework** | Bootstrap 5 | `^5.3.3` | Responsive layout, grid system, cards, modals, and typography |
| **Icons** | Lucide React | `^0.475.0` | Aviation and metric icon set |
| **Telemetry Charts**| Recharts | `^2.15.1` | Multi-channel wear curves, availability donuts, backlog bars |
| **HTTP Client** | Axios | `^1.7.9` | Asynchronous REST client with error interception and fallback |
| **Backend API** | Python Flask | `^3.1.0` | RESTful API server with modular blueprint architecture |
| **CORS Middleware**| Flask-CORS | `^5.0.0` | Cross-Origin Resource Sharing handling for React clients |
| **Database** | MySQL Server | `8.0+` | Relational database with InnoDB engine and foreign key constraints |
| **DB Driver** | mysql-connector-python | `^9.2.0` | Native Python connection pool with thread-safe management |
| **Machine Learning**| Scikit-learn | `^1.6.1` | Random Forest Regressor and preprocessing transformers |
| **Data Processing** | Pandas & NumPy | `^2.2.3` | Time-series rolling feature engineering and matrix computation |
| **Serialization** | Joblib | `^1.4.2` | Model artifact persistence and low-latency inference engine |
| **Dataset** | NASA C-MAPSS FD001 | 20,631 rows | Run-to-failure turbofan engine sensor telemetry |

---

## 4. NASA C-MAPSS FD001 Dataset Details

### Operational Conditions & Fault Modes
- **Dataset Subset:** FD001
- **Flight Condition:** Single condition (Sea Level: Altitude 0 ft, Mach 0.0)
- **Fault Mode:** High-Pressure Compressor (HPC) Degradation
- **Training Engines:** 100 units (run to failure, 20,631 records)
- **Testing Engines:** 100 units (truncated prior to failure, 13,096 records)
- **Ground Truth Test RUL:** 100 final cycles in `RUL_FD001.txt`

### Sensor Channels & Physical Mapping (26 Columns Total)
1. `unit_number`: Engine identifier (1–100)
2. `time_in_cycles`: Elapsed flight cycles (1, 2, ...)
3. `setting_1`: Operational Setting 1
4. `setting_2`: Operational Setting 2
5. `setting_3`: Operational Setting 3 (100.0)
6. `sensor_1` to `sensor_21`: 21 continuous physical sensor measurements:
   - `sensor_1` (T2): Total temperature at fan inlet (°R) — *Invariant (dropped in ML)*
   - `sensor_2` (T24): Total temperature at LPC outlet (°R)
   - `sensor_3` (T30): Total temperature at HPC outlet (°R)
   - `sensor_4` (T50): Total temperature at LPT outlet (°R)
   - `sensor_5` (P2): Pressure at fan inlet (psia) — *Invariant (dropped in ML)*
   - `sensor_6` (P15): Total pressure in bypass-duct (psia) — *Invariant (dropped in ML)*
   - `sensor_7` (P30): Total pressure at HPC outlet (psia)
   - `sensor_8` (Nf): Physical fan speed (rpm)
   - `sensor_9` (Nc): Physical core speed (rpm)
   - `sensor_10` (epr): Engine pressure ratio (P50/P2) — *Invariant (dropped in ML)*
   - `sensor_11` (Ps30): Static pressure at HPC outlet (psia)
   - `sensor_12` (phi): Ratio of fuel flow to Ps30 (pps/psia)
   - `sensor_13` (NRf): Corrected fan speed (rpm)
   - `sensor_14` (NRc): Corrected core speed (rpm)
   - `sensor_15` (BPR): Bypass Ratio
   - `sensor_16` (farB): Burner fuel-air ratio — *Invariant (dropped in ML)*
   - `sensor_17` (htBleed): Bleed Enthalpy
   - `sensor_18` (Nf_dmd): Demanded fan speed (rpm) — *Invariant (dropped in ML)*
   - `sensor_19` (PCNfR_dmd): Demanded corrected fan speed (rpm) — *Invariant (dropped in ML)*
   - `sensor_20` (W31): HPT coolant bleed (lbm/s)
   - `sensor_21` (W32): LPT coolant bleed (lbm/s)

---

## 5. Machine Learning Feature Matrix & Methodology

### 5.1 Causal Rolling Features (45 Total Features)
To prevent temporal data leakage, features only aggregate current and past cycles:
- **Base Features (17):** `time_in_cycles`, `setting_1`, `setting_2`, and 14 informative sensors (`sensor_2`, `3`, `4`, `7`, `8`, `9`, `11`, `12`, `13`, `14`, `15`, `17`, `20`, `21`).
- **Rolling Means (14):** 5-cycle backward rolling mean across the 14 informative sensors (`sensor_X_roll_mean`).
- **Rolling Standard Deviations (14):** 5-cycle backward rolling standard deviation across the 14 informative sensors (`sensor_X_roll_std`).

### 5.2 Target Formulation (Piecewise Linear RUL)
Early operating cycles exhibit negligible wear. Target Remaining Useful Life is capped at **125 cycles**:
$$\text{RUL}_{\text{target}}(t) = \min(125, \text{RUL}_{\text{raw}}(t))$$

### 5.3 Empirical Model Performance

| Metric | 5-Fold GroupKFold CV | Held-Out Test Set (Capped $\le 125$) | Held-Out Test Set (Raw) |
| :--- | :---: | :---: | :---: |
| **Mean Absolute Error (MAE)** | **11.17 cycles** | **12.70 cycles** | **13.77 cycles** |
| **Root Mean Squared Error (RMSE)** | **16.57 cycles** | **17.72 cycles** | **18.88 cycles** |
| **Coefficient of Determination ($R^2$)**| **0.8419** | **0.8044** | **0.7936** |
| **NASA Asymmetric Loss Score** | 129,694.6 | **564.5** | 632.4 |

---

## 6. Risk Tiering & Recommendation Architecture

| Risk Tier | Condition | Color Code | Action Required | Prescribed Action |
| :--- | :--- | :---: | :---: | :--- |
| **Low Risk** | $\text{RUL} > 75$ cycles | 🟢 Green | Routine | Nominal performance. Continue routine scheduled A-Check inspections. |
| **Medium Risk** | $31 \le \text{RUL} \le 75$ cycles | 🟡 Amber | Watchlist | Accelerating wear detected. Increase borescope inspection frequency. |
| **High Risk** | $11 \le \text{RUL} \le 30$ cycles | 🟠 Orange | Maintenance Due | Schedule shop visit. Inspect HPC compressor blades and turbine seals. |
| **Critical Risk**| $\text{RUL} \le 10$ cycles | 🔴 Red | Ground / Emergency | Severe degradation. Ground aircraft immediately; emergency engine overhaul. |

---

## 7. Verification Standards
- **Decoupled Architecture:** React frontend, Flask backend, and MySQL database run independently.
- **Data Integrity:** 0 orphan records, 0 duplicate keys, 0 null violations.
- **Automated Verification:** 50/50 automated backend and E2E integration tests passing.
- **Production Readiness:** Clean Vite production build (`dist/` generated with 0 errors).
