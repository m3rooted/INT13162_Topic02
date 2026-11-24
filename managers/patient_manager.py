"""Quản lý bệnh nhân theo sơ đồ lớp UML: thêm, sửa, xóa, hiển thị, tìm kiếm và sắp xếp."""

import json
from pathlib import Path

from models.patient import Inpatient, Outpatient


class PatientManager:
    """Quản lý danh sách bệnh nhân và xử lý các nghiệp vụ liên quan."""

    def __init__(self, patients=None, patient_file=None):
        # Lưu danh sách đối tượng Patient (Inpatient hoặc Outpatient)
        self.patients = list(patients) if patients else []
        self.patient_file = Path(patient_file) if patient_file is not None else None

    def _save_patients(self):
        """Lưu danh sách bệnh nhân nếu manager được cấu hình file JSON."""
        if self.patient_file is None:
            return

        temp_file = self.patient_file.with_name(self.patient_file.name + ".tmp")
        try:
            data = []
            for patient in self.patients:
                row = {
                    "patient_type": "inpatient" if isinstance(patient, Inpatient) else "outpatient",
                    "patient_id": patient.patient_id,
                    "full_name": patient.full_name,
                    "birth_year": patient.birth_year,
                    "phone": patient.phone,
                }
                if isinstance(patient, Inpatient):
                    row.update({
                        "admission_date": patient.admission_date.isoformat(),
                        "daily_fee": patient.daily_fee,
                        "days_stayed": patient.days_stayed,
                    })
                elif isinstance(patient, Outpatient):
                    row["consultation_fee"] = patient.consultation_fee
                else:
                    raise ValueError("Chỉ lưu được Inpatient hoặc Outpatient.")
                data.append(row)

            self.patient_file.parent.mkdir(parents=True, exist_ok=True)
            with temp_file.open("w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=2, allow_nan=False)
            temp_file.replace(self.patient_file)
        except (OSError, TypeError, ValueError, AttributeError) as error:
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except OSError:
                    pass
            raise ValueError(f"Không thể lưu dữ liệu bệnh nhân: {error}") from error

    def _find_by_id(self, patient_id):
        """Tìm bệnh nhân theo mã; trả về None nếu không tìm thấy."""
        clean_id = str(patient_id).strip()
        for patient in self.patients:
            if patient.patient_id == clean_id:
                return patient
        return None

    def add_patient(self, patient):
        """Thêm bệnh nhân mới nếu mã chưa trùng; từ chối nếu trùng hoặc không hợp lệ."""
        # Kiểm tra trùng mã trước để tránh sai lệch liên kết với hồ sơ khám.
        if self._find_by_id(patient.patient_id) is not None:
            raise ValueError(f"Mã bệnh nhân '{patient.patient_id}' đã tồn tại.")

        # Kiểm tra hợp lệ của đối tượng nếu model có hàm validate().
        if hasattr(patient, "validate") and not patient.validate():
            raise ValueError(f"Thông tin bệnh nhân '{patient.patient_id}' không hợp lệ.")

        self.patients.append(patient)
        try:
            self._save_patients()
        except Exception:
            self.patients.remove(patient)
            raise

    def update_patient(self, patient_id, changes):
        """Cập nhật thông tin bệnh nhân qua dict changes; lỗi ở trường nào thì không sửa trường nào."""
        patient = self._find_by_id(patient_id)
        if patient is None:
            raise ValueError(f"Không tìm thấy bệnh nhân có mã '{patient_id}'.")

        if not isinstance(changes, dict) or not changes:
            raise ValueError("Dữ liệu cập nhật phải là dict không rỗng.")

        # Chỉ cho phép sửa các trường đúng với loại bệnh nhân; không cho đổi patient_id.
        allowed_fields = {"full_name", "birth_year", "phone"}
        if isinstance(patient, Inpatient):
            allowed_fields.update({"admission_date", "daily_fee", "days_stayed"})
        elif isinstance(patient, Outpatient):
            allowed_fields.update({"consultation_fee"})

        # Lưu giá trị cũ để hoàn tác nếu có trường phía sau bị lỗi.
        old_values = {}
        for field in changes:
            if field == "patient_id":
                raise ValueError("Không được phép thay đổi mã bệnh nhân sau khi tạo.")
            if field not in allowed_fields:
                raise ValueError(
                    f"Trường '{field}' không hợp lệ hoặc không áp dụng cho loại bệnh nhân này."
                )
            old_values[field] = getattr(patient, field)

        try:
            for field, value in changes.items():
                setattr(patient, field, value)

            if hasattr(patient, "validate") and not patient.validate():
                raise ValueError(
                    f"Dữ liệu sau cập nhật của bệnh nhân '{patient_id}' không hợp lệ."
                )
            self._save_patients()
        except Exception:
            # Gặp lỗi thì trả lại toàn bộ giá trị ban đầu để tránh sửa dở dang.
            for field, old_val in old_values.items():
                setattr(patient, field, old_val)
            raise

        return True

    def delete_patient(self, patient_id, medical_records=None):
        """Xóa bệnh nhân nếu không còn hồ sơ khám liên quan; trả về True nếu xóa được."""
        patient = self._find_by_id(patient_id)
        if patient is None:
            return False

        # Chặn xóa nếu bệnh nhân đang có hồ sơ khám để tránh hồ sơ mồ côi.
        if medical_records:
            has_record = any(
                getattr(record, "patient_id", None) == patient.patient_id
                for record in medical_records
            )
            if has_record:
                raise ValueError(
                    f"Không thể xóa bệnh nhân '{patient.patient_id}' vì đang có hồ sơ khám."
                )

        index = self.patients.index(patient)
        self.patients.pop(index)
        try:
            self._save_patients()
        except Exception:
            self.patients.insert(index, patient)
            raise
        return True

    def display_patients(self):
        """Hiển thị danh sách bệnh nhân ra console."""
        if not self.patients:
            print("\nChưa có dữ liệu bệnh nhân.")
            return

        print("\n=== DANH SÁCH BỆNH NHÂN ===")
        for patient in self.patients:
            patient_type = "Nội trú" if isinstance(patient, Inpatient) else "Ngoại trú"
            fee = patient.calculate_fee()
            print(
                f"{patient.patient_id} | {patient.full_name} | "
                f"{patient.birth_year} | {patient.phone} | "
                f"{patient_type} | Phí: {fee:,.0f} đồng"
            )
        print(f"Tổng số: {len(self.patients)} bệnh nhân")

    def find_patients(self, keyword, search_type="all"):
        """Tìm bệnh nhân theo 'id', 'name' hoặc 'all'; trả về danh sách kết quả."""
        if not isinstance(search_type, str) or search_type not in {"id", "name", "all"}:
            raise ValueError("Kiểu tìm kiếm không hợp lệ (chỉ nhận 'id', 'name' hoặc 'all').")

        clean_keyword = str(keyword).strip().lower()
        if not clean_keyword:
            raise ValueError("Từ khóa tìm kiếm không được để trống.")

        results = []
        for patient in self.patients:
            matched_id = patient.patient_id.lower() == clean_keyword
            matched_name = clean_keyword in patient.full_name.lower()

            if search_type == "id" and matched_id:
                results.append(patient)
            elif search_type == "name" and matched_name:
                results.append(patient)
            elif search_type == "all" and (matched_id or matched_name):
                results.append(patient)
        return results

    def sort_patients(self, criterion="name", descending=False):
        """Sắp xếp bệnh nhân theo 'name' hoặc 'fee'; trả về danh sách mới đã sắp xếp."""
        if not self.patients:
            return []

        if criterion == "name":
            # Chuẩn hóa chữ thường để sắp xếp tên cho đều.
            return sorted(
                self.patients,
                key=lambda patient: patient.full_name.strip().lower(),
                reverse=descending,
            )
        if criterion == "fee":
            # Gọi calculate_fee() để tính phí theo từng loại bệnh nhân.
            return sorted(
                self.patients,
                key=lambda patient: patient.calculate_fee(),
                reverse=descending,
            )

        raise ValueError("Tiêu chí sắp xếp không hợp lệ (chỉ nhận 'name' hoặc 'fee').")


# Phụ trách: Nguyễn Quốc Anh — quản lý bệnh nhân (thêm, sửa, xóa, hiển thị, tìm kiếm, sắp xếp).
