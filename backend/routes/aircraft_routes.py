"""
Aircraft Management REST API Endpoints.
Provides CRUD capabilities for aircraft fleet inventory.
"""

from flask import Blueprint, request, jsonify
from services.aircraft_service import (
    get_all_aircraft,
    get_aircraft_by_id,
    create_aircraft,
    update_aircraft,
    delete_aircraft
)

aircraft_bp = Blueprint('aircraft', __name__, url_prefix='/api/aircraft')


@aircraft_bp.route('', methods=['GET'])
def list_aircraft():
    """
    GET /api/aircraft
    Query parameters:
      - search: string (matches tail_number, model, manufacturer)
      - status: string (OPERATIONAL, UNDER_MAINTENANCE, ATTENTION_REQUIRED, RETIRED, ALL)
    """
    search = request.args.get('search', None)
    status = request.args.get('status', None)

    aircraft_list = get_all_aircraft(search=search, status=status)
    return jsonify({
        'success': True,
        'count': len(aircraft_list),
        'data': aircraft_list
    }), 200


@aircraft_bp.route('/<int:aircraft_id>', methods=['GET'])
def get_aircraft(aircraft_id):
    """
    GET /api/aircraft/<id>
    Retrieves full details for a single aircraft.
    """
    aircraft = get_aircraft_by_id(aircraft_id)
    if not aircraft:
        return jsonify({
            'success': False,
            'error': 'Not Found',
            'message': f"Aircraft with ID #{aircraft_id} does not exist."
        }), 404

    return jsonify({
        'success': True,
        'data': aircraft
    }), 200


@aircraft_bp.route('', methods=['POST'])
def add_aircraft():
    """
    POST /api/aircraft
    Creates a new aircraft record.
    """
    data = request.get_json()
    if not data or not isinstance(data, dict):
        return jsonify({
            'success': False,
            'error': 'Bad Request',
            'message': 'Request payload must be a valid JSON object.'
        }), 400

    success, errors, created_aircraft = create_aircraft(data)
    if not success:
        return jsonify({
            'success': False,
            'error': 'Validation Error',
            'details': errors,
            'message': 'One or more required fields are invalid or missing.'
        }), 400

    return jsonify({
        'success': True,
        'message': f"Aircraft '{created_aircraft['tail_number']}' registered successfully.",
        'data': created_aircraft
    }), 201


@aircraft_bp.route('/<int:aircraft_id>', methods=['PUT'])
def edit_aircraft(aircraft_id):
    """
    PUT /api/aircraft/<id>
    Updates an existing aircraft record.
    """
    data = request.get_json()
    if not data or not isinstance(data, dict):
        return jsonify({
            'success': False,
            'error': 'Bad Request',
            'message': 'Request payload must be a valid JSON object.'
        }), 400

    success, errors, updated_aircraft = update_aircraft(aircraft_id, data)
    if not success:
        if errors and 'general' in errors:
            return jsonify({
                'success': False,
                'error': 'Not Found',
                'message': errors['general']
            }), 404
        return jsonify({
            'success': False,
            'error': 'Validation Error',
            'details': errors,
            'message': 'One or more update fields are invalid.'
        }), 400

    return jsonify({
        'success': True,
        'message': f"Aircraft '{updated_aircraft['tail_number']}' updated successfully.",
        'data': updated_aircraft
    }), 200


@aircraft_bp.route('/<int:aircraft_id>', methods=['DELETE'])
def remove_aircraft(aircraft_id):
    """
    DELETE /api/aircraft/<id>
    Removes an aircraft from the fleet.
    """
    success, message = delete_aircraft(aircraft_id)
    if not success:
        return jsonify({
            'success': False,
            'error': 'Not Found',
            'message': message
        }), 404

    return jsonify({
        'success': True,
        'message': message
    }), 200
