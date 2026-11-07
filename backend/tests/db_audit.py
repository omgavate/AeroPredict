"""Database Audit Script for Phase 12."""
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from config.database import get_db_connection

def run_db_audit():
    print("=" * 60)
    print("AEROPREDICT DATABASE INTEGRITY AUDIT")
    print("=" * 60)
    
    with get_db_connection() as conn:
        cur = conn.cursor(dictionary=True)
        
        # 1. Inspect Table Structures & Keys
        cur.execute("SHOW TABLES;")
        tables = [list(r.values())[0] for r in cur.fetchall()]
        print("\n--- 1. TABLE STRUCTURES & PRIMARY KEYS ---")
        for table in tables:
            cur.execute(f"SHOW KEYS FROM {table} WHERE Key_name = 'PRIMARY';")
            pk = [r['Column_name'] for r in cur.fetchall()]
            cur.execute(f"SELECT COUNT(*) as c FROM {table};")
            cnt = cur.fetchone()['c']
            print(f"Table: {table:22} | Primary Key: {pk} | Rows: {cnt}")
            
        # 2. Foreign Key References Audit
        print("\n--- 2. FOREIGN KEYS & CONSTRAINTS ---")
        cur.execute("""
            SELECT TABLE_NAME, COLUMN_NAME, CONSTRAINT_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = 'aeropredict_db' AND REFERENCED_TABLE_NAME IS NOT NULL;
        """)
        fks = cur.fetchall()
        for fk in fks:
            print(f"FK: {fk['TABLE_NAME']}.{fk['COLUMN_NAME']} -> {fk['REFERENCED_TABLE_NAME']}.{fk['REFERENCED_COLUMN_NAME']} [{fk['CONSTRAINT_NAME']}]")

        # 3. Orphan Check
        print("\n--- 3. ORPHAN RECORD AUDIT ---")
        for child in [('sensor_readings', 'aircraft_id'), ('maintenance_records', 'aircraft_id'), ('maintenance_alerts', 'aircraft_id'), ('rul_predictions', 'aircraft_id')]:
            tbl, col = child
            cur.execute(f"SELECT COUNT(*) as c FROM {tbl} WHERE {col} NOT IN (SELECT id FROM aircraft);")
            orphans = cur.fetchone()['c']
            status = "PASS (0 orphans)" if orphans == 0 else f"FAIL ({orphans} orphans!)"
            print(f"Reference Integrity {tbl}.{col} -> aircraft.id: {status}")

        # 4. Duplicate Check
        print("\n--- 4. DUPLICATES AUDIT ---")
        cur.execute("SELECT tail_number, COUNT(*) as c FROM aircraft GROUP BY tail_number HAVING c > 1;")
        dupe_tails = cur.fetchall()
        print(f"Duplicate aircraft.tail_number: {len(dupe_tails)}")
        cur.execute("SELECT cmapss_unit_id, COUNT(*) as c FROM aircraft WHERE cmapss_unit_id IS NOT NULL GROUP BY cmapss_unit_id HAVING c > 1;")
        dupe_units = cur.fetchall()
        print(f"Duplicate aircraft.cmapss_unit_id: {len(dupe_units)}")

        # 5. Null Checks on Key Columns
        print("\n--- 5. NULL INTEGRITY AUDIT ---")
        cur.execute("SELECT COUNT(*) as c FROM aircraft WHERE tail_number IS NULL OR model IS NULL OR engine_type IS NULL OR status IS NULL;")
        print(f"Aircraft mandatory NULLs: {cur.fetchone()['c']}")
        cur.execute("SELECT COUNT(*) as c FROM maintenance_records WHERE aircraft_id IS NULL OR title IS NULL OR priority IS NULL OR status IS NULL;")
        print(f"Maintenance mandatory NULLs: {cur.fetchone()['c']}")
        cur.execute("SELECT COUNT(*) as c FROM sensor_readings WHERE aircraft_id IS NULL OR cycle IS NULL;")
        print(f"Sensor readings mandatory NULLs: {cur.fetchone()['c']}")
        cur.execute("SELECT COUNT(*) as c FROM rul_predictions WHERE aircraft_id IS NULL OR cycle IS NULL OR predicted_rul IS NULL;")
        print(f"RUL predictions mandatory NULLs: {cur.fetchone()['c']}")
        cur.execute("SELECT COUNT(*) as c FROM maintenance_alerts WHERE aircraft_id IS NULL OR alert_type IS NULL OR severity IS NULL;")
        print(f"Alerts mandatory NULLs: {cur.fetchone()['c']}")

        print("\n" + "=" * 60)
        print("DATABASE AUDIT COMPLETED")
        print("=" * 60)

if __name__ == '__main__':
    run_db_audit()
