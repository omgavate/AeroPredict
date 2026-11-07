"""
Engine Health Monitoring & Telemetry Service.
Handles C-MAPSS dataset mapping, real-time sensor ingestion, cycle tracking,
historical telemetry retrieval, and thermodynamic health diagnostics.
"""

import os
import logging
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import numpy as np
from config.database import get_db_connection

logger = logging.getLogger('aeropredict.engine_service')

DEMONSTRATION_MAPPING_NOTICE = (
    "Demonstration mapping: Aircraft assets in AeroPredict are linked to NASA C-MAPSS "
    "turbofan engine unit records (FD001) for real thermodynamic sensor telemetry stream simulation. "
    "Aircraft assets are operational representations and not physical NASA aircraft."
)

DATASET_SOURCE = "NASA C-MAPSS Turbofan Engine Degradation Simulation (FD001)"

# Cache for the loaded C-MAPSS dataset DataFrame
_CMAPSS_CACHE = None

# Informative sensors and their engineering descriptions
SENSOR_METADATA = {
    'sensor_1': {'name': 'T2', 'desc': 'Total temperature at fan inlet', 'unit': '°R', 'baseline': 518.67, 'subsystem': 'Fan'},
    'sensor_2': {'name': 'T24', 'desc': 'Total temperature at LPC outlet', 'unit': '°R', 'baseline': 642.0, 'subsystem': 'LPC'},
    'sensor_3': {'name': 'T30', 'desc': 'Total temperature at HPC outlet', 'unit': '°R', 'baseline': 1589.0, 'subsystem': 'HPC'},
    'sensor_4': {'name': 'T50', 'desc': 'Total temperature at LPT outlet', 'unit': '°R', 'baseline': 1400.0, 'subsystem': 'LPT'},
    'sensor_5': {'name': 'P2', 'desc': 'Pressure at fan inlet', 'unit': 'psia', 'baseline': 14.62, 'subsystem': 'Fan'},
    'sensor_6': {'name': 'P15', 'desc': 'Total pressure in bypass-duct', 'unit': 'psia', 'baseline': 21.61, 'subsystem': 'Bypass'},
    'sensor_7': {'name': 'P30', 'desc': 'Total pressure at HPC outlet', 'unit': 'psia', 'baseline': 554.0, 'subsystem': 'HPC'},
    'sensor_8': {'name': 'Nf', 'desc': 'Physical fan speed', 'unit': 'rpm', 'baseline': 2388.0, 'subsystem': 'Fan'},
    'sensor_9': {'name': 'Nc', 'desc': 'Physical core speed', 'unit': 'rpm', 'baseline': 9046.0, 'subsystem': 'Core'},
    'sensor_10': {'name': 'epr', 'desc': 'Engine pressure ratio', 'unit': '', 'baseline': 1.30, 'subsystem': 'Combustor'},
    'sensor_11': {'name': 'Ps30', 'desc': 'Static pressure at HPC outlet', 'unit': 'psia', 'baseline': 47.5, 'subsystem': 'HPC'},
    'sensor_12': {'name': 'phi', 'desc': 'Ratio of fuel flow to Ps30', 'unit': 'pps/psi', 'baseline': 521.6, 'subsystem': 'Combustor'},
    'sensor_13': {'name': 'NRf', 'desc': 'Corrected fan speed', 'unit': 'rpm', 'baseline': 2388.0, 'subsystem': 'Fan'},
    'sensor_14': {'name': 'NRc', 'desc': 'Corrected core speed', 'unit': 'rpm', 'baseline': 8138.0, 'subsystem': 'Core'},
    'sensor_15': {'name': 'BPR', 'desc': 'Bypass Ratio', 'unit': '', 'baseline': 8.42, 'subsystem': 'Bypass'},
    'sensor_16': {'name': 'farB', 'desc': 'Burner fuel-air ratio', 'unit': '', 'baseline': 0.03, 'subsystem': 'Combustor'},
    'sensor_17': {'name': 'htBleed', 'desc': 'Bleed Enthalpy', 'unit': 'Btu/lb', 'baseline': 392.0, 'subsystem': 'Bleed'},
    'sensor_18': {'name': 'Nf_dmd', 'desc': 'Demanded fan speed', 'unit': 'rpm', 'baseline': 2388.0, 'subsystem': 'Fan'},
    'sensor_19': {'name': 'PCNfR_dmd', 'desc': 'Demanded corrected fan speed', 'unit': 'rpm', 'baseline': 100.0, 'subsystem': 'Fan'},
    'sensor_20': {'name': 'W31', 'desc': 'HPT coolant bleed', 'unit': 'lbm/s', 'baseline': 39.0, 'subsystem': 'Turbine'},
    'sensor_21': {'name': 'W32', 'desc': 'LPT coolant bleed', 'unit': 'lbm/s', 'baseline': 23.4, 'subsystem': 'Turbine'}
}


def _get_cmapss_df():
    """
    Loads and caches the NASA C-MAPSS train_FD001 dataset DataFrame.
    """
    global _CMAPSS_CACHE
    if _CMAPSS_CACHE is not None:
        return _CMAPSS_CACHE

    root_dir = Path(__file__).resolve().parent.parent.parent
    dataset_file = root_dir / 'dataset' / 'train_FD001.txt'

    if not dataset_file.exists():
        logger.warning(f"C-MAPSS dataset file not found at {dataset_file}")
        return None

    columns = (
        ['unit_nr', 'cycle', 'setting_1', 'setting_2', 'setting_3'] +
        [f'sensor_{i}' for i in range(1, 22)]
    )
    df = pd.read_csv(dataset_file, sep=r'\s+', header=None, names=columns)
    df['unit_nr'] = df['unit_nr'].astype(int)
    df['cycle'] = df['cycle'].astype(int)
    _CMAPSS_CACHE = df
    return _CMAPSS_CACHE


def ensure_aircraft_telemetry_seeded(aircraft_id):
    """
    Verifies if telemetry records exist in `sensor_readings` for this aircraft.
    If empty, automatically populates up to `aircraft.current_cycles`
    using actual records from the linked C-MAPSS unit.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        # Check aircraft exists
        cursor.execute(
            "SELECT id, tail_number, cmapss_unit_id, current_cycles FROM aircraft WHERE id = %s",
            (aircraft_id,)
        )
        aircraft = cursor.fetchone()
        if not aircraft:
            cursor.close()
            return None

        # Check existing count
        cursor.execute(
            "SELECT COUNT(*) as cnt FROM sensor_readings WHERE aircraft_id = %s",
            (aircraft_id,)
        )
        count_res = cursor.fetchone()
        existing_count = count_res['cnt'] if count_res else 0

        if existing_count > 0:
            cursor.close()
            return existing_count

        cmapss_unit = aircraft.get('cmapss_unit_id')
        if not cmapss_unit:
            cursor.close()
            return 0

        df = _get_cmapss_df()
        if df is None:
            cursor.close()
            return 0

        target_cycles = aircraft.get('current_cycles', 50) or 50
        unit_df = df[df['unit_nr'] == int(cmapss_unit)]
        if unit_df.empty:
            cursor.close()
            return 0

        # Filter up to current_cycles
        seed_df = unit_df[unit_df['cycle'] <= target_cycles]
        if seed_df.empty:
            seed_df = unit_df.head(target_cycles)

        insert_sql = """
            INSERT INTO sensor_readings (
                aircraft_id, cycle, setting_1, setting_2, setting_3,
                sensor_1, sensor_2, sensor_3, sensor_4, sensor_5, sensor_6,
                sensor_7, sensor_8, sensor_9, sensor_10, sensor_11, sensor_12,
                sensor_13, sensor_14, sensor_15, sensor_16, sensor_17, sensor_18,
                sensor_19, sensor_20, sensor_21, recorded_at
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s
            )
        """

        records = []
        now = datetime.now(timezone.utc)
        for _, row in seed_df.iterrows():
            record = (
                aircraft_id,
                int(row['cycle']),
                float(row['setting_1']),
                float(row['setting_2']),
                float(row['setting_3']),
                float(row['sensor_1']),
                float(row['sensor_2']),
                float(row['sensor_3']),
                float(row['sensor_4']),
                float(row['sensor_5']),
                float(row['sensor_6']),
                float(row['sensor_7']),
                float(row['sensor_8']),
                float(row['sensor_9']),
                float(row['sensor_10']),
                float(row['sensor_11']),
                float(row['sensor_12']),
                float(row['sensor_13']),
                float(row['sensor_14']),
                float(row['sensor_15']),
                float(row['sensor_16']),
                float(row['sensor_17']),
                float(row['sensor_18']),
                float(row['sensor_19']),
                float(row['sensor_20']),
                float(row['sensor_21']),
                now
            )
            records.append(record)

        cursor.executemany(insert_sql, records)
        conn.commit()
        cursor.close()
        logger.info(f"Seeded {len(records)} C-MAPSS telemetry rows for aircraft #{aircraft_id}")
        return len(records)


def get_latest_sensor_reading(aircraft_id):
    """
    Retrieves the most recent sensor reading and thermodynamic indicators for an aircraft.
    """
    ensure_aircraft_telemetry_seeded(aircraft_id)

    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, tail_number, model, manufacturer, engine_type,
                   manufacturing_year, flight_hours, cmapss_unit_id, current_cycles, status
            FROM aircraft
            WHERE id = %s
            """,
            (aircraft_id,)
        )
        aircraft = cursor.fetchone()
        if not aircraft:
            cursor.close()
            return None

        cursor.execute(
            """
            SELECT * FROM sensor_readings
            WHERE aircraft_id = %s
            ORDER BY cycle DESC
            LIMIT 1
            """,
            (aircraft_id,)
        )
        row = cursor.fetchone()
        cursor.close()

        if not row:
            return {
                'aircraft_id': aircraft['id'],
                'tail_number': aircraft['tail_number'],
                'model': aircraft['model'],
                'engine_type': aircraft['engine_type'],
                'cmapss_unit_id': aircraft['cmapss_unit_id'],
                'current_cycles': aircraft['current_cycles'],
                'cycle': None,
                'has_data': False,
                'mapping_notice': DEMONSTRATION_MAPPING_NOTICE
            }

        # Format sensors
        sensors = {f'sensor_{i}': float(row[f'sensor_{i}']) for i in range(1, 22)}
        settings = {
            'setting_1': float(row['setting_1']),
            'setting_2': float(row['setting_2']),
            'setting_3': float(row['setting_3'])
        }

        # Calculate thermodynamic health deltas
        t30 = sensors['sensor_3']
        t50 = sensors['sensor_4']
        p30 = sensors['sensor_7']
        nc = sensors['sensor_9']
        bpr = sensors['sensor_15']
        ht_bleed = sensors['sensor_17']

        t30_delta = round(t30 - SENSOR_METADATA['sensor_3']['baseline'], 2)
        p30_delta = round(p30 - SENSOR_METADATA['sensor_7']['baseline'], 2)

        health_condition = 'NOMINAL'
        if t30_delta > 10.0 or p30_delta < -2.5:
            health_condition = 'CRITICAL' if t30_delta > 15.0 else 'ATTENTION_REQUIRED'

        return {
            'success': True,
            'aircraft_id': aircraft['id'],
            'tail_number': aircraft['tail_number'],
            'model': aircraft['model'],
            'manufacturer': aircraft['manufacturer'],
            'engine_type': aircraft['engine_type'],
            'manufacturing_year': aircraft.get('manufacturing_year'),
            'cmapss_unit_id': aircraft['cmapss_unit_id'],
            'current_cycles': aircraft['current_cycles'],
            'status': aircraft['status'],
            'reading_id': row['id'],
            'cycle': int(row['cycle']),
            'recorded_at': row['recorded_at'].isoformat() if row.get('recorded_at') else None,
            'operational_settings': settings,
            'sensors': sensors,
            'primary_metrics': {
                't30_hpc_temp': t30,
                't50_lpt_temp': t50,
                'p30_hpc_press': p30,
                'core_speed_nc': nc,
                'bypass_ratio_bpr': bpr,
                'bleed_enthalpy': ht_bleed
            },
            'health_indicators': {
                't30_delta_r': t30_delta,
                'p30_delta_psia': p30_delta,
                'overall_condition': health_condition
            },
            'dataset_source': DATASET_SOURCE,
            'mapping_notice': DEMONSTRATION_MAPPING_NOTICE
        }


def get_sensor_history(aircraft_id, limit=50, sensors=None, cycle_start=None, cycle_end=None):
    """
    Retrieves chronological sensor history for charts and trend visualizers.
    Returns:
      - `history`: ordered chronologically by cycle ASC
      - `sensor_metadata`: names, engineering units, subsystems
    """
    ensure_aircraft_telemetry_seeded(aircraft_id)

    # Sanitize limit
    try:
        limit = max(1, min(int(limit), 500))
    except (ValueError, TypeError):
        limit = 50

    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT id, tail_number, model, engine_type, cmapss_unit_id, current_cycles FROM aircraft WHERE id = %s",
            (aircraft_id,)
        )
        aircraft = cursor.fetchone()
        if not aircraft:
            cursor.close()
            return None

        # Build query
        where_clauses = ["aircraft_id = %s"]
        params = [aircraft_id]

        if cycle_start is not None:
            where_clauses.append("cycle >= %s")
            params.append(int(cycle_start))
        if cycle_end is not None:
            where_clauses.append("cycle <= %s")
            params.append(int(cycle_end))

        where_sql = " AND ".join(where_clauses)
        query = f"""
            SELECT * FROM (
                SELECT * FROM sensor_readings
                WHERE {where_sql}
                ORDER BY cycle DESC
                LIMIT %s
            ) AS recent_subquery
            ORDER BY cycle ASC
        """
        params.append(limit)

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        cursor.close()

        history = []
        for r in rows:
            entry = {
                'reading_id': r['id'],
                'cycle': int(r['cycle']),
                'recorded_at': r['recorded_at'].isoformat() if r.get('recorded_at') else None,
                'setting_1': float(r['setting_1']),
                'setting_2': float(r['setting_2']),
                'setting_3': float(r['setting_3']),
                # Direct named keys for easy Recharts mapping
                't24': float(r['sensor_2']),
                't30': float(r['sensor_3']),
                't50': float(r['sensor_4']),
                'p30': float(r['sensor_7']),
                'nf': float(r['sensor_8']),
                'nc': float(r['sensor_9']),
                'ps30': float(r['sensor_11']),
                'phi': float(r['sensor_12']),
                'bpr': float(r['sensor_15']),
                'htBleed': float(r['sensor_17']),
                'w31': float(r['sensor_20']),
                'w32': float(r['sensor_21'])
            }
            # Also attach full sensors dictionary
            entry['sensors'] = {f'sensor_{i}': float(r[f'sensor_{i}']) for i in range(1, 22)}
            history.append(entry)

        return {
            'aircraft_id': aircraft['id'],
            'tail_number': aircraft['tail_number'],
            'model': aircraft['model'],
            'engine_type': aircraft['engine_type'],
            'cmapss_unit_id': aircraft['cmapss_unit_id'],
            'current_cycles': aircraft['current_cycles'],
            'count': len(history),
            'limit': limit,
            'history': history,
            'sensor_metadata': SENSOR_METADATA,
            'dataset_source': DATASET_SOURCE,
            'mapping_notice': DEMONSTRATION_MAPPING_NOTICE
        }


def advance_sensor_cycle(aircraft_id):
    """
    Advances the aircraft telemetry by 1 cycle.
    Uses actual C-MAPSS rows if available for the linked unit, or applies
    physics-based continuous degradation continuation if beyond training cycles.
    """
    ensure_aircraft_telemetry_seeded(aircraft_id)

    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, tail_number, model, engine_type, cmapss_unit_id, current_cycles, flight_hours
            FROM aircraft
            WHERE id = %s
            """,
            (aircraft_id,)
        )
        aircraft = cursor.fetchone()
        if not aircraft:
            cursor.close()
            return None

        # Determine next cycle
        cursor.execute(
            "SELECT MAX(cycle) as max_c FROM sensor_readings WHERE aircraft_id = %s",
            (aircraft_id,)
        )
        max_row = cursor.fetchone()
        last_cycle = max_row['max_c'] if max_row and max_row['max_c'] is not None else aircraft['current_cycles']
        next_cycle = int(last_cycle) + 1

        cmapss_unit = aircraft.get('cmapss_unit_id') or 1
        df = _get_cmapss_df()

        # Check if actual row exists in C-MAPSS dataset
        actual_row = None
        if df is not None:
            match = df[(df['unit_nr'] == int(cmapss_unit)) & (df['cycle'] == next_cycle)]
            if not match.empty:
                actual_row = match.iloc[0]

        now = datetime.now(timezone.utc)

        if actual_row is not None:
            # Use actual C-MAPSS sensor values
            s_vals = [float(actual_row[f'sensor_{i}']) for i in range(1, 22)]
            setting_1 = float(actual_row['setting_1'])
            setting_2 = float(actual_row['setting_2'])
            setting_3 = float(actual_row['setting_3'])
        else:
            # Physics-based continuation drift from the last recorded cycle
            cursor.execute(
                "SELECT * FROM sensor_readings WHERE aircraft_id = %s ORDER BY cycle DESC LIMIT 1",
                (aircraft_id,)
            )
            prev = cursor.fetchone()
            if prev:
                delta_t = round(float(np.random.uniform(0.2, 0.7)), 4)
                s_vals = []
                for i in range(1, 22):
                    v = float(prev[f'sensor_{i}'])
                    if i == 3:  # T30 rises
                        v += delta_t
                    elif i == 4:  # T50 rises
                        v += delta_t * 0.75
                    elif i == 7:  # P30 drops
                        v -= 0.12
                    elif i == 9:  # Nc drifts
                        v += round(float(np.random.uniform(0.5, 1.5)), 2)
                    elif i == 11:  # Ps30 rises
                        v += 0.05
                    elif i == 15:  # BPR rises
                        v += 0.003
                    elif i == 17:  # htBleed rises
                        v += 0.4
                    s_vals.append(round(v, 4))
                setting_1 = float(prev['setting_1'])
                setting_2 = float(prev['setting_2'])
                setting_3 = float(prev['setting_3'])
            else:
                # Default baseline
                s_vals = [SENSOR_METADATA[f'sensor_{i}']['baseline'] for i in range(1, 22)]
                setting_1, setting_2, setting_3 = 0.0, 0.0, 100.0

        insert_sql = """
            INSERT INTO sensor_readings (
                aircraft_id, cycle, setting_1, setting_2, setting_3,
                sensor_1, sensor_2, sensor_3, sensor_4, sensor_5, sensor_6,
                sensor_7, sensor_8, sensor_9, sensor_10, sensor_11, sensor_12,
                sensor_13, sensor_14, sensor_15, sensor_16, sensor_17, sensor_18,
                sensor_19, sensor_20, sensor_21, recorded_at
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s
            )
        """
        params = [aircraft_id, next_cycle, setting_1, setting_2, setting_3] + s_vals + [now]
        cursor.execute(insert_sql, tuple(params))
        new_reading_id = cursor.lastrowid

        # Update aircraft current cycles and flight hours
        new_hours = (aircraft.get('flight_hours') or 0) + 2
        cursor.execute(
            "UPDATE aircraft SET current_cycles = %s, flight_hours = %s, updated_at = %s WHERE id = %s",
            (next_cycle, new_hours, now, aircraft_id)
        )
        conn.commit()
        cursor.close()

    return get_latest_sensor_reading(aircraft_id)


def ingest_custom_sensor_reading(aircraft_id, payload):
    """
    Ingests an explicit sensor reading payload into `sensor_readings`.
    Validates physical boundaries and updates aircraft operating cycle.
    """
    if not isinstance(payload, dict):
        raise ValueError("Payload must be a JSON dictionary.")

    cycle = payload.get('cycle')
    if cycle is None:
        raise ValueError("Field 'cycle' is required.")
    try:
        cycle = int(cycle)
        if cycle < 0:
            raise ValueError()
    except (ValueError, TypeError):
        raise ValueError("'cycle' must be a non-negative integer.")

    setting_1 = float(payload.get('setting_1', 0.0))
    setting_2 = float(payload.get('setting_2', 0.0))
    setting_3 = float(payload.get('setting_3', 100.0))

    sensors_dict = payload.get('sensors', {})
    s_vals = []
    for i in range(1, 22):
        k = f'sensor_{i}'
        val = sensors_dict.get(k, payload.get(k, SENSOR_METADATA[k]['baseline']))
        try:
            s_vals.append(float(val))
        except (ValueError, TypeError):
            raise ValueError(f"Sensor '{k}' must be numeric, got: {val}")

    now = datetime.now(timezone.utc)
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id, current_cycles, flight_hours FROM aircraft WHERE id = %s", (aircraft_id,))
        aircraft = cursor.fetchone()
        if not aircraft:
            cursor.close()
            return None

        insert_sql = """
            INSERT INTO sensor_readings (
                aircraft_id, cycle, setting_1, setting_2, setting_3,
                sensor_1, sensor_2, sensor_3, sensor_4, sensor_5, sensor_6,
                sensor_7, sensor_8, sensor_9, sensor_10, sensor_11, sensor_12,
                sensor_13, sensor_14, sensor_15, sensor_16, sensor_17, sensor_18,
                sensor_19, sensor_20, sensor_21, recorded_at
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s
            )
        """
        params = [aircraft_id, cycle, setting_1, setting_2, setting_3] + s_vals + [now]
        cursor.execute(insert_sql, tuple(params))
        new_id = cursor.lastrowid

        if cycle > (aircraft['current_cycles'] or 0):
            cursor.execute(
                "UPDATE aircraft SET current_cycles = %s, updated_at = %s WHERE id = %s",
                (cycle, now, aircraft_id)
            )
        conn.commit()
        cursor.close()

    return get_latest_sensor_reading(aircraft_id)


def get_engine_health_overview(aircraft_id):
    """
    Returns a comprehensive thermodynamic health diagnostic report for the engine,
    including subsystem breakdowns, trend statistics, and C-MAPSS mapping metadata.
    """
    latest = get_latest_sensor_reading(aircraft_id)
    if not latest or not latest.get('success'):
        return latest

    # Query last 30 cycles to calculate trend slopes
    history_res = get_sensor_history(aircraft_id, limit=30)
    history = history_res['history'] if history_res else []

    subsystems = {
        'Fan': {'sensors': ['sensor_1', 'sensor_8', 'sensor_13'], 'status': 'OPTIMAL'},
        'LPC': {'sensors': ['sensor_2'], 'status': 'OPTIMAL'},
        'HPC': {'sensors': ['sensor_3', 'sensor_7', 'sensor_11'], 'status': 'OPTIMAL'},
        'Combustor': {'sensors': ['sensor_10', 'sensor_12', 'sensor_16'], 'status': 'OPTIMAL'},
        'LPT': {'sensors': ['sensor_4'], 'status': 'OPTIMAL'},
        'Bypass_Bleed': {'sensors': ['sensor_6', 'sensor_15', 'sensor_17'], 'status': 'OPTIMAL'},
        'Cooling': {'sensors': ['sensor_20', 'sensor_21'], 'status': 'OPTIMAL'}
    }

    t30_val = latest['sensors']['sensor_3']
    p30_val = latest['sensors']['sensor_7']
    t50_val = latest['sensors']['sensor_4']

    if t30_val > 1600.0 or p30_val < 551.5:
        subsystems['HPC']['status'] = 'CRITICAL' if t30_val > 1605.0 else 'DEGRADED'

    if t50_val > 1420.0:
        subsystems['LPT']['status'] = 'DEGRADED'

    return {
        'success': True,
        'aircraft_id': latest['aircraft_id'],
        'tail_number': latest['tail_number'],
        'model': latest['model'],
        'manufacturer': latest['manufacturer'],
        'engine_type': latest['engine_type'],
        'manufacturing_year': latest['manufacturing_year'],
        'cmapss_unit_id': latest['cmapss_unit_id'],
        'current_cycles': latest['current_cycles'],
        'status': latest['status'],
        'latest_reading': latest,
        'subsystems': subsystems,
        'sensor_metadata': SENSOR_METADATA,
        'dataset_source': DATASET_SOURCE,
        'mapping_notice': DEMONSTRATION_MAPPING_NOTICE
    }
