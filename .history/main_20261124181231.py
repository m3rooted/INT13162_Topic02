"""Giao diện console: hiển thị menu và gọi các manager/service hiện có."""

import json
from datetime import date
from pathlib import Path

from managers.doctor_manager import DoctorManager
from managers.medical_record_manager import MedicalRecordManager as RecordManager
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
            # Giới hạn ngày mẫu ở hôm nay để giữ đúng validation của model.
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

        choice = input("Mời bạn chọn chức năng: ").strip()
        if choice == "0":
            return

        action = actions.get(choice)
        if action is None:
            print("Lựa chọn không hợp lệ.")
            continue
        _call(action[1])


# --------------------------- BỆNH NHÂN ---------------------------

def _add_patient(manager):
    kind = input("Chọn loại bệnh nhân (1 - Nội trú, 2 - Ngoại trú): ").strip()
    patient_id = input("Nhập mã bệnh nhân: ").strip()
    name = input("Nhập họ và tên bệnh nhân: ").strip()
    year = int(input("Nhập năm sinh: ").strip())
    phone = input("Nhập số điện thoại: ").strip()

    if kind == "1":
        patient = Inpatient(
            patient_id,
            name,
            year,
            phone,
            date.fromisoformat(
                input("Nhập ngày nhập viện (định dạng YYYY-MM-DD): ").strip()
            ),
            float(input("Nhập phí nằm viện mỗi ngày: ").strip()),
            int(input("Nhập số ngày nằm viện: ").strip()),
        )
    elif kind == "2":
        patient = Outpatient(
            patient_id,
            name,
            year,
            phone,
            float(input("Nhập phí khám ngoại trú: ").strip()),
        )
    else:
        raise ValueError("Loại bệnh nhân chỉ nhận 1 hoặc 2.")

    manager.add_patient(patient)
    print("Thêm bệnh nhân thành công.")


def _update_patient(manager):
    patient_id = input("Nhập mã bệnh nhân cần cập nhật: ").strip()
    column = input(
        "Nhập tên cột cần sửa: "
    ).strip()
    field = {
        "họ tên": "full_name",
        "năm sinh": "birth_year",
        "số điện thoại": "phone",
        "ngày nhập viện": "admission_date",
        "phí mỗi ngày": "daily_fee",
        "số ngày nằm viện": "days_stayed",
        "phí khám": "consultation_fee",
    }.get(column.casefold(), column)
    new_value = input(
        "Nhập giá trị mới (ngày theo YYYY-MM-DD; trường số chỉ nhập số): "
    ).strip()

    if field in ("birth_year", "days_stayed"):
        new_value = int(new_value)
    elif field in ("daily_fee", "consultation_fee"):
        new_value = float(new_value)
    elif field == "admission_date":
        new_value = date.fromisoformat(new_value)

    changes = {field: new_value}
    if manager.update_patient(patient_id, changes):
        print("Cập nhật bệnh nhân thành công.")


def _delete_patient(manager, records):
    patient_id = input("Nhập mã bệnh nhân cần xóa: ").strip()
    deleted = manager.delete_patient(patient_id, records.medical_records)
    print("Xóa bệnh nhân thành công." if deleted else "Không tìm thấy bệnh nhân.")


def _show_patients(manager):
    if manager.display_patients():
        print("Hiển thị danh sách bệnh nhân thành công.")


def _search_patients(manager):
    kind = input(
        "Bạn muốn tìm theo tiêu chí nào? Nhập id (mã), name (họ tên) "
        "hoặc all (cả mã và họ tên): "
    ).strip()
    keyword = input("Nhập mã hoặc tên bệnh nhân cần tìm: ").strip()
    results = manager.find_patients(keyword, kind)
    if not results:
        print("Không tìm thấy bệnh nhân.")
        return
    if manager.display_patients(results):
        print(f"Tìm kiếm bệnh nhân thành công. Tìm thấy {len(results)} kết quả.")


def _sort_patients(manager):
    kind = input(
        "Sắp xếp bệnh nhân theo name (họ tên) hay fee (tổng phí)? "
        "Nhập name hoặc fee: "
    ).strip()
    descending = (
        input("Sắp xếp giảm dần? Nhập y (có) hoặc n (không): ")
        .strip()
        .casefold()
        == "y"
    )
    sorted_patients = manager.sort_patients(kind, descending)
    if manager.display_patients(sorted_patients):
        print("Sắp xếp danh sách bệnh nhân thành công.")


def _patient_menu(manager, records):
    _run_menu(
        "BỆNH NHÂN",
        {
            "1": ("Xem danh sách", lambda: _show_patients(manager)),
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
        input("Nhập mã bác sĩ: ").strip(),
        input("Nhập họ và tên bác sĩ: ").strip(),
        input("Nhập chuyên khoa: ").strip(),
    )
    manager.add_doctor(doctor)
    records.doctors = manager.get_all()
    print("Thêm bác sĩ thành công.")


def _update_doctor(manager):
    doctor_id = input("Nhập mã bác sĩ cần cập nhật: ").strip()
    column = input("Nhập tên cột cần sửa: Họ tên hoặc Chuyên khoa: ").strip()
    field = {
        "họ tên": "full_name",
        "chuyên khoa": "specialty",
    }.get(column.casefold(), column)
    new_value = input("Nhập giá trị mới cho thông tin vừa chọn: ").strip()
    changes = {field: new_value}
    if manager.update_doctor(doctor_id, changes):
        print("Cập nhật bác sĩ thành công.")


def _delete_doctor(manager, records):
    doctor_id = input("Nhập mã bác sĩ cần xóa: ").strip()
    deleted = manager.delete_doctor(doctor_id, records.medical_records)
    if deleted:
        records.doctors = manager.get_all()
        print("Xóa bác sĩ thành công.")
    else:
        print("Không tìm thấy bác sĩ.")


def _show_doctors(manager):
    if manager.display_doctors():
        print("Hiển thị danh sách bác sĩ thành công.")


def _search_doctors(manager):
    kind = input(
        "Bạn muốn tìm bác sĩ theo id (mã), name (họ tên) hay "
        "specialty (chuyên khoa)? Nhập một tiêu chí: "
    ).strip()
    keyword = input("Nhập thông tin cần tìm: ").strip()
    if kind == "id":
        result = manager.find_by_id(keyword)
        results = [result] if result is not None else []
    elif kind == "name":
        results = manager.find_by_name(keyword)
    elif kind == "specialty":
        results = manager.find_by_specialty(keyword)
    else:
        raise ValueError("Tiêu chí tìm kiếm chỉ nhận id, name hoặc specialty.")
    if not results:
        print("Không tìm thấy bác sĩ.")
        return
    if manager.display_doctors(results):
        print(f"Tìm kiếm bác sĩ thành công. Tìm thấy {len(results)} kết quả.")


def _doctor_menu(manager, records):
    _run_menu(
        "BÁC SĨ",
        {
            "1": ("Xem danh sách", lambda: _show_doctors(manager)),
            "2": ("Thêm", lambda: _add_doctor(manager, records)),
            "3": ("Cập nhật", lambda: _update_doctor(manager)),
            "4": ("Xóa", lambda: _delete_doctor(manager, records)),
            "5": ("Tìm kiếm", lambda: _search_doctors(manager)),
        },
    )


# ------------------------- HỒ SƠ KHÁM -------------------------

def _add_record(manager):
    record = MedicalRecord(
        input("Nhập mã hồ sơ khám: ").strip(),
        input("Nhập mã bệnh nhân của hồ sơ: ").strip(),
        input("Nhập mã bác sĩ phụ trách: ").strip(),
        date.fromisoformat(
            input("Nhập ngày khám (định dạng YYYY-MM-DD): ").strip()
        ),
        input("Nhập chẩn đoán: ").strip(),
        float(input("Nhập phí khám (nhập 0 nếu chưa có phí): ").strip()),
    )
    manager.create_medical_record(record)


def _update_record(manager):
    record_id = input("Nhập mã hồ sơ khám cần cập nhật: ").strip()
    column = input(
        "Nhập tên cột cần sửa: Mã bác sĩ, Ngày khám, Chẩn đoán "
        "hoặc Chi phí (đồng): "
    ).strip()
    field = {
        "mã bác sĩ": "doctor_id",
        "ngày khám": "visit_date",
        "chẩn đoán": "diagnosis",
        "chi phí (đồng)": "fee_at_visit",
    }.get(column.casefold(), column)
    new_value = input(
        "Nhập giá trị mới (nếu là ngày khám, dùng định dạng YYYY-MM-DD): "
    ).strip()

    if field == "visit_date":
        new_value = date.fromisoformat(new_value)
    elif field == "fee_at_visit":
        new_value = float(new_value)

    changes = {field: new_value}
    manager.update_medical_record(record_id, changes)


def _assign_doctor(manager):
    record_id = input("Nhập mã hồ sơ cần phân công bác sĩ: ").strip()
    doctor_id = input("Nhập mã bác sĩ sẽ phụ trách hồ sơ: ").strip()
    manager.assign_doctor(record_id, doctor_id)


def _search_records(manager):
    kind = input(
        "Bạn muốn tìm hồ sơ theo record_id (mã hồ sơ), patient_id (mã bệnh nhân), "
        "patient_name (tên bệnh nhân), doctor_id (mã bác sĩ) hay "
        "doctor_name (tên bác sĩ)? Nhập một tiêu chí: "
    ).strip()
    keyword = input("Nhập thông tin cần tìm: ").strip()
    results = manager.find_medical_records(keyword, kind)
    if not results:
        print("Không tìm thấy hồ sơ.")
        return
    if manager.display_medical_records(results):
        print(f"Tìm kiếm hồ sơ thành công. Tìm thấy {len(results)} kết quả.")


def _sort_records(manager):
    kind = input(
        "Sắp xếp hồ sơ theo visit_date (ngày khám) hay "
        "fee_at_visit (phí khám)? Nhập visit_date hoặc fee_at_visit: "
    ).strip()
    descending = (
        input("Sắp xếp giảm dần? Nhập y (có) hoặc n (không): ")
        .strip()
        .casefold()
        == "y"
    )
    sorted_records = manager.sort_medical_records(kind, descending)
    if sorted_records and manager.display_medical_records(sorted_records):
        print("Sắp xếp danh sách hồ sơ thành công.")


def _show_records(manager):
    if manager.display_medical_records():
        print("Hiển thị danh sách hồ sơ thành công.")


def _record_menu(manager):
    _run_menu(
        "HỒ SƠ KHÁM",
        {
            "1": ("Xem danh sách", lambda: _show_records(manager)),
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
    print("Tạo báo cáo thống kê thành công.")


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
