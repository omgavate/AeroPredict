"""
Automated Integration Tests for Aircraft Fleet Management API.
Tests CRUD, validation, search, filters, error handling, and DB persistence.
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


class AircraftApiTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app({'TESTING': True})
        self.client = self.app.test_client()

    def test_01_list_aircraft(self):
        """Test GET /api/aircraft returns list of fleet assets."""
        res = self.client.get('/api/aircraft')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        self.assertGreaterEqual(data['count'], 6)
        self.assertIsInstance(data['data'], list)

    def test_02_search_aircraft(self):
        """Test search query filtering by tail number and manufacturer."""
        res = self.client.get('/api/aircraft?search=N101AP')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(len(data['data']), 1)
        self.assertEqual(data['data'][0]['tail_number'], 'N101AP')

        # Search by manufacturer
        res_airbus = self.client.get('/api/aircraft?search=Airbus')
        data_airbus = json.loads(res_airbus.data)
        self.assertGreaterEqual(len(data_airbus['data']), 2)

    def test_03_filter_status(self):
        """Test filtering aircraft by status."""
        res = self.client.get('/api/aircraft?status=OPERATIONAL')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        for ac in data['data']:
            self.assertEqual(ac['status'], 'OPERATIONAL')

    def test_04_create_aircraft_success(self):
        """Test POST /api/aircraft creates new record in database."""
        payload = {
            'tail_number': 'TEST-99',
            'model': 'Boeing 737-900ER',
            'manufacturer': 'Boeing',
            'manufacturing_year': 2020,
            'engine_type': 'CFM56-7B27',
            'cmapss_unit_id': 99,
            'current_cycles': 50,
            'flight_hours': 1200,
            'status': 'OPERATIONAL'
        }
        res = self.client.post('/api/aircraft', json=payload)
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['tail_number'], 'TEST-99')
        created_id = data['data']['id']

        # Verify DB persistence via GET /api/aircraft/<id>
        res_get = self.client.get(f'/api/aircraft/{created_id}')
        self.assertEqual(res_get.status_code, 200)
        data_get = json.loads(res_get.data)
        self.assertEqual(data_get['data']['model'], 'Boeing 737-900ER')

    def test_05_create_aircraft_validation_errors(self):
        """Test POST /api/aircraft rejects invalid and duplicate inputs."""
        # 1. Missing tail number
        res = self.client.post('/api/aircraft', json={'model': 'Test Aircraft'})
        self.assertEqual(res.status_code, 400)
        data = json.loads(res.data)
        self.assertIn('tail_number', data['details'])

        # 2. Duplicate tail number
        res_dup = self.client.post('/api/aircraft', json={
            'tail_number': 'N101AP',
            'model': 'Boeing 737',
            'manufacturer': 'Boeing'
        })
        self.assertEqual(res_dup.status_code, 400)
        data_dup = json.loads(res_dup.data)
        self.assertIn('tail_number', data_dup['details'])

        # 3. Invalid manufacturing year
        res_year = self.client.post('/api/aircraft', json={
            'tail_number': 'TEST-INVALID',
            'model': 'Test Aircraft',
            'manufacturer': 'Airbus',
            'manufacturing_year': 1850
        })
        self.assertEqual(res_year.status_code, 400)
        data_year = json.loads(res_year.data)
        self.assertIn('manufacturing_year', data_year['details'])

        # 4. Invalid status
        res_status = self.client.post('/api/aircraft', json={
            'tail_number': 'TEST-INVALID2',
            'model': 'Test Aircraft',
            'manufacturer': 'Airbus',
            'status': 'FLYING_HIGH'
        })
        self.assertEqual(res_status.status_code, 400)
        data_status = json.loads(res_status.data)
        self.assertIn('status', data_status['details'])

    def test_06_update_aircraft(self):
        """Test PUT /api/aircraft/<id> updates existing record."""
        # Get existing test aircraft
        res = self.client.get('/api/aircraft?search=TEST-99')
        data = json.loads(res.data)
        ac_id = data['data'][0]['id']

        update_payload = {
            'status': 'UNDER_MAINTENANCE',
            'current_cycles': 55,
            'flight_hours': 1350
        }
        res_put = self.client.put(f'/api/aircraft/{ac_id}', json=update_payload)
        self.assertEqual(res_put.status_code, 200)
        data_put = json.loads(res_put.data)
        self.assertEqual(data_put['data']['status'], 'UNDER_MAINTENANCE')
        self.assertEqual(data_put['data']['current_cycles'], 55)

    def test_07_delete_aircraft(self):
        """Test DELETE /api/aircraft/<id> removes record."""
        res = self.client.get('/api/aircraft?search=TEST-99')
        data = json.loads(res.data)
        ac_id = data['data'][0]['id']

        res_del = self.client.delete(f'/api/aircraft/{ac_id}')
        self.assertEqual(res_del.status_code, 200)
        data_del = json.loads(res_del.data)
        self.assertTrue(data_del['success'])

        # Confirm 404 on subsequent get
        res_get = self.client.get(f'/api/aircraft/{ac_id}')
        self.assertEqual(res_get.status_code, 404)


if __name__ == '__main__':
    unittest.main()
