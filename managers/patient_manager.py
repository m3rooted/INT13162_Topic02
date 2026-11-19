"""Quản lý bệnh nhân theo sơ đồ lớp UML: thêm, sửa, xóa, hiển thị, tìm kiếm và sắp xếp."""

from models.patient import Inpatient, Outpatient


class PatientManager:
    """Quản lý danh sách bệnh nhân và xử lý các nghiệp vụ liên quan."""

    def __init__(self, patients=None):
        # Lưu danh sách đối tượng Patient (Inpatient hoặc Outpatient)
        self.patients = list(patients) if patients else []

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

    def update_patient(self, patient_id, changes):
        """Cập nhật thông tin bệnh nhân qua dict changes; trả về True nếu thành công."""
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

        for field, value in changes.items():
            if field == "patient_id":
                raise ValueError("Không được phép thay đổi mã bệnh nhân sau khi tạo.")
            if field not in allowed_fields:
                raise ValueError(
                    f"Trường '{field}' không hợp lệ hoặc không áp dụng cho loại bệnh nhân này."
                )
            setattr(patient, field, value)

        if hasattr(patient, "validate") and not patient.validate():
            raise ValueError(f"Dữ liệu sau cập nhật của bệnh nhân '{patient_id}' không hợp lệ.")

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

        self.patients.remove(patient)
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
            elif search_type not in {"id", "name", "all"}:
                raise ValueError("Kiểu tìm kiếm không hợp lệ (chỉ nhận 'id', 'name' hoặc 'all').")

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