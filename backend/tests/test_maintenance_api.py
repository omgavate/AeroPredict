"""
Automated Unit and Integration Tests for Maintenance Management REST API (Phase 10).
Tests create, read, update, delete operations, validation errors, status transitions,
and aircraft history queries.
"""

import sys
from pathlib import Path
import unittest
import json
from datetime import date

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app import create_app
from config.database import get_db_connection


class MaintenanceApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app({'TESTING': True})
        cls.client = cls.app.test_client()

    def test_01_list_maintenance_records(self):
        """Verify GET /api/maintenance returns 200 and list of joined work orders."""
        response = self.client.get('/api/maintenance')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('data', data)
        self.assertTrue(len(data['data']) > 0)
        first = data['data'][0]
        self.assertIn('tail_number', first)
        self.assertIn('title', first)
        self.assertIn('status', first)
        self.assertIn('priority', first)

    def test_02_get_single_maintenance_record(self):
        """Verify GET /api/maintenance/<id> returns 200 and single work order details."""
        list_res = self.client.get('/api/maintenance')
        first_id = json.loads(list_res.data)['data'][0]['id']

        response = self.client.get(f'/api/maintenance/{first_id}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['id'], first_id)

    def test_03_create_maintenance_record_success(self):
        """Verify POST /api/maintenance creates record and returns 201."""
        payload = {
            'aircraft_id': 1,
            'title': 'Test Turbine Blade Replacement',
            'description': 'Automated test work order description.',
            'priority': 'HIGH',
            'status': 'PENDING',
            'scheduled_date': '2026-11-20',
            'technician_notes': 'Allocated to Hangar 3.'
        }
        response = self.client.post('/api/maintenance', json=payload)
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        created = data['data']
        self.assertEqual(created['title'], payload['title'])
        self.assertEqual(created['aircraft_id'], 1)
        self.assertEqual(created['status'], 'PENDING')
        self.assertEqual(created['tail_number'], 'N101AP')

        # Clean up created record
        del_res = self.client.delete(f"/api/maintenance/{created['id']}")
        self.assertEqual(del_res.status_code, 200)

    def test_04_create_record_validation_failures(self):
        """Verify POST /api/maintenance rejects invalid payloads with 400 Bad Request."""
        # Missing title
        resp1 = self.client.post('/api/maintenance', json={
            'aircraft_id': 1,
            'title': '',
            'scheduled_date': '2026-11-20'
        })
        self.assertEqual(resp1.status_code, 400)
        data1 = json.loads(resp1.data)
        self.assertIn('title', data1['details'])

        # Invalid aircraft ID
        resp2 = self.client.post('/api/maintenance', json={
            'aircraft_id': 999999,
            'title': 'Valid Title',
            'scheduled_date': '2026-11-20'
        })
        self.assertEqual(resp2.status_code, 400)
        data2 = json.loads(resp2.data)
        self.assertIn('aircraft_id', data2['details'])

        # Invalid status
        resp3 = self.client.post('/api/maintenance', json={
            'aircraft_id': 1,
            'title': 'Valid Title',
            'status': 'UNKNOWN_STATUS',
            'scheduled_date': '2026-11-20'
        })
        self.assertEqual(resp3.status_code, 400)
        data3 = json.loads(resp3.data)
        self.assertIn('status', data3['details'])

        # Invalid date format
        resp4 = self.client.post('/api/maintenance', json={
            'aircraft_id': 1,
            'title': 'Valid Title',
            'scheduled_date': 'not-a-date'
        })
        self.assertEqual(resp4.status_code, 400)
        data4 = json.loads(resp4.data)
        self.assertIn('scheduled_date', data4['details'])

    def test_05_update_maintenance_record(self):
        """Verify PUT /api/maintenance/<id> updates status and technician notes."""
        # Create temp record
        create_res = self.client.post('/api/maintenance', json={
            'aircraft_id': 2,
            'title': 'Update Test Record',
            'scheduled_date': '2026-11-15',
            'priority': 'MEDIUM',
            'status': 'PENDING'
        })
        rec_id = json.loads(create_res.data)['data']['id']

        # Update to IN_PROGRESS
        update_res = self.client.put(f'/api/maintenance/{rec_id}', json={
            'status': 'IN_PROGRESS',
            'technician_notes': 'Work begun on stand.'
        })
        self.assertEqual(update_res.status_code, 200)
        updated = json.loads(update_res.data)['data']
        self.assertEqual(updated['status'], 'IN_PROGRESS')
        self.assertEqual(updated['technician_notes'], 'Work begun on stand.')

        # Update to COMPLETED
        comp_res = self.client.put(f'/api/maintenance/{rec_id}', json={
            'status': 'COMPLETED'
        })
        self.assertEqual(comp_res.status_code, 200)
        comp_data = json.loads(comp_res.data)['data']
        self.assertEqual(comp_data['status'], 'COMPLETED')
        self.assertIsNotNone(comp_data['completed_date'])

        # Clean up
        self.client.delete(f'/api/maintenance/{rec_id}')

    def test_06_delete_maintenance_record(self):
        """Verify DELETE /api/maintenance/<id> removes record from database."""
        # Create temp record
        create_res = self.client.post('/api/maintenance', json={
            'aircraft_id': 2,
            'title': 'Delete Test Record',
            'scheduled_date': '2026-11-18'
        })
        rec_id = json.loads(create_res.data)['data']['id']

        # Delete
        del_res = self.client.delete(f'/api/maintenance/{rec_id}')
        self.assertEqual(del_res.status_code, 200)

        # Subsequent fetch should be 404
        get_res = self.client.get(f'/api/maintenance/{rec_id}')
        self.assertEqual(get_res.status_code, 404)

    def test_07_aircraft_maintenance_history(self):
        """Verify GET /api/maintenance/history/<aircraft_id> returns airframe orders."""
        response = self.client.get('/api/maintenance/history/1')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['aircraft_id'], 1)
        self.assertIsInstance(data['data'], list)

    def test_08_status_and_priority_filtering(self):
        """Verify status and priority query parameters filter results properly."""
        res_comp = self.client.get('/api/maintenance?status=COMPLETED')
        self.assertEqual(res_comp.status_code, 200)
        data_comp = json.loads(res_comp.data)['data']
        for r in data_comp:
            self.assertEqual(r['status'], 'COMPLETED')

        res_crit = self.client.get('/api/maintenance?priority=CRITICAL')
        self.assertEqual(res_crit.status_code, 200)
        data_crit = json.loads(res_crit.data)['data']
        for r in data_crit:
            self.assertEqual(r['priority'], 'CRITICAL')

    def test_09_non_existent_record_404(self):
        """Verify GET /api/maintenance/999999 returns 404 Not Found."""
        response = self.client.get('/api/maintenance/999999')
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertFalse(data['success'])


if __name__ == '__main__':
    unittest.main()
