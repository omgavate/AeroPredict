# AeroPredict - Comprehensive Architectural Diagrams

This document collects all official UML and structural diagrams for the **AeroPredict** platform, formatted in standard Mermaid syntax.

---

## 1. System Architecture Diagram

```mermaid
flowchart TD
    subgraph Client["Presentation Tier (React 18 SPA)"]
        UI["React 18 UI (Vite + Bootstrap 5)"]
        RTR["React Router (7 Core Routes)"]
        RC["Recharts Visual Analytics"]
        AX["Axios HTTP Interceptor Layer"]
        UI --> RTR
        UI --> RC
        UI --> AX
    end

    subgraph Server["Application Tier (Flask REST API Server)"]
        FL["Flask Application Factory (Port 5000)"]
        CORS["Flask-CORS Policy"]
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

    subgraph Prognostics["Machine Learning Pipeline"]
        CMAPSS["NASA C-MAPSS FD001 (20,631 records)"]
        FE["Causal Rolling Feature Extractor (45 features)"]
        RF["Random Forest Regressor (100 Trees, Depth 18)"]
        MDL["Serialized Joblib Artifacts (.joblib & .json)"]
        
        CMAPSS --> FE --> RF --> MDL
        MDL --> PRS
    end

    subgraph Persistence["Persistence Tier (MySQL Server 8.0)"]
        POOL["Thread-Safe Connection Pool"]
        T1[("aircraft")]
        T2[("sensor_readings")]
        T3[("rul_predictions")]
        T4[("maintenance_alerts")]
        T5[("maintenance_records")]
        
        POOL --> T1
        POOL --> T2
        POOL --> T3
        POOL --> T4
        POOL --> T5
    end

    AX <-->|JSON over HTTP / REST| FL
    Services <--> POOL
```

---

## 2. Use Case Diagram

```mermaid
flowchart LR
    subgraph Users["Primary Actors"]
        FE["Flight Engineer"]
        MT["Maintenance Technician"]
        FM["Fleet Manager"]
    end

    subgraph UseCases["AeroPredict System Capabilities"]
        UC1["View Executive Dashboard & KPIs"]
        UC2["Register & Manage Aircraft Assets"]
        UC3["Monitor Real-Time Multi-Sensor Telemetry"]
        UC4["Simulate Engine Wear Cycles"]
        UC5["Request Prognostic RUL Inference"]
        UC6["Review Prescribed Maintenance Actions"]
        UC7["Create & Update Work Orders"]
        UC8["Acknowledge & Resolve Active Alerts"]
    end

    FE --> UC1
    FE --> UC3
    FE --> UC4
    FE --> UC5

    MT --> UC3
    MT --> UC6
    MT --> UC7
    MT --> UC8

    FM --> UC1
    FM --> UC2
    FM --> UC7
    FM --> UC8
```

---

## 3. Entity-Relationship (ER) Diagram

```mermaid
erDiagram
    AIRCRAFT ||--o{ SENSOR_READINGS : "transmits telemetry"
    AIRCRAFT ||--o{ RUL_PREDICTIONS : "receives predictions"
    AIRCRAFT ||--o{ MAINTENANCE_ALERTS : "triggers alerts"
    AIRCRAFT ||--o{ MAINTENANCE_RECORDS : "undergoes maintenance"

    AIRCRAFT {
        int id PK "Auto Increment"
        varchar tail_number UK "Unique, e.g. N101AP"
        varchar model "e.g. Boeing 737-800"
        varchar manufacturer "e.g. Boeing"
        int manufacturing_year "Manufacturing Year"
        varchar engine_type "e.g. CFM56-7B"
        int cmapss_unit_id UK "NASA C-MAPSS Unit (1-100)"
        int current_cycles "Elapsed Operating Cycles"
        int flight_hours "Total Flight Hours"
        enum status "OPERATIONAL, UNDER_MAINTENANCE, ATTENTION_REQUIRED, RETIRED"
        timestamp created_at
        timestamp updated_at
    }

    SENSOR_READINGS {
        bigint id PK "Auto Increment"
        int aircraft_id FK "References aircraft(id)"
        int cycle "Engine flight cycle number"
        decimal setting_1 "Operational setting 1"
        decimal setting_2 "Operational setting 2"
        decimal setting_3 "Operational setting 3"
        decimal sensor_1_to_21 "21 Physical Sensor Channels"
        timestamp recorded_at
    }

    MAINTENANCE_ALERTS {
        bigint id PK "Auto Increment"
        int aircraft_id FK "References aircraft(id)"
        enum alert_type "RUL_CRITICAL, RUL_WARNING, SENSOR_ANOMALY, MAINTENANCE_DUE"
        enum severity "LOW, MEDIUM, HIGH, CRITICAL"
        varchar message "Alert descriptive summary"
        int cycle "Telemetry cycle at trigger"
        decimal predicted_rul "Predicted RUL at trigger"
        boolean is_resolved "Resolution flag"
        timestamp resolved_at
        timestamp created_at
    }

    MAINTENANCE_RECORDS {
        int id PK "Auto Increment"
        int aircraft_id FK "References aircraft(id)"
        varchar title "Work order title"
        text description "Detailed maintenance description"
        enum priority "LOW, MEDIUM, HIGH, CRITICAL"
        enum status "PENDING, SCHEDULED, IN_PROGRESS, COMPLETED, CANCELLED"
        date scheduled_date "Planned maintenance date"
        date completed_date "Actual completion date"
        text technician_notes "Notes entered upon inspection"
        timestamp created_at
        timestamp updated_at
    }

    RUL_PREDICTIONS {
        bigint id PK "Auto Increment"
        int aircraft_id FK "References aircraft(id)"
        int cycle "Operating cycle at prediction"
        decimal predicted_rul "Inferred RUL in cycles"
        enum risk_level "LOW, MEDIUM, HIGH, CRITICAL"
        text recommendation "Automated maintenance prescription"
        timestamp predicted_at
    }
```

---

## 4. Data Flow Diagram (DFD Level-1)

```mermaid
flowchart TD
    User["Aviation Engineer / User"] -->|Select Aircraft & Cycle| P1["1.0 Telemetry Acquisition"]
    P1 -->|Query Cycle Telemetry| D1[("sensor_readings")]
    D1 -->|21-Channel Sensor Readings| P1
    P1 -->|Wear Data Vectors| P2["2.0 Engine Health Visualizer"]
    P2 -->|Multi-Sensor Degradation Curves| User

    User -->|Initiate Prognostic Prediction| P3["3.0 Prognostic Inference Service"]
    P3 -->|Extract 5-Cycle Backward History| D1
    P3 -->|Construct 45-Feature Vector| M1["Random Forest Model (.joblib)"]
    M1 -->|Predicted RUL Cycles| P3
    P3 -->|Persist Inferred RUL| D2[("rul_predictions")]
    P3 -->|If Critical/High Risk| D3[("maintenance_alerts")]
    P3 -->|RUL Gauge & Prescriptions| User

    User -->|Submit Work Order| P4["4.0 Maintenance Management"]
    P4 -->|Write Work Order Record| D4[("maintenance_records")]
    P4 -->|Update Aircraft Status| D5[("aircraft")]
    P4 -->|Updated Work Order Backlog| User

    D1 & D2 & D3 & D4 & D5 --> P5["5.0 Executive Dashboard Aggregator"]
    P5 -->|KPI Metrics & Visual Charts| User
```

---

## 5. Activity Diagram (Operational Lifecycle)

```mermaid
flowchart TD
    Start(["Start Application"]) --> Login["Access Executive Dashboard"]
    Login --> SelectNav{"Select Module"}

    SelectNav -->|"Fleet Assets"| ViewFleet["View Fleet Inventory"]
    ViewFleet --> ActionFleet{"Action?"}
    ActionFleet -->|"Add Aircraft"| RegAircraft["Input Details & Save to MySQL"] --> ViewFleet
    ActionFleet -->|"Telemetry"| ViewTelemetry
    ActionFleet -->|"Prognostics"| ViewPrognostics

    SelectNav -->|"Telemetry"| ViewTelemetry["Inspect 21-Sensor Telemetry Matrix"]
    ViewTelemetry --> AdvCycle{"Advance Cycle?"}
    AdvCycle -->|"Yes"| IngestWear["Simulate C-MAPSS Wear Step"] --> UpdateCurves["Update Recharts Degradation Curves"] --> ViewTelemetry
    AdvCycle -->|"No"| ViewTelemetry

    SelectNav -->|"Prognostics"| ViewPrognostics["Run RUL Inference"]
    ViewPrognostics --> EvalRisk{"Evaluate RUL Risk"}
    EvalRisk -->|"RUL > 75 (Low)"| LowRisk["Mark Nominal - Schedule A-Check"]
    EvalRisk -->|"31-75 (Medium)"| MedRisk["Place on Watchlist - Monitor Borescope"]
    EvalRisk -->|"11-30 (High)"| HighRisk["Trigger RUL_WARNING Alert & Plan Shop Visit"]
    EvalRisk -->|"<= 10 (Critical)"| CritRisk["Trigger RUL_CRITICAL Alert & Ground Aircraft"]

    HighRisk --> CreateWO["Create Maintenance Work Order"]
    CritRisk --> CreateWO
    CreateWO --> TrackWO["Assign Technician & Transition Status: PENDING -> IN_PROGRESS -> COMPLETED"]
    TrackWO --> ResolveAlert["Acknowledge & Resolve Alert"]
    ResolveAlert --> EndCycle(["Update Dashboard KPIs & End"])
```

---

## 6. Machine Learning Workflow Diagram

```mermaid
flowchart LR
    subgraph DataPrep["1. Ingestion & Preprocessing"]
        RAW["NASA C-MAPSS FD001\n(20,631 train rows)"]
        DROP["Drop 7 Invariant Sensors\n(std = 0)"]
        CAP["Piecewise Linear RUL\n(Cap at 125 cycles)"]
        RAW --> DROP --> CAP
    end

    subgraph FeatureEng["2. Causal Feature Engineering"]
        BASE["17 Base Features\n(Cycle, Settings, 14 Sensors)"]
        RMEAN["14 Rolling Means\n(Window W = 5)"]
        RSTD["14 Rolling Stds\n(Window W = 5)"]
        CAP --> BASE & RMEAN & RSTD
    end

    subgraph Validation["3. Zero-Leakage Cross-Validation"]
        VEC["45-Dimensional Causal Vector"]
        BASE & RMEAN & RSTD --> VEC
        GKF["5-Fold GroupKFold CV\n(Split by Engine unit_number)"]
        SCL["StandardScaler\n(Fitted on Train Split Only)"]
        VEC --> GKF --> SCL
    end

    subgraph ModelTrain["4. Model Training & Export"]
        RF["Random Forest Regressor\n(100 Trees, Depth 18, MinLeaf 2)"]
        EVAL["Evaluate on 100 Test Engines\n(MAE: 12.70, RMSE: 17.72)"]
        ART["Serialized Artifacts\n(Model, Scaler, Feature List)"]
        SCL --> RF --> EVAL --> ART
    end
```
