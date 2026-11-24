"""Các hàm validation dùng chung cho dữ liệu và các lớp thực thể."""

import math


def is_non_negative_finite_number(value) -> bool:
    """Kiểm tra giá trị là số hữu hạn, không âm và không phải bool."""
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return value >= 0 and math.isfinite(value)
    except OverflowError:
        return False
