"""
Test Suite for Dashboard API Endpoints.
Covers Module 1 (Executive Dashboard) integration:
- Complete aggregated dashboard payload (GET /api/dashboard)
- KPI stats (GET /api/dashboard/stats)
- Engine health overview (GET /api/dashboard/health-overview)
- Maintenance alerts feed and resolution (GET /api/dashboard/alerts, PUT /api/dashboard/alerts/<id>/resolve)
- Fleet summary quick-scan (GET /api/dashboard/fleet)
- Maintenance distribution (GET /api/dashboard/maintenance-distribution)
- Recent activity feed (GET /api/dashboard/activity)
"""

import unittest
import json
import os
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app import create_app
from config.database import get_db_connection


class TestDashboardAPI(unittest.TestCase):
    """Integration tests for Dashboard API endpoints."""

    @classmethod
    def setUpClass(cls):
        """Set up test Flask client."""
        cls.app = create_app({'TESTING': True})
        cls.client = cls.app.test_client()

    def test_01_get_complete_dashboard(self):
        """Verify GET /api/dashboard returns complete aggregated executive metrics."""
        response = self.client.get('/api/dashboard')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertTrue(data['success'])
        payload = data['data']

        # Ensure all required dashboard sections are present
        self.assertIn('stats', payload)
        self.assertIn('health_overview', payload)
        self.assertIn('maintenance_distribution', payload)
        self.assertIn('recent_alerts', payload)
        self.assertIn('fleet_summary', payload)
        self.assertIn('recent_activity', payload)

        # Verify stats contents
        stats = payload['stats']
        self.assertIn('total_aircraft', stats)
        self.assertIn('operational', stats)
        self.assertIn('under_maintenance', stats)
        self.assertIn('attention_required', stats)
        self.assertIn('pending_maintenance', stats)
        self.assertIn('active_alerts_count', stats)
        self.assertGreaterEqual(stats['total_aircraft'], 1)

    def test_02_get_dashboard_stats(self):
        """Verify GET /api/dashboard/stats returns KPI counts correctly."""
        response = self.client.get('/api/dashboard/stats')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertTrue(data['success'])
        stats = data['data']
        self.assertIsInstance(stats['total_aircraft'], int)
        self.assertIsInstance(stats['operational'], int)
        self.assertIsInstance(stats['pending_maintenance'], int)
        self.assertIsInstance(stats['active_alerts_count'], int)

    def test_03_get_health_overview(self):
        """Verify GET /api/dashboard/health-overview returns valid health summaries."""
        response = self.client.get('/api/dashboard/health-overview')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertTrue(data['success'])
        overview = data['data']
        self.assertIn('average_health_score', overview)
        self.assertIn('average_rul', overview)
        self.assertIn('risk_breakdown', overview)
        self.assertIn('distribution_chart', overview)
        self.assertGreaterEqual(overview['monitored_engines'], 1)

    def test_04_get_recent_alerts(self):
        """Verify GET /api/dashboard/alerts returns seeded or generated alerts."""
        response = self.client.get('/api/dashboard/alerts?limit=5')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertTrue(data['success'])
        alerts = data['data']
        self.assertIsInstance(alerts, list)
        self.assertGreaterEqual(len(alerts), 1)

        # Verify alert item structure
        alert = alerts[0]
        self.assertIn('id', alert)
        self.assertIn('tail_number', alert)
        self.assertIn('severity', alert)
        self.assertIn('message', alert)
        self.assertIn('is_resolved', alert)

    def test_05_resolve_alert(self):
        """Verify PUT /api/dashboard/alerts/<id>/resolve marks an alert as resolved."""
        # Ensure at least one test alert exists to resolve
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO maintenance_alerts 
                (aircraft_id, alert_type, severity, message, cycle, predicted_rul, is_resolved, created_at)
                VALUES (1, 'RUL_CRITICAL', 'CRITICAL', 'Test alert for resolution verification', 190, 8.5, FALSE, NOW())
            """)
            conn.commit()
            test_alert_id = cur.lastrowid
            cur.close()

        resolve_res = self.client.put(f'/api/dashboard/alerts/{test_alert_id}/resolve')
        self.assertEqual(resolve_res.status_code, 200)

        res_data = json.loads(resolve_res.data)
        self.assertTrue(res_data['success'])
        self.assertTrue(res_data['data']['is_resolved'])

        # Clean up test alert
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM maintenance_alerts WHERE id = %s", (test_alert_id,))
            conn.commit()
            cur.close()

    def test_06_resolve_nonexistent_alert(self):
        """Verify PUT /api/dashboard/alerts/999999/resolve returns 404."""
        response = self.client.put('/api/dashboard/alerts/999999/resolve')
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertFalse(data['success'])

    def test_07_get_fleet_summary(self):
        """Verify GET /api/dashboard/fleet returns aircraft with health scores."""
        response = self.client.get('/api/dashboard/fleet')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertTrue(data['success'])
        fleet = data['data']
        self.assertIsInstance(fleet, list)
        self.assertGreaterEqual(len(fleet), 1)

        item = fleet[0]
        self.assertIn('tail_number', item)
        self.assertIn('health_score', item)
        self.assertIn('status', item)
        self.assertIn('current_cycles', item)
        self.assertGreaterEqual(item['health_score'], 0)
        self.assertLessEqual(item['health_score'], 100)

    def test_08_get_maintenance_distribution(self):
        """Verify GET /api/dashboard/maintenance-distribution returns status and priority breakdowns."""
        response = self.client.get('/api/dashboard/maintenance-distribution')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertTrue(data['success'])
        dist = data['data']
        self.assertIn('by_status', dist)
        self.assertIn('by_priority', dist)
        self.assertIn('status_chart', dist)
        self.assertIn('priority_chart', dist)

    def test_09_get_recent_activity(self):
        """Verify GET /api/dashboard/activity returns chronological events."""
        response = self.client.get('/api/dashboard/activity?limit=6')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertTrue(data['success'])
        activities = data['data']
        self.assertIsInstance(activities, list)
        if activities:
            first = activities[0]
            self.assertIn('id', first)
            self.assertIn('type', first)
            self.assertIn('title', first)
            self.assertIn('tail_number', first)


if __name__ == '__main__':
    unittest.main()
