"""
Phụ trách: Nguyễn Văn Chung — quản lý hồ sơ khám
(tạo, cập nhật, phân công bác sĩ, tìm kiếm, sắp xếp,
hiển thị, kiểm tra liên kết).
"""

# Import lớp đối tượng MedicalRecord từ file models/medical_record.py
from models.medical_record import MedicalRecord


# ==========================================================
# CLASS PATIENT MANAGER - PHẦN QUẢN LÝ HỒ SƠ KHÁM
# ==========================================================

# Khai báo class PatientManager để quản lý hồ sơ khám
class PatientManager:
    """
    Phần triển khai các nghiệp vụ hồ sơ khám theo UML.

    Danh sách patients và doctors được cung cấp từ bên ngoài.
    """

    # Hàm khởi tạo class, nhận vào danh sách bệnh nhân và bác sĩ (mặc định None)
    def __init__(self, patients=None, doctors=None):
        # Gán danh sách bệnh nhân, nếu None thì tạo list rỗng để tránh lỗi
        self.patients = patients if patients is not None else []
        # Gán danh sách bác sĩ, nếu None thì tạo list rỗng
        self.doctors = doctors if doctors is not None else []
        # Khởi tạo danh sách hồ sơ khám rỗng
        self.medical_records = []

    # ---------------- KIỂM TRA LIÊN KẾT ----------------

    # Hàm kiểm tra xem bệnh nhân và bác sĩ trong hồ sơ có tồn tại không
    def validate_relations(self, record: MedicalRecord) -> bool:
        """Kiểm tra bệnh nhân và bác sĩ có tồn tại hay không."""

        # Nếu record không phải là đối tượng MedicalRecord thì trả về False ngay
        if not isinstance(record, MedicalRecord):
            return False

        # Dùng any() để kiểm tra: có bất kỳ bệnh nhân nào có patient_id trùng với record không
        patient_exists = any(
            # So sánh patient_id của từng bệnh nhân với patient_id của hồ sơ
            patient.patient_id == record.patient_id
            # Duyệt qua từng bệnh nhân trong danh sách patients
            for patient in self.patients
        )

        # Dùng any() để kiểm tra: có bất kỳ bác sĩ nào có doctor_id trùng với record không
        doctor_exists = any(
            # So sánh doctor_id của từng bác sĩ với doctor_id của hồ sơ
            doctor.doctor_id == record.doctor_id
            # Duyệt qua từng bác sĩ trong danh sách doctors
            for doctor in self.doctors
        )

        # Trả về True chỉ khi CẢ HAI đều tồn tại (dùng toán tử and)
        return patient_exists and doctor_exists

    # ---------------- TẠO HỒ SƠ ----------------

    # Hàm thêm hồ sơ khám mới vào hệ thống
    def create_medical_record(self, record: MedicalRecord) -> None:
        """Thêm hồ sơ khám mới."""

        # Kiểm tra kiểu dữ liệu: nếu không phải MedicalRecord thì báo lỗi
        if not isinstance(record, MedicalRecord):
            # In thông báo lỗi ra màn hình
            print("Dữ liệu hồ sơ không hợp lệ.")
            # Thoát hàm luôn, không xử lý tiếp
            return

        # Gọi hàm validate() của class MedicalRecord để kiểm tra tính hợp lệ dữ liệu
        if not record.validate():
            # In thông báo nếu dữ liệu không hợp lệ
            print("Thông tin hồ sơ không hợp lệ.")
            # Thoát hàm
            return

        # Kiểm tra mã hồ sơ trùng
        # Duyệt qua từng hồ sơ đã có trong danh sách
        for item in self.medical_records:
            # Nếu record_id bị trùng với hồ sơ đã tồn tại
            if item.record_id == record.record_id:
                # In thông báo trùng mã
                print("Mã hồ sơ đã tồn tại.")
                # Thoát hàm, không thêm
                return

        # Kiểm tra bệnh nhân và bác sĩ
        # Gọi hàm validate_relations để kiểm tra liên kết
        if not self.validate_relations(record):
            # In thông báo nếu bệnh nhân/bác sĩ không tồn tại
            print("Bệnh nhân hoặc bác sĩ không tồn tại.")
            # Thoát hàm
            return

        # Mọi thứ hợp lệ -> Thêm hồ sơ vào danh sách
        self.medical_records.append(record)
        # In thông báo thành công
        print("Thêm hồ sơ khám thành công.")

    # ---------------- CẬP NHẬT HỒ SƠ ----------------

    # Hàm cập nhật thông tin hồ sơ dựa vào mã hồ sơ
    def update_medical_record(
        self,
        record_id: str,
        changes: dict
    ) -> bool:
        """Cập nhật thông tin hồ sơ theo mã."""

        # Tìm hồ sơ có record_id tương ứng trong danh sách
        record = next(
            (
                # Duyệt qua từng hồ sơ, lấy hồ sơ có record_id khớp
                item for item in self.medical_records
                # Điều kiện: record_id khớp với tham số truyền vào
                if item.record_id == record_id
            ),
            # Nếu không tìm thấy thì trả về None (tham số thứ 2 của next)
            None
        )

        # Nếu không tìm thấy hồ sơ (record là None)
        if record is None:
            # In thông báo không tìm thấy
            print("Không tìm thấy hồ sơ.")
            # Trả về False báo thất bại
            return False

        # Kiểm tra changes có phải là dict và có dữ liệu không
        if not isinstance(changes, dict) or not changes:
            # In thông báo không hợp lệ
            print("Thông tin cập nhật không hợp lệ.")
            # Trả về False
            return False

        # Tập hợp các trường được phép cập nhật.
        # LƯU Ý: record_id và patient_id là thuộc tính CHỈ ĐỌC trong MedicalRecord
        # (chỉ có @property, không có @setter) nên KHÔNG được phép sửa.
        # Nghiệp vụ: một hồ sơ khám đã tạo không được chuyển sang bệnh nhân khác.
        allowed_fields = {
            "doctor_id",        # Mã bác sĩ
            "visit_date",       # Ngày khám
            "diagnosis",        # Chẩn đoán
            "fee_at_visit"      # Chi phí khám
        }

        # Không cho sửa mã hồ sơ, mã bệnh nhân và các trường không tồn tại
        # Kiểm tra: các key trong changes có nằm trong allowed_fields không
        if not set(changes).issubset(allowed_fields):
            # In thông báo có trường không được phép
            print("Có trường dữ liệu không được phép cập nhật.")
            # Trả về False
            return False

        # Tạo hồ sơ tạm để kiểm tra trước khi thay đổi dữ liệu thật
        # Tạo dict chứa giá trị hiện tại của hồ sơ
        new_values = {
            # Lấy patient_id hiện tại (vẫn phải truyền vào constructor vì là tham số bắt buộc,
            # nhưng giá trị này không bao giờ bị thay đổi)
            "patient_id": record.patient_id,
            # Lấy doctor_id hiện tại
            "doctor_id": record.doctor_id,
            # Lấy visit_date hiện tại
            "visit_date": record.visit_date,
            # Lấy diagnosis hiện tại
            "diagnosis": record.diagnosis,
            # Lấy fee_at_visit hiện tại
            "fee_at_visit": record.fee_at_visit
        }

        # Ghi đè các giá trị mới từ changes vào dict (các trường không có trong changes thì giữ nguyên)
        new_values.update(changes)

        # Thử tạo đối tượng mới với dữ liệu đã cập nhật để kiểm tra tính hợp lệ
        try:
            # Tạo MedicalRecord tạm với record_id cũ + các giá trị mới
            updated_record = MedicalRecord(
                # Giữ nguyên mã hồ sơ
                record_id=record.record_id,
                # Bung các key-value trong new_values ra làm tham số
                **new_values
            )
        # Bắt lỗi nếu dữ liệu mới sai định dạng (các setter của MedicalRecord ném ValueError)
        except (ValueError, TypeError):
            # In thông báo dữ liệu không hợp lệ
            print("Dữ liệu cập nhật không hợp lệ.")
            # Trả về False
            return False

        # Kiểm tra liên kết với dữ liệu mới (bệnh nhân/bác sĩ có tồn tại không)
        if not self.validate_relations(updated_record):
            # In thông báo nếu không tồn tại
            print("Bệnh nhân hoặc bác sĩ không tồn tại.")
            # Trả về False
            return False

        # Chỉ cập nhật khi toàn bộ dữ liệu hợp lệ
        # Chỉ gán các trường CÓ setter. KHÔNG gán patient_id vì nó chỉ đọc
        # (gán vào sẽ gây AttributeError).
        # Gán doctor_id mới vào hồ sơ thật
        record.doctor_id = updated_record.doctor_id
        # Gán visit_date mới vào hồ sơ thật
        record.visit_date = updated_record.visit_date
        # Gán diagnosis mới vào hồ sơ thật
        record.diagnosis = updated_record.diagnosis
        # Gán fee_at_visit mới vào hồ sơ thật
        record.fee_at_visit = updated_record.fee_at_visit

        # In thông báo cập nhật thành công
        print("Cập nhật hồ sơ thành công.")
        # Trả về True báo thành công
        return True

    # ---------------- PHÂN CÔNG BÁC SĨ ----------------

    # Hàm phân công bác sĩ cho hồ sơ khám
    def assign_doctor(
        self,
        record_id: str,
        doctor_id: str
    ) -> bool:
        """Phân công bác sĩ cho hồ sơ khám."""

        # Tìm hồ sơ có record_id tương ứng
        record = next(
            (
                # Duyệt qua danh sách hồ sơ
                item for item in self.medical_records
                # Điều kiện record_id khớp
                if item.record_id == record_id
            ),
            # Không tìm thấy thì trả về None
            None
        )

        # Nếu không tìm thấy hồ sơ
        if record is None:
            # In thông báo
            print("Không tìm thấy hồ sơ.")
            # Trả về False
            return False

        # Kiểm tra bác sĩ có tồn tại trong danh sách không
        doctor_exists = any(
            # So sánh doctor_id của từng bác sĩ với doctor_id truyền vào
            doctor.doctor_id == doctor_id
            # Duyệt qua danh sách bác sĩ
            for doctor in self.doctors
        )

        # Nếu bác sĩ không tồn tại
        if not doctor_exists:
            # In thông báo
            print("Không tìm thấy bác sĩ.")
            # Trả về False
            return False

        # Gán doctor_id mới vào hồ sơ (doctor_id có setter nên gán trực tiếp được)
        try:
            # Setter sẽ tự kiểm tra giá trị và ném ValueError nếu rỗng/sai kiểu
            record.doctor_id = doctor_id
        # Bắt lỗi nếu mã bác sĩ không hợp lệ
        except (ValueError, TypeError):
            # In thông báo mã bác sĩ không hợp lệ
            print("Mã bác sĩ không hợp lệ.")
            # Trả về False
            return False

        # In thông báo phân công thành công
        print("Phân công bác sĩ thành công.")
        # Trả về True
        return True

    # ---------------- TÌM KIẾM HỒ SƠ ----------------

    # Hàm tìm kiếm hồ sơ theo từ khóa và tiêu chí
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
        """

        # Kiểm tra từ khóa: phải là chuỗi và không rỗng sau khi strip
        if not isinstance(keyword, str) or not keyword.strip():
            # In thông báo lỗi
            print("Từ khóa tìm kiếm không hợp lệ.")
            # Trả về list rỗng
            return []

        # Chuẩn hóa từ khóa: xóa khoảng trắng 2 đầu, chuyển về chữ thường để so sánh không phân biệt hoa thường
        keyword = keyword.strip().casefold()

        # Khởi tạo list chứa kết quả
        results = []

        # Duyệt qua từng hồ sơ trong danh sách
        for record in self.medical_records:

            # Nếu tìm theo mã hồ sơ
            if search_type == "record_id":
                # So sánh chính xác record_id (casefold cả 2 để không phân biệt hoa thường)
                matched = record.record_id.casefold() == keyword

            # Nếu tìm theo mã bệnh nhân
            elif search_type == "patient_id":
                # So sánh chính xác patient_id
                matched = record.patient_id.casefold() == keyword

            # Nếu tìm theo mã bác sĩ
            elif search_type == "doctor_id":
                # So sánh chính xác doctor_id
                matched = record.doctor_id.casefold() == keyword

            # Nếu tìm theo tên bệnh nhân
            elif search_type == "patient_name":
                # Tìm đối tượng bệnh nhân ứng với record trong danh sách patients
                patient = next(
                    (
                        # Duyệt qua danh sách bệnh nhân
                        p for p in self.patients
                        # Điều kiện: patient_id của bệnh nhân khớp với patient_id của hồ sơ
                        if p.patient_id == record.patient_id
                    ),
                    # Không tìm thấy thì trả về None
                    None
                )

                # Kiểm tra: bệnh nhân phải tồn tại VÀ từ khóa nằm trong tên bệnh nhân (tìm gần đúng)
                matched = (
                    # Điều kiện 1: bệnh nhân phải tìm thấy
                    patient is not None
                    # Điều kiện 2: từ khóa là chuỗi con trong tên bệnh nhân (casefold 2 bên)
                    and keyword in patient.full_name.casefold()
                )

            # Nếu tìm theo tên bác sĩ
            elif search_type == "doctor_name":
                # Tìm đối tượng bác sĩ ứng với record trong danh sách doctors
                doctor = next(
                    (
                        # Duyệt qua danh sách bác sĩ
                        d for d in self.doctors
                        # Điều kiện: doctor_id của bác sĩ khớp với doctor_id của hồ sơ
                        if d.doctor_id == record.doctor_id
                    ),
                    # Không tìm thấy thì trả về None
                    None
                )

                # Kiểm tra: bác sĩ phải tồn tại VÀ từ khóa nằm trong tên bác sĩ
                matched = (
                    # Điều kiện 1: bác sĩ phải tìm thấy
                    doctor is not None
                    # Điều kiện 2: từ khóa là chuỗi con trong tên bác sĩ
                    and keyword in doctor.full_name.casefold()
                )

            # Nếu search_type không thuộc các trường hợp trên
            else:
                # In thông báo tiêu chí không hợp lệ
                print("Tiêu chí tìm kiếm không hợp lệ.")
                # Trả về list rỗng
                return []

            # Nếu hồ sơ thỏa mãn điều kiện tìm kiếm
            if matched:
                # Thêm vào list kết quả
                results.append(record)

        # Trả về danh sách kết quả tìm được
        return results

    # ---------------- SẮP XẾP HỒ SƠ ----------------

    # Hàm sắp xếp danh sách hồ sơ theo tiêu chí
    def sort_medical_records(
        self,
        criterion: str,
        descending: bool = False
    ) -> list[MedicalRecord]:
        """
        Sắp xếp theo:
        - visit_date: Ngày khám.
        - fee_at_visit: Chi phí khám.
        """

        # Nếu sắp xếp theo ngày khám
        if criterion == "visit_date":
            # Trả về danh sách đã sắp xếp (sorted trả về list mới, không đổi list gốc)
            return sorted(
                # Danh sách gốc cần sắp xếp
                self.medical_records,
                # Key dùng để so sánh: lấy thuộc tính visit_date của từng hồ sơ
                key=lambda record: record.visit_date,
                # reverse=True thì sắp xếp giảm dần, False thì tăng dần
                reverse=descending
            )

        # Nếu sắp xếp theo chi phí khám
        elif criterion == "fee_at_visit":
            # Trả về danh sách đã sắp xếp theo chi phí
            return sorted(
                # Danh sách gốc cần sắp xếp
                self.medical_records,
                # Key dùng để so sánh là một tuple (phí có None hay không, giá trị phí)
                # Mục đích: đẩy các hồ sơ có phí None xuống cuối (True > False), sau đó so sánh số tiền
                key=lambda record: (
                    # Phần tử 1: True nếu fee là None -> đẩy xuống cuối khi sắp xếp tăng dần
                    record.fee_at_visit is None,
                    # Phần tử 2: giá trị phí, nếu None thì dùng 0 để tránh lỗi so sánh
                    record.fee_at_visit or 0
                ),
                # reverse=True thì sắp xếp giảm dần
                reverse=descending
            )

        # Nếu criterion không thuộc 2 trường hợp trên
        print("Tiêu chí sắp xếp không hợp lệ.")
        # Trả về list rỗng
        return []

    # ---------------- HIỂN THỊ HỒ SƠ ----------------

    # Hàm hiển thị danh sách hồ sơ khám ra màn hình dạng bảng
    def display_medical_records(self) -> None:
        """Hiển thị danh sách hồ sơ khám theo dạng bảng."""

        # Nếu danh sách hồ sơ rỗng
        if not self.medical_records:
            # In thông báo danh sách trống
            print("Danh sách hồ sơ khám hiện đang trống.")
            # Thoát hàm
            return

        # Khai báo tiêu đề các cột của bảng
        headers = [
            "Mã hồ sơ",         # Cột 1
            "Mã bệnh nhân",     # Cột 2
            "Mã bác sĩ",        # Cột 3
            "Ngày khám",        # Cột 4
            "Chẩn đoán",        # Cột 5
            "Chi phí"           # Cột 6
        ]

        # Khởi tạo list chứa dữ liệu từng dòng
        rows = []

        # Duyệt qua từng hồ sơ để lấy dữ liệu
        for record in self.medical_records:
            # Thêm một dòng dữ liệu vào list rows
            rows.append([
                # Cột 1: mã hồ sơ
                record.record_id,
                # Cột 2: mã bệnh nhân
                record.patient_id,
                # Cột 3: mã bác sĩ
                record.doctor_id,
                # Cột 4: ngày khám đã format theo dạng dd/mm/yyyy
                record.visit_date.strftime("%d/%m/%Y"),
                # Cột 5: chẩn đoán
                record.diagnosis,
                # Cột 6: chi phí
                (
                    # Nếu fee không None thì format có dấu phẩy ngăn cách hàng nghìn, không phần thập phân
                    f"{record.fee_at_visit:,.0f}"
                    # Nếu fee None
                    if record.fee_at_visit is not None
                    # thì hiển thị "Chưa có"
                    else "Chưa có"
                )
            ])

        # Tính độ rộng từng cột
        # Duyệt qua từng cột i (từ 0 đến len(headers)-1)
        widths = [
            # Lấy max độ dài của chuỗi trong cột i, tính trên cả header và dữ liệu
            max(len(str(row[i])) for row in [headers] + rows)
            # Lặp cho từng cột
            for i in range(len(headers))
        ]

        # Tạo đường kẻ ngang phân cách (ví dụ: +------+------+)
        separator = "+-" + "-+-".join(
            # Mỗi cột là dấu "-" lặp lại theo độ rộng cột
            "-" * width for width in widths
        ) + "-+"

        # Định nghĩa hàm phụ để in một dòng dữ liệu
        def print_row(row):
            # In dòng với format: | giá trị 1 | giá trị 2 | ...
            print(
                # Bắt đầu bằng "| "
                "| "
                # Nối các ô bằng " | ", mỗi ô căn trái theo độ rộng của cột
                + " | ".join(
                    # Căn trái (ljust) giá trị theo độ rộng cột tương ứng
                    str(value).ljust(widths[i])
                    # Duyệt qua từng giá trị trong dòng, kèm chỉ số i
                    for i, value in enumerate(row)
                )
                # Kết thúc dòng bằng " |"
                + " |"
            )

        # In tiêu đề bảng
        print("\nDANH SÁCH HỒ SƠ KHÁM")
        # In đường kẻ ngang
        print(separator)
        # In dòng tiêu đề
        print_row(headers)
        # In đường kẻ ngang
        print(separator)

        # Duyệt qua từng dòng dữ liệu
        for row in rows:
            # In từng dòng
            print_row(row)

        # In đường kẻ ngang cuối bảng
        print(separator)
        # In tổng số hồ sơ
        print(f"Tổng số hồ sơ: {len(self.medical_records)}")
