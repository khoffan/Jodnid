from fastapi import APIRouter, Depends
from sqlmodel import Session

from helper.logger import JodNidLogger
from helper.utils import Utilities
from middleware.auth import get_current_user
from model.db import (
    DBManagerAdmin,
    DBManagerCategories,
    DBManagerMonitoring,
    DBManagerUsers,
)
from model.models import Administrator, get_session


class AdministratorAPIs:
    def __init__(self, logger: JodNidLogger, line_access_token: str):
        self.logger = logger
        self.line_access_token = line_access_token
        self.router = APIRouter(prefix="/api/administrator", tags=["administrator"])

    def setup_router(self):
        router = self.router
        logger = self.logger
        line_access_token = self.line_access_token

        @router.get("/status")
        def get_system_status(
            db: Session = Depends(get_session),
            user: Administrator = Depends(get_current_user),
        ):
            """สถานะจริงของระบบสำหรับการ์ดบนหน้าแรกของ console (เดิมเป็นค่า hardcode)"""
            logger.info(module="administrator", message="fetching status", user_id=user.uid)
            return {
                "success": True,
                "data": DBManagerAdmin.get_system_status(db, line_access_token),
            }

        @router.get("/metrics")
        def get_metrics(
            days: int = 7,
            db: Session = Depends(get_session),
            user: Administrator = Depends(get_current_user),
        ):
            """ตัวเลขภาพรวมสำหรับหน้า Stats"""
            logger.info(module="administrator", message="fetching metrics", user_id=user.uid)
            return {
                "success": True,
                "data": DBManagerMonitoring.get_admin_metrics(db, days=max(1, min(days, 90))),
            }

        @router.get("/logs")
        def get_logs(
            level: str = None,
            module: str = None,
            line_user_id: str = None,
            search: str = None,
            limit: int = 50,
            offset: int = 0,
            db: Session = Depends(get_session),
            user: Administrator = Depends(get_current_user),
        ):
            """อ่าน SystemLog พร้อมตัวกรอง — ที่เดียวที่ดู telemetry ของ OCR ได้โดยไม่ต้องเปิด DB"""
            return {
                "success": True,
                "data": DBManagerMonitoring.get_system_logs(
                    db,
                    level=level,
                    module=module,
                    user_id=line_user_id,
                    search=search,
                    limit=limit,
                    offset=offset,
                ),
                "modules": DBManagerMonitoring.get_log_modules(db),
            }

        @router.get("/users")
        def get_users(
            search: str = None,
            limit: int = 50,
            offset: int = 0,
            db: Session = Depends(get_session),
            user: Administrator = Depends(get_current_user),
        ):
            return {
                "success": True,
                "data": DBManagerUsers.search_users(db, search=search, limit=limit, offset=offset),
            }

        @router.patch("/users/bypass-mode")
        def set_user_bypass(
            data: dict,
            db: Session = Depends(get_session),
            user: Administrator = Depends(get_current_user),
        ):
            line_user_id = data.get("line_user_id")
            if not line_user_id:
                return {"success": False, "message": "Missing line_user_id"}

            enabled = bool(data.get("enabled"))
            logger.info(
                module="administrator",
                message=f"set bypass_mode={enabled} for {line_user_id}",
                user_id=user.uid,
            )
            return DBManagerUsers.set_user_bypass_mode(db, line_user_id, enabled)

        @router.get("/categories")
        def get_global_categories(
            db: Session = Depends(get_session),
            user: Administrator = Depends(get_current_user),
        ):
            return {"success": True, "data": DBManagerCategories.get_global_categories(db)}

        @router.post("/categories")
        def create_global_category(
            data: dict,
            db: Session = Depends(get_session),
            user: Administrator = Depends(get_current_user),
        ):
            logger.info(
                module="administrator",
                message=f"create global category: {data.get('name')}",
                user_id=user.uid,
            )
            return DBManagerCategories.create_global_category(
                db,
                name=data.get("name"),
                icon=data.get("icon"),
                parent_id=data.get("parent_id"),
            )

        @router.patch("/categories/{category_id}")
        def update_global_category(
            category_id: int,
            data: dict,
            db: Session = Depends(get_session),
            user: Administrator = Depends(get_current_user),
        ):
            logger.info(
                module="administrator",
                message=f"update global category {category_id}",
                user_id=user.uid,
            )
            return DBManagerCategories.update_global_category(
                db, category_id, name=data.get("name"), icon=data.get("icon")
            )

        @router.delete("/categories/{category_id}")
        def delete_global_category(
            category_id: int,
            db: Session = Depends(get_session),
            user: Administrator = Depends(get_current_user),
        ):
            logger.info(
                module="administrator",
                message=f"delete global category {category_id}",
                user_id=user.uid,
            )
            return DBManagerCategories.delete_global_category(db, category_id)

        @router.post("/config/refresh-cache")
        def refresh_config_cache(user: Administrator = Depends(get_current_user)):
            """
            ล้าง `@lru_cache` ของ `get_config_value` ด้วยมือ

            ปกติ endpoint ที่แก้ config ล้างให้อยู่แล้ว ตัวนี้ไว้ใช้ตอนแก้ค่าใน DB ตรงๆ
            หรือเมื่อสงสัยว่าค่าที่ระบบใช้ไม่ตรงกับที่เห็นในตาราง
            """
            Utilities.clear_config_cache()
            logger.info(module="administrator", message="config cache cleared", user_id=user.uid)
            return {"success": True, "message": "ล้างแคชการตั้งค่าเรียบร้อยแล้ว"}

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
