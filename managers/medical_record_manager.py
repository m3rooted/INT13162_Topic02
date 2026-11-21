"""
Phụ trách: Nguyễn Văn Chung — quản lý hồ sơ khám
(tạo, cập nhật, phân công bác sĩ, tìm kiếm, sắp xếp,
hiển thị, kiểm tra liên kết).
"""

import json
from datetime import date

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
        """
        Thêm hồ sơ khám mới.

        Raises:
            ValueError: dữ liệu không hợp lệ, trùng mã hồ sơ hoặc
                bệnh nhân/bác sĩ không tồn tại.
        """

        if not isinstance(record, MedicalRecord):
            raise ValueError("Dữ liệu hồ sơ không hợp lệ.")

        if not record.validate():
            raise ValueError("Thông tin hồ sơ không hợp lệ.")

        for item in self.medical_records:
            if item.record_id == record.record_id:
                raise ValueError("Mã hồ sơ đã tồn tại.")

        if not self.validate_relations(record):
            raise ValueError("Bệnh nhân hoặc bác sĩ không tồn tại.")

        self.medical_records.append(record)
        print("Thêm hồ sơ khám thành công.")

    # ---------------- CẬP NHẬT HỒ SƠ ----------------

    def update_medical_record(
        self,
        record_id: str,
        changes: dict
    ) -> bool:
        """
        Cập nhật thông tin hồ sơ theo mã. Trả về True khi cập nhật thành công.

        Raises:
            ValueError: không tìm thấy hồ sơ, thông tin cập nhật không hợp lệ,
                có trường không được phép sửa hoặc bệnh nhân/bác sĩ không tồn tại.
        """

        record = next(
            (
                item for item in self.medical_records
                if item.record_id == record_id
            ),
            None
        )

        if record is None:
            raise ValueError("Không tìm thấy hồ sơ.")

        if not isinstance(changes, dict) or not changes:
            raise ValueError("Thông tin cập nhật không hợp lệ.")

        # record_id và patient_id là thuộc tính CHỈ ĐỌC trong MedicalRecord
        # (chỉ có @property, không có @setter) nên không được phép sửa.
        # Nghiệp vụ: hồ sơ khám đã tạo không được chuyển sang bệnh nhân khác.
        allowed_fields = {
            "doctor_id",
            "visit_date",
            "diagnosis",
            "fee_at_visit"
        }

        if not set(changes).issubset(allowed_fields):
            raise ValueError("Có trường dữ liệu không được phép cập nhật.")

        # Dựng hồ sơ tạm để kiểm tra dữ liệu mới trước khi sửa hồ sơ thật,
        # nhờ đó nếu có lỗi thì hồ sơ thật không bị thay đổi dở dang.
        # patient_id vẫn phải truyền vào constructor (tham số bắt buộc) nhưng không đổi.
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
        except (ValueError, TypeError) as error:
            raise ValueError("Dữ liệu cập nhật không hợp lệ.") from error

        if not self.validate_relations(updated_record):
            raise ValueError("Bệnh nhân hoặc bác sĩ không tồn tại.")

        # Chỉ gán các trường có setter. Không gán patient_id vì nó chỉ đọc
        # (gán vào sẽ gây AttributeError).
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
        """
        Phân công bác sĩ cho hồ sơ khám. Trả về True khi phân công thành công.

        Raises:
            ValueError: không tìm thấy hồ sơ, không tìm thấy bác sĩ
                hoặc mã bác sĩ không hợp lệ.
        """

        record = next(
            (
                item for item in self.medical_records
                if item.record_id == record_id
            ),
            None
        )

        if record is None:
            raise ValueError("Không tìm thấy hồ sơ.")

        doctor_exists = any(
            doctor.doctor_id == doctor_id
            for doctor in self.doctors
        )

        if not doctor_exists:
            raise ValueError("Không tìm thấy bác sĩ.")

        try:
            record.doctor_id = doctor_id
        except (ValueError, TypeError) as error:
            raise ValueError("Mã bác sĩ không hợp lệ.") from error

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

        Trả về danh sách hồ sơ khớp (rỗng nếu không có hồ sơ nào khớp).

        Raises:
            ValueError: từ khóa hoặc tiêu chí tìm kiếm không hợp lệ.
        """

        if not isinstance(keyword, str) or not keyword.strip():
            raise ValueError("Từ khóa tìm kiếm không hợp lệ.")

        # Kiểm tra tiêu chí TRƯỚC khi duyệt hồ sơ để tiêu chí sai luôn bị
        # báo lỗi, kể cả khi danh sách hồ sơ đang trống.
        if search_type not in (
            "record_id",
            "patient_id",
            "patient_name",
            "doctor_id",
            "doctor_name"
        ):
            raise ValueError("Tiêu chí tìm kiếm không hợp lệ.")

        # casefold để so sánh không phân biệt hoa thường
        keyword = keyword.strip().casefold()

        results = []

        for record in self.medical_records:

            if search_type == "record_id":
                matched = record.record_id.casefold() == keyword

            elif search_type == "patient_id":
                matched = record.patient_id.casefold() == keyword

            elif search_type == "doctor_id":
                matched = record.doctor_id.casefold() == keyword

            # Tìm theo tên: tra bệnh nhân/bác sĩ của hồ sơ rồi so khớp gần đúng
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
                raise ValueError("Tiêu chí tìm kiếm không hợp lệ.")

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

        Raises:
            ValueError: tiêu chí sắp xếp không hợp lệ.
        """

        # sorted() trả về list mới, không làm thay đổi danh sách gốc
        if criterion == "visit_date":
            return sorted(
                self.medical_records,
                key=lambda record: record.visit_date,
                reverse=descending
            )

        elif criterion == "fee_at_visit":
            return sorted(
                self.medical_records,
                # Key là tuple (phí có None không, giá trị phí): hồ sơ chưa có phí
                # (None) bị đẩy xuống cuối, và tránh lỗi so sánh None với số.
                key=lambda record: (
                    record.fee_at_visit is None,
                    record.fee_at_visit or 0
                ),
                reverse=descending
            )

        raise ValueError("Tiêu chí sắp xếp không hợp lệ.")

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

        # Độ rộng mỗi cột = độ dài lớn nhất trong cột (tính cả tiêu đề)
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

    # ---------------- ĐỌC / GHI JSON ----------------

    @staticmethod
    def _record_to_dict(record: MedicalRecord) -> dict:
        """Chuyển MedicalRecord thành dict (ngày khám lưu dạng YYYY-MM-DD)."""

        return {
            "record_id": record.record_id,
            "patient_id": record.patient_id,
            "doctor_id": record.doctor_id,
            # JSON không có kiểu ngày nên lưu dạng chuỗi ISO, ví dụ "2026-11-10"
            "visit_date": record.visit_date.isoformat(),
            "diagnosis": record.diagnosis,
            "fee_at_visit": record.fee_at_visit
        }

    @staticmethod
    def _record_from_dict(row: dict) -> MedicalRecord:
        """Tạo MedicalRecord từ dict. Ném lỗi nếu thiếu trường hoặc sai định dạng."""

        return MedicalRecord(
            row["record_id"],
            row["patient_id"],
            row["doctor_id"],
            date.fromisoformat(row["visit_date"]),
            row["diagnosis"],
            row.get("fee_at_visit")
        )

    def load_from_json(self, path) -> None:
        """
        Nạp hồ sơ khám từ file JSON (key "medical_records").

        Từng hồ sơ đều được kiểm tra hợp lệ, trùng mã và liên kết
        bệnh nhân/bác sĩ. Hồ sơ lỗi bị bỏ qua và có thông báo số lượng.
        Danh sách hiện tại chỉ bị thay thế khi đọc file thành công.

        Raises:
            ValueError: không đọc được file, sai cú pháp JSON hoặc
                thiếu danh sách medical_records.
        """

        # utf-8-sig để đọc được cả file JSON có BOM
        try:
            with open(path, "r", encoding="utf-8-sig") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError("Không đọc được file dữ liệu.") from error

        rows = data.get("medical_records") if isinstance(data, dict) else None
        if not isinstance(rows, list):
            raise ValueError("File dữ liệu thiếu danh sách medical_records.")

        # Nạp vào danh sách tạm, chỉ gán vào self.medical_records khi xử lý xong
        loaded = []
        seen_ids = set()
        skipped = 0

        for row in rows:
            try:
                record = self._record_from_dict(row)
            except (ValueError, TypeError, KeyError, AttributeError):
                skipped += 1
                continue

            if record.record_id in seen_ids or not self.validate_relations(record):
                skipped += 1
                continue

            seen_ids.add(record.record_id)
            loaded.append(record)

        self.medical_records = loaded
        print(f"Đã nạp {len(loaded)} hồ sơ khám.")
        if skipped:
            print(f"Bỏ qua {skipped} hồ sơ không hợp lệ.")

    def save_to_json(self, path) -> None:
        """
        Lưu hồ sơ khám vào file JSON (key "medical_records").

        Nếu file đã có và là object JSON thì giữ nguyên các key khác
        trong file, chỉ thay phần "medical_records".

        Raises:
            ValueError: không chuyển được dữ liệu sang JSON hoặc không ghi được file.
        """

        # Đọc nội dung cũ (nếu có) để không làm mất các key khác trong file
        data = {}
        try:
            with open(path, "r", encoding="utf-8-sig") as file:
                existing = json.load(file)
            if isinstance(existing, dict):
                data = existing
        except (OSError, json.JSONDecodeError):
            pass

        data["medical_records"] = [
            self._record_to_dict(record) for record in self.medical_records
        ]

        # Tạo chuỗi JSON trước khi mở file ghi, để lỗi chuyển đổi không làm hỏng file cũ
        try:
            content = json.dumps(data, ensure_ascii=False, indent=2)
        except (TypeError, ValueError) as error:
            raise ValueError("Dữ liệu hồ sơ không thể chuyển sang JSON.") from error

        try:
            with open(path, "w", encoding="utf-8") as file:
                file.write(content + "\n")
        except OSError as error:
            raise ValueError("Không ghi được file dữ liệu.") from error

        print("Lưu hồ sơ khám thành công.")
