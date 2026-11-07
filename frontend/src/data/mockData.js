// Telemetry and Fleet Dataset for AeroPredict Frontend
// Grounded on NASA C-MAPSS FD001 turbofan degradation characteristics.

export const MOCK_AIRCRAFT = [
  {
    id: 1,
    tail_number: "N101AP",
    model: "Boeing 737-800",
    manufacturer: "Boeing",
    engine_type: "CFM56-7B",
    cmapss_unit_id: 1,
    current_cycles: 192,
    status: "ATTENTION_REQUIRED",
    health_score: 54,
    last_inspection: "2026-10-14",
    total_flight_hours: 4210
  },
  {
    id: 2,
    tail_number: "N204AP",
    model: "Airbus A320neo",
    manufacturer: "Airbus",
    engine_type: "LEAP-1A",
    cmapss_unit_id: 2,
    current_cycles: 125,
    status: "OPERATIONAL",
    health_score: 89,
    last_inspection: "2026-10-28",
    total_flight_hours: 2840
  },
  {
    id: 3,
    tail_number: "N308AP",
    model: "Boeing 777-300ER",
    manufacturer: "Boeing",
    engine_type: "GE90-115B",
    cmapss_unit_id: 3,
    current_cycles: 245,
    status: "UNDER_MAINTENANCE",
    health_score: 41,
    last_inspection: "2026-11-02",
    total_flight_hours: 6120
  },
  {
    id: 4,
    tail_number: "N412AP",
    model: "Airbus A350-900",
    manufacturer: "Airbus",
    engine_type: "Trent XWB-84",
    cmapss_unit_id: 4,
    current_cycles: 88,
    status: "OPERATIONAL",
    health_score: 96,
    last_inspection: "2026-10-10",
    total_flight_hours: 1950
  },
  {
    id: 5,
    tail_number: "VT-AER",
    model: "Boeing 737 MAX 8",
    manufacturer: "Boeing",
    engine_type: "LEAP-1B",
    cmapss_unit_id: 5,
    current_cycles: 210,
    status: "ATTENTION_REQUIRED",
    health_score: 48,
    last_inspection: "2026-10-05",
    total_flight_hours: 4790
  },
  {
    id: 6,
    tail_number: "VT-BLR",
    model: "Embraer E195-E2",
    manufacturer: "Embraer",
    engine_type: "PW1900G",
    cmapss_unit_id: 6,
    current_cycles: 64,
    status: "OPERATIONAL",
    health_score: 98,
    last_inspection: "2026-11-04",
    total_flight_hours: 1420
  }
];

export const MOCK_TELEMETRY_SERIES = [
  { cycle: 50,  t30: 1582.4, t50: 1395.2, p30: 554.8, nc: 9046.2, bpr: 8.39, htBleed: 391, rul: 112 },
  { cycle: 70,  t30: 1584.8, t50: 1398.6, p30: 554.2, nc: 9048.4, bpr: 8.41, htBleed: 392, rul: 92 },
  { cycle: 90,  t30: 1587.1, t50: 1402.1, p30: 553.8, nc: 9051.1, bpr: 8.42, htBleed: 392, rul: 72 },
  { cycle: 110, t30: 1589.6, t50: 1406.8, p30: 553.2, nc: 9054.6, bpr: 8.44, htBleed: 393, rul: 52 },
  { cycle: 130, t30: 1592.5, t50: 1411.3, p30: 552.4, nc: 9058.9, bpr: 8.46, htBleed: 394, rul: 32 },
  { cycle: 150, t30: 1596.2, t50: 1417.8, p30: 551.5, nc: 9064.2, bpr: 8.49, htBleed: 395, rul: 24 },
  { cycle: 170, t30: 1601.4, t50: 1424.5, p30: 550.2, nc: 9070.8, bpr: 8.53, htBleed: 396, rul: 15 },
  { cycle: 185, t30: 1606.8, t50: 1431.2, p30: 549.1, nc: 9077.5, bpr: 8.57, htBleed: 397, rul: 9 },
  { cycle: 192, t30: 1610.1, t50: 1435.6, p30: 548.3, nc: 9081.2, bpr: 8.60, htBleed: 398, rul: 6 }
];

export const MOCK_LATEST_SENSORS = {
  cycle: 192,
  setting_1: -0.0012,
  setting_2: 0.0004,
  setting_3: 100.0,
  sensor_1: 518.67,  // T2: Total temperature at fan inlet (°R)
  sensor_2: 643.12,  // T24: Total temp LPC outlet (°R)
  sensor_3: 1610.10, // T30: Total temp HPC outlet (°R) - Elevated
  sensor_4: 1435.60, // T50: Total temp LPT outlet (°R) - Elevated
  sensor_5: 14.62,   // P2: Pressure fan inlet (psia)
  sensor_6: 21.61,   // P15: Pressure bypass duct (psia)
  sensor_7: 548.30,  // P30: Pressure HPC outlet (psia) - Dropping
  sensor_8: 2388.16, // Nf: Physical fan speed (rpm)
  sensor_9: 9081.20, // Nc: Physical core speed (rpm) - Elevated
  sensor_10: 1.30,   // epr: Engine pressure ratio
  sensor_11: 47.92,  // Ps30: Static pressure HPC outlet
  sensor_12: 520.14, // phi: Fuel flow ratio
  sensor_13: 2388.18,// NRf: Corrected fan speed
  sensor_14: 8144.90,// NRc: Corrected core speed
  sensor_15: 8.602,  // BPR: Bypass ratio - Diverging
  sensor_16: 0.03,   // farB: Burner fuel-air ratio
  sensor_17: 398.0,  // htBleed: Bleed enthalpy - Elevated
  sensor_18: 2388.0, // Nf_dmd: Demanded fan speed
  sensor_19: 100.0,  // PCNfR_dmd: Demanded corrected fan speed
  sensor_20: 38.45,  // W31: HPT coolant bleed
  sensor_21: 23.018  // W32: LPT coolant bleed
};

export const MOCK_RUL_PREDICTION = {
  aircraft_id: 1,
  tail_number: "N101AP",
  cycle: 192,
  predicted_rul: 6.2,
  confidence_interval: "± 2.1 cycles",
  risk_level: "CRITICAL",
  risk_score: 94,
  recommendation: "Critical compressor thermal degradation detected. HPC outlet temperature T30 exceeded 1610°R. Ground aircraft and perform immediate borescope inspection of Stage 4-7 compressor rotor blades.",
  action_required: "Schedule Immediate Engine Overhaul (A-Check Level 4)",
  predicted_at: "2026-11-07 14:35:00 UTC"
};

export const MOCK_PREDICTION_HISTORY = [
  { id: 101, cycle: 150, predicted_rul: 24.5, risk_level: "HIGH", date: "2026-11-01" },
  { id: 102, cycle: 170, predicted_rul: 15.0, risk_level: "HIGH", date: "2026-11-04" },
  { id: 103, cycle: 185, predicted_rul: 9.1,  risk_level: "CRITICAL", date: "2026-11-06" },
  { id: 104, cycle: 192, predicted_rul: 6.2,  risk_level: "CRITICAL", date: "2026-11-07" }
];

export const MOCK_ALERTS = [
  {
    id: 1,
    aircraft_id: 1,
    tail_number: "N101AP",
    alert_type: "RUL_CRITICAL",
    severity: "CRITICAL",
    message: "Predicted RUL ≤ 10 flight cycles (Current estimated: 6.2 cycles).",
    cycle: 192,
    predicted_rul: 6.2,
    is_resolved: false,
    timestamp: "12 mins ago"
  },
  {
    id: 2,
    aircraft_id: 5,
    tail_number: "VT-AER",
    alert_type: "RUL_WARNING",
    severity: "HIGH",
    message: "HPC pressure drop indicates accelerating blade tip wear (RUL: 22.4 cycles).",
    cycle: 210,
    predicted_rul: 22.4,
    is_resolved: false,
    timestamp: "2 hours ago"
  },
  {
    id: 3,
    aircraft_id: 3,
    tail_number: "N308AP",
    alert_type: "MAINTENANCE_DUE",
    severity: "MEDIUM",
    message: "Scheduled 250-cycle C-Check inspection pending verification.",
    cycle: 245,
    predicted_rul: 48.0,
    is_resolved: false,
    timestamp: "1 day ago"
  },
  {
    id: 4,
    aircraft_id: 2,
    tail_number: "N204AP",
    alert_type: "SENSOR_ANOMALY",
    severity: "LOW",
    message: "Minor EGT thermocouple drift noted during climb-out; resolved upon calibration.",
    cycle: 125,
    predicted_rul: 84.1,
    is_resolved: true,
    timestamp: "3 days ago"
  }
];

export const MOCK_MAINTENANCE_RECORDS = [
  {
    id: 1,
    aircraft_id: 1,
    tail_number: "N101AP",
    title: "Emergency HPC Borescope & Blade Replacement",
    description: "Inspect High-Pressure Compressor rotor blades for foreign object damage or thermal cracking following high-risk RUL prediction alert.",
    priority: "CRITICAL",
    status: "SCHEDULED",
    scheduled_date: "2026-11-08",
    completed_date: null,
    technician_notes: "Parts allocated from Hangar Bay 4. Lead Powerplant Engineer assigned."
  },
  {
    id: 2,
    aircraft_id: 3,
    tail_number: "N308AP",
    title: "C-Check Turbofan Overhaul & LPT Seal Renewal",
    description: "Scheduled heavy check overhaul including combustor liner inspection and Low Pressure Turbine seal replacement.",
    priority: "HIGH",
    status: "IN_PROGRESS",
    scheduled_date: "2026-11-05",
    completed_date: null,
    technician_notes: "Engine removed and placed on test-cell stand. Inspection 60% complete."
  },
  {
    id: 3,
    aircraft_id: 5,
    tail_number: "VT-AER",
    title: "Fuel Flow Ratio & Sensor 12 Calibration",
    description: "Recalibrate static pressure tap and fuel metering unit following divergence detection.",
    priority: "MEDIUM",
    status: "SCHEDULED",
    scheduled_date: "2026-11-10",
    completed_date: null,
    technician_notes: "Awaiting aircraft arrival at BOM hub."
  },
  {
    id: 4,
    aircraft_id: 4,
    tail_number: "N412AP",
    title: "Routine A-Check 100-Cycle Lubrication Service",
    description: "Standard oil filter change, magnetic chip detector inspection, and hydraulic fluid servicing.",
    priority: "LOW",
    status: "COMPLETED",
    scheduled_date: "2026-10-30",
    completed_date: "2026-10-31",
    technician_notes: "Zero metal debris on magnetic chip detector. Oil samples sent to lab. Engine returned to flight service."
  }
];
