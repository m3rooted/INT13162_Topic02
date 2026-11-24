# ==========================================
# PATIENT - QUAN LY BENH NHAN
# ==========================================

from datetime import date
from abc import ABC, abstractmethod
import re

from utils.validators import is_non_negative_finite_number


# ==========================================
# 1. CLASS PATIENT - LOP BENH NHAN CO SO
# ==========================================

class Patient(ABC):

    def __init__(self, patient_id: str, full_name: str,
                 birth_year: int, phone: str):

        # Kiem tra ma benh nhan
        if not isinstance(patient_id, str) or not patient_id.strip():
            raise ValueError("Ma benh nhan khong duoc de trong!")

        self._patient_id = patient_id.strip()
        self.full_name = full_name
        self.birth_year = birth_year
        self.phone = phone

        # Validate only base fields here; subclass fields are initialized later.
        if not Patient.validate(self):
            raise ValueError("Thong tin benh nhan khong hop le!")

    # ==========================================
    # MA BENH NHAN - CHI DOC
    # ==========================================

    @property
    def patient_id(self) -> str:
        return self._patient_id

    # ==========================================
    # HO VA TEN BENH NHAN
    # ==========================================

    @property
    def full_name(self) -> str:
        return self._full_name

    @full_name.setter
    def full_name(self, value: str):

        if not isinstance(value, str) or not value.strip():
            raise ValueError("Họ và tên không được để trống!")

        self._full_name = value.strip()

    # ==========================================
    # NAM SINH
    # ==========================================

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

    # ==========================================
    # SO DIEN THOAI
    # ==========================================

    @property
    def phone(self) -> str:
        return self._phone

    @phone.setter
    def phone(self, value: str):

        if not isinstance(value, str) or not re.fullmatch(r"0\d{9}", value):
            raise ValueError("So dien thoai phai co 10 chu so!")

        self._phone = value

    # ==========================================
    # VALIDATION
    # ==========================================

    def validate(self) -> bool:

        return (
            isinstance(self._patient_id, str)
            and bool(self._patient_id.strip())

            and isinstance(self._full_name, str)
            and bool(self._full_name.strip())

            and isinstance(self._birth_year, int)
            and not isinstance(self._birth_year, bool)
            and 1900 <= self._birth_year <= date.today().year

            and isinstance(self._phone, str)
            and bool(re.fullmatch(r"0\d{9}", self._phone))
        )

    # ==========================================
    # HIEN THI THONG TIN
    # ==========================================

    def display_info(self) -> str:

        return (
            f"Ma benh nhan: {self.patient_id}\n"
            f"Họ và tên: {self.full_name}\n"
            f"Nam sinh: {self.birth_year}\n"
            f"So dien thoai: {self.phone}"
        )

    # ==========================================
    # PHUONG THUC TRUU TUONG
    # ==========================================

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

        # Goi constructor cua lop cha
        super().__init__(patient_id, full_name, birth_year, phone)

        self.admission_date = admission_date
        self.daily_fee = daily_fee
        self.days_stayed = days_stayed

        if not self.validate():
            raise ValueError("Thong tin benh nhan noi tru khong hop le!")

    # ==========================================
    # NGAY NHAP VIEN
    # ==========================================

    @property
    def admission_date(self) -> date:
        return self._admission_date

    @admission_date.setter
    def admission_date(self, value: date):

        if type(value) is not date or value > date.today():
            raise ValueError("Ngay nhap vien khong hop le!")

        self._admission_date = value

    # ==========================================
    # CHI PHI MOI NGAY
    # ==========================================

    @property
    def daily_fee(self) -> float:
        return self._daily_fee

    @daily_fee.setter
    def daily_fee(self, value: float):

        if not is_non_negative_finite_number(value):
            raise ValueError("Chi phi moi ngay phai la so khong am!")

        self._daily_fee = float(value)

    # ==========================================
    # SO NGAY NAM VIEN
    # ==========================================

    @property
    def days_stayed(self) -> int:
        return self._days_stayed

    @days_stayed.setter
    def days_stayed(self, value: int):

        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or value <= 0
        ):
            raise ValueError("So ngay nam vien phai lon hon 0!")

        self._days_stayed = value

    # ==========================================
    # VALIDATION
    # ==========================================

    def validate(self) -> bool:

        return (
            super().validate()

            and type(self._admission_date) is date
            and self._admission_date <= date.today()

            and is_non_negative_finite_number(self._daily_fee)

            and isinstance(self._days_stayed, int)
            and not isinstance(self._days_stayed, bool)
            and self._days_stayed > 0
        )

    # ==========================================
    # TINH VIEN PHI NOI TRU
    # ==========================================

    def calculate_fee(self) -> float:

        return self.daily_fee * self.days_stayed

    # ==========================================
    # HIEN THI THONG TIN NOI TRU
    # ==========================================

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

        # Goi constructor cua lop cha
        super().__init__(patient_id, full_name, birth_year, phone)

        self.consultation_fee = consultation_fee

        if not self.validate():
            raise ValueError("Thong tin benh nhan ngoai tru khong hop le!")

    # ==========================================
    # PHI KHAM BENH
    # ==========================================

    @property
    def consultation_fee(self) -> float:
        return self._consultation_fee

    @consultation_fee.setter
    def consultation_fee(self, value: float):

        if not is_non_negative_finite_number(value):
            raise ValueError("Phi kham phai la so khong am!")

        self._consultation_fee = float(value)

    # ==========================================
    # VALIDATION
    # ==========================================

    def validate(self) -> bool:

        return (
            super().validate()

            and is_non_negative_finite_number(self._consultation_fee)
        )

    # ==========================================
    # TINH PHI KHAM NGOAI TRU
    # ==========================================

    def calculate_fee(self) -> float:

        return self.consultation_fee

    # ==========================================
    # HIEN THI THONG TIN NGOAI TRU
    # ==========================================

    def display_info(self) -> str:

        return (
            super().display_info()
            + "\nLoai benh nhan: Ngoai tru"
            + f"\nPhi kham benh: {self.consultation_fee:,.0f} VND"
            + f"\nTong chi phi: {self.calculate_fee():,.0f} VND"
        )
