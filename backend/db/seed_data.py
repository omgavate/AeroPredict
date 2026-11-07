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

from config.database import get_db_connection

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


def seed_fleet():
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
        cursor.execute("SELECT COUNT(*) FROM aircraft;")
        count = cursor.fetchone()[0]
        cursor.close()
        print(f"Successfully seeded aircraft. Total count in DB: {count}")


if __name__ == '__main__':
    seed_fleet()
