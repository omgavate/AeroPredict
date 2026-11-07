"""
Engine Telemetry & Health Monitoring REST API Endpoints.
Provides endpoints for retrieving real-time sensor readings, cycle information,
chronological sensor histories, thermodynamic health summaries, and telemetry progression.
"""

from flask import Blueprint, request, jsonify
from services.engine_service import (
    get_latest_sensor_reading,
    get_sensor_history,
    advance_sensor_cycle,
    ingest_custom_sensor_reading,
    get_engine_health_overview,
    DEMONSTRATION_MAPPING_NOTICE,
    DATASET_SOURCE
)

engine_bp = Blueprint('engine', __name__)


# --------------------------------------------------------------------------
# 1. Latest Sensor Readings & Cycle Information
# --------------------------------------------------------------------------

@engine_bp.route('/api/aircraft/<int:aircraft_id>/sensors/latest', methods=['GET'])
@engine_bp.route('/api/engine/<int:aircraft_id>/readings', methods=['GET'])
def get_latest_readings(aircraft_id):
    """
    GET /api/aircraft/<id>/sensors/latest
    GET /api/engine/<id>/readings
    Returns the latest flight cycle, operational settings, 21 sensor values,
    and thermodynamic health indicator deltas.
    """
    result = get_latest_sensor_reading(aircraft_id)
    if result is None:
        return jsonify({
            'success': False,
            'error': 'Not Found',
            'message': f"Aircraft with ID #{aircraft_id} does not exist."
        }), 404

    return jsonify({
        'success': True,
        'data': result
    }), 200


# --------------------------------------------------------------------------
# 2. Sensor History & Trend Data
# --------------------------------------------------------------------------

@engine_bp.route('/api/aircraft/<int:aircraft_id>/sensors/history', methods=['GET'])
@engine_bp.route('/api/engine/<int:aircraft_id>/history', methods=['GET'])
def get_history(aircraft_id):
    """
    GET /api/aircraft/<id>/sensors/history
    GET /api/engine/<id>/history
    Query parameters:
      - limit: int (default 50, max 500)
      - cycle_start: int (optional)
      - cycle_end: int (optional)
      - sensors: string comma-separated (e.g. sensor_2,sensor_3,sensor_4,sensor_7)
    Returns chronological historical telemetry for charting.
    """
    limit_param = request.args.get('limit', 50)
    cycle_start = request.args.get('cycle_start', None)
    cycle_end = request.args.get('cycle_end', None)
    sensors_filter = request.args.get('sensors', None)

    try:
        limit = int(limit_param)
        if limit <= 0:
            limit = 50
    except (ValueError, TypeError):
        limit = 50

    try:
        start = int(cycle_start) if cycle_start is not None else None
    except (ValueError, TypeError):
        start = None

    try:
        end = int(cycle_end) if cycle_end is not None else None
    except (ValueError, TypeError):
        end = None

    result = get_sensor_history(
        aircraft_id,
        limit=limit,
        sensors=sensors_filter,
        cycle_start=start,
        cycle_end=end
    )

    if result is None:
        return jsonify({
            'success': False,
            'error': 'Not Found',
            'message': f"Aircraft with ID #{aircraft_id} does not exist."
        }), 404

    return jsonify({
        'success': True,
        'data': result
    }), 200


# --------------------------------------------------------------------------
# 3. Telemetry Cycle Progression (Advance / Ingest)
# --------------------------------------------------------------------------

@engine_bp.route('/api/aircraft/<int:aircraft_id>/sensors/advance-cycle', methods=['POST'])
@engine_bp.route('/api/aircraft/<int:aircraft_id>/sensors/simulate-cycle', methods=['POST'])
@engine_bp.route('/api/engine/<int:aircraft_id>/advance', methods=['POST'])
def advance_cycle(aircraft_id):
    """
    POST /api/aircraft/<id>/sensors/advance-cycle
    POST /api/aircraft/<id>/sensors/simulate-cycle
    POST /api/engine/<id>/advance
    Advances aircraft telemetry by 1 cycle using actual C-MAPSS FD001 data
    for the mapped unit (or physics-based continuation drift if beyond dataset cycles).
    """
    result = advance_sensor_cycle(aircraft_id)
    if result is None:
        return jsonify({
            'success': False,
            'error': 'Not Found',
            'message': f"Aircraft with ID #{aircraft_id} does not exist."
        }), 404

    return jsonify({
        'success': True,
        'message': f"Successfully advanced telemetry to flight cycle {result['cycle']}.",
        'data': result
    }), 200


# --------------------------------------------------------------------------
# 4. Custom Telemetry Ingestion
# --------------------------------------------------------------------------

@engine_bp.route('/api/aircraft/<int:aircraft_id>/sensors', methods=['POST'])
def ingest_reading(aircraft_id):
    """
    POST /api/aircraft/<id>/sensors
    Ingests an explicit custom sensor reading payload.
    """
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({
            'success': False,
            'error': 'Bad Request',
            'message': 'Request body must be a valid JSON object.'
        }), 400

    try:
        result = ingest_custom_sensor_reading(aircraft_id, payload)
        if result is None:
            return jsonify({
                'success': False,
                'error': 'Not Found',
                'message': f"Aircraft with ID #{aircraft_id} does not exist."
            }), 404

        return jsonify({
            'success': True,
            'message': f"Sensor reading for cycle {result['cycle']} recorded successfully.",
            'data': result
        }), 201
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': 'Validation Error',
            'message': str(e)
        }), 400


# --------------------------------------------------------------------------
# 5. Engine Health Diagnostic Overview
# --------------------------------------------------------------------------

@engine_bp.route('/api/aircraft/<int:aircraft_id>/engine', methods=['GET'])
@engine_bp.route('/api/engine/<int:aircraft_id>', methods=['GET'])
def get_engine_overview(aircraft_id):
    """
    GET /api/aircraft/<id>/engine
    GET /api/engine/<id>
    Retrieves full thermodynamic diagnostic summary, subsystem status,
    sensor baseline deltas, and C-MAPSS dataset mapping notice.
    """
    result = get_engine_health_overview(aircraft_id)
    if result is None:
        return jsonify({
            'success': False,
            'error': 'Not Found',
            'message': f"Aircraft with ID #{aircraft_id} does not exist."
        }), 404

    return jsonify({
        'success': True,
        'data': result
    }), 200
