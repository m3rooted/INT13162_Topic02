# ==========================================
# MEDICAL RECORD - HO SO KHAM BENH
# ==========================================

from datetime import date
from typing import Optional


class MedicalRecord:

    def __init__(self, record_id: str, patient_id: str,
                 doctor_id: str, visit_date: date,
                 diagnosis: str,
                 fee_at_visit: Optional[float] = None):
        self._record_id = record_id
        self._patient_id = patient_id
        self.doctor_id = doctor_id
        self.visit_date = visit_date
        self.diagnosis = diagnosis
        self.fee_at_visit = fee_at_visit

        if not self.validate():
            raise ValueError("Ho so kham benh khong hop le!")

    # Ma ho so chi doc
    @property
    def record_id(self) -> str:
        return self._record_id

    # Ma benh nhan chi doc
    @property
    def patient_id(self) -> str:
        return self._patient_id

    # Ma bac si phu trach
    @property
    def doctor_id(self) -> str:
        return self._doctor_id

    @doctor_id.setter
    def doctor_id(self, value: str):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Ma bac si khong duoc de trong!")
        self._doctor_id = value.strip()

    # Ngay kham benh
    @property
    def visit_date(self) -> date:
        return self._visit_date

    @visit_date.setter
    def visit_date(self, value: date):
        if not isinstance(value, date) or value > date.today():
            raise ValueError("Ngay kham khong hop le!")
        self._visit_date = value

    # Chan doan benh
    @property
    def diagnosis(self) -> str:
        return self._diagnosis

    @diagnosis.setter
    def diagnosis(self, value: str):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Chan doan khong duoc de trong!")
        self._diagnosis = value.strip()

    # Chi phi tai thoi diem kham
    @property
    def fee_at_visit(self) -> Optional[float]:
        return self._fee_at_visit

    @fee_at_visit.setter
    def fee_at_visit(self, value: Optional[float]):
        if value is not None:
            if (not isinstance(value, (int, float)) or isinstance(value, bool)
                    or value < 0):
                raise ValueError("Chi phi kham phai la so khong am!")
            value = float(value)
        self._fee_at_visit = value

    # Kiem tra tinh hop le cua ho so
    def validate(self) -> bool:
        return (
            isinstance(self._record_id, str)
            and bool(self._record_id.strip())
            and isinstance(self._patient_id, str)
            and bool(self._patient_id.strip())
            and bool(self._doctor_id.strip())
            and isinstance(self._visit_date, date)
            and self._visit_date <= date.today()
            and bool(self._diagnosis.strip())
            and (self._fee_at_visit is None or self._fee_at_visit >= 0)
        )

    # Hien thi thong tin ho so
    def display_info(self) -> str:
        fee = (
            f"{self.fee_at_visit:,.0f} VND"
            if self.fee_at_visit is not None
            else "Chua cap nhat"
        )

        return (
            f"Ma ho so: {self.record_id}\n"
            f"Ma benh nhan: {self.patient_id}\n"
            f"Ma bac si: {self.doctor_id}\n"
            f"Ngay kham: {self.visit_date}\n"
            f"Chan doan: {self.diagnosis}\n"
            f"Chi phi: {fee}"
        )

    def __str__(self) -> str:
        return f"{self.record_id} - {self.patient_id}"
