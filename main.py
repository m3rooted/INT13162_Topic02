"""Giao diện console: hiển thị menu và gọi các manager/service hiện có."""

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
    """Nạp dữ liệu ban đầu và kết nối các manager với nhau."""
    patients = []
    for row in _read("patients.json"):
        common = [row[key] for key in ("patient_id", "full_name", "birth_year", "phone")]
        if row["patient_type"] == "inpatient":
            admission = date.fromisoformat(row["admission_date"])
            patient = Inpatient(
                *common,
                min(admission, date.today()),
                row["daily_fee"],
                row["days_stayed"],
            )
            # Dữ liệu mẫu có ngày tương lai; giữ nguyên ngày gốc khi nạp.
            patient._admission_date = admission
        else:
            patient = Outpatient(*common, row["consultation_fee"])
        patients.append(patient)

    patient_manager = PatientManager(patients)
    doctor_manager = DoctorManager()
    record_manager = RecordManager(patient_manager.patients, doctor_manager.get_all())
    record_manager.medical_records = [
        MedicalRecord(
            row["record_id"],
            row["patient_id"],
            row["doctor_id"],
            date.fromisoformat(row["visit_date"]),
            row["diagnosis"],
            row.get("fee_at_visit"),
        )
        for row in _read("sample_data.json").get("medical_records", [])
    ]
    doctor_manager.set_record_checker(
        lambda doctor_id: any(
            record.doctor_id == doctor_id
            for record in record_manager.medical_records
        )
    )
    return patient_manager, doctor_manager, record_manager


def _call(action):
    """Chuyển lỗi nhập liệu/nghiệp vụ thành thông báo trên menu."""
    try:
        action()
    except (ValueError, KeyError, TypeError, AttributeError) as error:
        print(f"Lỗi: {error}")


def _run_menu(title, actions, exit_label="Quay lại"):
    """Hiển thị menu và gọi hàm tương ứng với lựa chọn của người dùng."""
    while True:
        print(f"\n{title}")
        for choice, (label, _) in actions.items():
            print(f"{choice}. {label}")
        print(f"0. {exit_label}")

        choice = input("Chọn: ").strip()
        if choice == "0":
            return

        action = actions.get(choice)
        if action is None:
            print("Lựa chọn không hợp lệ.")
            continue
        _call(action[1])


# --------------------------- BỆNH NHÂN ---------------------------

def _add_patient(manager):
    kind = input("Loại (1 nội trú, 2 ngoại trú): ").strip()
    patient_id = input("Mã BN: ").strip()
    name = input("Họ tên: ").strip()
    year = int(input("Năm sinh: ").strip())
    phone = input("Điện thoại: ").strip()

    if kind == "1":
        patient = Inpatient(
            patient_id,
            name,
            year,
            phone,
            date.fromisoformat(input("Ngày nhập viện YYYY-MM-DD: ").strip()),
            float(input("Phí mỗi ngày: ").strip()),
            int(input("Số ngày nằm viện: ").strip()),
        )
    elif kind == "2":
        patient = Outpatient(
            patient_id,
            name,
            year,
            phone,
            float(input("Phí khám: ").strip()),
        )
    else:
        raise ValueError("Loại bệnh nhân chỉ nhận 1 hoặc 2.")

    manager.add_patient(patient)


def _update_patient(manager):
    patient_id = input("Mã BN: ").strip()
    changes = json.loads(input('Trường sửa, ví dụ {"full_name":"Tên mới"}: '))
    for key in ("birth_year", "days_stayed"):
        if key in changes:
            changes[key] = int(changes[key])
    for key in ("daily_fee", "consultation_fee"):
        if key in changes:
            changes[key] = float(changes[key])
    if "admission_date" in changes:
        changes["admission_date"] = date.fromisoformat(changes["admission_date"])
    manager.update_patient(patient_id, changes)


def _delete_patient(manager, records):
    patient_id = input("Mã BN: ").strip()
    deleted = manager.delete_patient(patient_id, records.medical_records)
    print("Đã xóa." if deleted else "Không tìm thấy bệnh nhân.")


def _search_patients(manager):
    kind = input("Tìm theo id/name/all: ").strip()
    keyword = input("Từ khóa: ").strip()
    results = manager.find_patients(keyword, kind)
    if not results:
        print("Không tìm thấy bệnh nhân.")
        return
    for patient in results:
        print(patient.display_info())


def _sort_patients(manager):
    kind = input("Sắp xếp theo name/fee: ").strip()
    descending = input("Giảm dần? y/n: ").strip().casefold() == "y"
    for patient in manager.sort_patients(kind, descending):
        print(patient.display_info())


def _patient_menu(manager, records):
    _run_menu(
        "BỆNH NHÂN",
        {
            "1": ("Xem danh sách", manager.display_patients),
            "2": ("Thêm", lambda: _add_patient(manager)),
            "3": ("Cập nhật", lambda: _update_patient(manager)),
            "4": ("Xóa", lambda: _delete_patient(manager, records)),
            "5": ("Tìm kiếm", lambda: _search_patients(manager)),
            "6": ("Sắp xếp", lambda: _sort_patients(manager)),
        },
    )


# ---------------------------- BÁC SĨ ----------------------------

def _add_doctor(manager, records):
    doctor = Doctor(
        input("Mã BS: ").strip(),
        input("Họ tên: ").strip(),
        input("Chuyên khoa: ").strip(),
    )
    manager.add_doctor(doctor)
    records.doctors = manager.get_all()


def _update_doctor(manager):
    doctor_id = input("Mã BS: ").strip()
    changes = json.loads(input('Trường sửa, ví dụ {"specialty":"Nhi khoa"}: '))
    manager.update_doctor(doctor_id, changes)


def _delete_doctor(manager, records):
    doctor_id = input("Mã BS: ").strip()
    deleted = manager.delete_doctor(doctor_id, records.medical_records)
    if deleted:
        records.doctors = manager.get_all()
        print("Đã xóa.")
    else:
        print("Không tìm thấy bác sĩ.")


def _search_doctors(manager):
    kind = input("Tìm theo id/name/specialty: ").strip()
    keyword = input("Từ khóa: ").strip()
    if kind == "id":
        result = manager.find_by_id(keyword)
        results = [result] if result is not None else []
    elif kind == "name":
        results = manager.find_by_name(keyword)
    elif kind == "specialty":
        results = manager.find_by_specialty(keyword)
    else:
        raise ValueError("Tiêu chí tìm kiếm chỉ nhận id, name hoặc specialty.")
    manager.display_doctors(results)


def _doctor_menu(manager, records):
    _run_menu(
        "BÁC SĨ",
        {
            "1": ("Xem danh sách", manager.display_doctors),
            "2": ("Thêm", lambda: _add_doctor(manager, records)),
            "3": ("Cập nhật", lambda: _update_doctor(manager)),
            "4": ("Xóa", lambda: _delete_doctor(manager, records)),
            "5": ("Tìm kiếm", lambda: _search_doctors(manager)),
        },
    )


# ------------------------- HỒ SƠ KHÁM -------------------------

def _add_record(manager):
    record = MedicalRecord(
        input("Mã hồ sơ: ").strip(),
        input("Mã BN: ").strip(),
        input("Mã BS: ").strip(),
        date.fromisoformat(input("Ngày YYYY-MM-DD: ").strip()),
        input("Chẩn đoán: ").strip(),
        float(input("Phí (0 nếu chưa có): ").strip()),
    )
    manager.create_medical_record(record)


def _update_record(manager):
    record_id = input("Mã hồ sơ: ").strip()
    changes = json.loads(input('Trường sửa, ví dụ {"diagnosis":"Chẩn đoán mới"}: '))
    if "visit_date" in changes:
        changes["visit_date"] = date.fromisoformat(changes["visit_date"])
    if "fee_at_visit" in changes and changes["fee_at_visit"] is not None:
        changes["fee_at_visit"] = float(changes["fee_at_visit"])
    manager.update_medical_record(record_id, changes)


def _assign_doctor(manager):
    record_id = input("Mã hồ sơ: ").strip()
    doctor_id = input("Mã BS: ").strip()
    manager.assign_doctor(record_id, doctor_id)


def _search_records(manager):
    kind = input(
        "record_id/patient_id/patient_name/doctor_id/doctor_name: "
    ).strip()
    keyword = input("Từ khóa: ").strip()
    results = manager.find_medical_records(keyword, kind)
    if not results:
        print("Không tìm thấy hồ sơ.")
        return
    for record in results:
        print(record.display_info())


def _sort_records(manager):
    kind = input("Sắp xếp theo visit_date/fee_at_visit: ").strip()
    descending = input("Giảm dần? y/n: ").strip().casefold() == "y"
    for record in manager.sort_medical_records(kind, descending):
        print(record.display_info())


def _record_menu(manager):
    _run_menu(
        "HỒ SƠ KHÁM",
        {
            "1": ("Xem danh sách", manager.display_medical_records),
            "2": ("Thêm", lambda: _add_record(manager)),
            "3": ("Cập nhật", lambda: _update_record(manager)),
            "4": ("Phân công bác sĩ", lambda: _assign_doctor(manager)),
            "5": ("Tìm kiếm", lambda: _search_records(manager)),
            "6": ("Sắp xếp", lambda: _sort_records(manager)),
        },
    )


# ---------------------------- BÁO CÁO ----------------------------

def _show_report(patients, doctors, records):
    report = generate_statistical_report(
        patients.patients,
        doctors.get_all(),
        records.medical_records,
    )
    report_text = format_report(report)
    visible_lines = [
        line
        for line in report_text.splitlines()
        if not line.startswith("Tổng phí ghi nhận tại các lượt khám:")
    ]
    print("\n".join(visible_lines))


def main():
    patients, doctors, records = _load_managers()
    _run_menu(
        "QUẢN LÝ BỆNH VIỆN",
        {
            "1": ("Bệnh nhân", lambda: _patient_menu(patients, records)),
            "2": ("Bác sĩ", lambda: _doctor_menu(doctors, records)),
            "3": ("Hồ sơ khám", lambda: _record_menu(records)),
            "4": ("Báo cáo thống kê", lambda: _show_report(patients, doctors, records)),
        },
        exit_label="Thoát",
    )
    print("Đã thoát chương trình.")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError) as error:
        print(f"Lỗi dữ liệu: {error}")
