# ==========================================
#  Patient - QUAN LY BENH NHAN
# ==========================================

from datetime import date
from abc import ABC, abstractmethod
import re


# ==========================================
# 1. CLASS PATIENT - LOP BENH NHAN CO SO
# ==========================================

class Patient(ABC):

    def __init__(self, patient_id: str, full_name: str,
                 birth_year: int, phone: str):

        self._patient_id = patient_id
        self.full_name = full_name
        self.birth_year = birth_year
        self.phone = phone

    # Ma benh nhan chi doc
    @property
    def patient_id(self) -> str:
        return self._patient_id

    # Ho ten benh nhan
    @property
    def full_name(self) -> str:
        return self._full_name

    @full_name.setter
    def full_name(self, value: str):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Ho ten khong duoc de trong!")
        self._full_name = value.strip()

    # Nam sinh benh nhan
    @property
    def birth_year(self) -> int:
        return self._birth_year

    @birth_year.setter
    def birth_year(self, value: int):
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError("Nam sinh phai la so nguyen!")

        if value < 1900 or value > date.today().year:
            raise ValueError("Nam sinh khong hop le!")

        self._birth_year = value

    # So dien thoai
    @property
    def phone(self) -> str:
        return self._phone

    @phone.setter
    def phone(self, value: str):
        if not isinstance(value, str) or not re.fullmatch(r"0\d{9}", value):
            raise ValueError("So dien thoai phai co 10 chu so!")

        self._phone = value

    # Kiem tra thong tin benh nhan
    def validate(self) -> bool:
        return (
            isinstance(self._patient_id, str)
            and bool(self._patient_id.strip())
            and bool(self._full_name.strip())
            and 1900 <= self._birth_year <= date.today().year
            and bool(re.fullmatch(r"0\d{9}", self._phone))
        )

    # Hien thi thong tin benh nhan
    def display_info(self) -> str:
        return (
            f"Ma benh nhan: {self.patient_id}\n"
            f"Ho ten: {self.full_name}\n"
            f"Nam sinh: {self.birth_year}\n"
            f"So dien thoai: {self.phone}"
        )

    # Phuong thuc truu tuong
    @abstractmethod
    def calculate_fee(self) -> float:
        pass

    def __str__(self):
        return f"{self.patient_id} - {self.full_name}"


# ==========================================
# 2. CLASS INPATIENT - BENH NHAN NOI TRU
# ==========================================

class Inpatient(Patient):

    def __init__(self, patient_id: str, full_name: str,
                 birth_year: int, phone: str,
                 admission_date: date, daily_fee: float,
                 days_stayed: int):

        # Goi ham khoi tao lop cha
        super().__init__(patient_id, full_name, birth_year, phone)

        self.admission_date = admission_date
        self.daily_fee = daily_fee
        self.days_stayed = days_stayed

        if not self.validate():
            raise ValueError("Thong tin benh nhan noi tru khong hop le!")

    # Ngay nhap vien
    @property
    def admission_date(self) -> date:
        return self._admission_date

    @admission_date.setter
    def admission_date(self, value: date):
        # Chi chap nhan kieu date, khong chap nhan datetime
        if type(value) is not date or value > date.today():
            raise ValueError("Ngay nhap vien khong hop le!")

        self._admission_date = value

    # Chi phi moi ngay
    @property
    def daily_fee(self) -> float:
        return self._daily_fee

    @daily_fee.setter
    def daily_fee(self, value: float):
        if (not isinstance(value, (int, float)) or isinstance(value, bool)
                or value < 0):
            raise ValueError("Chi phi moi ngay phai la so khong am!")

        self._daily_fee = float(value)

    # So ngay nam vien
    @property
    def days_stayed(self) -> int:
        return self._days_stayed

    @days_stayed.setter
    def days_stayed(self, value: int):
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise ValueError("So ngay nam vien phai lon hon 0!")

        self._days_stayed = value

    # Kiem tra thong tin noi tru
    def validate(self) -> bool:
        return (
            super().validate()
            and type(self._admission_date) is date
            and self._admission_date <= date.today()
            and self._daily_fee >= 0
            and self._days_stayed > 0
        )

    # Tinh vien phi noi tru
    def calculate_fee(self) -> float:
        return self.daily_fee * self.days_stayed

    # Hien thi thong tin noi tru
    def display_info(self) -> str:
        return (
            super().display_info()
            + "\nLoai benh nhan: Noi tru"
            + f"\nNgay nhap vien: {self.admission_date}"
            + f"\nChi phi moi ngay: {self.daily_fee:,.0f} VND"
            + f"\nSo ngay nam vien: {self.days_stayed}"
            + f"\nTong vien phi: {self.calculate_fee():,.0f} VND"
        )


# ==========================================
# 3. CLASS OUTPATIENT - BENH NHAN NGOAI TRU
# ==========================================

class Outpatient(Patient):

    def __init__(self, patient_id: str, full_name: str,
                 birth_year: int, phone: str,
                 consultation_fee: float):

        # Goi ham khoi tao lop cha
        super().__init__(patient_id, full_name, birth_year, phone)

        self.consultation_fee = consultation_fee

        if not self.validate():
            raise ValueError("Thong tin benh nhan ngoai tru khong hop le!")

    # Phi kham benh
    @property
    def consultation_fee(self) -> float:
        return self._consultation_fee

    @consultation_fee.setter
    def consultation_fee(self, value: float):
        if (not isinstance(value, (int, float)) or isinstance(value, bool)
                or value < 0):
            raise ValueError("Phi kham phai la so khong am!")

        self._consultation_fee = float(value)

    # Kiem tra thong tin ngoai tru
    def validate(self) -> bool:
        return (
            super().validate()
            and self._consultation_fee >= 0
        )

    # Tinh phi kham ngoai tru
    def calculate_fee(self) -> float:
        return self.consultation_fee

    # Hien thi thong tin ngoai tru
    def display_info(self) -> str:
        return (
            super().display_info()
            + "\nLoai benh nhan: Ngoai tru"
            + f"\nPhi kham benh: {self.consultation_fee:,.0f} VND"
            + f"\nTong chi phi: {self.calculate_fee():,.0f} VND"
        )


# ==========================================
# 4. KIEM THU CAC LOP BENH NHAN
# ==========================================

if __name__ == "__main__":

    # Tao benh nhan noi tru
    patient1 = Inpatient(
        "BN01",
        "Nguyen Van An",
        2000,
        "0912345678",
        date(2026, 11, 10),
        300000,
        5
    )

    # Tao benh nhan ngoai tru
    patient2 = Outpatient(
        "BN02",
        "Tran Thi Binh",
        2002,
        "0987654321",
        150000
    )

    # Hien thi benh nhan noi tru
    print("========== BENH NHAN NOI TRU ==========")
    print(patient1.display_info())
    print("Validation:", patient1.validate())

    # Hien thi benh nhan ngoai tru
    print("\n========== BENH NHAN NGOAI TRU ==========")
    print(patient2.display_info())
    print("Validation:", patient2.validate())

    # Kiem tra da hinh
    print("\n========== KIEM TRA DA HINH ==========")
    patients = [patient1, patient2]

    for patient in patients:
        print(f"{patient.full_name}: {patient.calculate_fee():,.0f} VND")