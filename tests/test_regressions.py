import json
import io
import math
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date, timedelta
from pathlib import Path

import main
from managers.patient_manager import PatientManager
from models.medical_record import MedicalRecord
from models.patient import Inpatient, Outpatient
from services.statistics import calculate_inpatient_fee, calculate_outpatient_fee


class RemainingBugRegressionTests(unittest.TestCase):
    def test_future_sample_admissions_load_as_valid_and_can_be_updated(self):
        with redirect_stdout(io.StringIO()):
            patients, _, _ = main._load_managers()

        self.assertEqual(patients.data_path, main.DATA_DIR / "patients.json")
        for patient in patients.patients:
            self.assertTrue(patient.validate(), patient.patient_id)

        sample_future_admission = date.fromisoformat("2026-11-26")
        patient = patients._find_by_id("BN016")
        self.assertEqual(patient.admission_date, min(sample_future_admission, date.today()))
        patients.data_path = None
        self.assertTrue(patients.update_patient("BN016", {"full_name": "Updated Patient"}))

    def test_patient_add_update_delete_persist_json_without_overwriting_other_fields(self):
        future_admission = date.today() + timedelta(days=2)
        original_row = {
            "patient_type": "inpatient",
            "patient_id": "P001",
            "full_name": "Original Name",
            "birth_year": 1988,
            "phone": "0900000001",
            "admission_date": future_admission.isoformat(),
            "daily_fee": 100.0,
            "days_stayed": 1,
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            data_path = Path(temp_dir) / "patients.json"
            data_path.write_text(json.dumps([original_row]), encoding="utf-8")
            patient = Inpatient(
                "P001", "Original Name", 1988, "0900000001", date.today(), 100.0, 1
            )
            patients = PatientManager([patient], data_path=data_path)

            self.assertTrue(patients.update_patient("P001", {"full_name": "Updated Name"}))
            patients.add_patient(Outpatient("P002", "New Patient", 1990, "0900000002", 200.0))

            rows = json.loads(data_path.read_text(encoding="utf-8"))
            self.assertEqual(rows[0]["full_name"], "Updated Name")
            self.assertEqual(rows[0]["admission_date"], future_admission.isoformat())
            self.assertEqual(rows[1]["patient_id"], "P002")

            self.assertTrue(patients.delete_patient("P002"))
            rows = json.loads(data_path.read_text(encoding="utf-8"))
            self.assertEqual([row["patient_id"] for row in rows], ["P001"])

    def test_patient_and_record_models_reject_non_finite_fees(self):
        for fee in (math.nan, math.inf, -math.inf):
            with self.subTest(fee=fee), self.assertRaises(ValueError):
                Inpatient("P001", "Patient", 1988, "0900000001", date.today(), fee, 1)
            with self.subTest(fee=fee), self.assertRaises(ValueError):
                Outpatient("P002", "Patient", 1988, "0900000002", fee)
            with self.subTest(fee=fee), self.assertRaises(ValueError):
                MedicalRecord("R001", "P001", "D001", date.today(), "Diagnosis", fee)

    def test_fee_helpers_reject_non_finite_fees(self):
        for fee in (math.nan, math.inf, -math.inf):
            with self.subTest(fee=fee), self.assertRaises(ValueError):
                calculate_inpatient_fee(fee, 1)
            with self.subTest(fee=fee), self.assertRaises(ValueError):
                calculate_outpatient_fee(fee)

    def test_invalid_patient_search_type_raises_for_empty_and_nonempty_lists(self):
        managers = [
            PatientManager(),
            PatientManager([Outpatient("P001", "Patient", 1988, "0900000001", 10)]),
        ]
        for manager in managers:
            with self.subTest(patient_count=len(manager.patients)), self.assertRaises(ValueError):
                manager.find_patients("Patient", "unknown")


if __name__ == "__main__":
    unittest.main()
