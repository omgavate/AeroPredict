"""
AeroPredict Prediction REST API Routes.
Exposes endpoints for running RUL inference on engine sensor telemetry,
retrieving prognostic health assessments, and accessing model metadata.
"""

from flask import Blueprint, request, jsonify
from services.prediction_service import (
    PredictionService,
    ValidationError,
    AircraftNotFoundError,
    ModelArtifactError
)

prediction_bp = Blueprint('predictions', __name__, url_prefix='/api/predict')


@prediction_bp.route('', methods=['POST'])
def predict_rul_endpoint():
    """
    POST /api/predict
    Evaluates engine sensor telemetry and returns predicted Remaining Useful Life (RUL),
    risk tier, and actionable maintenance recommendations.
    
    Request Body:
    {
        "aircraft_id": 1,
        "cycle": 192,
        "telemetry": {
            "setting_1": -0.0012,
            "setting_2": 0.0004,
            "sensor_2": 643.12,
            "sensor_3": 1610.10,
            "sensor_4": 1435.60,
            ...
        },
        "save_to_db": true,
        "history": [ ... optional list of previous cycle dicts ... ]
    }
    """
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({
            'success': False,
            'error': 'Bad Request',
            'message': 'Request body must be a valid JSON object containing aircraft_id, cycle, and telemetry.'
        }), 400

    try:
        service = PredictionService()
        result = service.predict_rul(data)

        return jsonify({
            'success': True,
            'message': 'RUL prediction evaluated successfully.',
            'data': result
        }), 200

    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': 'Validation Error',
            'message': str(e)
        }), 400

    except AircraftNotFoundError as e:
        return jsonify({
            'success': False,
            'error': 'Not Found',
            'message': str(e)
        }), 404

    except ModelArtifactError as e:
        return jsonify({
            'success': False,
            'error': 'Service Unavailable',
            'message': str(e)
        }), 503

    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Internal Server Error',
            'message': f"Unexpected inference error: {str(e)}"
        }), 500


@prediction_bp.route('/latest/<int:aircraft_id>', methods=['GET'])
def get_latest_prediction_endpoint(aircraft_id):
    """
    GET /api/predict/latest/<aircraft_id>
    Retrieves the most recent RUL prediction recorded for an aircraft.
    """
    try:
        service = PredictionService()
        record = service.get_latest_prediction(aircraft_id)
        if not record:
            return jsonify({
                'success': False,
                'error': 'Not Found',
                'message': f"No prior prediction records found for aircraft ID {aircraft_id}."
            }), 404

        return jsonify({
            'success': True,
            'data': record
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Internal Server Error',
            'message': str(e)
        }), 500


@prediction_bp.route('/history/<int:aircraft_id>', methods=['GET'])
def get_prediction_history_endpoint(aircraft_id):
    """
    GET /api/predict/history/<aircraft_id>?limit=50
    Retrieves chronological prediction history for an aircraft.
    """
    limit = request.args.get('limit', default=50, type=int)
    limit = min(max(1, limit), 200)

    try:
        service = PredictionService()
        history = service.get_prediction_history(aircraft_id, limit=limit)
        return jsonify({
            'success': True,
            'count': len(history),
            'aircraft_id': aircraft_id,
            'data': history
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Internal Server Error',
            'message': str(e)
        }), 500


@prediction_bp.route('/model-info', methods=['GET'])
def get_model_info_endpoint():
    """
    GET /api/predict/model-info
    Returns information regarding the active machine learning model,
    validation metrics, top predictive features, and operational bounds.
    """
    try:
        service = PredictionService()
        metadata = service.get_model_metadata()
        return jsonify({
            'success': True,
            'data': metadata
        }), 200

    except ModelArtifactError as e:
        return jsonify({
            'success': False,
            'error': 'Service Unavailable',
            'message': str(e)
        }), 503

    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Internal Server Error',
            'message': str(e)
        }), 500
