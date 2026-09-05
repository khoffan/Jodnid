from fastapi import APIRouter, Depends
from sqlmodel import Session

from helper.logger import JodNidLogger
from helper.utils import Utilities
from middleware.auth import get_current_user
from model.db import DBManagerAdmin
from model.models import Administrator, get_session


class AdministratorAPIs:
    def __init__(self, logger: JodNidLogger, line_access_token: str):
        self.logger = logger
        self.line_access_token = line_access_token
        self.router = APIRouter(prefix="/api/administrator", tags=["administrator"])

    def setup_router(self):
        router = self.router
        logger = self.logger

        # administrator service
        @router.post("/sync")
        async def sync_data(
            data: dict,
            db: Session = Depends(get_session),
            user: Administrator = Depends(get_current_user),
        ):
            """
            อัปเดตโปรไฟล์ของ admin ให้ตรงกับ Firebase หลังล็อกอิน

            ยึด uid จาก token ที่ verify แล้วเท่านั้น ไม่เชื่อค่าใน body เพราะเป็น endpoint
            ที่ตัดสินสิทธิ์ และตัว `sync_administrator_profile` จะไม่สร้าง admin ใหม่ให้
            """
            result = DBManagerAdmin.sync_administrator_profile(
                db,
                uid=user.uid,
                email=data.get("email"),
                name=data.get("name"),
                phone=data.get("phone"),
                profile=data.get("profile"),
            )
            logger.info(
                module="administrator",
                message=f"profile sync for uid: {user.uid} success: {result.get('success')}",
                user_id=user.uid,
            )
            return result

        @router.post("/config/create")
        async def create_system_configuration(
            data: dict,
            db: Session = Depends(get_session),
            user: Administrator = Depends(get_current_user),
        ):
            name = data.get("name")
            key = data.get("key")
            value = data.get("value")
            value_type = data.get("value_type")
            description = data.get("description")
            if not name or not key or not value or not value_type:
                return {"success": False, "message": "Missing name or key or value or value_type"}

            logger.info(
                module="app",
                message=f"Creating system configuration for name: {name}, key: {key}, value: {value}, value_type: {value_type}, description: {description}",
                user_id=user.uid,
            )
            return DBManagerAdmin.create_system_config(
                db, name, key, value, value_type, description
            )

        @router.get("/all")
        def get_all_system_configuration(
            db: Session = Depends(get_session), user: Administrator = Depends(get_current_user)
        ):
            logger.info(
                module="app", message="Fetching all system configurations", user_id=user.uid
            )
            return DBManagerAdmin.get_system_config_data(db)

        @router.patch("/config/update")
        def update_system_configuration(
            data: dict,
            db: Session = Depends(get_session),
            user: Administrator = Depends(get_current_user),
        ):
            key = data.get("key")
            value = data.get("value")
            value_type = data.get("value_type")
            description = data.get("description")
            if not key or not value:
                return {"success": False, "message": "Missing key or value"}
            logger.info(
                module="app",
                message=f"Updating system configuration for key: {key}, value: {value}, value_type: {value_type}, description: {description}",
                user_id=user.uid,
            )
            result = DBManagerAdmin.update_system_config(
                db, key, value, value_type, description, name=data.get("name")
            )
            # ต้องล้าง cache "หลัง" เขียน DB เสร็จ ไม่งั้นมีช่วงที่ค่าเก่าถูกอ่านกลับเข้า cache
            Utilities.clear_config_cache()
            return result

        @router.patch("/config/toggle")
        def toggle_system_configuration(
            data: dict,
            db: Session = Depends(get_session),
            user: Administrator = Depends(get_current_user),
        ):
            key = data.get("key")
            value = data.get("value")
            if not key or not value:
                return {"success": False, "message": "Missing key or value"}
            logger.info(
                module="app",
                message=f"Toggling system configuration for key: {key}, value: {value}",
                user_id=user.uid,
            )
            result = DBManagerAdmin.update_system_config(db, key, value)
            Utilities.clear_config_cache()
            return result
