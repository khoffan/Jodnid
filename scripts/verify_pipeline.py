"""
ชุดตรวจสอบ pipeline รับ-จ่ายแบบออฟไลน์ — ไม่เรียก API ภายนอกและไม่แตะฐานข้อมูลจริง

ครอบคลุมจุดที่เคยพังมาแล้วทั้งหมด รันได้ทุกครั้งก่อนแก้โค้ดในเส้นทางนี้
    python scripts/verify_pipeline.py

ส่วนที่ต้องยิง API จริง (คุณภาพการอ่านใบเสร็จ) อยู่ที่ scripts/ocr_bench.py แยกต่างหาก
"""

import asyncio
import io
import sys
import time
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image, ImageDraw  # noqa: E402

RESULTS: list[tuple[str, bool, str]] = []


def check(name: str):
    """decorator ให้แต่ละหัวข้อรันแล้วเก็บผล ไม่ให้ข้อเดียวพังแล้วหยุดทั้งชุด"""

    def wrapper(fn):
        try:
            detail = fn() or ""
            RESULTS.append((name, True, detail))
        except AssertionError as e:
            RESULTS.append((name, False, str(e)))
        except Exception as e:
            RESULTS.append((name, False, f"{type(e).__name__}: {e}"))
        return fn

    return wrapper


def _make_receipt(width: int = 800, height: int = 3200) -> Image.Image:
    """ใบเสร็จจำลองที่มีบรรทัดยอดรวมอยู่โดดๆ ล่างสุด (จุดที่โค้ดเดิมทำหาย)"""
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    y = 60
    for block in range(8):
        for line in range(6):
            draw.text((40, y), f"ITEM {block}-{line} .......... {block * 10 + line}.00", fill="black")
            y += 22
        y += 90
    draw.text((40, height - 120), "TOTAL 1,234.00", fill="black")
    return img


def _dark_pixels(img: Image.Image) -> int:
    return img.convert("L").point(lambda p: 0 if p < 185 else 255).histogram()[0]


def _to_jpeg(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return buf.getvalue()


# ---------------------------------------------------------------- เตรียมรูป


@check("pre_process_image_file หมุนรูปตาม EXIF")
def _():
    from helper.utils import Utilities

    upright = _make_receipt(400, 900)
    rotated = upright.rotate(-90, expand=True)  # ภาพจริงถูกเก็บแบบตะแคง
    buf = io.BytesIO()
    exif = Image.Exif()
    exif[274] = 6  # Orientation = ต้องหมุน 90 องศาตามเข็ม
    rotated.save(buf, format="JPEG", exif=exif, quality=90)

    before = Image.open(io.BytesIO(buf.getvalue())).size
    after = Image.open(io.BytesIO(Utilities.pre_process_image_file(buf.getvalue()))).size
    assert after[1] > after[0], f"ยังตะแคงอยู่: {before} -> {after}"
    return f"{before} -> {after}"


@check("pre_process_image_file โหมด vlm คงภาพสี / legacy เป็นขาวดำ")
def _():
    from helper.utils import Utilities

    data = _to_jpeg(_make_receipt(600, 900))
    vlm = Image.open(io.BytesIO(Utilities.pre_process_image_file(data, mode="vlm")))
    legacy = Image.open(io.BytesIO(Utilities.pre_process_image_file(data, mode="legacy")))
    assert vlm.mode == "RGB", f"โหมด vlm ควรเป็น RGB แต่ได้ {vlm.mode}"
    assert legacy.mode == "L", f"โหมด legacy ควรเป็น L แต่ได้ {legacy.mode}"
    return f"vlm={vlm.mode} legacy={legacy.mode}"


@check("should_split_image แบ่งเฉพาะรูปที่ยาวผิดปกติ")
def _():
    from helper.utils import Utilities

    tall = _to_jpeg(_make_receipt(800, 3200))  # aspect 4.0
    normal = _to_jpeg(_make_receipt(800, 1200))  # aspect 1.5
    assert Utilities.should_split_image(tall), "รูปยาวควรถูกแบ่ง"
    assert not Utilities.should_split_image(normal), "รูปสัดส่วนปกติไม่ควรถูกแบ่ง"
    return "ยาว=แบ่ง / ปกติ=ไม่แบ่ง"


@check("split_image_into_text_blocks ไม่ทำข้อความหาย และเร็วพอ")
def _():
    from helper.utils import Utilities

    img = _make_receipt()
    data = _to_jpeg(img)

    started = time.monotonic()
    chunks = Utilities.split_image_into_text_blocks(data)
    elapsed_ms = (time.monotonic() - started) * 1000

    total_height = 0
    chunk_dark = 0
    for chunk in chunks:
        piece = Image.open(io.BytesIO(chunk))
        total_height += piece.height
        chunk_dark += _dark_pixels(piece)

    original_dark = _dark_pixels(img)
    assert total_height >= img.height, "ชิ้นที่ได้รวมกันไม่ครอบคลุมทั้งภาพ"
    assert chunk_dark >= original_dark * 0.99, (
        f"ข้อความหายไป เหลือ {chunk_dark / original_dark * 100:.1f}%"
    )
    assert elapsed_ms < 2000, f"ช้าเกินไป {elapsed_ms:.0f} ms"
    return f"{len(chunks)} ชิ้น, เก็บข้อความ {chunk_dark / original_dark * 100:.0f}%, {elapsed_ms:.0f} ms"


@check("_join_chunk_texts ตัดบรรทัดซ้ำตรงรอยต่อ")
def _():
    from ai.ocr import _join_chunk_texts

    first = "ร้านทดสอบ\nข้าวผัด 60.00\nน้ำเปล่า 10.00"
    second = "ข้าวผัด 60.00\nน้ำเปล่า 10.00\nรวม 70.00"
    joined = _join_chunk_texts([first, second])
    assert joined.count("ข้าวผัด") == 1, f"ยังซ้ำอยู่:\n{joined}"
    assert "รวม 70.00" in joined, "ข้อมูลท้ายชิ้นหลังหายไป"

    apart = _join_chunk_texts(["บรรทัด A", "บรรทัด B"])
    assert "บรรทัด A" in apart and "บรรทัด B" in apart, "ชิ้นที่ไม่ซ้ำกันต้องต่อครบ"
    return "ซ้ำถูกตัด / ไม่ซ้ำต่อครบ"


# ------------------------------------------------- ด่านคัดเอกสารการเงิน


@check("looks_like_money_document คัดถูกทั้งใบเสร็จจริงและข้อความมั่ว")
def _():
    from ai.ocr import looks_like_money_document

    slip = "Krungthai กรุงไทย\nโอนเงินสำเร็จ\nจำนวนเงิน 2,800.00 บาท\nค่าธรรมเนียม 0.00 บาท"
    receipt = "ใบเสร็จรับเงิน\nเนื้อวัว 92.00\nยอดสุทธิ : 269.00"
    assert looks_like_money_document(slip), "สลิปโอนเงินต้องผ่าน"
    assert looks_like_money_document(receipt), "ใบเสร็จต้องผ่าน"

    assert not looks_like_money_document("วันนี้อากาศดีจังเลยนะครับ"), "ข้อความทั่วไปไม่ควรผ่าน"
    assert not looks_like_money_document(""), "ข้อความว่างไม่ควรผ่าน"
    assert not looks_like_money_document("หน้า 12 บทที่ 3"), "ตัวเลขที่ไม่ใช่เงินไม่ควรผ่าน"
    return "สลิป/ใบเสร็จผ่าน, ข้อความทั่วไปไม่ผ่าน"


# ------------------------------------------- กติกาเลือกรายการที่จะบันทึก


@check("select_billable_items ตัดสินยอดถูกทุกรูปแบบใบเสร็จ")
def _():
    from model.db import select_billable_items

    cases = [
        # (ชื่อ, grand_total, รายการ, ยอดที่ควรบันทึก, ผลตรวจที่ควรได้)
        (
            "ใบแยก VAT",
            269.0,
            [
                {"amount": 92.0, "is_actual_item": True, "priority": False},
                {"amount": 150.0, "is_actual_item": True, "priority": False},
                {"amount": 9.4, "is_actual_item": True, "priority": False},
                {"amount": 17.6, "is_actual_item": False, "priority": True},
            ],
            269.0,
            True,
        ),
        (
            "ใบรวม VAT แล้ว",
            110.0,
            [
                {"amount": 110.0, "is_actual_item": True, "priority": False},
                {"amount": 7.2, "is_actual_item": False, "priority": True},
            ],
            110.0,
            True,
        ),
        (
            "มีบรรทัด Subtotal ปน",
            269.0,
            [
                {"amount": 92.0, "is_actual_item": True, "priority": False},
                {"amount": 150.0, "is_actual_item": True, "priority": False},
                {"amount": 9.4, "is_actual_item": True, "priority": False},
                {"amount": 251.4, "is_actual_item": False, "priority": False},
                {"amount": 17.6, "is_actual_item": False, "priority": True},
            ],
            269.0,
            True,
        ),
        ("สลิปโอนเงินรายการเดียว", 1500.0, [{"amount": 1500.0}], 1500.0, True),
        ("ไม่มี grand_total ให้เทียบ", None, [{"amount": 60.0}], 60.0, None),
        (
            "เลขไม่ลงตัวสักทาง",
            500.0,
            [
                {"amount": 92.0, "is_actual_item": True, "priority": False},
                {"amount": 7.0, "is_actual_item": False, "priority": True},
            ],
            99.0,
            False,
        ),
    ]

    for name, grand_total, items, expected_total, expected_matched in cases:
        picked, matched = select_billable_items(items, grand_total)
        total = sum(item["amount"] for item in picked)
        assert abs(total - expected_total) < 0.01, f"{name}: ยอด {total} ควรเป็น {expected_total}"
        assert matched is expected_matched, f"{name}: ผลตรวจ {matched} ควรเป็น {expected_matched}"

    return f"ผ่าน {len(cases)} รูปแบบ"


@check("บิลที่ผู้ใช้เห็นตรงกับยอดที่จะถูกบันทึก")
def _():
    from helper.utils import LineUtils
    from model.db import select_billable_items

    cases = {
        "ใบแยก VAT": {
            "grand_total": 269.0,
            "transactions": [
                {"item": "เนื้อวัว", "amount": 92.0, "category": "อาหารและเครื่องดื่ม",
                 "is_actual_item": True, "priority": False},
                {"item": "ไก่ผัก", "amount": 150.0, "category": "อาหารและเครื่องดื่ม",
                 "is_actual_item": True, "priority": False},
                {"item": "น้ำเปล่า", "amount": 9.4, "category": "อาหารและเครื่องดื่ม",
                 "is_actual_item": True, "priority": False},
                {"item": "VAT", "amount": 17.6, "category": "อื่นๆ",
                 "is_actual_item": False, "priority": True},
            ],
        },
        "ใบรวม VAT": {
            "grand_total": 110.0,
            "transactions": [
                {"item": "สินค้า", "amount": 110.0, "category": "ช้อปปิ้งและบันเทิง",
                 "is_actual_item": True, "priority": False},
                {"item": "VAT", "amount": 7.2, "category": "อื่นๆ",
                 "is_actual_item": False, "priority": True},
            ],
        },
    }

    details = []
    for name, data in cases.items():
        flex = LineUtils.create_dynamic_flex_receipt(data, temp_id="verify")
        amounts = []

        def walk(node):
            if isinstance(node, dict):
                text = node.get("text")
                if node.get("type") == "text" and isinstance(text, str) and text.startswith("฿"):
                    amounts.append(float(text.replace("฿", "").replace(",", "").strip()))
                for value in node.values():
                    walk(value)
            elif isinstance(node, list):
                for value in node:
                    walk(value)

        walk(flex)
        header, rows = amounts[0], amounts[1:]
        saved = sum(
            float(item["amount"])
            for item in select_billable_items(data["transactions"], data["grand_total"])[0]
        )
        assert abs(sum(rows) - saved) < 0.01, f"{name}: รายการใน Flex {sum(rows)} != ยอดบันทึก {saved}"
        assert abs(header - saved) < 0.01, f"{name}: หัวบิล {header} != ยอดบันทึก {saved}"
        details.append(f"{name} ฿{saved:,.2f}")

    return " / ".join(details)


# ------------------------------------------------ ด่านบังคับยืนยันก่อนบันทึก


class _FakeUser:
    def __init__(self, bypass: bool):
        self.use_bypass_mode = bypass


class _FakeLogger:
    def __init__(self):
        self.infos: list[str] = []
        self.errors: list[str] = []

    def info(self, module, message, user_id=None, payload=None):
        self.infos.append(message)

    def error(self, module, message, user_id=None, payload=None):
        self.errors.append(message)


_BAD = {
    "grand_total": 500.0,
    "transactions": [
        {"amount": 92.0, "item": "ก", "is_actual_item": True, "priority": False},
        {"amount": 7.0, "item": "VAT", "is_actual_item": False, "priority": True},
    ],
}
_GOOD = {
    "grand_total": 269.0,
    "transactions": [
        {"amount": 251.4, "item": "อาหาร", "is_actual_item": True, "priority": False},
        {"amount": 17.6, "item": "VAT", "is_actual_item": False, "priority": True},
    ],
}


@check("resolve_confirmation ตัดสินโหมดบันทึกด่วนถูกต้อง")
def _():
    from helper.webhook_helper import resolve_confirmation

    cases = [
        ("bypass ON + ยอดลงตัว", True, _GOOD, True, False),
        ("bypass ON + ยอดไม่ลงตัว", True, _BAD, False, True),
        ("bypass ON + ไม่มียอดสุทธิ", True, {"grand_total": None, "transactions": [{"amount": 60}]}, True, False),
        ("bypass ON + ส่งมาเป็น list", True, [{"amount": 60}], True, False),
        ("bypass OFF + ยอดไม่ลงตัว", False, _BAD, False, True),
        ("bypass OFF + ยอดลงตัว", False, _GOOD, False, False),
    ]
    for name, bypass, data, expect_skip, expect_review in cases:
        skip, review = resolve_confirmation(data, _FakeUser(bypass))
        assert (skip, review) == (expect_skip, expect_review), (
            f"{name}: ได้ (skip={skip}, review={review})"
        )
    return f"ผ่าน {len(cases)} สถานการณ์"


def _run_text_flow(user_text: str, extracted, bypass: bool):
    """เรียก handle_text_message จริงโดยแทน LINE API และ DB ด้วยตัวปลอม"""
    import helper.webhook_helper as wh

    logger = _FakeLogger()
    pushes: list = []
    saved: list = []
    temps: list = []

    patches = [
        patch.object(wh.LineUtils, "send_loading_indicator_v3"),
        patch.object(wh.LineUtils, "send_line_reply_v3"),
        patch.object(wh.LineUtils, "reply_budget_for_use"),
        patch.object(wh.LineUtils, "create_dynamic_flex_receipt", return_value={"type": "bubble"}),
        patch.object(
            wh.LineUtils,
            "send_push_notification",
            side_effect=lambda *a, **k: pushes.append(k.get("content") or a[1]),
        ),
        patch.object(wh, "extract_transactions", return_value=extracted),
        patch.object(
            wh.DBManagerTransactions,
            "confirm_and_save_transaction",
            side_effect=lambda *a, **k: saved.append(k)
            or {"undo_token": "u", "count": 1, "total": 0.0, "budgets": []},
        ),
        patch.object(
            wh.DBManagerTransactions,
            "save_temp_transaction",
            side_effect=lambda *a, **k: temps.append(k) or "temp-1",
        ),
    ]
    for p in patches:
        p.start()
    try:
        asyncio.run(
            wh.handle_text_message(
                None, "U1", user_text, "reply", "ltoken", "key", logger, _FakeUser(bypass)
            )
        )
    finally:
        for p in patches:
            p.stop()
    return logger, pushes, saved, temps


@check("ข้อความที่ไม่ใช่รายการรับ-จ่าย ตอบคำแนะนำ ไม่ใช่ error")
def _():
    logger, pushes, saved, _temps = _run_text_flow("วันนี้อากาศดีจัง", None, True)
    assert not logger.errors, f"เกิด error ที่ไม่ควรเกิด: {logger.errors}"
    assert not saved, "ไม่ควรบันทึกอะไรเลย"
    assert pushes and "ยังไม่เข้าใจ" in pushes[0], f"ควรตอบคำแนะนำ แต่ได้: {pushes}"
    return "ตอบคำแนะนำวิธีจด"


@check("bypass ON + ยอดไม่ลงตัว ต้องไม่บันทึกและต้องเตือน (ข้อความ)")
def _():
    logger, pushes, saved, temps = _run_text_flow("ค่าข้าว 500", _BAD, True)
    warned = any(isinstance(p, str) and "ไม่ตรงกับยอดสุทธิ" in p for p in pushes)
    assert not saved, "ยังบันทึกทันทีทั้งที่ยอดไม่ลงตัว"
    assert temps, "ต้องเก็บเป็น TempTransactions รอยืนยัน"
    assert warned, "ต้องส่งข้อความเตือนผู้ใช้"
    assert not logger.errors, f"เกิด error: {logger.errors}"
    return "ไม่บันทึก + เตือน + รอยืนยัน"


@check("bypass ON + ยอดลงตัว ยังบันทึกทันทีเหมือนเดิม (ข้อความ)")
def _():
    _logger, _pushes, saved, temps = _run_text_flow("ชาบู 269", _GOOD, True)
    assert saved, "โหมดบันทึกด่วนต้องยังทำงาน"
    assert not temps, "ไม่ควรเก็บเป็น temp"
    assert saved[0].get("grand_total") == 269.0, "ต้องส่ง grand_total ไปให้ save ด้วย"
    return "บันทึกทันที พร้อม grand_total"


def _run_image_flow(extracted, bypass: bool):
    """เรียก handle_image_message จริงโดยแทน LINE API, OCR และ DB ด้วยตัวปลอม"""
    import helper.webhook_helper as wh

    logger = _FakeLogger()
    pushes: list = []
    saved: list = []
    temps: list = []

    patches = [
        patch.object(wh.LineUtils, "send_loading_indicator_v3"),
        patch.object(wh.LineUtils, "send_line_reply_v3"),
        patch.object(wh.LineUtils, "reply_budget_for_use"),
        patch.object(wh.LineUtils, "get_content_line", return_value=b"fake-image"),
        patch.object(wh.LineUtils, "save_line_image", return_value="uploads/fake.jpg"),
        patch.object(wh.LineUtils, "create_dynamic_flex_receipt", return_value={"type": "bubble"}),
        patch.object(
            wh.LineUtils,
            "send_push_notification",
            side_effect=lambda *a, **k: pushes.append(k.get("content") or a[1]),
        ),
        patch.object(wh.Utilities, "pre_process_image_file", return_value=b"fake-image"),
        patch.object(wh, "extract_text_from_image", return_value={"success": True, "text": extracted}),
        patch.object(wh.DBManagerTransactions, "create_attachment_record", return_value="att-1"),
        patch.object(
            wh.DBManagerTransactions,
            "confirm_and_save_transaction",
            side_effect=lambda *a, **k: saved.append(k)
            or {"undo_token": "u", "count": 1, "total": 0.0, "budgets": []},
        ),
        patch.object(
            wh.DBManagerTransactions,
            "save_temp_transaction",
            side_effect=lambda *a, **k: temps.append(k) or "temp-1",
        ),
    ]
    for p in patches:
        p.start()
    try:
        asyncio.run(
            wh.handle_image_message(
                None, "U1", "msg-1", "reply", "ltoken", "key", logger, _FakeUser(bypass)
            )
        )
    finally:
        for p in patches:
            p.stop()
    return logger, pushes, saved, temps


@check("bypass ON + ยอดไม่ลงตัว ต้องไม่บันทึกและต้องเตือน (รูป)")
def _():
    logger, pushes, saved, temps = _run_image_flow(_BAD, True)
    warned = any(isinstance(p, str) and "ไม่ตรงกับยอดสุทธิ" in p for p in pushes)
    assert not saved, "ยังบันทึกทันทีทั้งที่ยอดไม่ลงตัว"
    assert temps and warned, "ต้องเก็บเป็น temp และเตือนผู้ใช้"
    assert not logger.errors, f"เกิด error: {logger.errors}"
    return "ไม่บันทึก + เตือน + รอยืนยัน"


@check("bypass ON + ยอดลงตัว บันทึกทันทีพร้อมไฟล์แนบ (รูป)")
def _():
    _logger, _pushes, saved, temps = _run_image_flow(_GOOD, True)
    assert saved and not temps, "โหมดบันทึกด่วนต้องยังทำงาน"
    assert saved[0].get("grand_total") == 269.0, "ต้องส่ง grand_total ไปด้วย"
    assert saved[0].get("attachment_id") == "att-1", "ต้องผูกไฟล์แนบไปด้วย"
    return "บันทึกทันที + ผูก attachment"


# ----------------------------------------------------------- Admin console


class _FakeQuery:
    def __init__(self, result):
        self._result = result

    def first(self):
        return self._result

    def all(self):
        return self._result or []


class _FakeSession:
    """session ปลอมไว้ตรวจ logic ของ DBManagerAdmin โดยไม่แตะฐานข้อมูลจริง"""

    def __init__(self, result=None):
        self._result = result
        self.added: list = []
        self.commits = 0

    def exec(self, _statement):
        return _FakeQuery(self._result)

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        self.commits += 1

    def refresh(self, _obj):
        pass

    def rollback(self):
        pass


def _admin_routes():
    from routes.api_administrator_v1 import AdministratorAPIs

    api = AdministratorAPIs(logger=_FakeLogger(), line_access_token="fake-token")
    api.setup_router()
    return api.router.routes


@check("สร้าง router ของ admin ได้โดยไม่แตะฐานข้อมูลตอน startup")
def _():
    routes = _admin_routes()
    assert routes, "ไม่มี route ถูกลงทะเบียน"
    return f"ลงทะเบียน {len(routes)} route โดยไม่ query DB"


@check("ทุก route ของ admin ต้องผ่าน get_current_user")
def _():
    import inspect

    from middleware.auth import get_current_user

    unprotected = []
    for route in _admin_routes():
        signature = inspect.signature(route.endpoint)
        guarded = any(
            getattr(param.default, "dependency", None) is get_current_user
            for param in signature.parameters.values()
        )
        if not guarded:
            unprotected.append(f"{next(iter(route.methods))} {route.path}")

    assert not unprotected, f"route ที่ไม่มีการตรวจสิทธิ์: {', '.join(unprotected)}"
    return f"ป้องกันครบ {len(_admin_routes())} route"


@check("get_system_config_data เรียกด้วย session อย่างเดียวได้")
def _():
    import inspect

    from model.db import DBManagerAdmin

    params = list(inspect.signature(DBManagerAdmin.get_system_config_data).parameters)
    assert params == ["session"], f"signature ผิด: {params}"

    result = DBManagerAdmin.get_system_config_data(_FakeSession([]))
    assert result["success"] is True, result
    return "signature ถูก และเรียกได้จริง"


@check("sync_administrator_profile ไม่สร้าง admin ใหม่ให้ uid ที่ไม่มีสิทธิ์")
def _():
    from model.db import DBManagerAdmin

    session = _FakeSession(None)  # ไม่พบ uid นี้ในตาราง
    result = DBManagerAdmin.sync_administrator_profile(
        session, uid="uid-ที่ไม่เคยมี", email="attacker@example.com"
    )
    assert result["success"] is False, "ต้องปฏิเสธ ไม่ใช่สร้างให้"
    assert not session.added, "ห้ามเขียนแถวใหม่ลงตาราง Administrator"
    assert session.commits == 0, "ห้าม commit อะไรทั้งสิ้น"
    return "ปฏิเสธและไม่เขียน DB"


@check("get_current_user ปฏิเสธ admin ที่ถูกปิดใช้งาน")
def _():
    import asyncio as _asyncio

    from fastapi import HTTPException

    import middleware.auth as auth_module

    class _Credentials:
        credentials = "fake-token"

    class _DisabledAdmin:
        uid = "uid-1"
        is_active = False

    class _FakeDBSession:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def exec(self, _statement):
            return _FakeQuery(_DisabledAdmin())

    with patch.object(auth_module.auth, "verify_id_token", return_value={"uid": "uid-1"}), \
         patch.object(auth_module, "Session", lambda _engine: _FakeDBSession()):
        try:
            _asyncio.run(auth_module.get_current_user(_Credentials()))
            raise AssertionError("ต้องปฏิเสธ แต่กลับผ่าน")
        except HTTPException as e:
            assert e.status_code == 403, f"ควรได้ 403 แต่ได้ {e.status_code}: {e.detail}"

    return "ตอบ 403 Forbidden"


@check("clear_config_cache ถูกเรียกหลังเขียน DB เสร็จ")
def _():
    import routes.api_administrator_v1 as admin_routes

    order: list[str] = []
    route = next(
        r for r in _admin_routes() if r.path.endswith("/config/update") and "PATCH" in r.methods
    )

    class _Admin:
        uid = "uid-1"

    with patch.object(
        admin_routes.DBManagerAdmin,
        "update_system_config",
        side_effect=lambda *a, **k: order.append("write") or {"success": True},
    ), patch.object(
        admin_routes.Utilities,
        "clear_config_cache",
        side_effect=lambda: order.append("clear_cache"),
    ):
        route.endpoint(
            data={"key": "is_maintenance_mode", "value": "true"},
            db=_FakeSession(),
            user=_Admin(),
        )

    assert order == ["write", "clear_cache"], f"ลำดับผิด: {order}"
    return " -> ".join(order)


@check("update/create system config คืน error แทนที่จะพังเมื่อชื่อซ้ำ")
def _():
    from sqlalchemy.exc import IntegrityError

    from model.db import DBManagerAdmin

    class _ConflictSession(_FakeSession):
        def commit(self):
            raise IntegrityError("duplicate", None, Exception("duplicate"))

    class _Existing:
        key = "k"
        value = "v"
        value_type = "string"
        description = None
        name = "old"
        updated_at = None

    result = DBManagerAdmin.update_system_config(
        _ConflictSession(_Existing()), key="k", value="v", name="ชื่อซ้ำ"
    )
    assert result["success"] is False and "ถูกใช้ไปแล้ว" in result["message"], result

    created = DBManagerAdmin.create_system_config(
        _ConflictSession(), "ชื่อซ้ำ", "k", "v", "string", None
    )
    assert created["success"] is False, created
    return "คืน success=False พร้อมข้อความภาษาไทย"


@check("get_system_status ไม่ล้มแม้ DB และ LINE API ใช้ไม่ได้")
def _():
    from model.db import DBManagerAdmin

    class _BrokenSession:
        def exec(self, _statement):
            raise RuntimeError("database is down")

    status = DBManagerAdmin.get_system_status(_BrokenSession(), line_access_token=None)
    assert status["database"]["ok"] is False, "ต้องรายงานว่า DB ล่ม ไม่ใช่โยน exception"
    assert status["line_api"]["ok"] is False, "ไม่มี token ต้องรายงานว่าใช้ไม่ได้"
    assert set(status["features"]) == {
        "is_ocr_active",
        "is_text_active",
        "is_maintenance_mode",
    }, status["features"]
    return "รายงานสถานะครบโดยไม่ล้ม"


@check("feature_enabled ค่าเริ่มต้นเป็นเปิดเสมอ")
def _():
    import helper.webhook_helper as wh

    with patch.object(wh.Utilities, "get_config_value", side_effect=lambda key, default: default):
        assert wh.feature_enabled("is_ocr_active") is True, "ยังไม่ได้สร้าง config ต้องถือว่าเปิด"

    with patch.object(wh.Utilities, "get_config_value", return_value=False):
        assert wh.feature_enabled("is_ocr_active") is False, "ตั้งเป็น false ต้องปิด"

    return "ไม่มี config = เปิด / false = ปิด"


def _run_webhook_event(message: dict, disabled_key: str | None):
    """เรียก process_webhook_event จริง โดยปิดสวิตช์ฟีเจอร์ที่ระบุ"""
    import helper.webhook_helper as wh

    logger = _FakeLogger()
    pushes: list = []
    handled: list = []

    def fake_config(key, default=None):
        if key == disabled_key:
            return False
        return default if default is not None else True

    async def record_text(*_a, **_k):
        handled.append("text")

    async def record_image(*_a, **_k):
        handled.append("image")

    patches = [
        patch.object(wh.LineUtils, "get_line_profile", return_value={"displayName": "ผู้ใช้ทดสอบ"}),
        patch.object(wh.DBManagerUsers, "get_or_create_user", return_value=_FakeUser(False)),
        patch.object(wh.Utilities, "get_config_value", side_effect=fake_config),
        patch.object(wh, "handle_text_message", side_effect=record_text),
        patch.object(wh, "handle_image_message", side_effect=record_image),
        patch.object(
            wh.LineUtils,
            "send_push_notification",
            side_effect=lambda *a, **k: pushes.append(k.get("content") or a[1]),
        ),
    ]
    for p in patches:
        p.start()
    try:
        asyncio.run(
            wh.process_webhook_event(
                None,
                {"type": "message", "message": message},
                "U1",
                "reply",
                "ltoken",
                "key",
                logger,
            )
        )
    finally:
        for p in patches:
            p.stop()
    return pushes, handled


@check("ปิดสวิตช์ OCR แล้ว webhook ต้องไม่ประมวลผลรูป")
def _():
    pushes, handled = _run_webhook_event({"type": "image", "id": "m1"}, "is_ocr_active")
    assert not handled, "ยังเรียก handler ทั้งที่ปิดสวิตช์แล้ว"
    assert any("ปิดปรับปรุงชั่วคราว" in str(p) for p in pushes), f"ต้องแจ้งผู้ใช้: {pushes}"

    pushes, handled = _run_webhook_event({"type": "image", "id": "m1"}, None)
    assert handled == ["image"], "เปิดสวิตช์แล้วต้องประมวลผลตามปกติ"
    return "ปิด=ไม่ประมวลผล+แจ้งผู้ใช้ / เปิด=ทำงานปกติ"


@check("ปิดสวิตช์ข้อความแล้ว webhook ต้องไม่ประมวลผลข้อความ")
def _():
    pushes, handled = _run_webhook_event({"type": "text", "text": "ค่าข้าว 60"}, "is_text_active")
    assert not handled, "ยังเรียก handler ทั้งที่ปิดสวิตช์แล้ว"
    assert any("ปิดปรับปรุงชั่วคราว" in str(p) for p in pushes), f"ต้องแจ้งผู้ใช้: {pushes}"

    pushes, handled = _run_webhook_event({"type": "text", "text": "ค่าข้าว 60"}, None)
    assert handled == ["text"], "เปิดสวิตช์แล้วต้องประมวลผลตามปกติ"
    return "ปิด=ไม่ประมวลผล+แจ้งผู้ใช้ / เปิด=ทำงานปกติ"


def main() -> int:
    passed = sum(1 for _n, ok, _d in RESULTS if ok)
    width = max(len(name) for name, _ok, _d in RESULTS)

    print()
    for name, ok, detail in RESULTS:
        mark = "PASS" if ok else "FAIL"
        print(f"  [{mark}] {name.ljust(width)}  {detail}")

    print(f"\n  ผ่าน {passed}/{len(RESULTS)} หัวข้อ")
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
