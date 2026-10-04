"""
สร้างค่า SystemConfiguration พื้นฐานให้ครบ เพื่อให้สวิตช์ในหน้า admin console มีให้กดตั้งแต่แรก

รันซ้ำได้ปลอดภัย — ตัวที่มีอยู่แล้วจะถูกข้าม ไม่ทับค่าที่ admin ตั้งไว้

    python scripts/seed_config.py           # สร้างเฉพาะตัวที่ยังไม่มี
    python scripts/seed_config.py --list    # ดูว่ามีอะไรอยู่แล้วบ้าง
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlmodel import Session, select  # noqa: E402

from model.models import SystemConfiguration, engine  # noqa: E402

# ค่าเริ่มต้นต้องตรงกับ default ที่โค้ดฝั่ง webhook ใช้จริง
# (helper/webhook_helper.py `feature_enabled` และ index.py `is_maintenance_mode`)
DEFAULT_CONFIGS = [
    {
        "name": "เปิดใช้งานการอ่านสลิป (OCR)",
        "key": "is_ocr_active",
        "value": "true",
        "value_type": "boolean",
        "description": "ปิดเมื่อ Typhoon OCR มีปัญหา ผู้ใช้ที่ส่งรูปจะได้ข้อความแจ้งปิดปรับปรุงแทน",
    },
    {
        "name": "เปิดใช้งานการจดด้วยข้อความ",
        "key": "is_text_active",
        "value": "true",
        "value_type": "boolean",
        "description": "ปิดเมื่อโมเดลสกัดข้อความมีปัญหา ผู้ใช้ที่พิมพ์ข้อความจะได้ข้อความแจ้งปิดปรับปรุงแทน",
    },
    {
        "name": "โหมดปิดปรับปรุงระบบ",
        "key": "is_maintenance_mode",
        "value": "false",
        "value_type": "boolean",
        "description": "เปิดเพื่อหยุดรับ event จาก LINE ทั้งหมด ใช้ตอนแก้ระบบหรือย้ายฐานข้อมูล",
    },
]


def list_configs(session: Session) -> None:
    configs = session.exec(select(SystemConfiguration).order_by(SystemConfiguration.key)).all()
    if not configs:
        print("ยังไม่มีค่าตั้งค่าใดๆ ในตาราง SystemConfiguration")
        return

    print(f"ค่าตั้งค่าทั้งหมด {len(configs)} รายการ\n")
    for config in configs:
        print(f"  {config.key:<24} = {config.value:<10} ({config.value_type})  {config.name}")


def seed(session: Session) -> int:
    created = 0
    for item in DEFAULT_CONFIGS:
        exists = session.exec(
            select(SystemConfiguration).where(SystemConfiguration.key == item["key"])
        ).first()
        if exists:
            print(f"  ข้าม {item['key']:<24} (มีอยู่แล้ว ค่าปัจจุบัน = {exists.value})")
            continue

        session.add(SystemConfiguration(**item))
        created += 1
        print(f"  สร้าง {item['key']:<24} = {item['value']}")

    if created:
        session.commit()
    print(f"\nสร้างใหม่ {created} รายการ จากทั้งหมด {len(DEFAULT_CONFIGS)} รายการ")
    if created:
        print("อย่าลืมกด 'Refresh Cache' ใน admin console ถ้าแอปกำลังรันอยู่")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="สร้างค่าตั้งค่าพื้นฐานของ JodNid")
    parser.add_argument("--list", action="store_true", help="แสดงค่าตั้งค่าที่มีอยู่")
    args = parser.parse_args()

    with Session(engine) as session:
        if args.list:
            list_configs(session)
            return 0
        return seed(session)


if __name__ == "__main__":
    raise SystemExit(main())
