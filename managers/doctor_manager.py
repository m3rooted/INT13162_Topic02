"""
Phụ trách: Nguyễn Văn Tuấn — quản lý bác sĩ
(thêm, sửa, xóa, tìm kiếm, hiển thị).
"""

import json
import unicodedata
from pathlib import Path
from typing import Callable, Dict, List, Optional

from models.doctor import Doctor


def _normalize(text: str) -> str:
    """Chuẩn hóa chuỗi để tìm gần đúng: bỏ khoảng trắng thừa, dấu, hoa/thường."""
    text = " ".join(str(text).split()).replace("đ", "d").replace("Đ", "D")
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text.casefold()


class DoctorManager:
    """
    Quản lý danh sách bác sĩ.
    Chỉ xử lý dữ liệu, không input()/print(); việc hỏi xác nhận và in thông báo
    do menu trong main.py đảm nhiệm. Lỗi nghiệp vụ báo bằng ValueError/KeyError.
    Mọi thay đổi (thêm/sửa/xóa) được tự động lưu vào data/doctors.json.
    """

    # Chỉ cho sửa họ và tên, chuyên khoa; mã bác sĩ đã gắn với hồ sơ khám nên cố định
    EDITABLE_FIELDS = ("full_name", "specialty")

    # Đường dẫn file dữ liệu, dùng chung cho cả đọc và ghi
    DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "doctors.json"

    def __init__(self, record_checker: Optional[Callable[[str], bool]] = None):
        """
        record_checker(doctor_id) -> True nếu bác sĩ đang có hồ sơ khám.
        Dùng để chặn xóa; ghép nối trong main.py:
            dm.set_record_checker(
                lambda did: any(r.doctor_id == did for r in records.medical_records))
        """
        # Khóa là mã bác sĩ đã chuẩn hóa, giá trị là đối tượng Doctor
        self._doctors: Dict[str, Doctor] = {}
        self._record_checker = record_checker
        self._load_initial_doctors()

    # ---------------- ĐỌC / GHI FILE ----------------

    def _load_initial_doctors(self) -> None:
        """Nạp bác sĩ ban đầu từ data/doctors.json, mỗi dict thành một Doctor."""
        data_path = self.DATA_PATH

        try:
            doctors_data = json.loads(data_path.read_text(encoding="utf-8-sig"))
        except FileNotFoundError as error:
            raise RuntimeError(f"Không tìm thấy file dữ liệu bác sĩ: {data_path}") from error
        except json.JSONDecodeError as error:
            raise RuntimeError(f"File dữ liệu bác sĩ không hợp lệ: {data_path}") from error

        if not isinstance(doctors_data, list):
            raise ValueError("Dữ liệu bác sĩ phải có dạng danh sách.")

        for index, doctor_data in enumerate(doctors_data, start=1):
            if not isinstance(doctor_data, dict):
                raise ValueError(f"Bản ghi bác sĩ thứ {index} phải có dạng dict.")
            try:
                # Dùng _add (không ghi file) để tránh ghi lại file khi đang nạp
                self._add(Doctor(
                    doctor_id=doctor_data["doctor_id"],
                    full_name=doctor_data["full_name"],
                    specialty=doctor_data["specialty"],
                ))
            except KeyError as error:
                raise ValueError(
                    f"Bản ghi bác sĩ thứ {index} thiếu trường {error.args[0]!r}."
                ) from error
            except (TypeError, ValueError) as error:
                raise ValueError(
                    f"Bản ghi bác sĩ thứ {index} không hợp lệ: {error}"
                ) from error

    def save(self) -> None:
        """
        Ghi toàn bộ danh sách bác sĩ hiện tại ra data/doctors.json.
        Ghi vào file tạm rồi thay thế file thật để không làm hỏng dữ liệu nếu lỗi giữa chừng.
        """
        data = [
            {
                "doctor_id": d.doctor_id,
                "full_name": d.full_name,
                "specialty": d.specialty,
            }
            for d in self.get_all()
        ]
        tmp_path = self.DATA_PATH.with_suffix(".json.tmp")
        # ensure_ascii=False để giữ nguyên tiếng Việt, không bị ghi thành \uXXXX
        tmp_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tmp_path.replace(self.DATA_PATH)

    # ---------------- TÍCH HỢP VỚI MODULE KHÁC ----------------

    def set_record_checker(self, checker: Callable[[str], bool]) -> None:
        """Gắn hàm kiểm tra liên kết hồ sơ (dùng khi manager hồ sơ tạo sau)."""
        self._record_checker = checker

    @property
    def doctors(self):
        """Danh sách bác sĩ tự cập nhật, truyền cho manager hồ sơ khám (chỉ để đọc)."""
        return self._doctors.values()

    def exists(self, doctor_id: str) -> bool:
        """Kiểm tra mã bác sĩ có tồn tại hay không."""
        return self.find_by_id(doctor_id) is not None

    # ---------------- THÊM BÁC SĨ ----------------

    def _add(self, doctor: Doctor) -> None:
        """Kiểm tra và thêm vào dict trong bộ nhớ, KHÔNG ghi file."""
        if not isinstance(doctor, Doctor):
            raise ValueError("Đối tượng thêm vào phải là Doctor.")
        if not doctor.validate():
            raise ValueError(f"Thông tin bác sĩ '{doctor.doctor_id}' không hợp lệ.")

        key = self._key(doctor.doctor_id)
        if key in self._doctors:
            raise ValueError(f"Mã bác sĩ '{doctor.doctor_id}' đã tồn tại.")

        self._doctors[key] = doctor

    def add_doctor(self, doctor: Doctor) -> None:
        """Thêm bác sĩ mới (từ chối dữ liệu không hợp lệ hoặc trùng mã) và lưu file."""
        self._add(doctor)
        self.save()

    # ---------------- SỬA THÔNG TIN BÁC SĨ ----------------

    def update_doctor(
        self,
        doctor_id: str,
        changes: Optional[Dict[str, str]] = None,
        **kwargs: str,
    ) -> bool:
        """
        Sửa họ và tên và/hoặc chuyên khoa theo mã, rồi lưu file.
        Nhận dict changes theo UML; cũng hỗ trợ truyền các trường bằng keyword.
        """
        doctor = self._require(doctor_id)

        if changes is not None and kwargs:
            raise ValueError("Truyền changes hoặc các trường keyword, không được dùng cả hai.")
        if changes is not None and not isinstance(changes, dict):
            raise ValueError("Dữ liệu cập nhật phải là dict.")

        updates = changes if changes is not None else kwargs
        if not updates:
            raise ValueError("Chưa có trường nào để cập nhật.")
        if "doctor_id" in updates:
            raise ValueError("Không được đổi mã bác sĩ vì đã gắn với hồ sơ khám.")

        invalid = [key for key in updates if key not in self.EDITABLE_FIELDS]
        if invalid:
            raise ValueError(
                f"Trường không được phép sửa: {', '.join(invalid)}. "
                f"Chỉ sửa: {', '.join(self.EDITABLE_FIELDS)}."
            )

        # Tạo đối tượng tạm để validation toàn bộ dữ liệu trước khi sửa bác sĩ hiện tại.
        updated_doctor = Doctor(
            doctor_id=doctor.doctor_id,
            full_name=updates.get("full_name", doctor.full_name),
            specialty=updates.get("specialty", doctor.specialty),
        )
        doctor.full_name = updated_doctor.full_name
        doctor.specialty = updated_doctor.specialty

        self.save()
        return True

    # ---------------- XÓA BÁC SĨ ----------------

    def delete_doctor(
        self, doctor_id: str, medical_records=None
    ) -> bool:
        """
        Xóa bác sĩ nếu không còn hồ sơ khám tham chiếu, rồi lưu file.
        Có thể truyền medical_records hoặc gắn record_checker để kiểm tra liên kết.
        """
        doctor = self.find_by_id(doctor_id)
        if doctor is None:
            return False

        has_linked_record = (
            self._record_checker is not None
            and self._record_checker(doctor.doctor_id)
        ) or (
            medical_records is not None
            and any(
                getattr(record, "doctor_id", None) == doctor.doctor_id
                for record in medical_records
            )
        )
        if has_linked_record:
            raise ValueError(
                f"Không thể xóa bác sĩ '{doctor.doctor_id}': "
                "đang có hồ sơ khám liên kết."
            )

        del self._doctors[self._key(doctor_id)]
        self.save()
        return True

    # ---------------- TÌM KIẾM BÁC SĨ ----------------

    def find_doctor(self, doctor_id: str) -> Optional[Doctor]:
        """Tìm theo mã bác sĩ; tên hàm tương thích với sơ đồ UML."""
        return self.find_by_id(doctor_id)

    def find_by_id(self, doctor_id: str) -> Optional[Doctor]:
        """Tìm chính xác theo mã, không thấy trả về None."""
        return self._doctors.get(self._key(doctor_id))

    def find_by_name(self, keyword: str) -> List[Doctor]:
        """Tìm gần đúng theo họ và tên."""
        return self._search("full_name", keyword)

    def find_by_specialty(self, keyword: str) -> List[Doctor]:
        """Tìm gần đúng theo chuyên khoa."""
        return self._search("specialty", keyword)

    # ---------------- HIỂN THỊ BÁC SĨ ----------------

    def get_all(self) -> List[Doctor]:
        """Danh sách bác sĩ sắp theo mã."""
        return sorted(self._doctors.values(), key=lambda d: _normalize(d.doctor_id))

    def count(self) -> int:
        """Số lượng bác sĩ."""
        return len(self._doctors)

    def display_doctors(self, doctors: Optional[List[Doctor]] = None) -> bool:
        """
        Hiển thị bảng danh sách bác sĩ ra console.
        Truyền doctors để hiển thị kết quả tìm kiếm; bỏ trống thì hiển thị tất cả.
        """
        rows = self.get_all() if doctors is None else doctors
        print(self.format_doctors(rows))
        return bool(rows)

    def format_doctors(self, doctors: Optional[List[Doctor]] = None) -> str:
        """Tạo chuỗi bảng bác sĩ để menu có thể ghép vào giao diện riêng."""
        rows = self.get_all() if doctors is None else doctors
        if not rows:
            return "Chưa có dữ liệu"

        headers = ("STT", "Mã BS", "Họ và tên", "Chuyên khoa")
        data = [(str(i), d.doctor_id, d.full_name, d.specialty)
                for i, d in enumerate(rows, 1)]

        # Độ rộng mỗi cột = chuỗi dài nhất trong cột (kể cả tiêu đề)
        widths = [max(len(h), *(len(r[c]) for r in data))
                  for c, h in enumerate(headers)]
        line = "+" + "+".join("-" * (w + 2) for w in widths) + "+"

        def fmt(cells):
            return "| " + " | ".join(c.ljust(w) for c, w in zip(cells, widths)) + " |"

        return "\n".join([line, fmt(headers), line, *map(fmt, data), line])

    def display_doctor_detail(self, doctor_id: str) -> str:
        """Thông tin chi tiết một bác sĩ (KeyError nếu không có)."""
        d = self._require(doctor_id)
        return (
            f"Mã bác sĩ : {d.doctor_id}\n"
            f"Họ và tên  : {d.full_name}\n"
            f"Chuyên khoa: {d.specialty}"
        )

    # ---------------- HÀM NỘI BỘ ----------------

    @staticmethod
    def _key(doctor_id: str) -> str:
        """Khóa so sánh mã: bỏ khoảng trắng thừa, không phân biệt hoa/thường."""
        return " ".join(str(doctor_id).split()).upper()

    def _require(self, doctor_id: str) -> Doctor:
        """Lấy bác sĩ theo mã, KeyError nếu không tồn tại."""
        doctor = self.find_by_id(doctor_id)
        if doctor is None:
            raise KeyError(f"Không tìm thấy bác sĩ có mã '{doctor_id}'.")
        return doctor

    def _search(self, attr: str, keyword: str) -> List[Doctor]:
        """Tìm các bác sĩ có trường attr chứa từ khóa."""
        if not keyword or not str(keyword).strip():
            raise ValueError("Từ khóa tìm kiếm không được để trống.")
        kw = _normalize(keyword)
        return [d for d in self.get_all() if kw in _normalize(getattr(d, attr))]