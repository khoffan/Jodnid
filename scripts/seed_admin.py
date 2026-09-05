"""
เพิ่ม / แก้ไข / ปิดใช้งาน ผู้ดูแลระบบ (Administrator)

เป็น **ทางเดียว** ที่สร้าง admin ใหม่ได้ เพราะ `POST /api/administrator/sync` ถูกปิดไม่ให้
สร้างแถวใหม่แล้ว (ถ้าเปิดไว้ ใครที่สมัคร Firebase account เองก็ยกระดับตัวเองเป็น admin ได้)

ขั้นตอน
-------
1) สร้างผู้ใช้ใน Firebase Authentication ก่อน (คอนโซล Firebase) แล้วคัดลอก UID มา
2) รันคำสั่งนี้เพื่อให้สิทธิ์ admin กับ UID นั้น

    python scripts/seed_admin.py --uid <firebase-uid> --email admin@example.com --name "ชื่อผู้ดูแล"
    python scripts/seed_admin.py --list
    python scripts/seed_admin.py --uid <firebase-uid> --deactivate
    python scripts/seed_admin.py --uid <firebase-uid> --activate
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlmodel import Session, select  # noqa: E402

from model.models import Administrator, engine  # noqa: E402


def list_admins(session: Session) -> None:
    admins = session.exec(select(Administrator).order_by(Administrator.created_at)).all()
    if not admins:
        print("ยังไม่มีผู้ดูแลระบบในตาราง Administrator")
        return

    print(f"ผู้ดูแลระบบทั้งหมด {len(admins)} คน\n")
    print(f"  {'สถานะ':<8} {'role':<8} {'email':<32} uid")
    for admin in admins:
        status = "ใช้งาน" if admin.is_active else "ปิดอยู่"
        print(f"  {status:<8} {admin.role:<8} {admin.email:<32} {admin.uid}")


def upsert_admin(session: Session, args: argparse.Namespace) -> int:
    admin = session.exec(select(Administrator).where(Administrator.uid == args.uid)).first()

    if args.deactivate or args.activate:
        if not admin:
            print(f"ไม่พบผู้ดูแลระบบ uid: {args.uid}")
            return 1
        admin.is_active = bool(args.activate)
        session.add(admin)
        session.commit()
        print(f"{'เปิด' if admin.is_active else 'ปิด'}การใช้งาน {admin.email} แล้ว")
        return 0

    if admin:
        if args.email:
            admin.email = args.email
        if args.name:
            admin.name = args.name
        if args.role:
            admin.role = args.role
        session.add(admin)
        session.commit()
        session.refresh(admin)
        print(f"อัปเดตผู้ดูแลระบบเดิมแล้ว: {admin.email} (role={admin.role})")
        return 0

    if not args.email:
        print("การสร้างผู้ดูแลระบบใหม่ต้องระบุ --email ด้วย")
        return 1

    admin = Administrator(
        uid=args.uid,
        email=args.email,
        name=args.name,
        role=args.role or "admin",
    )
    session.add(admin)
    session.commit()
    session.refresh(admin)
    print(f"สร้างผู้ดูแลระบบใหม่แล้ว: {admin.email} (role={admin.role})")
    print(f"  uid: {admin.uid}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="จัดการผู้ดูแลระบบของ JodNid")
    parser.add_argument("--uid", help="Firebase UID ของผู้ใช้ที่จะให้สิทธิ์")
    parser.add_argument("--email", help="อีเมล (จำเป็นตอนสร้างใหม่)")
    parser.add_argument("--name", help="ชื่อที่แสดง")
    parser.add_argument("--role", help="สิทธิ์ เช่น admin หรือ viewer (ค่าเริ่มต้น admin)")
    parser.add_argument("--list", action="store_true", help="แสดงผู้ดูแลระบบทั้งหมด")
    parser.add_argument("--deactivate", action="store_true", help="ปิดการใช้งานผู้ดูแลระบบคนนี้")
    parser.add_argument("--activate", action="store_true", help="เปิดการใช้งานผู้ดูแลระบบคนนี้")
    args = parser.parse_args()

    if args.deactivate and args.activate:
        print("เลือก --activate กับ --deactivate พร้อมกันไม่ได้")
        return 1

    with Session(engine) as session:
        if args.list:
            list_admins(session)
            return 0

        if not args.uid:
            parser.print_help()
            return 1

        return upsert_admin(session, args)


if __name__ == "__main__":
    raise SystemExit(main())
