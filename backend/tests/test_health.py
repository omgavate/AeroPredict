"""
Automated Integration Tests for AeroPredict Backend Health & DB Connectivity.
"""

import sys
from pathlib import Path
import unittest
import json

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app import create_app
from config.database import check_db_connection, get_db_connection


class HealthAndDatabaseTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app({'TESTING': True})
        self.client = self.app.test_client()

    def test_root_endpoint(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'online')
        self.assertIn('AeroPredict', data['service'])

    def test_health_endpoint(self):
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['status'], 'healthy')
        self.assertTrue(data['database']['connected'])
        self.assertEqual(data['database']['database'], 'aeropredict_db')

    def test_database_direct_query(self):
        with get_db_connection() as conn:
            self.assertTrue(conn.is_connected())
            cursor = conn.cursor()
            cursor.execute("SELECT 1 + 1 AS result;")
            row = cursor.fetchone()
            self.assertEqual(row[0], 2)
            cursor.close()

    def test_tables_exist(self):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SHOW TABLES;")
            tables = [t[0] for t in cursor.fetchall()]
            required_tables = ['aircraft', 'sensor_readings', 'maintenance_alerts', 'maintenance_records']
            for table in required_tables:
                self.assertIn(table, tables, f"Expected table '{table}' in aeropredict_db")
            cursor.close()

    def test_404_error_handler(self):
        response = self.client.get('/api/invalid_route_xyz')
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'Not Found')


if __name__ == '__main__':
    unittest.main()
