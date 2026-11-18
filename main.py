"""Chương trình console đọc và hiển thị dữ liệu mẫu của hệ thống."""

import json
from pathlib import Path


# Tạo đường dẫn từ vị trí của main.py để chương trình chạy được ở mọi thư mục hiện hành.
DATA_DIR = Path(__file__).resolve().parent / "data"


def load_json(filename):
    """Đọc JSON UTF-8; báo lỗi dễ hiểu nếu file thiếu hoặc nội dung không hợp lệ."""
    file_path = DATA_DIR / filename
    try:
        return json.loads(file_path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as error:
        raise RuntimeError(f"Không tìm thấy file dữ liệu: {file_path}") from error
    except json.JSONDecodeError as error:
        raise RuntimeError(f"File JSON không hợp lệ: {file_path}") from error


def show_patients(patients):
    """Hiển thị thông tin chung và loại bệnh nhân."""
    print("\n=== DANH SÁCH BỆNH NHÂN ===")
    for patient in patients:
        patient_type = "Nội trú" if patient["patient_type"] == "inpatient" else "Ngoại trú"
        print(
            f'{patient["patient_id"]} | {patient["full_name"]} | '
            f'{patient["birth_year"]} | {patient["phone"]} | {patient_type}'
        )
    print(f"Tổng số: {len(patients)} bệnh nhân")


def show_doctors(doctors):
    """Hiển thị mã, tên và chuyên khoa của từng bác sĩ."""
    print("\n=== DANH SÁCH BÁC SĨ ===")
    for doctor in doctors:
        print(
            f'{doctor["doctor_id"]} | {doctor["full_name"]} | '
            f'{doctor["specialty"]}'
        )
    print(f"Tổng số: {len(doctors)} bác sĩ")


def show_medical_records(records):
    """Hiển thị hồ sơ khám cùng mã bệnh nhân và bác sĩ liên quan."""
    print("\n=== HỒ SƠ KHÁM ===")
    for record in records:
        print(
            f'{record["record_id"]} | Ngày khám: {record["visit_date"]} | '
            f'Bệnh nhân: {record["patient_id"]} | Bác sĩ: {record["doctor_id"]} | '
            f'{record["diagnosis"]} | {record["fee_at_visit"]:,.0f} đồng'
        )
    print(f"Tổng số: {len(records)} hồ sơ")


def main():
    """Nạp dữ liệu một lần rồi chạy menu cho đến khi người dùng chọn thoát."""
    patients = load_json("patients.json")
    doctors = load_json("doctors.json")
    records_data = load_json("sample_data.json")
    records = records_data.get("medical_records", [])

    while True:
        print(
            "\n===== QUẢN LÝ BỆNH NHÂN =====\n"
            "1. Xem danh sách bệnh nhân\n"
            "2. Xem danh sách bác sĩ\n"
            "3. Xem hồ sơ khám\n"
            "4. Xem thống kê số lượng\n"
            "0. Thoát"
        )
        choice = input("Chọn chức năng: ").strip()

        if choice == "1":
            show_patients(patients)
        elif choice == "2":
            show_doctors(doctors)
        elif choice == "3":
            show_medical_records(records)
        elif choice == "4":
            inpatient_count = sum(
                patient["patient_type"] == "inpatient" for patient in patients
            )
            outpatient_count = len(patients) - inpatient_count
            print(
                f"\nBệnh nhân: {len(patients)} "
                f"(nội trú: {inpatient_count}, ngoại trú: {outpatient_count})\n"
                f"Bác sĩ: {len(doctors)}\n"
                f"Hồ sơ khám: {len(records)}"
            )
        elif choice == "0":
            print("Đã thoát chương trình.")
            break
        else:
            print("Lựa chọn không hợp lệ. Vui lòng chọn lại.")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as error:
        print(f"Lỗi dữ liệu: {error}")


# Phụ trách: Nguyễn Dương Quang — menu console, nhập liệu, xử lý ngoại lệ, tích hợp module và kiểm thử tích hợp.
