"""
Maintenance Management REST API Routes.
Provides CRUD endpoints for maintenance work orders, status tracking,
technician logs, and airframe maintenance histories.
"""

from flask import Blueprint, request, jsonify
from services.maintenance_service import (
    get_all_maintenance_records,
    get_maintenance_record_by_id,
    create_maintenance_record,
    update_maintenance_record,
    delete_maintenance_record
)

maintenance_bp = Blueprint('maintenance', __name__)


# --------------------------------------------------------------------------
# 1. List Maintenance Records
# --------------------------------------------------------------------------

@maintenance_bp.route('/api/maintenance', methods=['GET'])
def list_maintenance_records():
    """
    GET /api/maintenance
    Query parameters:
      - aircraft_id: int (filter by aircraft)
      - status: PENDING, SCHEDULED, IN_PROGRESS, COMPLETED, CANCELLED, ALL
      - priority: LOW, MEDIUM, HIGH, CRITICAL, ALL
      - search: string (matches title, description, tail_number, model)
    """
    aircraft_id = request.args.get('aircraft_id', None)
    status = request.args.get('status', None)
    priority = request.args.get('priority', None)
    search = request.args.get('search', None)

    records = get_all_maintenance_records(
        aircraft_id=aircraft_id,
        status=status,
        priority=priority,
        search=search
    )

    return jsonify({
        'success': True,
        'count': len(records),
        'data': records
    }), 200


# --------------------------------------------------------------------------
# 2. Get Single Maintenance Record
# --------------------------------------------------------------------------

@maintenance_bp.route('/api/maintenance/<int:record_id>', methods=['GET'])
def get_maintenance_record(record_id):
    """
    GET /api/maintenance/<record_id>
    Retrieves full details for a single work order.
    """
    record = get_maintenance_record_by_id(record_id)
    if not record:
        return jsonify({
            'success': False,
            'error': 'Not Found',
            'message': f"Maintenance work order #{record_id} does not exist."
        }), 404

    return jsonify({
        'success': True,
        'data': record
    }), 200


# --------------------------------------------------------------------------
# 3. Create Maintenance Record
# --------------------------------------------------------------------------

@maintenance_bp.route('/api/maintenance', methods=['POST'])
def add_maintenance_record():
    """
    POST /api/maintenance
    Creates a new maintenance work order.
    Request Body:
    {
        "aircraft_id": 1,
        "title": "HPC Rotor Stage 5 Borescope Inspection",
        "description": "Inspect blades for thermal cracking.",
        "priority": "HIGH",
        "status": "PENDING",
        "scheduled_date": "2026-11-12",
        "technician_notes": "Assigned to Powerplant Depot."
    }
    """
    payload = request.get_json(silent=True)
    if not payload or not isinstance(payload, dict):
        return jsonify({
            'success': False,
            'error': 'Bad Request',
            'message': 'Request body must be a valid JSON object.'
        }), 400

    result = create_maintenance_record(payload)
    if not result['success']:
        return jsonify(result), 400

    return jsonify(result), 201


# --------------------------------------------------------------------------
# 4. Update Maintenance Record
# --------------------------------------------------------------------------

@maintenance_bp.route('/api/maintenance/<int:record_id>', methods=['PUT'])
def update_record(record_id):
    """
    PUT /api/maintenance/<record_id>
    Updates an existing maintenance work order.
    """
    payload = request.get_json(silent=True)
    if not payload or not isinstance(payload, dict):
        return jsonify({
            'success': False,
            'error': 'Bad Request',
            'message': 'Request body must be a valid JSON object.'
        }), 400

    result = update_maintenance_record(record_id, payload)
    if not result['success']:
        status_code = 404 if result.get('error') == 'Not Found' else 400
        return jsonify(result), status_code

    return jsonify(result), 200


# --------------------------------------------------------------------------
# 5. Delete Maintenance Record
# --------------------------------------------------------------------------

@maintenance_bp.route('/api/maintenance/<int:record_id>', methods=['DELETE'])
def remove_record(record_id):
    """
    DELETE /api/maintenance/<record_id>
    Permanently deletes a maintenance record.
    """
    result = delete_maintenance_record(record_id)
    if not result['success']:
        return jsonify(result), 404

    return jsonify(result), 200


# --------------------------------------------------------------------------
# 6. Aircraft Maintenance History
# --------------------------------------------------------------------------

@maintenance_bp.route('/api/maintenance/history/<int:aircraft_id>', methods=['GET'])
@maintenance_bp.route('/api/aircraft/<int:aircraft_id>/maintenance', methods=['GET'])
def get_aircraft_maintenance_history(aircraft_id):
    """
    GET /api/maintenance/history/<aircraft_id>
    GET /api/aircraft/<aircraft_id>/maintenance
    Retrieves all past and active maintenance work orders for a specific airframe.
    """
    records = get_all_maintenance_records(aircraft_id=aircraft_id)
    return jsonify({
        'success': True,
        'aircraft_id': aircraft_id,
        'count': len(records),
        'data': records
    }), 200
