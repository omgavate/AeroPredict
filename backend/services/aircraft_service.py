"""
Aircraft Fleet Management Service.
Handles business logic, database queries, and input validation for aircraft assets.
"""

from datetime import datetime
import re
from mysql.connector import Error
from config.database import get_db_connection

VALID_STATUSES = {'OPERATIONAL', 'UNDER_MAINTENANCE', 'ATTENTION_REQUIRED', 'RETIRED'}


def validate_aircraft_data(data, is_update=False, existing_id=None):
    """
    Validates aircraft payload according to Task 3 rules:
    - Aircraft name / registration (tail_number): non-empty, unique, valid format
    - Aircraft model: non-empty, string
    - Manufacturer: non-empty, string
    - Manufacturing year: valid year (1950 - current year)
    - Flight hours: non-negative integer >= 0
    - Aircraft status: valid ENUM option
    - C-MAPSS unit ID: integer 1-100 or null, unique if provided
    """
    errors = {}

    # 1. Tail Number / Aircraft Name
    tail_number = data.get('tail_number')
    if not is_update or 'tail_number' in data:
        if not tail_number or not str(tail_number).strip():
            errors['tail_number'] = "Aircraft registration / tail number is required."
        else:
            tail_clean = str(tail_number).strip().upper()
            if len(tail_clean) < 2 or len(tail_clean) > 20:
                errors['tail_number'] = "Tail number must be between 2 and 20 characters."
            elif not re.match(r'^[A-Z0-9\-]+$', tail_clean):
                errors['tail_number'] = "Tail number may only contain uppercase letters, numbers, and hyphens."
            else:
                # Check uniqueness in database
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    if is_update and existing_id:
                        cursor.execute("SELECT id FROM aircraft WHERE tail_number = %s AND id != %s;", (tail_clean, existing_id))
                    else:
                        cursor.execute("SELECT id FROM aircraft WHERE tail_number = %s;", (tail_clean,))
                    if cursor.fetchone():
                        errors['tail_number'] = f"Aircraft with registration '{tail_clean}' already exists."
                    cursor.close()

    # 2. Aircraft Model
    model = data.get('model')
    if not is_update or 'model' in data:
        if not model or not str(model).strip():
            errors['model'] = "Aircraft model is required (e.g. Boeing 737-800)."
        elif len(str(model).strip()) > 50:
            errors['model'] = "Aircraft model cannot exceed 50 characters."

    # 3. Manufacturer
    manufacturer = data.get('manufacturer')
    if not is_update or 'manufacturer' in data:
        if not manufacturer or not str(manufacturer).strip():
            errors['manufacturer'] = "Manufacturer is required (e.g. Boeing, Airbus)."
        elif len(str(manufacturer).strip()) > 50:
            errors['manufacturer'] = "Manufacturer cannot exceed 50 characters."

    # 4. Manufacturing Year
    current_year = datetime.now().year
    if 'manufacturing_year' in data and data['manufacturing_year'] is not None and str(data['manufacturing_year']).strip() != '':
        try:
            year = int(data['manufacturing_year'])
            if year < 1950 or year > current_year + 1:
                errors['manufacturing_year'] = f"Manufacturing year must be between 1950 and {current_year + 1}."
        except (ValueError, TypeError):
            errors['manufacturing_year'] = "Manufacturing year must be a valid 4-digit integer."

    # 5. Flight Hours
    if 'flight_hours' in data and data['flight_hours'] is not None:
        try:
            hours = int(data['flight_hours'])
            if hours < 0:
                errors['flight_hours'] = "Flight hours cannot be negative."
        except (ValueError, TypeError):
            errors['flight_hours'] = "Flight hours must be a non-negative integer."

    # 6. Current Cycles
    if 'current_cycles' in data and data['current_cycles'] is not None:
        try:
            cycles = int(data['current_cycles'])
            if cycles < 0:
                errors['current_cycles'] = "Operating cycles cannot be negative."
        except (ValueError, TypeError):
            errors['current_cycles'] = "Current cycles must be a non-negative integer."

    # 7. Operational Status
    if 'status' in data and data['status'] is not None:
        status_clean = str(data['status']).strip().upper()
        if status_clean not in VALID_STATUSES:
            errors['status'] = f"Status must be one of: {', '.join(sorted(VALID_STATUSES))}."

    # 8. C-MAPSS Unit Mapping
    if 'cmapss_unit_id' in data and data['cmapss_unit_id'] is not None and str(data['cmapss_unit_id']).strip() != '':
        try:
            unit_id = int(data['cmapss_unit_id'])
            if unit_id < 1 or unit_id > 100:
                errors['cmapss_unit_id'] = "NASA C-MAPSS Unit ID must be between 1 and 100."
            else:
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    if is_update and existing_id:
                        cursor.execute("SELECT id FROM aircraft WHERE cmapss_unit_id = %s AND id != %s;", (unit_id, existing_id))
                    else:
                        cursor.execute("SELECT id FROM aircraft WHERE cmapss_unit_id = %s;", (unit_id,))
                    existing = cursor.fetchone()
                    if existing:
                        errors['cmapss_unit_id'] = f"C-MAPSS Unit #{unit_id} is already mapped to another aircraft."
                    cursor.close()
        except (ValueError, TypeError):
            errors['cmapss_unit_id'] = "C-MAPSS Unit ID must be a valid integer between 1 and 100."

    return errors


def get_all_aircraft(search=None, status=None):
    """
    Retrieves all aircraft records with optional search filter and status filter.
    Returns list of aircraft dictionaries.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT 
                a.id,
                a.tail_number,
                a.model,
                a.manufacturer,
                a.manufacturing_year,
                a.engine_type,
                a.cmapss_unit_id,
                a.current_cycles,
                a.flight_hours,
                a.status,
                a.created_at,
                a.updated_at,
                (SELECT COUNT(*) FROM maintenance_records m WHERE m.aircraft_id = a.id AND m.status != 'COMPLETED') AS pending_maintenance_count,
                (SELECT COUNT(*) FROM maintenance_alerts al WHERE al.aircraft_id = a.id AND al.is_resolved = FALSE) AS active_alerts_count
            FROM aircraft a
            WHERE 1=1
        """
        params = []

        if search:
            search_pattern = f"%{search.strip()}%"
            query += " AND (a.tail_number LIKE %s OR a.model LIKE %s OR a.manufacturer LIKE %s)"
            params.extend([search_pattern, search_pattern, search_pattern])

        if status and status.upper() != 'ALL':
            query += " AND a.status = %s"
            params.append(status.upper())

        query += " ORDER BY a.tail_number ASC;"

        cursor.execute(query, tuple(params))
        results = cursor.fetchall()
        cursor.close()

        # Format dates as ISO strings
        for row in results:
            if row.get('created_at'):
                row['created_at'] = row['created_at'].isoformat()
            if row.get('updated_at'):
                row['updated_at'] = row['updated_at'].isoformat()

        return results


def get_aircraft_by_id(aircraft_id):
    """
    Retrieves a single aircraft record by ID including diagnostic overview.
    Returns aircraft dictionary or None.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                a.id,
                a.tail_number,
                a.model,
                a.manufacturer,
                a.manufacturing_year,
                a.engine_type,
                a.cmapss_unit_id,
                a.current_cycles,
                a.flight_hours,
                a.status,
                a.created_at,
                a.updated_at
            FROM aircraft a
            WHERE a.id = %s;
        """, (aircraft_id,))
        aircraft = cursor.fetchone()

        if not aircraft:
            cursor.close()
            return None

        # Fetch recent maintenance records
        cursor.execute("""
            SELECT id, title, description, priority, status, scheduled_date, completed_date, technician_notes
            FROM maintenance_records
            WHERE aircraft_id = %s
            ORDER BY created_at DESC
            LIMIT 5;
        """, (aircraft_id,))
        aircraft['recent_maintenance'] = cursor.fetchall()

        # Fetch recent alerts
        cursor.execute("""
            SELECT id, alert_type, severity, message, cycle, predicted_rul, is_resolved, created_at
            FROM maintenance_alerts
            WHERE aircraft_id = %s
            ORDER BY created_at DESC
            LIMIT 5;
        """, (aircraft_id,))
        aircraft['recent_alerts'] = cursor.fetchall()

        # Fetch latest RUL prediction if available
        cursor.execute("""
            SELECT predicted_rul, risk_level, recommendation, predicted_at
            FROM rul_predictions
            WHERE aircraft_id = %s
            ORDER BY predicted_at DESC
            LIMIT 1;
        """, (aircraft_id,))
        aircraft['latest_prediction'] = cursor.fetchone()

        cursor.close()

        # Format timestamps
        if aircraft.get('created_at'):
            aircraft['created_at'] = aircraft['created_at'].isoformat()
        if aircraft.get('updated_at'):
            aircraft['updated_at'] = aircraft['updated_at'].isoformat()
        for m in aircraft['recent_maintenance']:
            if m.get('scheduled_date'):
                m['scheduled_date'] = str(m['scheduled_date'])
            if m.get('completed_date'):
                m['completed_date'] = str(m['completed_date']) if m['completed_date'] else None
        for al in aircraft['recent_alerts']:
            if al.get('created_at'):
                al['created_at'] = al['created_at'].isoformat()

        return aircraft


def create_aircraft(data):
    """
    Inserts a new aircraft record into the database.
    """
    errors = validate_aircraft_data(data, is_update=False)
    if errors:
        return False, errors, None

    tail_number = str(data['tail_number']).strip().upper()
    model = str(data['model']).strip()
    manufacturer = str(data.get('manufacturer', 'Boeing')).strip()
    manufacturing_year = data.get('manufacturing_year')
    if manufacturing_year is not None and str(manufacturing_year).strip() != '':
        manufacturing_year = int(manufacturing_year)
    else:
        manufacturing_year = None

    engine_type = str(data.get('engine_type', 'CFM56-7B')).strip()
    cmapss_unit_id = data.get('cmapss_unit_id')
    if cmapss_unit_id is not None and str(cmapss_unit_id).strip() != '':
        cmapss_unit_id = int(cmapss_unit_id)
    else:
        cmapss_unit_id = None

    current_cycles = int(data.get('current_cycles', 0))
    flight_hours = int(data.get('flight_hours', 0))
    status = str(data.get('status', 'OPERATIONAL')).strip().upper()

    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            INSERT INTO aircraft (
                tail_number, model, manufacturer, manufacturing_year,
                engine_type, cmapss_unit_id, current_cycles, flight_hours, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (
            tail_number, model, manufacturer, manufacturing_year,
            engine_type, cmapss_unit_id, current_cycles, flight_hours, status
        ))
        conn.commit()
        new_id = cursor.lastrowid
        cursor.close()

    created_aircraft = get_aircraft_by_id(new_id)
    return True, None, created_aircraft


def update_aircraft(aircraft_id, data):
    """
    Updates an existing aircraft record in the database.
    """
    existing = get_aircraft_by_id(aircraft_id)
    if not existing:
        return False, {'general': f"Aircraft with ID #{aircraft_id} not found."}, None

    errors = validate_aircraft_data(data, is_update=True, existing_id=aircraft_id)
    if errors:
        return False, errors, None

    tail_number = str(data.get('tail_number', existing['tail_number'])).strip().upper()
    model = str(data.get('model', existing['model'])).strip()
    manufacturer = str(data.get('manufacturer', existing['manufacturer'])).strip()

    if 'manufacturing_year' in data:
        my = data['manufacturing_year']
        manufacturing_year = int(my) if my is not None and str(my).strip() != '' else None
    else:
        manufacturing_year = existing['manufacturing_year']

    engine_type = str(data.get('engine_type', existing['engine_type'])).strip()

    if 'cmapss_unit_id' in data:
        c_unit = data['cmapss_unit_id']
        cmapss_unit_id = int(c_unit) if c_unit is not None and str(c_unit).strip() != '' else None
    else:
        cmapss_unit_id = existing['cmapss_unit_id']

    current_cycles = int(data.get('current_cycles', existing['current_cycles']))
    flight_hours = int(data.get('flight_hours', existing['flight_hours']))
    status = str(data.get('status', existing['status'])).strip().upper()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE aircraft SET
                tail_number = %s,
                model = %s,
                manufacturer = %s,
                manufacturing_year = %s,
                engine_type = %s,
                cmapss_unit_id = %s,
                current_cycles = %s,
                flight_hours = %s,
                status = %s
            WHERE id = %s;
        """, (
            tail_number, model, manufacturer, manufacturing_year,
            engine_type, cmapss_unit_id, current_cycles, flight_hours, status,
            aircraft_id
        ))
        conn.commit()
        cursor.close()

    updated_aircraft = get_aircraft_by_id(aircraft_id)
    return True, None, updated_aircraft


def delete_aircraft(aircraft_id):
    """
    Deletes an aircraft by ID. Relies on MySQL ON DELETE CASCADE for child records.
    """
    existing = get_aircraft_by_id(aircraft_id)
    if not existing:
        return False, f"Aircraft with ID #{aircraft_id} not found."

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM aircraft WHERE id = %s;", (aircraft_id,))
        conn.commit()
        cursor.close()

    return True, f"Aircraft '{existing['tail_number']}' (ID #{aircraft_id}) was successfully deleted."
