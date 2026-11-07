"""
Automated Unit and Integration Test Suite for AeroPredict Prediction REST API.
Tests model metadata endpoint, RUL inference, risk categorization,
database persistence in rul_predictions and maintenance_alerts, and error handling.
"""

import os
import sys
import unittest
import json
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app import create_app
from config.database import get_db_connection

# Sample telemetry for near-failure engine (Cycle 192 of Engine 1 in C-MAPSS)
SAMPLE_NEAR_FAILURE_TELEMETRY = {
    'setting_1': -0.0012,
    'setting_2': 0.0004,
    'setting_3': 100.0,
    'sensor_1': 518.67,
    'sensor_2': 643.12,
    'sensor_3': 1610.10,
    'sensor_4': 1435.60,
    'sensor_5': 14.62,
    'sensor_6': 21.61,
    'sensor_7': 548.30,
    'sensor_8': 2388.16,
    'sensor_9': 9081.20,
    'sensor_10': 1.30,
    'sensor_11': 47.92,
    'sensor_12': 520.14,
    'sensor_13': 2388.18,
    'sensor_14': 8144.90,
    'sensor_15': 8.602,
    'sensor_16': 0.03,
    'sensor_17': 398.0,
    'sensor_18': 2388.0,
    'sensor_19': 100.0,
    'sensor_20': 38.45,
    'sensor_21': 23.018
}

# Sample telemetry for brand-new healthy engine (Cycle 5 of Engine 1 in C-MAPSS)
SAMPLE_HEALTHY_TELEMETRY = {
    'setting_1': 0.0019,
    'setting_2': -0.0002,
    'setting_3': 100.0,
    'sensor_1': 518.67,
    'sensor_2': 642.35,
    'sensor_3': 1587.99,
    'sensor_4': 1404.20,
    'sensor_5': 14.62,
    'sensor_6': 21.61,
    'sensor_7': 554.26,
    'sensor_8': 2388.08,
    'sensor_9': 9046.85,
    'sensor_10': 1.30,
    'sensor_11': 47.15,
    'sensor_12': 522.28,
    'sensor_13': 2388.04,
    'sensor_14': 8133.80,
    'sensor_15': 8.4294,
    'sensor_16': 0.03,
    'sensor_17': 393.0,
    'sensor_18': 2388.0,
    'sensor_19': 100.0,
    'sensor_20': 38.88,
    'sensor_21': 23.38
}


class PredictionApiTestCase(unittest.TestCase):
    """Test cases for /api/predict routes."""

    @classmethod
    def setUpClass(cls):
        cls.app = create_app({'TESTING': True})
        cls.client = cls.app.test_client()
        # Clean up any lingering test prediction or alert records
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM maintenance_alerts WHERE aircraft_id IN (1, 2)")
            cursor.execute("DELETE FROM rul_predictions WHERE aircraft_id IN (1, 2)")
            conn.commit()
            cursor.close()

    @classmethod
    def tearDownClass(cls):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM maintenance_alerts WHERE aircraft_id IN (1, 2)")
            cursor.execute("DELETE FROM rul_predictions WHERE aircraft_id IN (1, 2)")
            conn.commit()
            cursor.close()

    def test_01_get_model_info(self):
        """Test GET /api/predict/model-info returns 200 with model metrics."""
        response = self.client.get('/api/predict/model-info')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        meta = data['data']
        self.assertEqual(meta['status'], 'loaded')
        self.assertEqual(meta['model_type'], 'RandomForestRegressor')
        self.assertEqual(meta['feature_count'], 45)
        self.assertIn('mae', meta['test_metrics_capped'])
        self.assertIn('rmse', meta['test_metrics_capped'])
        self.assertIn('CRITICAL', meta['risk_thresholds'])
        self.assertIn('EDUCATIONAL NOTICE', meta['disclaimer'])

    def test_02_predict_near_failure_creates_prediction_and_alert(self):
        """Test POST /api/predict with near-failure telemetry produces low RUL, CRITICAL risk and alert."""
        payload = {
            'aircraft_id': 1,
            'cycle': 192,
            'telemetry': SAMPLE_NEAR_FAILURE_TELEMETRY,
            'save_to_db': True
        }
        response = self.client.post(
            '/api/predict',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        res = data['data']

        # Assert prediction properties
        self.assertEqual(res['aircraft_id'], 1)
        self.assertEqual(res['cycle'], 192)
        self.assertLess(res['predicted_rul'], 25.0)  # Near failure
        self.assertEqual(res['risk_level'], 'CRITICAL')
        self.assertGreaterEqual(res['risk_score'], 80.0)
        self.assertTrue(res['alert_created'])
        self.assertIsNotNone(res['alert_id'])
        self.assertTrue(res['db_saved'])
        self.assertIn('Ground Aircraft', res['action_required'])
        self.assertIn('EDUCATIONAL NOTICE', res['disclaimer'])

        # Verify record in database
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM rul_predictions WHERE id = %s", (res['prediction_id'],))
            pred_row = cursor.fetchone()
            self.assertIsNotNone(pred_row)
            self.assertEqual(pred_row['risk_level'], 'CRITICAL')

            cursor.execute("SELECT * FROM maintenance_alerts WHERE id = %s", (res['alert_id'],))
            alert_row = cursor.fetchone()
            self.assertIsNotNone(alert_row)
            self.assertEqual(alert_row['severity'], 'CRITICAL')
            cursor.close()

    def test_03_predict_healthy_engine(self):
        """Test POST /api/predict with brand-new healthy telemetry produces high RUL and LOW risk."""
        payload = {
            'aircraft_id': 2,
            'cycle': 5,
            'telemetry': SAMPLE_HEALTHY_TELEMETRY,
            'save_to_db': True
        }
        response = self.client.post(
            '/api/predict',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        res = data['data']

        self.assertGreater(res['predicted_rul'], 75.0)
        self.assertEqual(res['risk_level'], 'LOW')
        self.assertLess(res['risk_score'], 45.0)
        self.assertFalse(res['alert_created'])  # No alert for LOW risk

    def test_04_predict_aircraft_not_found(self):
        """Test POST /api/predict with non-existent aircraft ID returns 404."""
        payload = {
            'aircraft_id': 99999,
            'cycle': 50,
            'telemetry': SAMPLE_HEALTHY_TELEMETRY
        }
        response = self.client.post(
            '/api/predict',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'Not Found')

    def test_05_predict_negative_cycle(self):
        """Test POST /api/predict with negative cycle returns 400."""
        payload = {
            'aircraft_id': 1,
            'cycle': -10,
            'telemetry': SAMPLE_HEALTHY_TELEMETRY
        }
        response = self.client.post(
            '/api/predict',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn("'cycle' must be a positive integer", data['message'])

    def test_06_predict_missing_telemetry(self):
        """Test POST /api/predict without telemetry dictionary returns 400."""
        payload = {
            'aircraft_id': 1,
            'cycle': 50
        }
        response = self.client.post(
            '/api/predict',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_07_predict_missing_required_sensor(self):
        """Test POST /api/predict with incomplete sensor readings returns 400."""
        incomplete_telemetry = SAMPLE_HEALTHY_TELEMETRY.copy()
        del incomplete_telemetry['sensor_4']  # Delete critical sensor

        payload = {
            'aircraft_id': 1,
            'cycle': 50,
            'telemetry': incomplete_telemetry
        }
        response = self.client.post(
            '/api/predict',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn("sensor_4", data['message'])

    def test_08_predict_physically_implausible_sensor(self):
        """Test POST /api/predict with out-of-bounds sensor reading returns 400."""
        implausible_telemetry = SAMPLE_HEALTHY_TELEMETRY.copy()
        implausible_telemetry['sensor_3'] = 99999.0  # Impossible HPC temp

        payload = {
            'aircraft_id': 1,
            'cycle': 50,
            'telemetry': implausible_telemetry
        }
        response = self.client.post(
            '/api/predict',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn("physically implausible", data['message'])

    def test_09_get_latest_prediction(self):
        """Test GET /api/predict/latest/<aircraft_id> returns latest saved prediction."""
        response = self.client.get('/api/predict/latest/1')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['aircraft_id'], 1)
        self.assertEqual(data['data']['cycle'], 192)

    def test_10_get_prediction_history(self):
        """Test GET /api/predict/history/<aircraft_id> returns prediction history list."""
        response = self.client.get('/api/predict/history/1?limit=10')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertGreaterEqual(data['count'], 1)
        self.assertIsInstance(data['data'], list)


if __name__ == '__main__':
    unittest.main()
