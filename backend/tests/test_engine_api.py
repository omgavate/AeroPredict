"""
Automated Unit and Integration Tests for Engine Health Monitoring REST API (Phase 8).
Validates latest readings, cycle progression, sensor history, subsystem diagnostics,
input validations, error handling, and C-MAPSS dataset mapping notices.
"""

import sys
from pathlib import Path
import unittest
import json

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app import create_app
from config.database import get_db_connection


class EngineHealthMonitoringTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app({'TESTING': True})
        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls):
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM sensor_readings WHERE cycle >= 500")
            cur.execute("UPDATE aircraft SET current_cycles = 192 WHERE id = 1")
            conn.commit()
            cur.close()

    def test_01_get_latest_sensors_success(self):
        """Verify GET /api/aircraft/1/sensors/latest returns 200 and structured 21-sensor payload."""
        response = self.client.get('/api/aircraft/1/sensors/latest')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        res = data['data']
        self.assertEqual(res['aircraft_id'], 1)
        self.assertEqual(res['tail_number'], 'N101AP')
        self.assertIn('sensors', res)
        self.assertEqual(len(res['sensors']), 21)
        self.assertIn('sensor_3', res['sensors'])
        self.assertIn('primary_metrics', res)
        self.assertIn('t30_hpc_temp', res['primary_metrics'])
        self.assertIn('mapping_notice', res)
        self.assertIn('Demonstration mapping', res['mapping_notice'])

    def test_02_get_sensor_history_success(self):
        """Verify GET /api/aircraft/1/sensors/history returns chronological series."""
        response = self.client.get('/api/aircraft/1/sensors/history?limit=25')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        history = data['data']['history']
        self.assertTrue(len(history) > 0)
        self.assertLessEqual(len(history), 25)
        # Check chronological ordering
        cycles = [entry['cycle'] for entry in history]
        self.assertEqual(cycles, sorted(cycles))
        # Check direct charting keys
        first = history[0]
        self.assertIn('t30', first)
        self.assertIn('p30', first)
        self.assertIn('nc', first)
        self.assertIn('bpr', first)

    def test_03_advance_cycle_success(self):
        """Verify POST /api/aircraft/1/sensors/advance-cycle increments cycle correctly."""
        # Get current cycle
        res1 = self.client.get('/api/aircraft/1/sensors/latest')
        initial_cycle = json.loads(res1.data)['data']['cycle']

        # Advance cycle
        response = self.client.post('/api/aircraft/1/sensors/advance-cycle')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        new_cycle = data['data']['cycle']
        self.assertEqual(new_cycle, initial_cycle + 1)

    def test_04_get_engine_overview_subsystems(self):
        """Verify GET /api/aircraft/1/engine returns complete subsystem health diagnostics."""
        response = self.client.get('/api/aircraft/1/engine')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        res = data['data']
        self.assertIn('subsystems', res)
        self.assertIn('HPC', res['subsystems'])
        self.assertIn('LPT', res['subsystems'])
        self.assertIn('Fan', res['subsystems'])
        self.assertIn('mapping_notice', res)
        self.assertIn('NASA C-MAPSS', res['dataset_source'])

    def test_05_alias_routes(self):
        """Verify /api/engine/<id>/readings and /api/engine/<id>/history work identically."""
        res_readings = self.client.get('/api/engine/1/readings')
        self.assertEqual(res_readings.status_code, 200)
        data_readings = json.loads(res_readings.data)
        self.assertTrue(data_readings['success'])

        res_hist = self.client.get('/api/engine/1/history?limit=10')
        self.assertEqual(res_hist.status_code, 200)
        data_hist = json.loads(res_hist.data)
        self.assertTrue(data_hist['success'])

    def test_06_non_existent_aircraft_404(self):
        """Verify 404 response for non-existent aircraft ID."""
        response = self.client.get('/api/aircraft/999999/sensors/latest')
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'Not Found')

    def test_07_custom_sensor_ingestion_validation(self):
        """Verify POST /api/aircraft/1/sensors validates required fields."""
        # Missing cycle
        resp_bad = self.client.post('/api/aircraft/1/sensors', json={'setting_1': 0.0})
        self.assertEqual(resp_bad.status_code, 400)

        # Non-numeric sensor
        resp_bad2 = self.client.post('/api/aircraft/1/sensors', json={'cycle': 999, 'sensor_3': 'invalid'})
        self.assertEqual(resp_bad2.status_code, 400)

    def test_08_sensor_history_filtering(self):
        """Verify cycle_start and cycle_end query parameters filter history properly."""
        response = self.client.get('/api/aircraft/1/sensors/history?cycle_start=150&cycle_end=160')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        history = data['data']['history']
        for item in history:
            self.assertGreaterEqual(item['cycle'], 150)
            self.assertLessEqual(item['cycle'], 160)

    def test_09_custom_sensor_ingestion_success(self):
        """Verify valid custom sensor ingestion returns 201 and stores data."""
        custom_payload = {
            'cycle': 500,
            'setting_1': 0.001,
            'setting_2': 0.0,
            'setting_3': 100.0,
            'sensor_3': 1612.5,
            'sensor_4': 1440.2,
            'sensor_7': 550.1
        }
        resp = self.client.post('/api/aircraft/1/sensors', json=custom_payload)
        self.assertEqual(resp.status_code, 201)
        data = json.loads(resp.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['cycle'], 500)
        self.assertEqual(data['data']['sensors']['sensor_3'], 1612.5)

        # Clean up custom test record
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM sensor_readings WHERE cycle = 500 AND aircraft_id = 1")
            cur.execute("UPDATE aircraft SET current_cycles = 192 WHERE id = 1")
            conn.commit()
            cur.close()


if __name__ == '__main__':
    unittest.main()
