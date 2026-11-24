import io
import math
import unittest
from contextlib import redirect_stdout
from datetime import date

import main
from managers.patient_manager import PatientManager
from models.medical_record import MedicalRecord
from models.patient import Inpatient, Outpatient
from services.statistics import calculate_inpatient_fee, calculate_outpatient_fee


class RemainingBugRegressionTests(unittest.TestCase):
    def test_future_sample_admissions_load_as_valid_and_can_be_updated(self):
        with redirect_stdout(io.StringIO()):
            patients, _, _ = main._load_managers()

        for patient in patients.patients:
            self.assertTrue(patient.validate(), patient.patient_id)

        sample_future_admission = date.fromisoformat("2026-11-26")
        patient = patients._find_by_id("BN016")
        self.assertEqual(patient.admission_date, min(sample_future_admission, date.today()))
        self.assertTrue(patients.update_patient("BN016", {"full_name": "Updated Patient"}))

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
