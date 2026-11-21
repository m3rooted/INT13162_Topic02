# ==========================================
# DOCTOR - QUAN LY THONG TIN BAC SI
# ==========================================


class Doctor:

    def __init__(self, doctor_id: str, full_name: str, specialty: str):

        # Kiem tra ma bac si
        if not isinstance(doctor_id, str) or not doctor_id.strip():
            raise ValueError("Ma bac si khong duoc de trong!")

        self._doctor_id = doctor_id.strip()
        self.full_name = full_name
        self.specialty = specialty

        if not self.validate():
            raise ValueError("Thong tin bac si khong hop le!")

    # ==========================================
    # MA BAC SI - CHI DOC
    # ==========================================

    @property
    def doctor_id(self) -> str:
        return self._doctor_id

    # ==========================================
    # HO TEN BAC SI
    # ==========================================

    @property
    def full_name(self) -> str:
        return self._full_name

    @full_name.setter
    def full_name(self, value: str):

        if not isinstance(value, str) or not value.strip():
            raise ValueError("Ho ten bac si khong duoc de trong!")

        self._full_name = value.strip()

    # ==========================================
    # CHUYEN KHOA
    # ==========================================

    @property
    def specialty(self) -> str:
        return self._specialty

    @specialty.setter
    def specialty(self, value: str):

        if not isinstance(value, str) or not value.strip():
            raise ValueError("Chuyen khoa khong duoc de trong!")

        self._specialty = value.strip()

    # ==========================================
    # VALIDATION
    # ==========================================

    def validate(self) -> bool:

        return (
            isinstance(self._doctor_id, str)
            and bool(self._doctor_id.strip())

            and isinstance(self._full_name, str)
            and bool(self._full_name.strip())

            and isinstance(self._specialty, str)
            and bool(self._specialty.strip())
        )

    # ==========================================
    # HIEN THI THONG TIN
    # ==========================================

    def display_info(self) -> str:

        return (
            f"Ma bac si: {self.doctor_id}\n"
            f"Ho ten: {self.full_name}\n"
            f"Chuyen khoa: {self.specialty}"
        )

    # ==========================================
    # CHUYEN DOI DOI TUONG THANH CHUOI
    # ==========================================

    def __str__(self) -> str:

        return f"{self.doctor_id} - {self.full_name}"