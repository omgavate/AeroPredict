# AeroPredict - Implementation Plan & Final API Specifications

## 1. Development Principles & Architecture Compliance

1. **Modular Phased Strategy:** Incremental development ensuring complete isolation between Presentation (React), Application (Flask), Machine Learning, and Persistence (MySQL).
2. **Strict Verification:** Every endpoint, service, and user-facing component validated through automated unit/integration tests before progressing to the next phase.
3. **Reproducible Machine Learning:** GroupKFold cross-validation (grouped strictly by engine `unit_number`) to prevent temporal data leakage. Empirical evaluation against ground-truth labels in `RUL_FD001.txt`.
4. **Data Integrity & Relational Safety:** Strict foreign keys with cascade constraints, comprehensive payload validation, parameterized SQL execution, and responsive error handling.

---

## 2. Final REST API Specification

All API responses follow a uniform JSON structure:

**Success Response Envelope:**
```json
{
  "success": true,
  "data": { ... },
  "message": "Descriptive success string"
}
```

**Error Response Envelope:**
```json
{
  "success": false,
  "error": "Error category",
  "message": "Specific error details"
}
```

---

### 2.1 System Health & Diagnostics
| Method | Endpoint | Description | Status Code |
| :--- | :--- | :--- | :---: |
| `GET` | `/` | API server info, version, and status | `200` |
| `GET` | `/api/health` | Comprehensive MySQL connection pool and system health check | `200` / `503` |

---

### 2.2 Aircraft Fleet Management (`/api/aircraft`)
| Method | Endpoint | Parameters / Payload | Description | Status Code |
| :--- | :--- | :--- | :--- | :---: |
| `GET` | `/api/aircraft` | Query: `search`, `status` | List fleet aircraft with cycles and pending counts | `200` |
| `POST` | `/api/aircraft` | Body: `{tail_number, model, manufacturer, manufacturing_year, engine_type, cmapss_unit_id, current_cycles, flight_hours, status}` | Register new aircraft into MySQL | `201` / `400` |
| `GET` | `/api/aircraft/<id>` | Path: `id` | Retrieve single aircraft details | `200` / `404` |
| `PUT` | `/api/aircraft/<id>` | Body: updated aircraft fields | Update airframe profile or operational status | `200` / `400` / `404` |
| `DELETE` | `/api/aircraft/<id>` | Path: `id` | Delete aircraft (cascades to readings, orders, alerts) | `200` / `404` |

---

### 2.3 Engine Health Monitoring & Sensor Telemetry (`/api/aircraft/<id>/sensors`, `/api/engine`)
| Method | Endpoint | Parameters / Payload | Description | Status Code |
| :--- | :--- | :--- | :--- | :---: |
| `GET` | `/api/aircraft/<id>/sensors/latest` | Path: `id` (Alias: `/api/engine/<id>/readings`) | Get current cycle and all 21 physical sensor readings | `200` / `404` |
| `GET` | `/api/aircraft/<id>/sensors/history` | Query: `limit`, `cycle_start`, `cycle_end` (Alias: `/api/engine/<id>/history`) | Historical time-series sensor wear data | `200` / `404` |
| `POST` | `/api/aircraft/<id>/sensors/advance-cycle` | Path: `id` (Alias: `/api/engine/<id>/advance`) | Simulate advancing engine cycle by ingesting next wear state | `200` / `404` |
| `POST` | `/api/aircraft/<id>/sensors` | Body: `{cycle, setting_1..3, sensor_1..21}` | Custom sensor ingestion endpoint | `201` / `400` / `404` |
| `GET` | `/api/aircraft/<id>/engine` | Path: `id` (Alias: `/api/engine/<id>`) | 7 subsystem diagnostic health breakdown report | `200` / `404` |

---

### 2.4 Predictive Maintenance & Prognostics (`/api/predict`)
| Method | Endpoint | Parameters / Payload | Description | Status Code |
| :--- | :--- | :--- | :--- | :---: |
| `POST` | `/api/predict` | Body: `{aircraft_id, cycle, telemetry: {sensor_1..21}}` | Run Random Forest RUL inference, classify risk, generate recommendations, persist prediction & alert | `200` / `400` / `404` |
| `GET` | `/api/predict/latest/<id>` | Path: `id` | Retrieve most recent saved prediction for aircraft | `200` / `404` |
| `GET` | `/api/predict/history/<id>` | Path: `id`, Query: `limit` | Historical RUL prediction series for aircraft | `200` / `404` |
| `GET` | `/api/predict/model-info` | None | Returns verified model hyperparameters and empirical metrics | `200` |

---

### 2.5 Maintenance Work Order Management (`/api/maintenance`)
| Method | Endpoint | Parameters / Payload | Description | Status Code |
| :--- | :--- | :--- | :--- | :---: |
| `GET` | `/api/maintenance` | Query: `aircraft_id`, `status`, `priority`, `search` | List work orders joined with aircraft metadata | `200` |
| `POST` | `/api/maintenance` | Body: `{aircraft_id, title, description, priority, status, scheduled_date}` | Create new work order & update airframe status | `201` / `400` |
| `GET` | `/api/maintenance/<id>` | Path: `id` | Retrieve single work order details | `200` / `404` |
| `PUT` | `/api/maintenance/<id>` | Body: updated work order fields (`status`, `notes`, etc.) | Update work order status and technician notes | `200` / `400` / `404` |
| `DELETE` | `/api/maintenance/<id>` | Path: `id` | Delete work order record from MySQL | `200` / `404` |
| `GET` | `/api/maintenance/history/<id>`| Path: `id` (Alias: `/api/aircraft/<id>/maintenance`) | Comprehensive maintenance history for specific aircraft | `200` / `404` |

---

### 2.6 Executive Fleet Dashboard (`/api/dashboard`)
| Method | Endpoint | Parameters / Payload | Description | Status Code |
| :--- | :--- | :--- | :--- | :---: |
| `GET` | `/api/dashboard` | None | Complete aggregated dashboard payload (KPI stats, health, maintenance distribution, alerts, fleet summary, activity) | `200` |
| `GET` | `/api/dashboard/stats` | None | Fleet KPI counts & airworthiness percentage | `200` |
| `GET` | `/api/dashboard/health-overview`| None | Fleet engine health breakdown, mean RUL & risk counts | `200` |
| `GET` | `/api/dashboard/alerts` | Query: `limit`, `unresolved` | Active maintenance alerts feed | `200` |
| `PUT` | `/api/dashboard/alerts/<id>/resolve` | Path: `id` | Mark maintenance alert as acknowledged / resolved | `200` / `404` |
| `GET` | `/api/dashboard/fleet` | None | Fleet quick-scan telemetry with calculated health scores | `200` |
| `GET` | `/api/dashboard/maintenance-distribution`| None | Work order backlog counts by status and priority | `200` |
| `GET` | `/api/dashboard/activity` | Query: `limit` | Chronological operational timeline of events | `200` |

---

## 3. Development Phase Roadmap & Verification Status

| Milestone / Phase | Scope & Key Deliverables | Status | Verification Summary |
| :--- | :--- | :---: | :--- |
| **Milestone 0** | Architecture, environment verification, NASA C-MAPSS dataset validation | 🟢 Complete | 20,631 train rows, 13,096 test rows, 100 RUL ground-truth confirmed |
| **Phase 1** | System architecture, DDL schema, API planning & project specifications | 🟢 Complete | Documentation verified, 5 tables defined, strict FK constraints |
| **Phase 2** | React 18 SPA, Vite setup, Bootstrap 5 Harbor Blue theme, 5 module pages | 🟢 Complete | Clean Vite production build, responsive layout, reusable components |
| **Phase 3** | Flask backend setup, MySQL connection pool, health check API, unit tests | 🟢 Complete | 5 backend tests passing, `GET /api/health` confirmed |
| **Phase 4** | Aircraft Fleet Management CRUD APIs, React UI integration, search & filters | 🟢 Complete | 7 integration tests passing (12 total), form validations active |
| **Phase 5** | NASA C-MAPSS preprocessing, variance audit, rolling feature extraction | 🟢 Complete | 7 invariant sensors dropped, 45 rolling features, 6 unit tests passing |
| **Phase 6** | ML model training (Random Forest), GroupKFold CV, artifact persistence | 🟢 Complete | 5-fold CV (MAE 11.17), 100 test engines (MAE 12.70), 5 tests passing |
| **Phase 7** | Prediction service & API (`POST /api/predict`), physical validation, alerts | 🟢 Complete | 10 integration tests passing (22 total), MySQL persistence active |
| **Phase 8** | Engine Health Monitoring, C-MAPSS mapping, 21-sensor ingestion, Recharts | 🟢 Complete | 9 integration tests passing (31 total), 7 subsystem health statuses |
| **Phase 9** | Predictive Maintenance Interface, real-time RUL gauge, tone-coded cards | 🟢 Complete | End-to-end integration verified, clean Vite production build |
| **Phase 10** | Maintenance Management CRUD, status lifecycle, airframe status realignment | 🟢 Complete | 9 integration tests passing (40 total), Add/Edit/View modals active |
| **Phase 11** | Unified Dashboard Integration, real KPIs, Recharts donut & bar charts | 🟢 Complete | 9 integration tests passing (49 total), alert resolution active |
| **Phase 12** | Full Application Technical Audit, E2E lifecycle test, security verification | 🟢 Complete | 50/50 automated tests passing, 0 orphans/nulls, clean Vite build |
| **Phase 13** | Academic Documentation, Project Report, Architecture Diagrams, Viva Prep | 🟢 Complete | Complete 23-chapter report, 6 Mermaid diagrams, viva defense guide |
