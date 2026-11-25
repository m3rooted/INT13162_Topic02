"""
Phụ trách: Nguyễn Văn Chung — quản lý hồ sơ khám
(tạo, cập nhật, phân công bác sĩ, tìm kiếm, sắp xếp,
hiển thị, kiểm tra liên kết).
"""

import json
from pathlib import Path
from datetime import date

from models.medical_record import MedicalRecord

"""Quản lý danh sách hồ sơ khám bệnh."""
class MedicalRecordManager:

    """Khởi tạo MedicalRecordManager."""
    def __init__(self, patients=None, doctors=None, medical_record_file=None):

        # Xác định thư mục gốc của dự án
        project_dir = Path(__file__).resolve().parent.parent

        # Đường dẫn file JSON lưu hồ sơ khám bệnh
        self.medical_record_file = Path(medical_record_file) if medical_record_file is not None else project_dir / "data" / "sample_data.json"

        # Nhận danh sách bệnh nhân và bác sĩ từ manager tương ứng
        self.patients = patients if patients is not None else []
        self.doctors = doctors if doctors is not None else []

        # Danh sách lưu các đối tượng MedicalRecord
        self.medical_records = []

        # Tạo thư mục data nếu chưa tồn tại
        self.medical_record_file.parent.mkdir(parents=True, exist_ok=True)

        # Tạo file JSON nếu chưa tồn tại
        if not self.medical_record_file.exists():
            self._save_medical_records()

        # Đọc dữ liệu từ JSON
        self._load_medical_records()

    # ==================================================
    # HÀM HỖ TRỢ 1: ĐỌC FILE JSON
    # ==================================================

    """Đọc dữ liệu từ file JSON."""
    def _read_json(self):

        try:
            with open(self.medical_record_file, "r", encoding="utf-8-sig") as file:
                data = json.load(file)

            if not isinstance(data, dict):
                raise ValueError("Dữ liệu JSON phải có dạng dictionary.")

            return data

        except FileNotFoundError:
            print("Không tìm thấy file JSON.")
            return None

        except json.JSONDecodeError as error:
            print(f"Lỗi định dạng JSON: {error}")
            return None

        except OSError as error:
            print(f"Lỗi đọc file: {error}")
            return None

    # ==================================================
    # HÀM HỖ TRỢ 2: LƯU FILE JSON
    # ==================================================

    """Lưu danh sách hồ sơ khám bệnh vào JSON."""
    def _save_medical_records(self):

        temp_file = self.medical_record_file.with_name(self.medical_record_file.name + ".tmp")

        try:
            data = {
                "medical_records": [
                    {
                        "record_id": record.record_id,
                        "patient_id": record.patient_id,
                        "doctor_id": record.doctor_id,
                        "visit_date": record.visit_date.isoformat(),
                        "diagnosis": record.diagnosis,
                        "fee_at_visit": record.fee_at_visit
                    }
                    for record in self.medical_records
                ]
            }

            # Ghi dữ liệu vào file tạm trước
            with open(temp_file, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)

            # Ghi thành công mới thay thế file chính
            temp_file.replace(self.medical_record_file)

            return True

        except (OSError, TypeError, ValueError, AttributeError) as error:
            print(f"Lỗi lưu hồ sơ khám bệnh: {error}")

            # Xóa file tạm nếu có lỗi
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except OSError:
                    pass

            return False

    # ==================================================
    # HÀM HỖ TRỢ 3: ĐỌC DỮ LIỆU TỪ JSON
    # ==================================================

    """Chuyển dữ liệu JSON thành danh sách MedicalRecord."""
    def _load_medical_records(self):

        data = self._read_json()

        if data is None:
            return

        records_data = data.get("medical_records", [])

        if not isinstance(records_data, list):
            print("Dữ liệu medical_records phải là một danh sách.")
            return

        loaded_records = []

        for item in records_data:
            try:
                if not isinstance(item, dict):
                    raise TypeError("Dữ liệu hồ sơ không hợp lệ.")

                # Chuyển chuỗi ngày thành đối tượng date
                visit_date = date.fromisoformat(item["visit_date"])

                # Tạo đối tượng MedicalRecord
                record = MedicalRecord(
                    item["record_id"],
                    item["patient_id"],
                    item["doctor_id"],
                    visit_date,
                    item["diagnosis"],
                    item.get("fee_at_visit")
                )

                # Kiểm tra thông tin hồ sơ
                if not record.validate():
                    print(f"Bỏ qua hồ sơ không hợp lệ: {item.get('record_id')}")
                    continue

                # Kiểm tra mã hồ sơ trùng
                if any(old.record_id == record.record_id for old in loaded_records):
                    print(f"Bỏ qua hồ sơ trùng mã: {record.record_id}")
                    continue

                loaded_records.append(record)

            except (KeyError, TypeError, ValueError, AttributeError) as error:
                print(f"Lỗi đọc một hồ sơ: {error}")

        self.medical_records = loaded_records

        print(f"Đã tải {len(self.medical_records)} hồ sơ khám bệnh.")

    # ==================================================
    # 1. CREATE MEDICAL RECORD
    # ==================================================

    """Thêm hồ sơ khám bệnh mới."""
    def create_medical_record(self, record: MedicalRecord) -> None:

        try:
            # Kiểm tra kiểu dữ liệu
            if not isinstance(record, MedicalRecord):
                raise TypeError("Dữ liệu phải là đối tượng MedicalRecord.")

            # Kiểm tra thông tin hồ sơ
            if not record.validate():
                raise ValueError("Thông tin hồ sơ không hợp lệ.")

            # Kiểm tra mã hồ sơ đã tồn tại chưa
            for item in self.medical_records:
                if item.record_id == record.record_id:
                    raise ValueError(f"Mã hồ sơ {record.record_id} đã tồn tại.")

            # Kiểm tra bệnh nhân và bác sĩ
            if not self.validate_relations(record):
                raise ValueError("Bệnh nhân hoặc bác sĩ không tồn tại.")

            # Thêm hồ sơ vào danh sách
            self.medical_records.append(record)

            # Lưu vào JSON
            if not self._save_medical_records():
                self.medical_records.remove(record)
                print("Không thể lưu hồ sơ vào JSON.")
                return

            print("Thêm hồ sơ khám bệnh thành công.")

        except (TypeError, ValueError, AttributeError) as error:
            print(f"Lỗi thêm hồ sơ: {error}")

    # ==================================================
    # 2. UPDATE MEDICAL RECORD
    # ==================================================

    """Cập nhật thông tin hồ sơ khám bệnh."""
    def update_medical_record(self, record_id: str, changes: dict) -> bool:

        try:
            if not isinstance(changes, dict):
                raise TypeError("changes phải là dictionary.")

            # Tìm hồ sơ cần cập nhật
            record = next((item for item in self.medical_records if item.record_id == record_id), None)

            if record is None:
                print("Không tìm thấy hồ sơ cần cập nhật.")
                return False

            # Những trường được phép cập nhật
            allowed_fields = {"doctor_id", "visit_date", "diagnosis", "fee_at_visit"}

            # Kiểm tra các trường cập nhật
            for field in changes:
                if field not in allowed_fields:
                    raise ValueError(f"Không thể cập nhật trường: {field}")

            if not changes:
                print("Không có thông tin cần cập nhật.")
                return False

            # Lấy thông tin hiện tại
            new_doctor_id = record.doctor_id
            new_visit_date = record.visit_date
            new_diagnosis = record.diagnosis
            new_fee = record.fee_at_visit

            # Cập nhật thông tin mới
            if "doctor_id" in changes:
                new_doctor_id = changes["doctor_id"]

            if "visit_date" in changes:
                new_visit_date = changes["visit_date"]

                # Nếu ngày khám là chuỗi thì chuyển thành date
                if isinstance(new_visit_date, str):
                    new_visit_date = date.fromisoformat(new_visit_date)

            if "diagnosis" in changes:
                new_diagnosis = changes["diagnosis"]

            if "fee_at_visit" in changes:
                new_fee = changes["fee_at_visit"]

            # Tạo đối tượng tạm để kiểm tra dữ liệu mới
            updated_record = MedicalRecord(
                record.record_id,
                record.patient_id,
                new_doctor_id,
                new_visit_date,
                new_diagnosis,
                new_fee
            )

            if not updated_record.validate():
                raise ValueError("Thông tin cập nhật không hợp lệ.")

            # Kiểm tra quan hệ bệnh nhân và bác sĩ
            if not self.validate_relations(updated_record):
                raise ValueError("Bệnh nhân hoặc bác sĩ không tồn tại.")

            # Lưu dữ liệu cũ để khôi phục nếu lưu thất bại
            old_values = (record.doctor_id, record.visit_date, record.diagnosis, record.fee_at_visit)

            # Cập nhật object
            record.doctor_id = new_doctor_id
            record.visit_date = new_visit_date
            record.diagnosis = new_diagnosis
            record.fee_at_visit = new_fee

            # Lưu vào JSON
            if not self._save_medical_records():

                # Khôi phục dữ liệu cũ
                record.doctor_id = old_values[0]
                record.visit_date = old_values[1]
                record.diagnosis = old_values[2]
                record.fee_at_visit = old_values[3]

                return False

            print("Cập nhật hồ sơ thành công.")
            return True

        except (TypeError, ValueError, AttributeError) as error:
            print(f"Lỗi cập nhật hồ sơ: {error}")
            return False

    # ==================================================
    # 3. ASSIGN DOCTOR
    # ==================================================

    """Phân công bác sĩ cho hồ sơ khám bệnh."""
    def assign_doctor(self, record_id: str, doctor_id: str) -> bool:

        try:
            # Tìm hồ sơ
            record = next((item for item in self.medical_records if item.record_id == record_id), None)

            if record is None:
                print("Không tìm thấy hồ sơ.")
                return False

            # Kiểm tra bác sĩ
            doctor_exists = any(doctor.doctor_id == doctor_id for doctor in self.doctors)

            if not doctor_exists:
                print("Không tìm thấy bác sĩ.")
                return False

            # Lưu mã bác sĩ cũ
            old_doctor_id = record.doctor_id

            # Gán bác sĩ mới
            record.doctor_id = doctor_id

            # Lưu thay đổi vào JSON
            if not self._save_medical_records():
                record.doctor_id = old_doctor_id
                return False

            print("Phân công bác sĩ thành công.")
            return True

        except (TypeError, ValueError, AttributeError) as error:
            print(f"Lỗi phân công bác sĩ: {error}")
            return False

    # ==================================================
    # 4. FIND MEDICAL RECORDS
    # ==================================================

    """Tìm kiếm hồ sơ khám bệnh."""
    def find_medical_records(self, keyword: str, search_type: str) -> list[MedicalRecord]:

        try:
            if not isinstance(keyword, str):
                raise TypeError("keyword phải là chuỗi.")

            if not isinstance(search_type, str):
                raise TypeError("search_type phải là chuỗi.")

            keyword = keyword.strip().casefold()
            search_type = search_type.strip().casefold()

            if not keyword:
                print("Từ khóa tìm kiếm không được để trống.")
                return []

            # Các kiểu tìm kiếm được hỗ trợ
            allowed_types = {"record_id", "patient_id", "patient_name", "doctor_id", "doctor_name"}

            if search_type not in allowed_types:
                raise ValueError("Loại tìm kiếm không hợp lệ.")

            results = []

            # Duyệt từng hồ sơ
            for record in self.medical_records:
                value = ""

                if search_type == "record_id":
                    value = record.record_id

                elif search_type == "patient_id":
                    value = record.patient_id

                elif search_type == "doctor_id":
                    value = record.doctor_id

                elif search_type == "patient_name":

                    # Tìm bệnh nhân theo mã bệnh nhân
                    patient = next((item for item in self.patients if item.patient_id == record.patient_id), None)

                    if patient is not None:
                        value = patient.full_name

                elif search_type == "doctor_name":

                    # Tìm bác sĩ theo mã bác sĩ
                    doctor = next((item for item in self.doctors if item.doctor_id == record.doctor_id), None)

                    if doctor is not None:
                        value = doctor.full_name

                # So sánh từ khóa không phân biệt chữ hoa, chữ thường
                if keyword in str(value).casefold():
                    results.append(record)

            print(f"Tìm thấy {len(results)} hồ sơ.")

            return results

        except (TypeError, ValueError, AttributeError) as error:
            print(f"Lỗi tìm kiếm: {error}")
            return []

    # ==================================================
    # 5. SORT MEDICAL RECORDS
    # ==================================================

    """Sắp xếp hồ sơ theo ngày khám hoặc chi phí."""
    def sort_medical_records(self, criteria: str, descending: bool) -> list[MedicalRecord]:

        try:
            if not isinstance(criteria, str):
                raise TypeError("criteria phải là chuỗi.")

            if not isinstance(descending, bool):
                raise TypeError("descending phải là True hoặc False.")

            criteria = criteria.strip().casefold()

            # Kiểm tra tiêu chí sắp xếp
            if criteria not in {"visit_date", "fee_at_visit"}:
                raise ValueError("Tiêu chí sắp xếp không hợp lệ.")

            # Sao chép danh sách để không thay đổi danh sách gốc
            records = self.medical_records.copy()

            if criteria == "visit_date":

                # Sắp xếp theo ngày khám
                records.sort(key=lambda item: item.visit_date, reverse=descending)

            elif criteria == "fee_at_visit":

                # Những hồ sơ có chi phí
                records_with_fee = [item for item in records if item.fee_at_visit is not None]

                # Những hồ sơ chưa có chi phí
                records_without_fee = [item for item in records if item.fee_at_visit is None]

                # Sắp xếp theo chi phí
                records_with_fee.sort(key=lambda item: item.fee_at_visit, reverse=descending)

                # Hồ sơ chưa có chi phí luôn nằm cuối
                records = records_with_fee + records_without_fee

            return records

        except (TypeError, ValueError, AttributeError) as error:
            print(f"Lỗi sắp xếp: {error}")
            return []

    # ==================================================
    # 6. DISPLAY MEDICAL RECORDS
    # ==================================================

    """Hiển thị danh sách hồ sơ khám bệnh."""
    def display_medical_records(self, records=None) -> bool:

        try:
            rows = self.medical_records if records is None else records
            if not rows:
                print("Chưa có hồ sơ khám bệnh.")
                return False

            print("\n=== DANH SÁCH HỒ SƠ KHÁM BỆNH ===")
            headers = (
                "STT",
                "Mã hồ sơ",
                "Mã bệnh nhân",
                "Mã bác sĩ",
                "Ngày khám",
                "Chẩn đoán",
                "Chi phí (đồng)",
            )
            data = []
            for index, record in enumerate(rows, 1):
                fee = (
                    f"{record.fee_at_visit:,.0f}"
                    if record.fee_at_visit is not None
                    else "Chưa có"
                )
                data.append(
                    (
                        str(index),
                        record.record_id,
                        record.patient_id,
                        record.doctor_id,
                        record.visit_date.isoformat(),
                        record.diagnosis,
                        fee,
                    )
                )

            widths = [
                max(len(header), *(len(row[column]) for row in data))
                for column, header in enumerate(headers)
            ]
            border = "+" + "+".join("-" * (width + 2) for width in widths) + "+"

            def format_row(cells):
                formatted = [
                    cell.rjust(width) if column in (0, 6) else cell.ljust(width)
                    for column, (cell, width) in enumerate(zip(cells, widths))
                ]
                return "| " + " | ".join(formatted) + " |"

            print(border)
            print(format_row(headers))
            print(border)
            for row in data:
                print(format_row(row))
            print(border)
            print(f"Tổng số hồ sơ: {len(rows)}")
            return True

        except (TypeError, ValueError, AttributeError) as error:
            print(f"Lỗi hiển thị hồ sơ: {error}")
            return False

    # ==================================================
    # 7. VALIDATE RELATIONS
    # ==================================================

    """Kiểm tra bệnh nhân và bác sĩ có tồn tại không."""
    def validate_relations(self, record: MedicalRecord) -> bool:

        try:
            if not isinstance(record, MedicalRecord):
                return False

            # Kiểm tra bệnh nhân
            patient_exists = any(patient.patient_id == record.patient_id for patient in self.patients)

            # Kiểm tra bác sĩ
            doctor_exists = any(doctor.doctor_id == record.doctor_id for doctor in self.doctors)

            if not patient_exists:
                print(f"Không tồn tại bệnh nhân: {record.patient_id}")

            if not doctor_exists:
                print(f"Không tồn tại bác sĩ: {record.doctor_id}")

            return patient_exists and doctor_exists

        except (TypeError, ValueError, AttributeError) as error:
            print(f"Lỗi kiểm tra quan hệ: {error}")
            return False