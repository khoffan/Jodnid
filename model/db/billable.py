"""กติกาการเลือกรายการที่ต้องบันทึกจริงจากผลที่ LLM สกัดมา"""

from typing import Any, Dict, List


BILLABLE_TOTAL_TOLERANCE = 1.0


def _amount_of(item: Dict[str, Any]) -> float:
    try:
        return float(str(item.get("amount", 0)).replace(",", "").strip())
    except (TypeError, ValueError):
        return 0.0


def select_billable_items(
    transactions: List[Dict[str, Any]],
    grand_total: float = None,
    tolerance: float = BILLABLE_TOTAL_TOLERANCE,
) -> tuple[List[Dict[str, Any]], bool]:
    """
    เลือกรายการที่ต้องบันทึกจริง โดยยึด `grand_total` เป็นตัวตัดสิน

    เชื่อ flag `priority` จาก LLM อย่างเดียวไม่ได้ เพราะใบเสร็จไทยมีสองแบบปนกัน
    - แบบแยก VAT: ราคาสินค้ายังไม่รวม VAT ต้องบวกบรรทัด VAT เพิ่มถึงจะได้ยอดสุทธิ
    - แบบรวม VAT: ราคาสินค้ารวม VAT แล้ว บรรทัด VAT แสดงไว้เพื่อบอกข้อมูลเฉยๆ
    LLM ติด `priority=true` ให้ทั้งสองแบบเหมือนกัน ถ้าบวกหมดใบแบบที่สองจะเกิน
    ถ้าไม่บวกเลยใบแบบแรกจะขาด จึงต้องเทียบผลรวมกับ `grand_total` (ซึ่งวัดแล้วแม่นกว่า flag มาก)

    คืน (รายการที่ต้องบันทึก, ยอดตรงกับ grand_total หรือไม่)
    `False` แปลว่าเลขไม่ลงตัวสักทาง ควรให้ผู้ใช้ยืนยันก่อนบันทึก
    """
    base: List[Dict[str, Any]] = []
    extra: List[Dict[str, Any]] = []
    for item in transactions or []:
        if not isinstance(item, dict):
            continue
        if item.get("priority", False):
            # ยอดเสริมที่ "อาจ" ต้องบวกเพิ่ม เช่น VAT / Service Charge ที่แยกบรรทัดมา
            extra.append(item)
        elif item.get("is_actual_item", True):
            base.append(item)
        # ที่เหลือคือบรรทัดสรุปยอด (Subtotal) ซึ่งซ้ำกับรายการอื่นอยู่แล้ว ตัดทิ้งได้

    if grand_total is None:
        return base + extra, False

    total_base = sum(_amount_of(item) for item in base)
    total_extra = sum(_amount_of(item) for item in extra)

    if abs(total_base + total_extra - grand_total) <= tolerance:
        return base + extra, True  # ใบแบบแยก VAT: บวกยอดเสริมแล้วลงตัวพอดี
    if abs(total_base - grand_total) <= tolerance:
        return base, True  # ใบแบบรวม VAT: ราคาสินค้ารวมทุกอย่างแล้ว

    return base + extra, False
