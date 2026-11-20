"""Giao diện console: nhập lựa chọn và gọi các manager/service hiện có."""

import json
from datetime import date
from pathlib import Path

from managers.doctor_manager import DoctorManager
from managers.medical_record_manager import PatientManager as RecordManager
from managers.patient_manager import PatientManager
from models.doctor import Doctor
from models.medical_record import MedicalRecord
from models.patient import Inpatient, Outpatient
from services.statistics import format_report, generate_statistical_report


DATA_DIR = Path(__file__).resolve().parent / "data"


def _read(filename):
    path = DATA_DIR / filename
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (FileNotFoundError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Không đọc được dữ liệu: {path}") from error


def _load_managers():
    patients = []
    for row in _read("patients.json"):
        common = [row[key] for key in ("patient_id", "full_name", "birth_year", "phone")]
        if row["patient_type"] == "inpatient":
            admission = date.fromisoformat(row["admission_date"])
            patient = Inpatient(*common, min(admission, date.today()),
                                row["daily_fee"], row["days_stayed"])
            # Dữ liệu mẫu có ngày tương lai; giữ nguyên ngày gốc khi nạp.
            patient._admission_date = admission
        else:
            patient = Outpatient(*common, row["consultation_fee"])
        patients.append(patient)

    patient_manager = PatientManager(patients)
    doctor_manager = DoctorManager()
    record_manager = RecordManager(patient_manager.patients, doctor_manager.get_all())
    record_manager.medical_records = [
        MedicalRecord(row["record_id"], row["patient_id"], row["doctor_id"],
                      date.fromisoformat(row["visit_date"]), row["diagnosis"],
                      row.get("fee_at_visit"))
        for row in _read("sample_data.json").get("medical_records", [])
    ]
    doctor_manager.set_record_checker(
        lambda doctor_id: any(r.doctor_id == doctor_id for r in record_manager.medical_records)
    )
    return patient_manager, doctor_manager, record_manager


def _call(action):
    try:
        action()
    except (ValueError, KeyError, TypeError, AttributeError) as error:
        print(f"Lỗi: {error}")


def _add_patient(manager):
    kind = input("Loại (1 nội trú, 2 ngoại trú): ").strip()
    patient_id = input("Mã BN: ").strip()
    name = input("Họ tên: ").strip()
    year = int(input("Năm sinh: ").strip())
    phone = input("Điện thoại: ").strip()
    if kind == "1":
        patient = Inpatient(patient_id, name, year, phone,
            date.fromisoformat(input("Ngày nhập viện YYYY-MM-DD: ").strip()),
            float(input("Phí mỗi ngày: ").strip()), int(input("Số ngày nằm viện: ").strip()))
    elif kind == "2":
        patient = Outpatient(patient_id, name, year, phone, float(input("Phí khám: ").strip()))
    else:
        raise ValueError("Loại bệnh nhân chỉ nhận 1 hoặc 2.")
    manager.add_patient(patient)


def _patient_menu(manager, records):
    while True:
        print("\nBỆNH NHÂN: 1 xem | 2 thêm | 3 sửa JSON | 4 xóa | 5 tìm | 6 sắp xếp | 0 quay lại")
        choice = input("Chọn: ").strip()
        if choice == "0": return
        if choice == "1": _call(manager.display_patients)
        elif choice == "2": _call(lambda: _add_patient(manager))
        elif choice == "3":
            def update():
                patient_id = input("Mã BN: ").strip()
                changes = json.loads(input('Trường sửa, ví dụ {"full_name":"Tên mới"}: '))
                for key in ("birth_year", "days_stayed"):
                    if key in changes: changes[key] = int(changes[key])
                for key in ("daily_fee", "consultation_fee"):
                    if key in changes: changes[key] = float(changes[key])
                if "admission_date" in changes:
                    changes["admission_date"] = date.fromisoformat(changes["admission_date"])
                manager.update_patient(patient_id, changes)
            _call(update)
        elif choice == "4":
            _call(lambda: print("Đã xóa." if manager.delete_patient(
                input("Mã BN: ").strip(), records.medical_records) else "Không tìm thấy bệnh nhân."))
        elif choice == "5":
            def search():
                kind = input("Tìm theo id/name/all: ").strip()
                results = manager.find_patients(input("Từ khóa: ").strip(), kind)
                for patient in results: print(patient.display_info())
            _call(search)
        elif choice == "6":
            def sort():
                kind = input("Sắp xếp theo name/fee: ").strip()
                desc = input("Giảm dần? y/n: ").strip().casefold() == "y"
                for patient in manager.sort_patients(kind, desc): print(patient.display_info())
            _call(sort)
        else: print("Lựa chọn không hợp lệ.")


def _doctor_menu(manager, records):
    while True:
        print("\nBÁC SĨ: 1 xem | 2 thêm | 3 sửa JSON | 4 xóa | 5 tìm | 0 quay lại")
        choice = input("Chọn: ").strip()
        if choice == "0": return
        if choice == "1": _call(manager.display_doctors)
        elif choice == "2":
            def add():
                manager.add_doctor(Doctor(input("Mã BS: ").strip(), input("Họ tên: ").strip(),
                                          input("Chuyên khoa: ").strip()))
                records.doctors = manager.get_all()
            _call(add)
        elif choice == "3":
            def update():
                doctor_id = input("Mã BS: ").strip()
                manager.update_doctor(doctor_id, json.loads(input('Trường sửa, ví dụ {"specialty":"Nhi khoa"}: ')))
            _call(update)
        elif choice == "4":
            def delete():
                if manager.delete_doctor(input("Mã BS: ").strip(), records.medical_records):
                    records.doctors = manager.get_all()
                    print("Đã xóa.")
                else: print("Không tìm thấy bác sĩ.")
            _call(delete)
        elif choice == "5":
            def search():
                kind, key = input("Tìm theo id/name/specialty: ").strip(), input("Từ khóa: ").strip()
                result = (manager.find_by_id(key) if kind == "id" else
                          manager.find_by_name(key) if kind == "name" else
                          manager.find_by_specialty(key) if kind == "specialty" else None)
                manager.display_doctors([result] if isinstance(result, Doctor) else result or [])
            _call(search)
        else: print("Lựa chọn không hợp lệ.")


def _record_menu(manager):
    while True:
        print("\nHỒ SƠ: 1 xem | 2 thêm | 3 sửa JSON | 4 phân công | 5 xóa | 6 tìm | 7 sắp xếp | 0 quay lại")
        choice = input("Chọn: ").strip()
        if choice == "0": return
        if choice == "1": _call(manager.display_medical_records)
        elif choice == "2":
            def add():
                record = MedicalRecord(input("Mã hồ sơ: ").strip(), input("Mã BN: ").strip(),
                    input("Mã BS: ").strip(), date.fromisoformat(input("Ngày YYYY-MM-DD: ").strip()),
                    input("Chẩn đoán: ").strip(), float(input("Phí (0 nếu chưa có): ").strip()))
                manager.create_medical_record(record)
            _call(add)
        elif choice == "3":
            def update():
                record_id = input("Mã hồ sơ: ").strip()
                changes = json.loads(input('Trường sửa, ví dụ {"diagnosis":"Chẩn đoán mới"}: '))
                if "visit_date" in changes:
                    changes["visit_date"] = date.fromisoformat(changes["visit_date"])
                if "fee_at_visit" in changes and changes["fee_at_visit"] is not None:
                    changes["fee_at_visit"] = float(changes["fee_at_visit"])
                manager.update_medical_record(record_id, changes)
            _call(update)
        elif choice == "4":
            _call(lambda: manager.assign_doctor(input("Mã hồ sơ: ").strip(), input("Mã BS: ").strip()))
        elif choice == "5":
            delete = getattr(manager, "delete_medical_record", None)
            if delete is None: print("Manager hồ sơ chưa có chức năng xóa; người phụ trách module sẽ bổ sung.")
            else: _call(lambda: delete(input("Mã hồ sơ: ").strip()))
        elif choice == "6":
            def search():
                kind = input("record_id/patient_id/patient_name/doctor_id/doctor_name: ").strip()
                for record in manager.find_medical_records(input("Từ khóa: ").strip(), kind):
                    print(record.display_info())
            _call(search)
        elif choice == "7":
            def sort():
                kind = input("Sắp xếp theo visit_date/fee_at_visit: ").strip()
                desc = input("Giảm dần? y/n: ").strip().casefold() == "y"
                for record in manager.sort_medical_records(kind, desc): print(record.display_info())
            _call(sort)
        else: print("Lựa chọn không hợp lệ.")


def main():
    patients, doctors, records = _load_managers()
    while True:
        print("\n1. Bệnh nhân\n2. Bác sĩ\n3. Hồ sơ khám\n4. Báo cáo thống kê\n0. Thoát")
        choice = input("Chọn: ").strip()
        if choice == "1": _patient_menu(patients, records)
        elif choice == "2": _doctor_menu(doctors, records)
        elif choice == "3": _record_menu(records)
        elif choice == "4":
            _call(lambda: print(format_report(generate_statistical_report(
                patients.patients, doctors.get_all(), records.medical_records))))
        elif choice == "0": break
        else: print("Lựa chọn không hợp lệ.")
    print("Đã thoát chương trình.")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError) as error:
        print(f"Lỗi dữ liệu: {error}")
