from datetime import datetime

from fastapi import APIRouter, Depends
from sqlmodel import Session

from helper.logger import JodNidLogger
from helper.utils import Utilities
from middleware.auth import ROLE_ADMIN, get_current_user, require_role
from model.db import (
    DBManagerAdmin,
    DBManagerBudget,
    DBManagerCategories,
    DBManagerMonitoring,
    DBManagerUsers,
)
from model.models import Administrator, get_session


def audit_log(logger: JodNidLogger, user: Administrator, action: str, detail: dict = None):
    """
    บันทึกว่าใครทำอะไรใน admin console ลง SystemLog (module `admin_audit`)

    ใช้ตารางเดิมที่มี `payload` เป็น JSON column อยู่แล้ว จึงไม่ต้องทำ migration
    ดูย้อนหลังได้จากหน้า Logs โดยกรอง module = admin_audit
    """
    logger.info(
        module="admin_audit",
        message=f"{user.email} -> {action}",
        user_id=user.uid,
        payload={"action": action, "actor": user.email, "role": user.role, **(detail or {})},
    )


def _succeeded(result) -> bool:
    """ผลจาก DBManager ที่คืน `{"success": False, ...}` = ทำไม่สำเร็จ — ใช้บันทึกใน audit log"""
    return not (isinstance(result, dict) and result.get("success") is False)


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
            user: Administrator = Depends(require_role(ROLE_ADMIN)),
        ):
            line_user_id = data.get("line_user_id")
            if not line_user_id:
                return {"success": False, "message": "Missing line_user_id"}

            enabled = bool(data.get("enabled"))
            result = DBManagerUsers.set_user_bypass_mode(db, line_user_id, enabled)
            audit_log(
                logger,
                user,
                "set_user_bypass_mode",
                {"line_user_id": line_user_id, "enabled": enabled, "success": _succeeded(result)},
            )
            return result

        @router.post("/users/sync-budgets")
        def sync_user_budgets(
            data: dict,
            db: Session = Depends(get_session),
            user: Administrator = Depends(require_role(ROLE_ADMIN)),
        ):
            """ซ่อมยอดงบเดือนนี้ของผู้ใช้หนึ่งคนให้ตรงกับรายการจริง"""
            line_user_id = data.get("line_user_id")
            if not line_user_id:
                return {"success": False, "message": "Missing line_user_id"}

            now = datetime.now()
            result = DBManagerBudget.sync_user_budgets(db, line_user_id, now.month, now.year)
            audit_log(
                logger,
                user,
                "sync_user_budgets",
                {"line_user_id": line_user_id, "updated": result["updated"], "success": True},
            )
            return {"success": True, "data": result}

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
            user: Administrator = Depends(require_role(ROLE_ADMIN)),
        ):
            result = DBManagerCategories.create_global_category(
                db,
                name=data.get("name"),
                icon=data.get("icon"),
                parent_id=data.get("parent_id"),
            )
            audit_log(
                logger,
                user,
                "create_global_category",
                {"name": data.get("name"), "success": _succeeded(result)},
            )
            return result

        @router.patch("/categories/{category_id}")
        def update_global_category(
            category_id: int,
            data: dict,
            db: Session = Depends(get_session),
            user: Administrator = Depends(require_role(ROLE_ADMIN)),
        ):
            result = DBManagerCategories.update_global_category(
                db, category_id, name=data.get("name"), icon=data.get("icon")
            )
            audit_log(
                logger,
                user,
                "update_global_category",
                {
                    "category_id": category_id,
                    "name": data.get("name"),
                    "success": _succeeded(result),
                },
            )
            return result

        @router.delete("/categories/{category_id}")
        def delete_global_category(
            category_id: int,
            db: Session = Depends(get_session),
            user: Administrator = Depends(require_role(ROLE_ADMIN)),
        ):
            result = DBManagerCategories.delete_global_category(db, category_id)
            audit_log(
                logger,
                user,
                "delete_global_category",
                {"category_id": category_id, "success": _succeeded(result)},
            )
            return result

        @router.post("/config/refresh-cache")
        def refresh_config_cache(user: Administrator = Depends(require_role(ROLE_ADMIN))):
            """
            ล้าง `@lru_cache` ของ `get_config_value` ด้วยมือ

            ปกติ endpoint ที่แก้ config ล้างให้อยู่แล้ว ตัวนี้ไว้ใช้ตอนแก้ค่าใน DB ตรงๆ
            หรือเมื่อสงสัยว่าค่าที่ระบบใช้ไม่ตรงกับที่เห็นในตาราง
            """
            Utilities.clear_config_cache()
            audit_log(logger, user, "refresh_config_cache")
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
            # ไม่รับ email จาก body — email คือ actor ใน audit log ถ้าแก้เองได้ก็ปลอมตัวในบันทึกได้
            # (email ถูกตั้งตอน seed_admin.py)
            result = DBManagerAdmin.sync_administrator_profile(
                db,
                uid=user.uid,
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
            user: Administrator = Depends(require_role(ROLE_ADMIN)),
        ):
            name = data.get("name")
            key = data.get("key")
            value = data.get("value")
            value_type = data.get("value_type")
            description = data.get("description")
            if not name or not key or value is None or not value_type:
                return {"success": False, "message": "Missing name or key or value or value_type"}

            result = DBManagerAdmin.create_system_config(
                db, name, key, value, value_type, description
            )
            Utilities.clear_config_cache()
            audit_log(
                logger,
                user,
                "create_system_config",
                {
                    "key": key,
                    "name": name,
                    "value": value,
                    "value_type": value_type,
                    "success": _succeeded(result),
                },
            )
            return result

        @router.get("/all")
        def get_all_system_configuration(
            db: Session = Depends(get_session), user: Administrator = Depends(get_current_user)
        ):
            logger.info(
                module="administrator",
                message="Fetching all system configurations",
                user_id=user.uid,
            )
            return DBManagerAdmin.get_system_config_data(db)

        @router.patch("/config/update")
        def update_system_configuration(
            data: dict,
            db: Session = Depends(get_session),
            user: Administrator = Depends(require_role(ROLE_ADMIN)),
        ):
            key = data.get("key")
            value = data.get("value")
            value_type = data.get("value_type")
            description = data.get("description")
            # ค่าว่าง ("") เป็นค่าที่ถูกต้องของ config ชนิด string — ตรวจแค่ว่าส่งมาหรือไม่
            if not key or value is None:
                return {"success": False, "message": "Missing key or value"}
            result = DBManagerAdmin.update_system_config(
                db, key, value, value_type, description, name=data.get("name")
            )
            # ต้องล้าง cache "หลัง" เขียน DB เสร็จ ไม่งั้นมีช่วงที่ค่าเก่าถูกอ่านกลับเข้า cache
            Utilities.clear_config_cache()
            audit_log(
                logger,
                user,
                "update_system_config",
                {
                    "key": key,
                    "value": value,
                    "value_type": value_type,
                    "success": _succeeded(result),
                },
            )
            return result

        @router.patch("/config/toggle")
        def toggle_system_configuration(
            data: dict,
            db: Session = Depends(get_session),
            user: Administrator = Depends(require_role(ROLE_ADMIN)),
        ):
            key = data.get("key")
            value = data.get("value")
            if not key or value is None:
                return {"success": False, "message": "Missing key or value"}
            result = DBManagerAdmin.update_system_config(db, key, value)
            Utilities.clear_config_cache()
            audit_log(
                logger,
                user,
                "toggle_system_config",
                {"key": key, "value": value, "success": _succeeded(result)},
            )
            return result
