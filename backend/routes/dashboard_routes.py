"""
AeroPredict Dashboard API Routes.
Exposes endpoints for aggregated executive fleet statistics, health overview,
alerts feed, and maintenance distribution.
"""

from flask import Blueprint, jsonify, request
from services.dashboard_service import (
    get_complete_dashboard,
    get_kpi_stats,
    get_health_overview,
    get_recent_alerts,
    get_fleet_summary,
    get_maintenance_distribution,
    get_recent_activity,
    resolve_alert
)

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')


@dashboard_bp.route('', methods=['GET'])
def get_dashboard_root():
    """
    GET /api/dashboard
    Returns the comprehensive aggregated executive dashboard dataset:
    KPI stats, engine health distribution, maintenance backlog, recent alerts,
    fleet summary telemetry, and recent activity feed.
    """
    try:
        data = get_complete_dashboard()
        return jsonify({
            'success': True,
            'data': data
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Dashboard Aggregation Error',
            'message': str(e)
        }), 500


@dashboard_bp.route('/stats', methods=['GET'])
def get_dashboard_statistics():
    """
    GET /api/dashboard/stats
    Returns fleet KPI metrics (total, operational, under maintenance, attention required,
    pending maintenance, active alerts).
    """
    try:
        stats = get_kpi_stats()
        return jsonify({
            'success': True,
            'data': stats
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Stats Query Error',
            'message': str(e)
        }), 500


@dashboard_bp.route('/health-overview', methods=['GET'])
def get_health_overview_endpoint():
    """
    GET /api/dashboard/health-overview
    Returns fleet-wide engine health breakdown and average RUL indicators.
    """
    try:
        overview = get_health_overview()
        return jsonify({
            'success': True,
            'data': overview
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Health Overview Error',
            'message': str(e)
        }), 500


@dashboard_bp.route('/alerts', methods=['GET'])
def get_dashboard_alerts():
    """
    GET /api/dashboard/alerts
    Returns recent high/critical maintenance alerts with optional limit and filtering.
    """
    try:
        limit = request.args.get('limit', default=10, type=int)
        unresolved_only = request.args.get('unresolved', default='false').lower() in ('true', '1')
        alerts = get_recent_alerts(limit=limit, unresolved_only=unresolved_only)
        return jsonify({
            'success': True,
            'data': alerts,
            'count': len(alerts)
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Alerts Query Error',
            'message': str(e)
        }), 500


@dashboard_bp.route('/alerts/<int:alert_id>/resolve', methods=['PUT'])
def resolve_dashboard_alert(alert_id):
    """
    PUT /api/dashboard/alerts/<id>/resolve
    Marks a maintenance alert as acknowledged / resolved.
    """
    try:
        result = resolve_alert(alert_id)
        if not result.get('success'):
            return jsonify({
                'success': False,
                'error': 'Alert Resolution Failed',
                'message': result.get('message', 'Unable to resolve alert.')
            }), 404

        return jsonify({
            'success': True,
            'message': f'Alert #{alert_id} marked as resolved.',
            'data': result
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Alert Resolution Error',
            'message': str(e)
        }), 500


@dashboard_bp.route('/fleet', methods=['GET'])
def get_dashboard_fleet():
    """
    GET /api/dashboard/fleet
    Returns all aircraft with calculated health scores and operational states.
    """
    try:
        fleet = get_fleet_summary()
        return jsonify({
            'success': True,
            'data': fleet,
            'count': len(fleet)
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Fleet Summary Error',
            'message': str(e)
        }), 500


@dashboard_bp.route('/maintenance-distribution', methods=['GET'])
def get_dashboard_maintenance_dist():
    """
    GET /api/dashboard/maintenance-distribution
    Returns maintenance distribution by priority and status.
    """
    try:
        dist = get_maintenance_distribution()
        return jsonify({
            'success': True,
            'data': dist
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Maintenance Distribution Error',
            'message': str(e)
        }), 500


@dashboard_bp.route('/activity', methods=['GET'])
def get_dashboard_activity():
    """
    GET /api/dashboard/activity
    Returns latest fleet operational activity events.
    """
    try:
        limit = request.args.get('limit', default=8, type=int)
        activity = get_recent_activity(limit=limit)
        return jsonify({
            'success': True,
            'data': activity,
            'count': len(activity)
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Activity Query Error',
            'message': str(e)
        }), 500
