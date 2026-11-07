"""Routes package for AeroPredict Backend."""
from .health_routes import health_bp
from .aircraft_routes import aircraft_bp
from .prediction_routes import prediction_bp
from .engine_routes import engine_bp
from .maintenance_routes import maintenance_bp
from .dashboard_routes import dashboard_bp

__all__ = [
    'health_bp',
    'aircraft_bp',
    'prediction_bp',
    'engine_bp',
    'maintenance_bp',
    'dashboard_bp'
]
