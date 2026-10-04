import json

import firebase_admin
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth, credentials
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from core.config_settings import settings
from model.models import Administrator, engine

# 1. Initialize Firebase (ควรใช้ environment variable เพื่อความปลอดภัย)
if not firebase_admin._apps:
    try:
        firebase_key_json = json.loads(settings.FIREBASE_ACCOUNT_KEY)
        # ใน Production แนะนำให้ใช้ ENV หรือโหลดไฟล์ผ่าน Path ที่ปลอดภัย
        cred = credentials.Certificate(firebase_key_json)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        # ตั้งค่า Firebase ไม่ได้ = ตรวจ token ของ admin ไม่ได้ทั้งระบบ ให้แอปล้มตั้งแต่ startup ดีกว่า
        raise RuntimeError("Error initializing Firebase: invalid FIREBASE_ACCOUNT_KEY") from e

# ใช้ HTTPBearer เพื่อดักจับ Header "Authorization: Bearer <token>"
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    ฟังก์ชัน Dependency สำหรับตรวจสอบ Firebase ID Token
    """
    token = credentials.credentials

    try:
        # 2. ตรวจสอบ Token กับ Firebase
        decoded_token = auth.verify_id_token(token)

        # คืนค่าข้อมูล User (เช่น uid, email, name) ออกไปให้ Route เรียกใช้
        # โหลด role_data มาพร้อมกัน — object ถูกใช้หลังปิด session (require_role อ่าน user.role)
        statement = (
            select(Administrator)
            .where(Administrator.uid == decoded_token["uid"])
            .options(selectinload(Administrator.role_data))
        )
        with Session(engine) as session:
            userAdmin = session.exec(statement).first()

            if not userAdmin:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="บัญชีนี้ไม่มีสิทธิ์เข้าใช้งาน console",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # ต้องเช็คด้วย ไม่งั้นการปิดใช้งาน admin ในตารางจะไม่มีผลอะไรเลย
            if not userAdmin.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="บัญชีผู้ดูแลนี้ถูกปิดใช้งาน",
                )

            return userAdmin

    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="เซสชันหมดอายุ กรุณาเข้าสู่ระบบใหม่",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except HTTPException:
        # ต้องดักก่อน `except Exception` ไม่งั้นผลการตรวจสิทธิ์ด้านบนจะถูกกลืน
        # แล้วกลายเป็น 401 "ยืนยันตัวตนไม่สำเร็จ" ทุกกรณี
        raise
    except Exception:
        # ไม่แนบข้อความ exception — อาจมีรายละเอียดภายในของ Firebase/ระบบ
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ยืนยันตัวตนไม่สำเร็จ กรุณาเข้าสู่ระบบใหม่",
            headers={"WWW-Authenticate": "Bearer"},
        )


# บทบาทที่ระบบรู้จัก — `viewer` เข้าดูได้อย่างเดียว แก้อะไรไม่ได้
ROLE_ADMIN = "admin"
ROLE_VIEWER = "viewer"
KNOWN_ROLES = (ROLE_ADMIN, ROLE_VIEWER)


def require_role(*allowed_roles: str):
    """
    Dependency สำหรับ route ที่ต้องการบทบาทเฉพาะ

    เทียบกับชื่อ role ในตาราง `Role` (ผ่าน `Administrator.role_id`) — admin ที่ไม่มี role_id
    จะได้ `role = None` และถูกปฏิเสธทุก route ที่เขียนข้อมูล

    ใช้กับ route ที่ "เขียน" ข้อมูล ส่วน route ที่อ่านอย่างเดียวใช้ `get_current_user` ตามเดิม
    """

    async def dependency(user: Administrator = Depends(get_current_user)) -> Administrator:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"ต้องมีสิทธิ์ {' หรือ '.join(allowed_roles)} จึงจะทำรายการนี้ได้",
            )
        return user

    return dependency
