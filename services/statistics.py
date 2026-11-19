'''
Phụ trách: Nguyễn Tiến Dũng 
Ngày : 19/11/2026
Nhiệm vụ: thống kê, tính viện phí nội trú/ngoại trú và tổng hợp báo cáo.
'''

# Tên loại bệnh nhân, dùng làm khóa trong các dict kết quả
INPATIENT = "inpatient"      # Nội trú
OUTPATIENT = "outpatient"    # Ngoại trú


# =====================================================================
# 1. NHẬN DIỆN LOẠI BỆNH NHÂN
# =====================================================================

def get_patient_type(patient):
    # Lấy tên lớp (vd: Inpatient) rồi đổi thành chữ thường (inpatient)
    class_name = type(patient).__name__.lower()

    # Chỉ chấp nhận đúng hai loại bệnh nhân
    if class_name in (INPATIENT, OUTPATIENT):
        return class_name

    # Loại khác (vd: lớp Patient gốc) -> báo lỗi thay vì tính sai
    raise ValueError(f"Không xác định được loại bệnh nhân: {type(patient).__name__}")


# =====================================================================
# 2. TÍNH VIỆN PHÍ
# =====================================================================

def calculate_inpatient_fee(daily_fee, days_stayed):
    # Viện phí nội trú = phí mỗi ngày x số ngày nằm viện
    # Dữ liệu đầu vào không được âm
    if daily_fee < 0 or days_stayed < 0:
        raise ValueError("Phí mỗi ngày và số ngày nằm viện không được âm.")

    # Nhân phí ngày với số ngày, ép về số thực
    return float(daily_fee) * days_stayed


def calculate_outpatient_fee(consultation_fee):
    # Viện phí ngoại trú = phí khám một lần
    # Phí khám âm là dữ liệu sai
    if consultation_fee < 0:
        raise ValueError("Phí khám không được âm.")

    return float(consultation_fee)


def calculate_patient_fee(patient):
    # Mỗi lớp con tự cài calculate_fee() nên không cần kiểm tra loại (đa hình)
    return float(patient.calculate_fee())


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
        record.patient_id
        for record in records
        if record.doctor_id == doctor_id
    }
    return len(unique_patients)


def count_visits_by_doctor(records, doctors):
    # Bước 1: mỗi bác sĩ bắt đầu từ 0 (bác sĩ chưa khám vẫn xuất hiện)
    counts = {doctor.doctor_id: 0 for doctor in doctors}

    # Bước 2: duyệt từng hồ sơ, cộng một lượt cho bác sĩ phụ trách
    for record in records:
        # Bỏ qua hồ sơ trỏ tới bác sĩ không tồn tại
        if record.doctor_id in counts:
            counts[record.doctor_id] += 1

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
        record.fee_at_visit
        for record in records
        if record.fee_at_visit is not None
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
            doctor.doctor_id: count_patients_by_doctor(records, doctor.doctor_id)
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

    # Thêm mỗi bác sĩ một dòng: mã - số lượt khám / số bệnh nhân
    for doctor_id, visits in report["visits_by_doctor"].items():
        patients = report["patients_by_doctor"][doctor_id]
        lines.append(f"  {doctor_id}: {visits} / {patients}")

    # Nối các dòng bằng ký tự xuống dòng
    return "\n".join(lines)


