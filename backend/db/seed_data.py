"""
Seed Script for AeroPredict Database.
Populates initial aircraft fleet assets into MySQL aeropredict_db.
"""

import sys
from pathlib import Path

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from config.database import get_db_connection, init_database_schema
from services.engine_service import ensure_aircraft_telemetry_seeded

INITIAL_FLEET = [
  {
    "tail_number": "N101AP",
    "model": "Boeing 737-800",
    "manufacturer": "Boeing",
    "manufacturing_year": 2018,
    "engine_type": "CFM56-7B",
    "cmapss_unit_id": 1,
    "current_cycles": 192,
    "flight_hours": 4210,
    "status": "ATTENTION_REQUIRED"
  },
  {
    "tail_number": "N204AP",
    "model": "Airbus A320neo",
    "manufacturer": "Airbus",
    "manufacturing_year": 2021,
    "engine_type": "LEAP-1A",
    "cmapss_unit_id": 2,
    "current_cycles": 125,
    "flight_hours": 2840,
    "status": "OPERATIONAL"
  },
  {
    "tail_number": "N308AP",
    "model": "Boeing 777-300ER",
    "manufacturer": "Boeing",
    "manufacturing_year": 2016,
    "engine_type": "GE90-115B",
    "cmapss_unit_id": 3,
    "current_cycles": 245,
    "flight_hours": 6120,
    "status": "UNDER_MAINTENANCE"
  },
  {
    "tail_number": "N412AP",
    "model": "Airbus A350-900",
    "manufacturer": "Airbus",
    "manufacturing_year": 2022,
    "engine_type": "Trent XWB-84",
    "cmapss_unit_id": 4,
    "current_cycles": 88,
    "flight_hours": 1950,
    "status": "OPERATIONAL"
  },
  {
    "tail_number": "VT-AER",
    "model": "Boeing 737 MAX 8",
    "manufacturer": "Boeing",
    "manufacturing_year": 2019,
    "engine_type": "LEAP-1B",
    "cmapss_unit_id": 5,
    "current_cycles": 210,
    "flight_hours": 4790,
    "status": "ATTENTION_REQUIRED"
  },
  {
    "tail_number": "VT-BLR",
    "model": "Embraer E195-E2",
    "manufacturer": "Embraer",
    "manufacturing_year": 2023,
    "engine_type": "PW1900G",
    "cmapss_unit_id": 6,
    "current_cycles": 64,
    "flight_hours": 1420,
    "status": "OPERATIONAL"
  }
]


SAMPLE_MAINTENANCE = [
  {
    "tail_number": "N101AP",
    "title": "Emergency HPC Borescope & Blade Replacement",
    "description": "Inspect High-Pressure Compressor rotor blades for foreign object damage or thermal cracking following high-risk RUL prediction alert.",
    "priority": "CRITICAL",
    "status": "PENDING",
    "scheduled_date": "2026-11-08",
    "completed_date": None,
    "technician_notes": "Parts allocated from Hangar Bay 4. Lead Powerplant Engineer assigned."
  },
  {
    "tail_number": "N308AP",
    "title": "C-Check Turbofan Overhaul & LPT Seal Renewal",
    "description": "Scheduled heavy check overhaul including combustor liner inspection and Low Pressure Turbine seal replacement.",
    "priority": "HIGH",
    "status": "IN_PROGRESS",
    "scheduled_date": "2026-11-05",
    "completed_date": None,
    "technician_notes": "Engine removed and placed on test-cell stand. Inspection 60% complete."
  },
  {
    "tail_number": "VT-AER",
    "title": "Fuel Flow Ratio & Sensor 12 Calibration",
    "description": "Recalibrate static pressure tap and fuel metering unit following divergence detection.",
    "priority": "MEDIUM",
    "status": "PENDING",
    "scheduled_date": "2026-11-10",
    "completed_date": None,
    "technician_notes": "Awaiting aircraft arrival at BOM hub."
  },
  {
    "tail_number": "N412AP",
    "title": "Routine A-Check 100-Cycle Lubrication Service",
    "description": "Standard oil filter change, magnetic chip detector inspection, and hydraulic fluid servicing.",
    "priority": "LOW",
    "status": "COMPLETED",
    "scheduled_date": "2026-10-30",
    "completed_date": "2026-10-31",
    "technician_notes": "Zero metal debris on magnetic chip detector. Oil samples sent to lab. Engine returned to flight service."
  }
]


def seed_fleet():
    print("Step 1: Initializing database schema...")
    success, msg = init_database_schema()
    if not success:
        print(f"Schema warning: {msg}")
    else:
        print(f"Schema: {msg}")

    print("Step 2: Seeding initial aircraft fleet...")
    aircraft_id_map = {}
    with get_db_connection() as conn:
        cursor = conn.cursor()
        for ac in INITIAL_FLEET:
            cursor.execute("""
                INSERT INTO aircraft (
                    tail_number, model, manufacturer, manufacturing_year,
                    engine_type, cmapss_unit_id, current_cycles, flight_hours, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    model = VALUES(model),
                    manufacturer = VALUES(manufacturer),
                    manufacturing_year = VALUES(manufacturing_year),
                    engine_type = VALUES(engine_type),
                    cmapss_unit_id = VALUES(cmapss_unit_id),
                    current_cycles = VALUES(current_cycles),
                    flight_hours = VALUES(flight_hours),
                    status = VALUES(status);
            """, (
                ac['tail_number'], ac['model'], ac['manufacturer'], ac['manufacturing_year'],
                ac['engine_type'], ac['cmapss_unit_id'], ac['current_cycles'], ac['flight_hours'],
                ac['status']
            ))
        conn.commit()

        cursor.execute("SELECT id, tail_number FROM aircraft;")
        rows = cursor.fetchall()
        aircraft_id_map = {row[1]: row[0] for row in rows}
        print(f"Aircraft registered: {len(aircraft_id_map)} aircraft in fleet.")

        print("Step 3: Seeding sample maintenance work orders...")
        for rec in SAMPLE_MAINTENANCE:
            ac_id = aircraft_id_map.get(rec['tail_number'])
            if not ac_id:
                continue
            cursor.execute("""
                SELECT id FROM maintenance_records
                WHERE aircraft_id = %s AND title = %s;
            """, (ac_id, rec['title']))
            existing = cursor.fetchone()
            if not existing:
                cursor.execute("""
                    INSERT INTO maintenance_records (
                        aircraft_id, title, description, priority, status,
                        scheduled_date, completed_date, technician_notes
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                """, (
                    ac_id, rec['title'], rec['description'], rec['priority'], rec['status'],
                    rec['scheduled_date'], rec['completed_date'], rec['technician_notes']
                ))
        conn.commit()
        cursor.execute("SELECT COUNT(*) FROM maintenance_records;")
        m_count = cursor.fetchone()[0]
        cursor.close()
        print(f"Maintenance records in DB: {m_count}")

    print("Step 4: Ensuring C-MAPSS telemetry is seeded for demonstration fleet...")
    for tail, ac_id in aircraft_id_map.items():
        try:
            cnt = ensure_aircraft_telemetry_seeded(ac_id)
            print(f"  - {tail} (ID {ac_id}): {cnt} sensor cycles available.")
        except Exception as e:
            print(f"  - {tail} (ID {ac_id}): telemetry notice: {e}")

    print("\nDatabase initialization and seeding complete! AeroPredict is ready.")


if __name__ == '__main__':
    seed_fleet()
