# AeroPredict - REST API Reference

This document provides the technical specification for all REST API endpoints exposed by the **AeroPredict** backend server.

---

## 1. Global Specifications

- **Base URL:** `http://localhost:5000/api`
- **Default Content-Type:** `application/json`
- **Cross-Origin Resource Sharing (CORS):** Enabled for all standard local clients (`http://localhost:5173`, `http://localhost:3000`).
- **Response Format:** All endpoints return standard JSON envelopes with status indicators:
  ```json
  {
    "success": true,
    "data": { ... }
  }
  ```
- **Centralized Error Responses:**
  ```json
  {
    "success": false,
    "error": "ErrorCategory",
    "message": "Human-readable explanation of failure",
    "details": {}
  }
  ```

---

## 2. Health & System Diagnostics

### `GET /api/health`
Checks server, database connection pool, and ML model availability.

**Response `200 OK`:**
```json
{
  "status": "healthy",
  "service": "AeroPredict REST API Server",
  "version": "1.0.0",
  "database": {
    "connected": true,
    "database": "aeropredict_db",
    "pool_active": true
  },
  "model": {
    "loaded": true,
    "model_type": "RandomForestRegressor",
    "features_count": 45,
    "cv_mae": 11.17,
    "test_mae": 12.70
  }
}
```

---

## 3. Fleet Asset Management

### `GET /api/aircraft`
Retrieves a paginated or filtered list of aircraft assets.

**Query Parameters:**
- `status` (optional): Filter by status (`OPERATIONAL`, `UNDER_MAINTENANCE`, `ATTENTION_REQUIRED`, `RETIRED`).
- `search` (optional): Filter by tail number, model, or manufacturer substring.

**Response `200 OK`:**
```json
{
  "success": true,
  "count": 6,
  "aircraft": [
    {
      "id": 1,
      "tail_number": "N101AP",
      "model": "Boeing 737-800",
      "manufacturer": "Boeing",
      "manufacturing_year": 2018,
      "engine_type": "CFM56-7B",
      "cmapss_unit_id": 1,
      "current_cycles": 192,
      "flight_hours": 4210,
      "status": "ATTENTION_REQUIRED",
      "created_at": "2026-11-07T16:11:00Z"
    }
  ]
}
```

### `POST /api/aircraft`
Registers a new aircraft in the fleet database.

**Request Body:**
```json
{
  "tail_number": "N550AP",
  "model": "Airbus A321neo",
  "manufacturer": "Airbus",
  "manufacturing_year": 2023,
  "engine_type": "CFM LEAP-1A",
  "cmapss_unit_id": 7,
  "current_cycles": 34,
  "flight_hours": 750,
  "status": "OPERATIONAL"
}
```

**Response `201 Created`:**
```json
{
  "success": true,
  "message": "Aircraft registered successfully",
  "aircraft_id": 7
}
```

### `GET /api/aircraft/<id>`
Retrieves full details for an individual aircraft asset.

**Response `200 OK`:**
```json
{
  "success": true,
  "aircraft": {
    "id": 1,
    "tail_number": "N101AP",
    "model": "Boeing 737-800",
    "manufacturer": "Boeing",
    "engine_type": "CFM56-7B",
    "current_cycles": 192,
    "flight_hours": 4210,
    "status": "ATTENTION_REQUIRED"
  }
}
```

---

## 4. Engine Health & Telemetry

### `GET /api/engine/readings/<aircraft_id>`
Retrieves historical 21-channel sensor records for an aircraft.

**Query Parameters:**
- `limit` (default: 50): Number of cycles to retrieve.
- `from_cycle` (optional): Start cycle filter.
- `to_cycle` (optional): End cycle filter.

**Response `200 OK`:**
```json
{
  "success": true,
  "aircraft_id": 1,
  "tail_number": "N101AP",
  "count": 50,
  "readings": [
    {
      "cycle": 192,
      "setting_1": -0.0007,
      "setting_2": -0.0004,
      "setting_3": 100.0,
      "sensor_1": 518.67,
      "sensor_2": 643.02,
      "sensor_3": 1599.82,
      "sensor_4": 1423.45,
      "sensor_7": 552.12,
      "sensor_8": 2388.19,
      "sensor_9": 9054.34,
      "sensor_11": 48.02,
      "sensor_12": 519.82,
      "sensor_13": 2388.21,
      "sensor_14": 8132.45,
      "sensor_15": 8.48,
      "sensor_17": 395.0,
      "sensor_20": 38.65,
      "sensor_21": 23.21
    }
  ]
}
```

### `POST /api/engine/readings`
Records an incoming flight cycle telemetry snapshot.

---

## 5. Predictive Maintenance & RUL Inference

### `POST /api/predict`
Calculates Remaining Useful Life (RUL), risk classification, and maintenance prescriptions.

**Request Body (Option A - Aircraft ID):**
```json
{
  "aircraft_id": 1
}
```

**Request Body (Option B - Direct Sensor Vector):**
```json
{
  "cycle": 192,
  "settings": [-0.0007, -0.0004, 100.0],
  "sensors": {
    "sensor_2": 643.02,
    "sensor_3": 1599.82,
    "sensor_4": 1423.45,
    "sensor_7": 552.12,
    "sensor_8": 2388.19,
    "sensor_9": 9054.34,
    "sensor_11": 48.02,
    "sensor_12": 519.82,
    "sensor_13": 2388.21,
    "sensor_14": 8132.45,
    "sensor_15": 8.48,
    "sensor_17": 395.0,
    "sensor_20": 38.65,
    "sensor_21": 23.21
  }
}
```

**Response `200 OK`:**
```json
{
  "success": true,
  "aircraft_id": 1,
  "tail_number": "N101AP",
  "cycle": 192,
  "predicted_rul": 18.42,
  "risk_level": "CRITICAL",
  "recommendation": "Immediate ground recommendation (AOG). Issue emergency HPC blade inspection work order.",
  "confidence_score": 0.92,
  "features_used": 45
}
```

### `GET /api/predict/history/<aircraft_id>`
Retrieves the chronological inference history for an aircraft.

---

## 6. Maintenance Management

### `GET /api/maintenance`
Retrieves all work orders.

**Query Parameters:**
- `status`: `PENDING`, `IN_PROGRESS`, `COMPLETED`
- `priority`: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`
- `aircraft_id`: Integer filter

**Response `200 OK`:**
```json
{
  "success": true,
  "count": 4,
  "records": [
    {
      "id": 1,
      "aircraft_id": 1,
      "tail_number": "N101AP",
      "title": "Emergency HPC Borescope & Blade Replacement",
      "description": "Inspect High-Pressure Compressor rotor blades following high-risk RUL alert.",
      "priority": "CRITICAL",
      "status": "PENDING",
      "scheduled_date": "2026-11-08",
      "completed_date": null,
      "technician_notes": "Parts allocated from Hangar Bay 4.",
      "created_at": "2026-11-07T17:52:07Z"
    }
  ]
}
```

### `POST /api/maintenance`
Creates a new maintenance work order.

**Request Body:**
```json
{
  "aircraft_id": 1,
  "title": "HPC Stage 3 Inspection",
  "description": "Routine optical borescope check",
  "priority": "HIGH",
  "status": "PENDING",
  "scheduled_date": "2026-11-15",
  "technician_notes": "Assigned to Lead Powerplant Specialist"
}
```

### `PUT /api/maintenance/<id>`
Updates an existing maintenance work order (e.g. status transition from `PENDING` to `IN_PROGRESS` or `COMPLETED`).

### `DELETE /api/maintenance/<id>`
Deletes a work order record if supported by authorization policy.

---

## 7. Executive Dashboard Aggregation

### `GET /api/dashboard`
Returns high-level statistics, health distributions, and recent fleet alerts in a single query-optimized call.

**Response `200 OK`:**
```json
{
  "success": true,
  "kpis": {
    "total_aircraft": 6,
    "operational": 4,
    "under_maintenance": 1,
    "attention_required": 1,
    "pending_maintenance": 2,
    "active_work_orders": 3
  },
  "health_distribution": {
    "normal": 4,
    "warning": 1,
    "critical": 1
  },
  "recent_maintenance": [
    {
      "id": 1,
      "tail_number": "N101AP",
      "title": "Emergency HPC Borescope & Blade Replacement",
      "priority": "CRITICAL",
      "status": "PENDING"
    }
  ]
}
```
