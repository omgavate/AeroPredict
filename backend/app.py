"""
AeroPredict Backend Application Factory & Server Runner.
Initializes Flask, CORS, database utilities, blueprints, and centralized error handling.
"""

import os
import sys
from pathlib import Path
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Load environment configuration
env_path = backend_dir / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

from routes.health_routes import health_bp
from routes.aircraft_routes import aircraft_bp
from routes.prediction_routes import prediction_bp
from routes.engine_routes import engine_bp
from routes.maintenance_routes import maintenance_bp
from routes.dashboard_routes import dashboard_bp


def create_app(test_config=None):
    """
    Application factory for AeroPredict Flask API.
    """
    app = Flask(__name__)

    # Default configuration
    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY', 'aeropredict-dev-secret-key-2026'),
        JSON_SORT_KEYS=False
    )

    if test_config is not None:
        app.config.update(test_config)

    # Enable Cross-Origin Resource Sharing (CORS)
    cors_origins = [o.strip() for o in os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000').split(',') if o.strip()]
    CORS(app, resources={r"/api/*": {"origins": cors_origins + ["*"]}})

    # Register Blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(aircraft_bp)
    app.register_blueprint(prediction_bp)
    app.register_blueprint(engine_bp)
    app.register_blueprint(maintenance_bp)
    app.register_blueprint(dashboard_bp)

    # Root informational route
    @app.route('/', methods=['GET'])
    def root():
        return jsonify({
            'service': 'AeroPredict REST API Server',
            'version': '1.0.0',
            'status': 'online',
            'endpoints': {
                'health': '/api/health',
                'documentation': '/api/docs (Phase 4)'
            }
        }), 200

    # Centralized Error Handlers
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'success': False,
            'error': 'Bad Request',
            'message': getattr(error, 'description', 'Invalid request payload or parameters.')
        }), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 'Not Found',
            'message': getattr(error, 'description', 'The requested resource was not found on this server.')
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'success': False,
            'error': 'Method Not Allowed',
            'message': 'HTTP method is not supported for this endpoint.'
        }), 405

    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({
            'success': False,
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred on the server.'
        }), 500

    @app.errorhandler(Exception)
    def handle_unexpected_exception(error):
        app.logger.error(f"Unhandled Exception: {error}", exc_info=True)
        message = str(error) if app.config.get('DEBUG') else 'An unexpected server error occurred.'
        return jsonify({
            'success': False,
            'error': 'Server Exception',
            'message': message
        }), 500

    return app


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', '1') == '1'
    app = create_app()
    print(f"✈️ Starting AeroPredict API Server on http://localhost:{port} (Debug: {debug})")
    app.run(host='0.0.0.0', port=port, debug=debug)
