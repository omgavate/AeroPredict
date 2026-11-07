"""
End-to-End Workflow Integration Test for AeroPredict (Phase 12 Task 5).
Validates the complete 7-step lifecycle:
1. Add aircraft
2. View aircraft
3. Retrieve engine readings
4. Generate RUL prediction
5. Create maintenance record
6. Update maintenance status
7. View dashboard statistics
"""

import unittest
import json
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app import create_app
from config.database import get_db_connection

class TestE2EWorkflow(unittest.TestCase):
    """Verifies complete end-to-end operational workflow."""

    @classmethod
    def setUpClass(cls):
        cls.app = create_app({'TESTING': True})
        cls.client = cls.app.test_client()

    def test_complete_aircraft_lifecycle_workflow(self):
        # ---------------------------------------------------------
        # Step 1: Add aircraft
        # ---------------------------------------------------------
        create_payload = {
            'tail_number': 'TEST-E2E-99',
            'model': 'Boeing 787-9 Dreamliner',
            'manufacturer': 'Boeing',
            'manufacturing_year': 2023,
            'engine_type': 'GEnx-1B',
            'cmapss_unit_id': 99,
            'current_cycles': 140,
            'flight_hours': 2800,
            'status': 'OPERATIONAL'
        }
        res_step1 = self.client.post('/api/aircraft', json=create_payload)
        self.assertIn(res_step1.status_code, (200, 201), f"Step 1 Failed: {res_step1.data}")
        data_step1 = json.loads(res_step1.data)
        self.assertTrue(data_step1['success'])
        aircraft_id = data_step1['data']['id']
        print(f"\n[Step 1] Aircraft Registered Successfully: ID #{aircraft_id} (TEST-E2E-99)")

        try:
            # ---------------------------------------------------------
            # Step 2: View aircraft
            # ---------------------------------------------------------
            res_step2 = self.client.get(f'/api/aircraft/{aircraft_id}')
            self.assertEqual(res_step2.status_code, 200, f"Step 2 Failed: {res_step2.data}")
            data_step2 = json.loads(res_step2.data)
            self.assertTrue(data_step2['success'])
            self.assertEqual(data_step2['data']['tail_number'], 'TEST-E2E-99')
            self.assertEqual(data_step2['data']['current_cycles'], 140)
            print(f"[Step 2] Aircraft Details Verified: {data_step2['data']['model']}")

            # ---------------------------------------------------------
            # Step 3: Ingest & Retrieve engine readings
            # ---------------------------------------------------------
            telemetry_payload = {
                'cycle': 141,
                'setting_1': 0.0012,
                'setting_2': 0.0002,
                'setting_3': 100.0,
                'sensor_1': 518.67, 'sensor_2': 642.85, 'sensor_3': 1588.20, 'sensor_4': 1405.10,
                'sensor_5': 14.62, 'sensor_6': 21.61, 'sensor_7': 553.80, 'sensor_8': 2388.08,
                'sensor_9': 9046.50, 'sensor_10': 1.30, 'sensor_11': 47.45, 'sensor_12': 521.65,
                'sensor_13': 2388.09, 'sensor_14': 8130.20, 'sensor_15': 8.4210, 'sensor_16': 0.03,
                'sensor_17': 393.0, 'sensor_18': 2388.0, 'sensor_19': 100.0, 'sensor_20': 38.95,
                'sensor_21': 23.3850
            }
            res_ingest = self.client.post(f'/api/aircraft/{aircraft_id}/sensors', json=telemetry_payload)
            self.assertIn(res_ingest.status_code, (200, 201), f"Ingest Failed: {res_ingest.data}")

            res_step3 = self.client.get(f'/api/aircraft/{aircraft_id}/sensors/latest')
            self.assertEqual(res_step3.status_code, 200, f"Step 3 Failed: {res_step3.data}")
            data_step3 = json.loads(res_step3.data)
            self.assertTrue(data_step3['success'])
            self.assertEqual(data_step3['data']['cycle'], 141)
            print(f"[Step 3] Engine Telemetry Retrieved: Cycle {data_step3['data']['cycle']}")

            # ---------------------------------------------------------
            # Step 4: Generate RUL prediction
            # ---------------------------------------------------------
            predict_payload = {
                'aircraft_id': aircraft_id,
                'cycle': 141,
                'telemetry': telemetry_payload
            }
            res_step4 = self.client.post('/api/predict', json=predict_payload)
            self.assertEqual(res_step4.status_code, 200, f"Step 4 Failed: {res_step4.data}")
            data_step4 = json.loads(res_step4.data)
            self.assertTrue(data_step4['success'])
            predicted_rul = data_step4['data']['predicted_rul']
            risk_level = data_step4['data']['risk_level']
            self.assertIsInstance(predicted_rul, (int, float))
            self.assertIn(risk_level, ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL'))
            print(f"[Step 4] RUL Prediction Generated: {predicted_rul} cycles ({risk_level} Risk)")

            # ---------------------------------------------------------
            # Step 5: Create maintenance record
            # ---------------------------------------------------------
            maint_payload = {
                'aircraft_id': aircraft_id,
                'title': 'E2E Validation Routine Engine Check',
                'description': 'Scheduled borescope inspection following prognostic prediction run.',
                'priority': 'HIGH',
                'status': 'PENDING',
                'scheduled_date': '2026-11-15'
            }
            res_step5 = self.client.post('/api/maintenance', json=maint_payload)
            self.assertIn(res_step5.status_code, (200, 201), f"Step 5 Failed: {res_step5.data}")
            data_step5 = json.loads(res_step5.data)
            self.assertTrue(data_step5['success'])
            work_order_id = data_step5['data']['id']
            print(f"[Step 5] Maintenance Work Order Created: #{work_order_id} ({maint_payload['title']})")

            # ---------------------------------------------------------
            # Step 6: Update maintenance status
            # ---------------------------------------------------------
            update_payload = {
                'status': 'IN_PROGRESS',
                'technician_notes': 'Maintenance team assigned. Engine access panels opened.'
            }
            res_step6 = self.client.put(f'/api/maintenance/{work_order_id}', json=update_payload)
            self.assertEqual(res_step6.status_code, 200, f"Step 6 Failed: {res_step6.data}")
            data_step6 = json.loads(res_step6.data)
            self.assertTrue(data_step6['success'])
            self.assertEqual(data_step6['data']['status'], 'IN_PROGRESS')
            print(f"[Step 6] Maintenance Status Updated: IN_PROGRESS")

            # ---------------------------------------------------------
            # Step 7: View dashboard statistics
            # ---------------------------------------------------------
            res_step7 = self.client.get('/api/dashboard')
            self.assertEqual(res_step7.status_code, 200, f"Step 7 Failed: {res_step7.data}")
            data_step7 = json.loads(res_step7.data)
            self.assertTrue(data_step7['success'])
            dash_payload = data_step7['data']
            self.assertGreaterEqual(dash_payload['stats']['total_aircraft'], 1)
            # Find our created aircraft in fleet summary
            matching_aircraft = [ac for ac in dash_payload['fleet_summary'] if ac['id'] == aircraft_id]
            self.assertEqual(len(matching_aircraft), 1)
            self.assertEqual(matching_aircraft[0]['tail_number'], 'TEST-E2E-99')
            print(f"[Step 7] Dashboard Statistics Verified: {dash_payload['stats']['total_aircraft']} Aircraft Total")

        finally:
            # Cleanup test artifacts from MySQL to preserve database cleanliness
            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute("DELETE FROM maintenance_records WHERE aircraft_id = %s", (aircraft_id,))
                cur.execute("DELETE FROM maintenance_alerts WHERE aircraft_id = %s", (aircraft_id,))
                cur.execute("DELETE FROM rul_predictions WHERE aircraft_id = %s", (aircraft_id,))
                cur.execute("DELETE FROM sensor_readings WHERE aircraft_id = %s", (aircraft_id,))
                cur.execute("DELETE FROM aircraft WHERE id = %s", (aircraft_id,))
                conn.commit()
                cur.close()
                print("[Cleanup] Test aircraft and relational data cleaned up cleanly.")

if __name__ == '__main__':
    unittest.main()
