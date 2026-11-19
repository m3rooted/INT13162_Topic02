
"""
Phụ trách: Nguyễn Văn Chung — quản lý hồ sơ khám
(tạo, cập nhật, phân công bác sĩ, tìm kiếm, sắp xếp,
hiển thị, kiểm tra liên kết).
"""

from models.medical_record import MedicalRecord


# ==========================================================
# CLASS PATIENT MANAGER - PHẦN QUẢN LÝ HỒ SƠ KHÁM
# ==========================================================

class PatientManager:
    """
    Phần triển khai các nghiệp vụ hồ sơ khám theo UML.

    Danh sách patients và doctors được cung cấp từ bên ngoài.
    """

    def __init__(self, patients=None, doctors=None):
        self.patients = patients if patients is not None else []
        self.doctors = doctors if doctors is not None else []
        self.medical_records = []

    # ---------------- KIỂM TRA LIÊN KẾT ----------------

    def validate_relations(self, record: MedicalRecord) -> bool:
        """Kiểm tra bệnh nhân và bác sĩ có tồn tại hay không."""

        if not isinstance(record, MedicalRecord):
            return False

        patient_exists = any(
            patient.patient_id == record.patient_id
            for patient in self.patients
        )

        doctor_exists = any(
            doctor.doctor_id == record.doctor_id
            for doctor in self.doctors
        )

        return patient_exists and doctor_exists

    # ---------------- TẠO HỒ SƠ ----------------

    def create_medical_record(self, record: MedicalRecord) -> None:
        """Thêm hồ sơ khám mới."""

        if not isinstance(record, MedicalRecord):
            print("Dữ liệu hồ sơ không hợp lệ.")
            return

        if not record.validate():
            print("Thông tin hồ sơ không hợp lệ.")
            return

        # Kiểm tra mã hồ sơ trùng
        for item in self.medical_records:
            if item.record_id == record.record_id:
                print("Mã hồ sơ đã tồn tại.")
                return

        # Kiểm tra bệnh nhân và bác sĩ
        if not self.validate_relations(record):
            print("Bệnh nhân hoặc bác sĩ không tồn tại.")
            return

        self.medical_records.append(record)
        print("Thêm hồ sơ khám thành công.")

    # ---------------- CẬP NHẬT HỒ SƠ ----------------

    def update_medical_record(
        self,
        record_id: str,
        changes: dict
    ) -> bool:
        """Cập nhật thông tin hồ sơ theo mã."""

        record = next(
            (
                item for item in self.medical_records
                if item.record_id == record_id
            ),
            None
        )

        if record is None:
            print("Không tìm thấy hồ sơ.")
            return False

        if not isinstance(changes, dict) or not changes:
            print("Thông tin cập nhật không hợp lệ.")
            return False

        allowed_fields = {
            "patient_id",
            "doctor_id",
            "visit_date",
            "diagnosis",
            "fee_at_visit"
        }

        # Không cho sửa mã hồ sơ và trường không tồn tại
        if not set(changes).issubset(allowed_fields):
            print("Có trường dữ liệu không được phép cập nhật.")
            return False

        # Tạo hồ sơ tạm để kiểm tra trước khi thay đổi dữ liệu thật
        new_values = {
            "patient_id": record.patient_id,
            "doctor_id": record.doctor_id,
            "visit_date": record.visit_date,
            "diagnosis": record.diagnosis,
            "fee_at_visit": record.fee_at_visit
        }

        new_values.update(changes)

        try:
            updated_record = MedicalRecord(
                record_id=record.record_id,
                **new_values
            )
        except (ValueError, TypeError):
            print("Dữ liệu cập nhật không hợp lệ.")
            return False

        if not self.validate_relations(updated_record):
            print("Bệnh nhân hoặc bác sĩ không tồn tại.")
            return False

        # Chỉ cập nhật khi toàn bộ dữ liệu hợp lệ
        record.patient_id = updated_record.patient_id
        record.doctor_id = updated_record.doctor_id
        record.visit_date = updated_record.visit_date
        record.diagnosis = updated_record.diagnosis
        record.fee_at_visit = updated_record.fee_at_visit

        print("Cập nhật hồ sơ thành công.")
        return True

    # ---------------- PHÂN CÔNG BÁC SĨ ----------------

    def assign_doctor(
        self,
        record_id: str,
        doctor_id: str
    ) -> bool:
        """Phân công bác sĩ cho hồ sơ khám."""

        record = next(
            (
                item for item in self.medical_records
                if item.record_id == record_id
            ),
            None
        )

        if record is None:
            print("Không tìm thấy hồ sơ.")
            return False

        doctor_exists = any(
            doctor.doctor_id == doctor_id
            for doctor in self.doctors
        )

        if not doctor_exists:
            print("Không tìm thấy bác sĩ.")
            return False

        record.doctor_id = doctor_id

        print("Phân công bác sĩ thành công.")
        return True

    # ---------------- TÌM KIẾM HỒ SƠ ----------------

    def find_medical_records(
        self,
        keyword: str,
        search_type: str
    ) -> list[MedicalRecord]:
        """
        Tìm kiếm theo:
        - record_id: Mã hồ sơ chính xác.
        - patient_id: Mã bệnh nhân chính xác.
        - patient_name: Tên bệnh nhân gần đúng.
        - doctor_id: Mã bác sĩ chính xác.
        - doctor_name: Tên bác sĩ gần đúng.
        """

        if not isinstance(keyword, str) or not keyword.strip():
            print("Từ khóa tìm kiếm không hợp lệ.")
            return []

        keyword = keyword.strip().casefold()

        results = []

        for record in self.medical_records:

            if search_type == "record_id":
                matched = record.record_id.casefold() == keyword

            elif search_type == "patient_id":
                matched = record.patient_id.casefold() == keyword

            elif search_type == "doctor_id":
                matched = record.doctor_id.casefold() == keyword

            elif search_type == "patient_name":
                patient = next(
                    (
                        p for p in self.patients
                        if p.patient_id == record.patient_id
                    ),
                    None
                )

                matched = (
                    patient is not None
                    and keyword in patient.full_name.casefold()
                )

            elif search_type == "doctor_name":
                doctor = next(
                    (
                        d for d in self.doctors
                        if d.doctor_id == record.doctor_id
                    ),
                    None
                )

                matched = (
                    doctor is not None
                    and keyword in doctor.full_name.casefold()
                )

            else:
                print("Tiêu chí tìm kiếm không hợp lệ.")
                return []

            if matched:
                results.append(record)

        return results

    # ---------------- SẮP XẾP HỒ SƠ ----------------

    def sort_medical_records(
        self,
        criterion: str,
        descending: bool = False
    ) -> list[MedicalRecord]:
        """
        Sắp xếp theo:
        - visit_date: Ngày khám.
        - fee_at_visit: Chi phí khám.
        """

        if criterion == "visit_date":
            return sorted(
                self.medical_records,
                key=lambda record: record.visit_date,
                reverse=descending
            )

        elif criterion == "fee_at_visit":
            return sorted(
                self.medical_records,
                key=lambda record: (
                    record.fee_at_visit is None,
                    record.fee_at_visit or 0
                ),
                reverse=descending
            )

        print("Tiêu chí sắp xếp không hợp lệ.")
        return []

    # ---------------- HIỂN THỊ HỒ SƠ ----------------

    def display_medical_records(self) -> None:
        """Hiển thị danh sách hồ sơ khám theo dạng bảng."""

        if not self.medical_records:
            print("Danh sách hồ sơ khám hiện đang trống.")
            return

        headers = [
            "Mã hồ sơ",
            "Mã bệnh nhân",
            "Mã bác sĩ",
            "Ngày khám",
            "Chẩn đoán",
            "Chi phí"
        ]

        rows = []

        for record in self.medical_records:
            rows.append([
                record.record_id,
                record.patient_id,
                record.doctor_id,
                record.visit_date.strftime("%d/%m/%Y"),
                record.diagnosis,
                (
                    f"{record.fee_at_visit:,.0f}"
                    if record.fee_at_visit is not None
                    else "Chưa có"
                )
            ])

        # Tính độ rộng từng cột
        widths = [
            max(len(str(row[i])) for row in [headers] + rows)
            for i in range(len(headers))
        ]

        separator = "+-" + "-+-".join(
            "-" * width for width in widths
        ) + "-+"

        def print_row(row):
            print(
                "| "
                + " | ".join(
                    str(value).ljust(widths[i])
                    for i, value in enumerate(row)
                )
                + " |"
            )

        print("\nDANH SÁCH HỒ SƠ KHÁM")
        print(separator)
        print_row(headers)
        print(separator)

        for row in rows:
            print_row(row)

        print(separator)
        print(f"Tổng số hồ sơ: {len(self.medical_records)}")
