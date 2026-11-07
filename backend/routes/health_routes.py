"""
Health and Diagnostic Endpoints for AeroPredict API.
Verifies service availability, system timestamp, and MySQL database connectivity.
"""

from datetime import datetime, timezone
import sys
from flask import Blueprint, jsonify
from config.database import check_db_connection

health_bp = Blueprint('health', __name__, url_prefix='/api')


@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    GET /api/health
    Performs end-to-end service and database connectivity check.
    """
    db_ok, db_message, db_details = check_db_connection()

    status_code = 200 if db_ok else 503

    response = {
        'success': db_ok,
        'status': 'healthy' if db_ok else 'degraded',
        'service': 'AeroPredict REST API',
        'version': '1.0.0',
        'environment': 'development',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'runtime': {
            'python_version': sys.version.split()[0],
            'platform': sys.platform
        },
        'database': {
            'connected': db_ok,
            'message': db_message,
            'host': db_details.get('host'),
            'port': db_details.get('port'),
            'database': db_details.get('database'),
            'server_version': db_details.get('server_version'),
            'database_exists': db_details.get('database_exists', False),
            'error_code': db_details.get('error_code')
        }
    }

    return jsonify(response), status_code
