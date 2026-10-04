"""กติกาการเลือกรายการที่ต้องบันทึกจริงจากผลที่ LLM สกัดมา"""

from typing import Any, Dict, List, Optional


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
) -> tuple[List[Dict[str, Any]], Optional[bool]]:
    """
    เลือกรายการที่ต้องบันทึกจริง โดยยึด `grand_total` เป็นตัวตัดสิน

    เชื่อ flag `priority` จาก LLM อย่างเดียวไม่ได้ เพราะใบเสร็จไทยมีสองแบบปนกัน
    - แบบแยก VAT: ราคาสินค้ายังไม่รวม VAT ต้องบวกบรรทัด VAT เพิ่มถึงจะได้ยอดสุทธิ
    - แบบรวม VAT: ราคาสินค้ารวม VAT แล้ว บรรทัด VAT แสดงไว้เพื่อบอกข้อมูลเฉยๆ
    LLM ติด `priority=true` ให้ทั้งสองแบบเหมือนกัน ถ้าบวกหมดใบแบบที่สองจะเกิน
    ถ้าไม่บวกเลยใบแบบแรกจะขาด จึงต้องเทียบผลรวมกับ `grand_total` (ซึ่งวัดแล้วแม่นกว่า flag มาก)

    คืน (รายการที่ต้องบันทึก, ผลการตรวจยอด) โดยผลการตรวจยอดมี 3 ค่า
    - `True`  ยอดลงตัวกับ `grand_total`
    - `False` เลขไม่ลงตัวสักทาง = AI อ่านตัวเลขเพี้ยน ควรให้ผู้ใช้ยืนยันก่อนบันทึก
    - `None`  ไม่มี `grand_total` ให้เทียบ (เช่นข้อความสั้นๆ อย่าง "ค่าข้าว 60") จึงตรวจไม่ได้
      ต้องแยกจาก `False` ให้ชัด ไม่งั้นการจดด้วยข้อความทุกครั้งจะถูกบังคับให้ยืนยันไปหมด
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
        return base + extra, None

    total_base = sum(_amount_of(item) for item in base)
    total_extra = sum(_amount_of(item) for item in extra)

    if abs(total_base + total_extra - grand_total) <= tolerance:
        return base + extra, True  # ใบแบบแยก VAT: บวกยอดเสริมแล้วลงตัวพอดี
    if abs(total_base - grand_total) <= tolerance:
        return base, True  # ใบแบบรวม VAT: ราคาสินค้ารวมทุกอย่างแล้ว

    return base + extra, False


def build_temp_edit_view(raw_data: Any) -> Dict[str, Any]:
    """ข้อมูลสำหรับหน้าแก้ไขใบเสร็จ: เฉพาะบรรทัดที่จะถูกบันทึกจริง + ยอดสุทธิจากใบเสร็จ

    ผู้ใช้จึงเห็นรายการตรงกับยอดที่จะตัดงบ บรรทัดที่ส่งออกไปถูกตั้ง `is_actual_item=True, priority=False`
    เพราะเมื่อผู้ใช้แก้แล้ว รายการนั้นคือยอดสุดท้าย ตอนบันทึก (ไม่มี grand_total) จึงถูกบันทึกครบทุกบรรทัด
    ไม่ถูกคัดซ้ำด้วย flag เดิมของ LLM
    """
    if isinstance(raw_data, dict):
        transactions = raw_data.get("transactions", [])
        grand_total = raw_data.get("grand_total")
    else:  # temp รุ่นเก่าเก็บเป็น list ของรายการ ไม่มี grand_total
        transactions, grand_total = raw_data or [], None

    billable, total_matched = select_billable_items(transactions, grand_total)
    items = [{**item, "is_actual_item": True, "priority": False} for item in billable]
    return {"items": items, "grand_total": grand_total, "total_matched": total_matched}
