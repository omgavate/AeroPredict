"""
AeroPredict Dashboard Service
Aggregates executive fleet metrics, engine health diagnostics, maintenance backlog,
telemetry quick-scans, and active alert feeds for Module 1 (Executive Dashboard).
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal
from config.database import get_db_connection
from services.maintenance_service import ensure_maintenance_seeded

logger = logging.getLogger(__name__)

INITIAL_SEEDED_ALERTS = [
    {
        'aircraft_id': 1,
        'alert_type': 'RUL_CRITICAL',
        'severity': 'CRITICAL',
        'message': 'Predicted RUL ≤ 10 flight cycles (Current estimated: 6.2 cycles). Immediate borescope inspection required.',
        'cycle': 192,
        'predicted_rul': 6.20
    },
    {
        'aircraft_id': 5,
        'alert_type': 'RUL_WARNING',
        'severity': 'HIGH',
        'message': 'HPC pressure drop indicates accelerating blade tip wear (Predicted RUL: 22.4 cycles).',
        'cycle': 210,
        'predicted_rul': 22.40
    },
    {
        'aircraft_id': 3,
        'alert_type': 'MAINTENANCE_DUE',
        'severity': 'HIGH',
        'message': 'Scheduled C-Check turbofan overhaul in progress; clearance checks pending LPT seal renewal.',
        'cycle': 245,
        'predicted_rul': 18.50
    },
    {
        'aircraft_id': 2,
        'alert_type': 'SENSOR_ANOMALY',
        'severity': 'MEDIUM',
        'message': 'EGT margin drift detected on Core Sensor 4 (T50) during high altitude climb.',
        'cycle': 125,
        'predicted_rul': 78.50
    }
]


def ensure_alerts_seeded():
    """
    Seeds initial realistic alerts if maintenance_alerts table is empty.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT COUNT(*) as cnt FROM maintenance_alerts")
            row = cursor.fetchone()
            if row and row['cnt'] == 0:
                insert_sql = """
                    INSERT INTO maintenance_alerts 
                    (aircraft_id, alert_type, severity, message, cycle, predicted_rul, is_resolved, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, FALSE, NOW())
                """
                for item in INITIAL_SEEDED_ALERTS:
                    cursor.execute(insert_sql, (
                        item['aircraft_id'],
                        item['alert_type'],
                        item['severity'],
                        item['message'],
                        item['cycle'],
                        item['predicted_rul']
                    ))
                conn.commit()
                logger.info("Initial maintenance alerts seeded into MySQL.")
            cursor.close()
    except Exception as e:
        logger.warning(f"Error checking/seeding maintenance alerts: {e}")


def _calculate_health_score(predicted_rul, current_cycles, status):
    """
    Computes a realistic 0-100% engine health score based on predicted RUL
    and engine flight cycles.
    """
    if predicted_rul is not None:
        rul_val = float(predicted_rul)
        if rul_val <= 0:
            return 15.0
        elif rul_val <= 10:
            return round(18.0 + (rul_val / 10.0) * 22.0, 1)  # 18% - 40%
        elif rul_val <= 30:
            return round(40.0 + ((rul_val - 10.0) / 20.0) * 20.0, 1)  # 40% - 60%
        elif rul_val <= 75:
            return round(60.0 + ((rul_val - 30.0) / 45.0) * 22.0, 1)  # 60% - 82%
        elif rul_val <= 125:
            return round(82.0 + ((rul_val - 75.0) / 50.0) * 15.0, 1)  # 82% - 97%
        else:
            return 98.5

    # Fallback estimation from flight cycles and airframe status
    if status == 'UNDER_MAINTENANCE':
        return 42.0
    if status == 'ATTENTION_REQUIRED':
        return 52.0

    cycles = current_cycles or 0
    if cycles <= 70:
        return round(99.0 - (cycles / 70.0) * 4.0, 1)  # 95% - 99%
    elif cycles <= 140:
        return round(95.0 - ((cycles - 70.0) / 70.0) * 10.0, 1)  # 85% - 95%
    elif cycles <= 200:
        return round(85.0 - ((cycles - 140.0) / 60.0) * 20.0, 1)  # 65% - 85%
    else:
        return max(20.0, round(65.0 - ((cycles - 200.0) / 60.0) * 35.0, 1))


def _classify_risk_from_rul(predicted_rul, health_score):
    """
    Maps RUL or health score to risk tier: CRITICAL, HIGH, MEDIUM, LOW.
    """
    if predicted_rul is not None:
        rul = float(predicted_rul)
        if rul <= 10:
            return 'CRITICAL'
        elif rul <= 30:
            return 'HIGH'
        elif rul <= 75:
            return 'MEDIUM'
        else:
            return 'LOW'

    if health_score <= 45:
        return 'CRITICAL'
    elif health_score <= 65:
        return 'HIGH'
    elif health_score <= 82:
        return 'MEDIUM'
    else:
        return 'LOW'


def _format_relative_time(dt):
    """
    Formats a datetime object to human-readable relative time.
    """
    if not dt:
        return "Unknown"
    now = datetime.now()
    diff = now - dt
    total_seconds = int(diff.total_seconds())

    if total_seconds < 60:
        return "Just now"
    elif total_seconds < 3600:
        mins = total_seconds // 60
        return f"{mins}m ago"
    elif total_seconds < 86400:
        hrs = total_seconds // 3600
        return f"{hrs}h ago"
    else:
        days = total_seconds // 86400
        return f"{days}d ago"


def get_kpi_stats():
    """
    Returns executive fleet KPI counts.
    """
    ensure_maintenance_seeded()
    ensure_alerts_seeded()

    stats = {
        'total_aircraft': 0,
        'operational': 0,
        'under_maintenance': 0,
        'attention_required': 0,
        'retired': 0,
        'pending_maintenance': 0,
        'in_progress_maintenance': 0,
        'total_maintenance_records': 0,
        'active_alerts_count': 0,
        'critical_alerts_count': 0,
        'airworthy_rate': 0.0
    }

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            # Aircraft counts
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'OPERATIONAL' THEN 1 ELSE 0 END) as operational,
                    SUM(CASE WHEN status = 'UNDER_MAINTENANCE' THEN 1 ELSE 0 END) as under_maint,
                    SUM(CASE WHEN status = 'ATTENTION_REQUIRED' THEN 1 ELSE 0 END) as attention_req,
                    SUM(CASE WHEN status = 'RETIRED' THEN 1 ELSE 0 END) as retired
                FROM aircraft
            """)
            ac_row = cursor.fetchone()
            if ac_row and ac_row['total'] is not None:
                stats['total_aircraft'] = int(ac_row['total'])
                stats['operational'] = int(ac_row['operational'] or 0)
                stats['under_maintenance'] = int(ac_row['under_maint'] or 0)
                stats['attention_required'] = int(ac_row['attention_req'] or 0)
                stats['retired'] = int(ac_row['retired'] or 0)
                if stats['total_aircraft'] > 0:
                    stats['airworthy_rate'] = round((stats['operational'] / stats['total_aircraft']) * 100.0, 1)

            # Maintenance records counts
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'PENDING' THEN 1 ELSE 0 END) as pending_cnt,
                    SUM(CASE WHEN status = 'IN_PROGRESS' THEN 1 ELSE 0 END) as in_prog_cnt
                FROM maintenance_records
            """)
            maint_row = cursor.fetchone()
            if maint_row and maint_row['total'] is not None:
                stats['total_maintenance_records'] = int(maint_row['total'])
                stats['pending_maintenance'] = int(maint_row['pending_cnt'] or 0)
                stats['in_progress_maintenance'] = int(maint_row['in_prog_cnt'] or 0)

            # Maintenance alerts counts
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN is_resolved = 0 THEN 1 ELSE 0 END) as active_cnt,
                    SUM(CASE WHEN is_resolved = 0 AND severity = 'CRITICAL' THEN 1 ELSE 0 END) as crit_cnt
                FROM maintenance_alerts
            """)
            alert_row = cursor.fetchone()
            if alert_row and alert_row['total'] is not None:
                stats['active_alerts_count'] = int(alert_row['active_cnt'] or 0)
                stats['critical_alerts_count'] = int(alert_row['crit_cnt'] or 0)

            cursor.close()
    except Exception as e:
        logger.error(f"Error querying dashboard KPI stats: {e}")

    return stats


def get_health_overview():
    """
    Returns fleet engine health summary, risk distribution, and average RUL.
    """
    ensure_maintenance_seeded()
    ensure_alerts_seeded()

    summary = {
        'average_health_score': 0.0,
        'average_rul': 0.0,
        'monitored_engines': 0,
        'risk_breakdown': {
            'CRITICAL': 0,
            'HIGH': 0,
            'MEDIUM': 0,
            'LOW': 0
        },
        'status_breakdown': {
            'OPERATIONAL': 0,
            'UNDER_MAINTENANCE': 0,
            'ATTENTION_REQUIRED': 0,
            'RETIRED': 0
        },
        'distribution_chart': [
            {'category': 'Nominal (>75)', 'key': 'LOW', 'count': 0, 'fill': '#10B981'},
            {'category': 'Moderate (31-75)', 'key': 'MEDIUM', 'count': 0, 'fill': '#3B82F6'},
            {'category': 'Watchlist (11-30)', 'key': 'HIGH', 'count': 0, 'fill': '#F59E0B'},
            {'category': 'Critical (≤10)', 'key': 'CRITICAL', 'count': 0, 'fill': '#EF4444'}
        ]
    }

    try:
        fleet_items = get_fleet_summary()
        summary['monitored_engines'] = len(fleet_items)

        if not fleet_items:
            return summary

        total_health = 0.0
        total_rul = 0.0
        rul_count = 0

        for ac in fleet_items:
            health = ac['health_score']
            total_health += health

            if ac['latest_predicted_rul'] is not None:
                total_rul += float(ac['latest_predicted_rul'])
                rul_count += 1

            risk = ac['latest_risk_level']
            if risk in summary['risk_breakdown']:
                summary['risk_breakdown'][risk] += 1

            status = ac['status']
            if status in summary['status_breakdown']:
                summary['status_breakdown'][status] += 1

        summary['average_health_score'] = round(total_health / len(fleet_items), 1)
        if rul_count > 0:
            summary['average_rul'] = round(total_rul / rul_count, 1)
        else:
            summary['average_rul'] = 65.0

        # Update distribution chart counts
        for slice_item in summary['distribution_chart']:
            key = slice_item['key']
            slice_item['count'] = summary['risk_breakdown'].get(key, 0)

    except Exception as e:
        logger.error(f"Error calculating health overview: {e}")

    return summary


def get_maintenance_distribution():
    """
    Returns maintenance distribution by status and priority.
    """
    ensure_maintenance_seeded()

    distribution = {
        'by_status': {
            'PENDING': 0,
            'SCHEDULED': 0,
            'IN_PROGRESS': 0,
            'COMPLETED': 0,
            'CANCELLED': 0
        },
        'by_priority': {
            'CRITICAL': 0,
            'HIGH': 0,
            'MEDIUM': 0,
            'LOW': 0
        },
        'status_chart': [],
        'priority_chart': []
    }

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            # Query by status
            cursor.execute("""
                SELECT status, COUNT(*) as cnt 
                FROM maintenance_records 
                GROUP BY status
            """)
            for row in cursor.fetchall():
                st = row['status']
                if st in distribution['by_status']:
                    distribution['by_status'][st] = int(row['cnt'])

            # Query by priority
            cursor.execute("""
                SELECT priority, COUNT(*) as cnt 
                FROM maintenance_records 
                GROUP BY priority
            """)
            for row in cursor.fetchall():
                pr = row['priority']
                if pr in distribution['by_priority']:
                    distribution['by_priority'][pr] = int(row['cnt'])

            cursor.close()

        # Build chart friendly arrays
        distribution['status_chart'] = [
            {'name': 'Pending', 'value': distribution['by_status']['PENDING'], 'fill': '#F59E0B'},
            {'name': 'Scheduled', 'value': distribution['by_status']['SCHEDULED'], 'fill': '#3B82F6'},
            {'name': 'In Progress', 'value': distribution['by_status']['IN_PROGRESS'], 'fill': '#8B5CF6'},
            {'name': 'Completed', 'value': distribution['by_status']['COMPLETED'], 'fill': '#10B981'}
        ]

        distribution['priority_chart'] = [
            {'priority': 'Critical', 'count': distribution['by_priority']['CRITICAL'], 'fill': '#EF4444'},
            {'priority': 'High', 'count': distribution['by_priority']['HIGH'], 'fill': '#F97316'},
            {'priority': 'Medium', 'count': distribution['by_priority']['MEDIUM'], 'fill': '#FBBF24'},
            {'priority': 'Low', 'count': distribution['by_priority']['LOW'], 'fill': '#10B981'}
        ]

    except Exception as e:
        logger.error(f"Error querying maintenance distribution: {e}")

    return distribution


def get_recent_alerts(limit=10, unresolved_only=False):
    """
    Returns recent maintenance alerts joined with aircraft details.
    """
    ensure_alerts_seeded()
    alerts = []

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            where_clause = "WHERE al.is_resolved = FALSE" if unresolved_only else ""
            query = f"""
                SELECT 
                    al.id,
                    al.aircraft_id,
                    ac.tail_number,
                    ac.model,
                    al.alert_type,
                    al.severity,
                    al.message,
                    al.cycle,
                    al.predicted_rul,
                    al.is_resolved,
                    al.resolved_at,
                    al.created_at
                FROM maintenance_alerts al
                LEFT JOIN aircraft ac ON al.aircraft_id = ac.id
                {where_clause}
                ORDER BY al.is_resolved ASC, al.created_at DESC
                LIMIT %s
            """
            cursor.execute(query, (limit,))
            rows = cursor.fetchall()
            cursor.close()

            for row in rows:
                rul_val = float(row['predicted_rul']) if row.get('predicted_rul') is not None else None
                created_dt = row.get('created_at')
                alerts.append({
                    'id': row['id'],
                    'aircraft_id': row['aircraft_id'],
                    'tail_number': row['tail_number'] or f"AC-{row['aircraft_id']}",
                    'model': row['model'] or "Turbofan Airframe",
                    'alert_type': row['alert_type'],
                    'severity': row['severity'],
                    'message': row['message'],
                    'cycle': row['cycle'],
                    'predicted_rul': rul_val,
                    'is_resolved': bool(row['is_resolved']),
                    'resolved_at': row['resolved_at'].isoformat() if row.get('resolved_at') else None,
                    'created_at': created_dt.isoformat() if created_dt else None,
                    'timestamp': _format_relative_time(created_dt)
                })

    except Exception as e:
        logger.error(f"Error querying recent alerts: {e}")

    return alerts


def resolve_alert(alert_id):
    """
    Marks a maintenance alert as resolved.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, is_resolved FROM maintenance_alerts WHERE id = %s",
                (alert_id,)
            )
            existing = cursor.fetchone()
            if not existing:
                cursor.close()
                return {'success': False, 'message': f'Alert #{alert_id} not found.'}

            cursor.execute("""
                UPDATE maintenance_alerts 
                SET is_resolved = TRUE, resolved_at = NOW() 
                WHERE id = %s
            """, (alert_id,))
            conn.commit()
            cursor.close()
            return {'success': True, 'alert_id': alert_id, 'is_resolved': True}
    except Exception as e:
        logger.error(f"Error resolving alert #{alert_id}: {e}")
        return {'success': False, 'message': str(e)}


def get_fleet_summary():
    """
    Returns an aggregated list of aircraft with real-time calculated health score,
    latest RUL prediction, and operational status.
    """
    fleet = []

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            # Query all aircraft with their most recent prediction
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
                    p.predicted_rul,
                    p.risk_level,
                    p.predicted_at,
                    (SELECT COUNT(*) FROM maintenance_records m WHERE m.aircraft_id = a.id AND m.status != 'COMPLETED') AS pending_maintenance_count,
                    (SELECT COUNT(*) FROM maintenance_alerts al WHERE al.aircraft_id = a.id AND al.is_resolved = FALSE) AS active_alerts_count
                FROM aircraft a
                LEFT JOIN (
                    SELECT p1.aircraft_id, p1.predicted_rul, p1.risk_level, p1.predicted_at
                    FROM rul_predictions p1
                    INNER JOIN (
                        SELECT aircraft_id, MAX(id) as max_id
                        FROM rul_predictions
                        GROUP BY aircraft_id
                    ) p2 ON p1.id = p2.max_id
                ) p ON a.id = p.aircraft_id
                ORDER BY a.tail_number ASC
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()

            for row in rows:
                predicted_rul = float(row['predicted_rul']) if row.get('predicted_rul') is not None else None
                health_score = _calculate_health_score(predicted_rul, row.get('current_cycles'), row.get('status'))
                risk_level = row.get('risk_level') or _classify_risk_from_rul(predicted_rul, health_score)

                fleet.append({
                    'id': row['id'],
                    'tail_number': row['tail_number'],
                    'model': row['model'],
                    'manufacturer': row['manufacturer'],
                    'manufacturing_year': row.get('manufacturing_year'),
                    'engine_type': row['engine_type'],
                    'cmapss_unit_id': row['cmapss_unit_id'],
                    'current_cycles': row['current_cycles'],
                    'flight_hours': row['flight_hours'],
                    'status': row['status'],
                    'health_score': health_score,
                    'latest_predicted_rul': predicted_rul,
                    'latest_risk_level': risk_level,
                    'pending_maintenance_count': int(row.get('pending_maintenance_count') or 0),
                    'active_alerts_count': int(row.get('active_alerts_count') or 0),
                    'created_at': row['created_at'].isoformat() if row.get('created_at') else None,
                    'updated_at': row['updated_at'].isoformat() if row.get('updated_at') else None,
                })

    except Exception as e:
        logger.error(f"Error querying fleet summary: {e}")

    return fleet


def get_recent_activity(limit=8):
    """
    Returns a unified chronological activity stream of work orders, alerts, and predictions.
    """
    activities = []

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            # 1. Maintenance work orders
            cursor.execute("""
                SELECT m.id, m.aircraft_id, a.tail_number, m.title, m.status, m.priority, m.updated_at
                FROM maintenance_records m
                LEFT JOIN aircraft a ON m.aircraft_id = a.id
                ORDER BY m.updated_at DESC
                LIMIT 5
            """)
            for row in cursor.fetchall():
                dt = row.get('updated_at') or datetime.now()
                activities.append({
                    'id': f"maint-{row['id']}",
                    'type': 'MAINTENANCE',
                    'title': f"Work Order: {row['title']}",
                    'tail_number': row['tail_number'] or f"AC-{row['aircraft_id']}",
                    'description': f"Status: {row['status'].replace('_', ' ').title()} • Priority: {row['priority']}",
                    'severity': row['priority'],
                    'raw_date': dt,
                    'timestamp': _format_relative_time(dt)
                })

            # 2. Critical/High alerts
            cursor.execute("""
                SELECT al.id, al.aircraft_id, a.tail_number, al.alert_type, al.severity, al.message, al.created_at
                FROM maintenance_alerts al
                LEFT JOIN aircraft a ON al.aircraft_id = a.id
                ORDER BY al.created_at DESC
                LIMIT 5
            """)
            for row in cursor.fetchall():
                dt = row.get('created_at') or datetime.now()
                activities.append({
                    'id': f"alert-{row['id']}",
                    'type': 'ALERT',
                    'title': f"Alert: {row['alert_type'].replace('_', ' ')}",
                    'tail_number': row['tail_number'] or f"AC-{row['aircraft_id']}",
                    'description': row['message'],
                    'severity': row['severity'],
                    'raw_date': dt,
                    'timestamp': _format_relative_time(dt)
                })

            # 3. RUL predictions
            cursor.execute("""
                SELECT p.id, p.aircraft_id, a.tail_number, p.predicted_rul, p.risk_level, p.cycle, p.predicted_at
                FROM rul_predictions p
                LEFT JOIN aircraft a ON p.aircraft_id = a.id
                ORDER BY p.predicted_at DESC
                LIMIT 4
            """)
            for row in cursor.fetchall():
                dt = row.get('predicted_at') or datetime.now()
                rul_num = float(row['predicted_rul'])
                activities.append({
                    'id': f"pred-{row['id']}",
                    'type': 'PREDICTION',
                    'title': f"Inference: Cycle {row['cycle']}",
                    'tail_number': row['tail_number'] or f"AC-{row['aircraft_id']}",
                    'description': f"Predicted RUL: {rul_num:.1f} cycles ({row['risk_level']} Risk)",
                    'severity': row['risk_level'],
                    'raw_date': dt,
                    'timestamp': _format_relative_time(dt)
                })

            cursor.close()

        # Sort all activities descending by datetime
        activities.sort(key=lambda x: x['raw_date'], reverse=True)
        # Drop raw_date before returning
        for item in activities:
            del item['raw_date']

    except Exception as e:
        logger.error(f"Error querying recent activity: {e}")

    return activities[:limit]


def get_complete_dashboard():
    """
    Returns full unified dashboard payload in a single, fast invocation.
    Follows approved architecture for Module 1.
    """
    return {
        'stats': get_kpi_stats(),
        'health_overview': get_health_overview(),
        'maintenance_distribution': get_maintenance_distribution(),
        'recent_alerts': get_recent_alerts(limit=8),
        'fleet_summary': get_fleet_summary(),
        'recent_activity': get_recent_activity(limit=6)
    }
