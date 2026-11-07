"""
Maintenance Management Service.
Handles work order lifecycle, database queries, business validations,
technician notes, and aircraft operational status alignment.
"""

from datetime import datetime, date
import re
import logging
from config.database import get_db_connection

logger = logging.getLogger('aeropredict.maintenance_service')

VALID_PRIORITIES = {'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'}
VALID_STATUSES = {'PENDING', 'SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED'}

INITIAL_SEEDED_ORDERS = [
    {
        'aircraft_id': 1,
        'title': 'Emergency HPC Borescope & Blade Replacement',
        'description': 'Inspect High-Pressure Compressor rotor blades for foreign object damage or thermal cracking following high-risk RUL prediction alert.',
        'priority': 'CRITICAL',
        'status': 'PENDING',
        'scheduled_date': '2026-11-08',
        'completed_date': None,
        'technician_notes': 'Parts allocated from Hangar Bay 4. Lead Powerplant Engineer assigned.'
    },
    {
        'aircraft_id': 3,
        'title': 'C-Check Turbofan Overhaul & LPT Seal Renewal',
        'description': 'Scheduled heavy check overhaul including combustor liner inspection and Low Pressure Turbine seal replacement.',
        'priority': 'HIGH',
        'status': 'IN_PROGRESS',
        'scheduled_date': '2026-11-05',
        'completed_date': None,
        'technician_notes': 'Engine removed and placed on test-cell stand. Inspection 60% complete.'
    },
    {
        'aircraft_id': 5,
        'title': 'Fuel Flow Ratio & Sensor 12 Calibration',
        'description': 'Recalibrate static pressure tap and fuel metering unit following divergence detection.',
        'priority': 'MEDIUM',
        'status': 'PENDING',
        'scheduled_date': '2026-11-10',
        'completed_date': None,
        'technician_notes': 'Awaiting aircraft arrival at BOM hub.'
    },
    {
        'aircraft_id': 4,
        'title': 'Routine A-Check 100-Cycle Lubrication Service',
        'description': 'Standard oil filter change, magnetic chip detector inspection, and hydraulic fluid servicing.',
        'priority': 'LOW',
        'status': 'COMPLETED',
        'scheduled_date': '2026-10-30',
        'completed_date': '2026-10-31',
        'technician_notes': 'Zero metal debris on magnetic chip detector. Oil samples sent to lab. Engine returned to flight service.'
    }
]


def ensure_maintenance_seeded():
    """
    Seeds initial realistic maintenance work orders if table is empty.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT COUNT(*) as cnt FROM maintenance_records")
            row = cursor.fetchone()
            if row and row['cnt'] == 0:
                insert_sql = """
                    INSERT INTO maintenance_records (
                        aircraft_id, title, description, priority, status,
                        scheduled_date, completed_date, technician_notes, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                """
                for item in INITIAL_SEEDED_ORDERS:
                    cursor.execute(insert_sql, (
                        item['aircraft_id'],
                        item['title'],
                        item['description'],
                        item['priority'],
                        item['status'],
                        item['scheduled_date'],
                        item['completed_date'],
                        item['technician_notes']
                    ))
                conn.commit()
                logger.info("Initial maintenance work orders seeded into MySQL.")
            cursor.close()
    except Exception as e:
        logger.warning(f"Error checking/seeding maintenance records: {e}")


def validate_maintenance_payload(data, is_update=False):
    """
    Validates work order fields according to Phase 10 requirements:
    - Aircraft ID: positive integer, must exist in `aircraft` table
    - Title / Issue Description: 3-150 characters, non-empty
    - Scheduled Date: valid YYYY-MM-DD
    - Priority: LOW, MEDIUM, HIGH, CRITICAL
    - Status: PENDING, SCHEDULED, IN_PROGRESS, COMPLETED, CANCELLED
    - Completed Date: valid YYYY-MM-DD if provided
    """
    errors = {}

    # 1. Aircraft ID
    if not is_update or 'aircraft_id' in data:
        aircraft_id = data.get('aircraft_id')
        if aircraft_id is None:
            errors['aircraft_id'] = "Aircraft ID is required."
        else:
            try:
                aid = int(aircraft_id)
                if aid <= 0:
                    errors['aircraft_id'] = "Aircraft ID must be a positive integer."
                else:
                    # Check existence
                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT id FROM aircraft WHERE id = %s", (aid,))
                        if not cursor.fetchone():
                            errors['aircraft_id'] = f"Aircraft with ID #{aid} does not exist."
                        cursor.close()
            except (ValueError, TypeError):
                errors['aircraft_id'] = "Aircraft ID must be a valid integer."

    # 2. Title
    if not is_update or 'title' in data:
        title = data.get('title')
        if not title or not str(title).strip():
            errors['title'] = "Work order title / issue summary is required."
        else:
            clean_title = str(title).strip()
            if len(clean_title) < 3 or len(clean_title) > 150:
                errors['title'] = "Title must be between 3 and 150 characters."

    # 3. Priority
    if not is_update or 'priority' in data:
        priority = data.get('priority', 'MEDIUM')
        if str(priority).upper() not in VALID_PRIORITIES:
            errors['priority'] = f"Invalid priority. Allowed options: {', '.join(sorted(VALID_PRIORITIES))}."

    # 4. Status
    if not is_update or 'status' in data:
        status = data.get('status', 'PENDING')
        if str(status).upper() not in VALID_STATUSES:
            errors['status'] = f"Invalid status. Allowed options: {', '.join(sorted(VALID_STATUSES))}."

    # 5. Scheduled Date
    if not is_update or 'scheduled_date' in data:
        sched_date = data.get('scheduled_date')
        if not sched_date:
            errors['scheduled_date'] = "Scheduled maintenance date is required."
        else:
            try:
                if isinstance(sched_date, str):
                    datetime.strptime(sched_date.strip(), '%Y-%m-%d')
            except ValueError:
                errors['scheduled_date'] = "Scheduled date must be in YYYY-MM-DD format."

    # 6. Completed Date (optional)
    if 'completed_date' in data and data['completed_date']:
        comp_date = data['completed_date']
        try:
            if isinstance(comp_date, str):
                datetime.strptime(comp_date.strip(), '%Y-%m-%d')
        except ValueError:
            errors['completed_date'] = "Completed date must be in YYYY-MM-DD format."

    return errors


def get_all_maintenance_records(aircraft_id=None, status=None, priority=None, search=None):
    """
    Fetches all maintenance records joined with aircraft details.
    Supports filtering by aircraft_id, status, priority, and text search.
    """
    ensure_maintenance_seeded()

    query = """
        SELECT m.id, m.aircraft_id, m.title, m.description, m.priority,
               m.status, m.scheduled_date, m.completed_date, m.technician_notes,
               m.created_at, m.updated_at,
               a.tail_number, a.model, a.manufacturer, a.engine_type, a.status as aircraft_status
        FROM maintenance_records m
        JOIN aircraft a ON m.aircraft_id = a.id
        WHERE 1=1
    """
    params = []

    if aircraft_id:
        try:
            query += " AND m.aircraft_id = %s"
            params.append(int(aircraft_id))
        except (ValueError, TypeError):
            pass

    if status and str(status).upper() != 'ALL':
        clean_status = str(status).strip().upper()
        # If user searches PENDING, also match SCHEDULED for compatibility
        if clean_status == 'PENDING':
            query += " AND m.status IN ('PENDING', 'SCHEDULED')"
        else:
            query += " AND m.status = %s"
            params.append(clean_status)

    if priority and str(priority).upper() != 'ALL':
        query += " AND m.priority = %s"
        params.append(str(priority).strip().upper())

    if search and str(search).strip():
        term = f"%{str(search).strip()}%"
        query += " AND (m.title LIKE %s OR m.description LIKE %s OR a.tail_number LIKE %s OR a.model LIKE %s)"
        params.extend([term, term, term, term])

    query += " ORDER BY m.scheduled_date DESC, m.id DESC"

    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        cursor.close()

        results = []
        for r in rows:
            results.append({
                'id': r['id'],
                'aircraft_id': r['aircraft_id'],
                'tail_number': r['tail_number'],
                'model': r['model'],
                'manufacturer': r['manufacturer'],
                'engine_type': r['engine_type'],
                'aircraft_status': r['aircraft_status'],
                'title': r['title'],
                'description': r['description'] or '',
                'priority': r['priority'],
                'status': r['status'],
                'scheduled_date': r['scheduled_date'].strftime('%Y-%m-%d') if r.get('scheduled_date') else None,
                'completed_date': r['completed_date'].strftime('%Y-%m-%d') if r.get('completed_date') else None,
                'technician_notes': r['technician_notes'] or '',
                'created_at': r['created_at'].isoformat() if r.get('created_at') else None,
                'updated_at': r['updated_at'].isoformat() if r.get('updated_at') else None
            })
        return results


def get_maintenance_record_by_id(record_id):
    """
    Fetches a single maintenance work order by ID.
    """
    ensure_maintenance_seeded()

    query = """
        SELECT m.id, m.aircraft_id, m.title, m.description, m.priority,
               m.status, m.scheduled_date, m.completed_date, m.technician_notes,
               m.created_at, m.updated_at,
               a.tail_number, a.model, a.manufacturer, a.engine_type, a.status as aircraft_status
        FROM maintenance_records m
        JOIN aircraft a ON m.aircraft_id = a.id
        WHERE m.id = %s
    """
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, (record_id,))
        r = cursor.fetchone()
        cursor.close()

        if not r:
            return None

        return {
            'id': r['id'],
            'aircraft_id': r['aircraft_id'],
            'tail_number': r['tail_number'],
            'model': r['model'],
            'manufacturer': r['manufacturer'],
            'engine_type': r['engine_type'],
            'aircraft_status': r['aircraft_status'],
            'title': r['title'],
            'description': r['description'] or '',
            'priority': r['priority'],
            'status': r['status'],
            'scheduled_date': r['scheduled_date'].strftime('%Y-%m-%d') if r.get('scheduled_date') else None,
            'completed_date': r['completed_date'].strftime('%Y-%m-%d') if r.get('completed_date') else None,
            'technician_notes': r['technician_notes'] or '',
            'created_at': r['created_at'].isoformat() if r.get('created_at') else None,
            'updated_at': r['updated_at'].isoformat() if r.get('updated_at') else None
        }


def create_maintenance_record(data):
    """
    Creates a new maintenance work order.
    """
    errors = validate_maintenance_payload(data, is_update=False)
    if errors:
        return {'success': False, 'error': 'Validation Error', 'details': errors}

    aircraft_id = int(data['aircraft_id'])
    title = str(data['title']).strip()
    description = str(data.get('description', '')).strip()
    priority = str(data.get('priority', 'MEDIUM')).strip().upper()
    status = str(data.get('status', 'PENDING')).strip().upper()
    scheduled_date = str(data['scheduled_date']).strip()
    completed_date = str(data['completed_date']).strip() if data.get('completed_date') else None
    technician_notes = str(data.get('technician_notes', '')).strip()

    if status == 'COMPLETED' and not completed_date:
        completed_date = date.today().strftime('%Y-%m-%d')

    with get_db_connection() as conn:
        cursor = conn.cursor()
        insert_sql = """
            INSERT INTO maintenance_records (
                aircraft_id, title, description, priority, status,
                scheduled_date, completed_date, technician_notes, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """
        cursor.execute(insert_sql, (
            aircraft_id,
            title,
            description,
            priority,
            status,
            scheduled_date,
            completed_date,
            technician_notes
        ))
        new_id = cursor.lastrowid

        # If priority is CRITICAL or status is IN_PROGRESS, align aircraft status
        if status == 'IN_PROGRESS':
            cursor.execute("UPDATE aircraft SET status = 'UNDER_MAINTENANCE' WHERE id = %s", (aircraft_id,))
        elif priority == 'CRITICAL':
            cursor.execute(
                "UPDATE aircraft SET status = 'ATTENTION_REQUIRED' WHERE id = %s AND status = 'OPERATIONAL'",
                (aircraft_id,)
            )

        conn.commit()
        cursor.close()

    created_record = get_maintenance_record_by_id(new_id)
    return {'success': True, 'data': created_record}


def update_maintenance_record(record_id, data):
    """
    Updates an existing maintenance record.
    """
    existing = get_maintenance_record_by_id(record_id)
    if not existing:
        return {'success': False, 'error': 'Not Found', 'message': f"Maintenance record #{record_id} does not exist."}

    errors = validate_maintenance_payload(data, is_update=True)
    if errors:
        return {'success': False, 'error': 'Validation Error', 'details': errors}

    # Extract update fields
    aircraft_id = int(data.get('aircraft_id', existing['aircraft_id']))
    title = str(data.get('title', existing['title'])).strip()
    description = str(data.get('description', existing['description'])).strip()
    priority = str(data.get('priority', existing['priority'])).strip().upper()
    status = str(data.get('status', existing['status'])).strip().upper()
    scheduled_date = str(data.get('scheduled_date', existing['scheduled_date'])).strip()
    completed_date = data.get('completed_date', existing['completed_date'])

    if status == 'COMPLETED' and not completed_date:
        completed_date = date.today().strftime('%Y-%m-%d')
    elif status != 'COMPLETED' and 'completed_date' not in data:
        completed_date = None

    technician_notes = str(data.get('technician_notes', existing['technician_notes'])).strip()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        update_sql = """
            UPDATE maintenance_records
            SET aircraft_id = %s,
                title = %s,
                description = %s,
                priority = %s,
                status = %s,
                scheduled_date = %s,
                completed_date = %s,
                technician_notes = %s,
                updated_at = NOW()
            WHERE id = %s
        """
        cursor.execute(update_sql, (
            aircraft_id,
            title,
            description,
            priority,
            status,
            scheduled_date,
            completed_date,
            technician_notes,
            record_id
        ))

        # Check aircraft operational realignment on completion
        if status == 'COMPLETED':
            cursor.execute("""
                SELECT COUNT(*) as active_cnt
                FROM maintenance_records
                WHERE aircraft_id = %s AND status IN ('PENDING', 'SCHEDULED', 'IN_PROGRESS') AND id != %s
            """, (aircraft_id, record_id))
            active = cursor.fetchone()
            if active and active[0] == 0:
                # No other active work orders, mark aircraft operational if it was under maintenance
                cursor.execute(
                    "UPDATE aircraft SET status = 'OPERATIONAL' WHERE id = %s AND status = 'UNDER_MAINTENANCE'",
                    (aircraft_id,)
                )
        elif status == 'IN_PROGRESS':
            cursor.execute("UPDATE aircraft SET status = 'UNDER_MAINTENANCE' WHERE id = %s", (aircraft_id,))

        conn.commit()
        cursor.close()

    updated_record = get_maintenance_record_by_id(record_id)
    return {'success': True, 'data': updated_record}


def delete_maintenance_record(record_id):
    """
    Deletes a maintenance record.
    """
    existing = get_maintenance_record_by_id(record_id)
    if not existing:
        return {'success': False, 'error': 'Not Found', 'message': f"Maintenance record #{record_id} does not exist."}

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM maintenance_records WHERE id = %s", (record_id,))
        conn.commit()
        cursor.close()

    return {'success': True, 'message': f"Maintenance record #{record_id} permanently removed."}
