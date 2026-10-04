"""
เพิ่ม / แก้ไข / ปิดใช้งาน ผู้ดูแลระบบ (Administrator)

เป็น **ทางเดียว** ที่สร้าง admin ใหม่ได้ เพราะ `POST /api/administrator/sync` ถูกปิดไม่ให้
สร้างแถวใหม่แล้ว (ถ้าเปิดไว้ ใครที่สมัคร Firebase account เองก็ยกระดับตัวเองเป็น admin ได้)

ขั้นตอน
-------
ระบุแค่ --email ได้เลย สคริปต์จะทำให้ครบทั้งสองฝั่ง
1) Firebase Authentication — หา UID จากอีเมล ถ้ายังไม่มีบัญชีจะสร้างให้ (ถามรหัสผ่านแบบไม่แสดงบนจอ)
2) ระบบเรา — ผูก role จากตาราง `Role` (สร้างแถว admin / viewer ให้ถ้ายังไม่มี)
   แล้วเพิ่มหรืออัปเดตแถว `Administrator` ด้วย `role_id`

รันซ้ำได้ — บัญชี Firebase ที่มีอยู่แล้วจะใช้ UID เดิม ไม่สร้างซ้ำ

    python scripts/seed_admin.py --email admin@example.com --name "ชื่อผู้ดูแล"
    python scripts/seed_admin.py --email viewer@example.com --role viewer
    python scripts/seed_admin.py --email admin@example.com --reset-password
    python scripts/seed_admin.py --email admin@example.com --deactivate
    python scripts/seed_admin.py --list

ถ้ามี UID อยู่แล้ว (เช่น สร้างผ่านคอนโซล Firebase) ใช้ --uid แทนได้ จะไม่แตะ Firebase

    python scripts/seed_admin.py --uid <firebase-uid> --email admin@example.com
"""

import argparse
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from firebase_admin import auth  # noqa: E402
from sqlalchemy.orm import selectinload  # noqa: E402
from sqlmodel import Session, select  # noqa: E402

# import middleware.auth = initialize Firebase Admin SDK จาก FIREBASE_ACCOUNT_KEY ไปด้วย
from middleware.auth import KNOWN_ROLES, ROLE_ADMIN, ROLE_VIEWER  # noqa: E402
from model.models import Administrator, Role, engine  # noqa: E402
from model.permissionEnum import PermissionEnum  # noqa: E402

# ค่าเริ่มต้นตอนตาราง Role ยังว่าง — viewer ได้เฉพาะสิทธิ์ดู/อ่าน
DEFAULT_ROLES = {
    ROLE_ADMIN: ("แก้ไขได้ทุกอย่าง", list(PermissionEnum)),
    ROLE_VIEWER: (
        "เข้าดูได้อย่างเดียว",
        [p for p in PermissionEnum if p.value.endswith(("_view", "_read"))],
    ),
}


def get_or_create_role(session: Session, name: str) -> Role:
    role = session.exec(select(Role).where(Role.name == name)).first()
    if role:
        return role

    description, permissions = DEFAULT_ROLES[name]
    role = Role(name=name, description=description, permissions=[p.value for p in permissions])
    session.add(role)
    session.commit()
    session.refresh(role)
    print(f"สร้าง role '{name}' ในตาราง Role แล้ว (id={role.id})")
    return role


def list_admins(session: Session) -> None:
    admins = session.exec(
        select(Administrator)
        .options(selectinload(Administrator.role_data))
        .order_by(Administrator.created_at)
    ).all()
    if not admins:
        print("ยังไม่มีผู้ดูแลระบบในตาราง Administrator")
        return

    print(f"ผู้ดูแลระบบทั้งหมด {len(admins)} คน\n")
    print(f"  {'สถานะ':<8} {'role':<8} {'email':<32} uid")
    for admin in admins:
        status = "ใช้งาน" if admin.is_active else "ปิดอยู่"
        print(f"  {status:<8} {admin.role or '-':<8} {admin.email:<32} {admin.uid}")


def prompt_password() -> str | None:
    password = getpass.getpass("รหัสผ่าน (อย่างน้อย 6 ตัวอักษร): ")
    if len(password) < 6:
        print("รหัสผ่านต้องยาวอย่างน้อย 6 ตัวอักษร (ข้อกำหนดของ Firebase)")
        return None
    if getpass.getpass("ยืนยันรหัสผ่าน: ") != password:
        print("รหัสผ่านทั้งสองครั้งไม่ตรงกัน")
        return None
    return password


def resolve_firebase_uid(args: argparse.Namespace) -> str | None:
    """หา UID จากอีเมลใน Firebase ถ้ายังไม่มีบัญชีให้สร้างใหม่ (ยกเว้นตอน activate/deactivate)"""
    try:
        fb_user = auth.get_user_by_email(args.email)
    except auth.UserNotFoundError:
        fb_user = None

    if fb_user:
        print(f"พบบัญชี Firebase เดิม: {fb_user.email} (uid: {fb_user.uid})")
        if args.reset_password:
            password = prompt_password()
            if not password:
                return None
            auth.update_user(fb_user.uid, password=password)
            print("ตั้งรหัสผ่านใหม่ใน Firebase แล้ว")
        return fb_user.uid

    if args.deactivate or args.activate or args.reset_password:
        print(f"ไม่พบบัญชี Firebase ของ {args.email}")
        return None

    print(f"ยังไม่มีบัญชี Firebase ของ {args.email} — จะสร้างใหม่")
    password = prompt_password()
    if not password:
        return None

    try:
        fb_user = auth.create_user(
            email=args.email,
            password=password,
            display_name=args.name or None,
        )
    except (ValueError, auth.EmailAlreadyExistsError) as e:
        print(f"สร้างบัญชี Firebase ไม่สำเร็จ: {e}")
        return None

    print(f"สร้างบัญชี Firebase แล้ว (uid: {fb_user.uid})")
    return fb_user.uid


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
        # admin เดิมที่ยังไม่มี role_id (ก่อนย้ายมาใช้ตาราง Role) ให้ได้ role เริ่มต้นไปด้วย
        if args.role or admin.role_id is None:
            admin.role_id = get_or_create_role(session, args.role or ROLE_ADMIN).id
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
        role_id=get_or_create_role(session, args.role or ROLE_ADMIN).id,
    )
    session.add(admin)
    session.commit()
    session.refresh(admin)
    print(f"สร้างผู้ดูแลระบบใหม่แล้ว: {admin.email} (role={admin.role})")
    print(f"  uid: {admin.uid}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="จัดการผู้ดูแลระบบของ JodNid")
    parser.add_argument(
        "--uid",
        help="Firebase UID ที่มีอยู่แล้ว (ไม่ระบุก็ได้ ถ้าใส่ --email จะหา/สร้างใน Firebase ให้)",
    )
    parser.add_argument("--email", help="อีเมล (จำเป็นตอนสร้างใหม่)")
    parser.add_argument("--name", help="ชื่อที่แสดง")
    parser.add_argument(
        "--role",
        choices=KNOWN_ROLES,
        help="admin = แก้ไขได้ทุกอย่าง, viewer = เข้าดูได้อย่างเดียว (ค่าเริ่มต้น admin)",
    )
    parser.add_argument("--list", action="store_true", help="แสดงผู้ดูแลระบบทั้งหมด")
    parser.add_argument("--deactivate", action="store_true", help="ปิดการใช้งานผู้ดูแลระบบคนนี้")
    parser.add_argument("--activate", action="store_true", help="เปิดการใช้งานผู้ดูแลระบบคนนี้")
    parser.add_argument(
        "--reset-password",
        action="store_true",
        help="ตั้งรหัสผ่านใหม่ให้บัญชี Firebase ที่มีอยู่แล้ว (ใช้คู่กับ --email)",
    )
    args = parser.parse_args()

    if args.deactivate and args.activate:
        print("เลือก --activate กับ --deactivate พร้อมกันไม่ได้")
        return 1

    with Session(engine) as session:
        if args.list:
            list_admins(session)
            return 0

        if not args.uid and not args.email:
            parser.print_help()
            return 1

        if args.uid and args.reset_password:
            print("--reset-password ใช้คู่กับ --email โดยไม่ระบุ --uid")
            return 1

        if not args.uid:
            uid = resolve_firebase_uid(args)
            if not uid:
                return 1
            args.uid = uid

        return upsert_admin(session, args)


if __name__ == "__main__":
    raise SystemExit(main())
