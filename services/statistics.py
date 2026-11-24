'''
Phụ trách: Nguyễn Tiến Dũng 
Ngày : 19/11/2026
Nhiệm vụ: thống kê, tính viện phí nội trú/ngoại trú và tổng hợp báo cáo.
'''

from utils.validators import is_non_negative_finite_number

# Tên loại bệnh nhân, dùng làm khóa trong các dict kết quả
INPATIENT = "inpatient"      # Nội trú
OUTPATIENT = "outpatient"    # Ngoại trú


# =====================================================================
# 0. KHAI BÁO CHUNG VÀ HÀM HỖ TRỢ
# =====================================================================

def _get(item, field, default=None):
    # Nếu là dict (dữ liệu đọc thẳng từ JSON) thì lấy theo khóa
    if isinstance(item, dict):
        return item.get(field, default)

    # Nếu là đối tượng (Patient, Doctor, MedicalRecord) thì lấy theo thuộc tính
    return getattr(item, field, default)


# =====================================================================
# 1. NHẬN DIỆN LOẠI BỆNH NHÂN
# =====================================================================

def get_patient_type(patient):
    # Dict: lấy từ trường patient_type; đối tượng: lấy từ tên lớp (Inpatient -> inpatient)
    if isinstance(patient, dict):
        patient_type = patient.get("patient_type", "")
    else:
        patient_type = type(patient).__name__.lower()

    # Chỉ chấp nhận đúng hai loại bệnh nhân
    if patient_type in (INPATIENT, OUTPATIENT):
        return patient_type

    # Loại khác -> báo lỗi thay vì tính sai
    raise ValueError(f"Không xác định được loại bệnh nhân: {patient_type!r}")


# =====================================================================
# 2. TÍNH VIỆN PHÍ
# =====================================================================

def calculate_inpatient_fee(daily_fee, days_stayed):
    # Viện phí nội trú = phí mỗi ngày x số ngày nằm viện
    # Dữ liệu đầu vào không được âm
    if (
        not is_non_negative_finite_number(daily_fee)
        or not isinstance(days_stayed, int)
        or isinstance(days_stayed, bool)
        or days_stayed < 0
    ):
        raise ValueError("Phí mỗi ngày và số ngày nằm viện không được âm.")

    # Nhân phí ngày với số ngày, ép về số thực
    return float(daily_fee) * days_stayed


def calculate_outpatient_fee(consultation_fee):
    # Viện phí ngoại trú = phí khám một lần
    # Phí khám âm là dữ liệu sai
    if not is_non_negative_finite_number(consultation_fee):
        raise ValueError("Phí khám không được âm.")

    return float(consultation_fee)


def calculate_patient_fee(patient):
    # Đối tượng: mỗi lớp con tự cài calculate_fee() nên gọi thẳng (đa hình)
    if not isinstance(patient, dict):
        return float(patient.calculate_fee())

    # Dict (từ JSON): tự tính theo loại bệnh nhân
    if get_patient_type(patient) == INPATIENT:
        return calculate_inpatient_fee(
            patient.get("daily_fee", 0), patient.get("days_stayed", 0)
        )
    return calculate_outpatient_fee(patient.get("consultation_fee", 0))


# =====================================================================
# 3. THỐNG KÊ SỐ LƯỢNG
# =====================================================================

def count_visits(records):
    # Mỗi hồ sơ khám là một lượt khám
    return len(records)


def count_patients_by_type(patients):
    # Bước 1: khởi tạo hai bộ đếm bằng 0
    counts = {INPATIENT: 0, OUTPATIENT: 0}

    # Bước 2: duyệt từng bệnh nhân, tăng bộ đếm của đúng loại
    for patient in patients:
        counts[get_patient_type(patient)] += 1

    return counts


def count_patients_by_doctor(records, doctor_id):
    # Set chỉ giữ mã bệnh nhân duy nhất, nên khám nhiều lần vẫn tính một
    unique_patients = {
        _get(record, "patient_id")
        for record in records
        if _get(record, "doctor_id") == doctor_id
    }
    return len(unique_patients)


def count_visits_by_doctor(records, doctors):
    # Bước 1: mỗi bác sĩ bắt đầu từ 0 (bác sĩ chưa khám vẫn xuất hiện)
    counts = {_get(doctor, "doctor_id"): 0 for doctor in doctors}

    # Bước 2: duyệt từng hồ sơ, cộng một lượt cho bác sĩ phụ trách
    for record in records:
        doctor_id = _get(record, "doctor_id")

        # Bỏ qua hồ sơ trỏ tới bác sĩ không tồn tại
        if doctor_id in counts:
            counts[doctor_id] += 1

    return counts


# =====================================================================
# 4. THỐNG KÊ TIỀN
# =====================================================================

def total_fee_by_type(patients):
    # Bước 1: tổng tiền mỗi loại bắt đầu từ 0
    totals = {INPATIENT: 0.0, OUTPATIENT: 0.0}

    # Bước 2: cộng viện phí từng bệnh nhân vào đúng nhóm
    for patient in patients:
        patient_type = get_patient_type(patient)
        totals[patient_type] += calculate_patient_fee(patient)

    # Bước 3: tổng chung = nội trú + ngoại trú
    totals["total"] = totals[INPATIENT] + totals[OUTPATIENT]
    return totals


def total_fee_from_records(records):
    # Chỉ cộng hồ sơ đã có phí, tránh lỗi khi gặp None
    return sum(
        _get(record, "fee_at_visit")
        for record in records
        if _get(record, "fee_at_visit") is not None
    )


# =====================================================================
# 5. TỔNG HỢP BÁO CÁO
# =====================================================================

def generate_statistical_report(patients, doctors, records):
    return {
        # Tổng số lượng
        "total_patients": len(patients),
        "total_doctors": len(doctors),
        "total_visits": count_visits(records),

        # Số bệnh nhân nội trú / ngoại trú
        "patients_by_type": count_patients_by_type(patients),

        # Viện phí theo loại và tổng chung
        "fee_by_type": total_fee_by_type(patients),

        # Tổng phí ghi nhận tại các lượt khám
        "total_fee_at_visit": total_fee_from_records(records),

        # Số lượt khám của mỗi bác sĩ
        "visits_by_doctor": count_visits_by_doctor(records, doctors),

        # Số bệnh nhân khác nhau của mỗi bác sĩ
        "patients_by_doctor": {
            _get(doctor, "doctor_id"): count_patients_by_doctor(
                records, _get(doctor, "doctor_id")
            )
            for doctor in doctors
        },
    }


def format_report(report):
    # Lấy sẵn hai nhóm dữ liệu để các dòng bên dưới viết ngắn hơn
    by_type = report["patients_by_type"]
    fees = report["fee_by_type"]

    # Mỗi phần tử trong danh sách là một dòng của báo cáo
    # (:,.0f = ngăn cách hàng nghìn bằng dấu phẩy, bỏ phần thập phân)
    lines = [
        "=== BÁO CÁO THỐNG KÊ ===",
        f"Bệnh nhân: {report['total_patients']} "
        f"(nội trú: {by_type[INPATIENT]}, ngoại trú: {by_type[OUTPATIENT]})",
        f"Bác sĩ: {report['total_doctors']}",
        f"Lượt khám: {report['total_visits']}",
        f"Viện phí nội trú: {fees[INPATIENT]:,.0f} đồng",
        f"Viện phí ngoại trú: {fees[OUTPATIENT]:,.0f} đồng",
        f"Tổng viện phí: {fees['total']:,.0f} đồng",
        f"Tổng phí ghi nhận tại các lượt khám: {report['total_fee_at_visit']:,.0f} đồng",
        "Theo bác sĩ (lượt khám / số bệnh nhân):",
    ]

    # Chỉ liệt kê bác sĩ đã có lượt khám để báo cáo gọn, vừa một màn hình
    idle_doctors = []
    for doctor_id, visits in report["visits_by_doctor"].items():
        patients = report["patients_by_doctor"][doctor_id]
        if visits == 0 and patients == 0:
            idle_doctors.append(doctor_id)
        else:
            lines.append(f"  {doctor_id}: {visits} / {patients}")

    # Bác sĩ chưa khám ai gộp thành một dòng thay vì in nhiều dòng "0 / 0"
    if idle_doctors:
        lines.append(f"  Chưa có lượt khám: {len(idle_doctors)} bác sĩ")

    # Nối các dòng bằng ký tự xuống dòng
    return "\n".join(lines)


def show_report(report, hide_visit_fee=True):
    # In báo cáo rồi DỪNG chờ người dùng, để menu không vẽ lại ngay
    # và đẩy báo cáo trôi khỏi màn hình
    text = format_report(report)

    # Ẩn dòng tổng phí ghi nhận tại lượt khám nếu được yêu cầu
    if hide_visit_fee:
        text = "\n".join(
            line
            for line in text.splitlines()
            if not line.startswith("Tổng phí ghi nhận tại các lượt khám:")
        )

    print()
    print(text)
    print()
    input("Nhấn Enter để quay lại menu...")
