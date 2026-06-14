from datetime import datetime, timedelta

import requests
from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from helper.logger import JodNidLogger
from helper.utils import Utilities
from middleware.auth import get_current_user
from model.db_manament import DBManagerAdmin
from model.models import Administrator, SystemLog, get_session


class AdministratorAPIs:
    def __init__(self, logger: JodNidLogger, line_access_token: str):
        self.logger = logger
        self.line_access_token = line_access_token
        self.router = APIRouter(prefix="/api/administrator", tags=["administrator"])

    def setup_router(self):
        router = self.router
        logger = self.logger
        users = Utilities.get_all_users(next(get_session()))
        user_id = None
        for user in users:
            user_id = user.line_user_id

        # administrator service
        @router.post("/sync")
        async def sync_data(
            data: dict,
            db: Session = Depends(get_session),
        ):
            logger.info(
                module="app", message=f"Syncing data for user_id: {user_id}", user_id=user_id
            )
            email = data.get("email")
            uid = data.get("uid")
            if not email or not uid:
                return {"success": False, "message": "Missing email or uid or name"}
            result = DBManagerAdmin.update_administrator_data_system(db, uid, email)
            logger.info(
                module="administrator",
                message=f"Data sync for uid: {uid} result: {result}",
                user_id=uid,
            )
            if result.get("success") == False:
                logger.info(
                    module="administrator", message=f"Data sync failed for uid: {uid}", user_id=uid
                )
                return {"success": False, "message": "Data sync failed"}
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
            Utilities.clear_config_cache()
            logger.info(
                module="app",
                message=f"Updating system configuration for key: {key}, value: {value}, value_type: {value_type}, description: {description}",
                user_id=user.uid,
            )
            return DBManagerAdmin.update_system_config(db, key, value, value_type, description)

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
            Utilities.clear_config_cache()
            logger.info(
                module="app",
                message=f"Toggling system configuration for key: {key}, value: {value}",
                user_id=user.uid,
            )
            return DBManagerAdmin.update_system_config(db, key, value)

        @router.get("/logs")
        def get_logs(
            page: int = 1,
            per_page: int = 20,
            level: str | None = None,
            module: str | None = None,
            user_id: str | None = None,
            start_ts: str | None = None,
            end_ts: str | None = None,
            db: Session = Depends(get_session),
            user: Administrator = Depends(get_current_user),
        ):
            # Build base query
            stmt = select(SystemLog)
            if level:
                stmt = stmt.where(SystemLog.level == level)
            if module:
                stmt = stmt.where(SystemLog.module == module)
            if user_id:
                stmt = stmt.where(SystemLog.user_id == user_id)
            if start_ts:
                try:
                    start_dt = datetime.fromisoformat(start_ts)
                    stmt = stmt.where(SystemLog.created_at >= start_dt)
                except Exception:
                    pass
            if end_ts:
                try:
                    end_dt = datetime.fromisoformat(end_ts)
                    stmt = stmt.where(SystemLog.created_at <= end_dt)
                except Exception:
                    pass

            all_logs = db.exec(stmt.order_by(SystemLog.created_at.desc())).all()
            total = len(all_logs)
            offset = (page - 1) * per_page
            page_items = all_logs[offset : offset + per_page]

            def _serialize(l: SystemLog):
                return {
                    "id": l.id,
                    "timestamp": l.created_at.isoformat() if l.created_at else None,
                    "level": l.level,
                    "module": l.module,
                    "message": l.message,
                    "user_id": l.user_id,
                }

            return {
                "success": True,
                "data": [_serialize(l) for l in page_items],
                "total": total,
                "page": page,
                "per_page": per_page,
            }

        @router.get("/logs/{log_id}")
        def get_log_detail(
            log_id: str,
            db: Session = Depends(get_session),
            user: Administrator = Depends(get_current_user),
        ):
            log = db.get(SystemLog, log_id)
            if not log:
                return {"success": False, "message": "Log not found"}
            return {
                "success": True,
                "data": {
                    "id": log.id,
                    "timestamp": log.created_at.isoformat() if log.created_at else None,
                    "level": log.level,
                    "module": log.module,
                    "message": log.message,
                    "payload": log.payload,
                    "stack_trace": log.stack_trace,
                    "user_id": log.user_id,
                },
            }

        @router.delete("/logs/clear")
        def clear_old_logs(
            days: int = 30,
            db: Session = Depends(get_session),
            user: Administrator = Depends(get_current_user),
        ):
            cutoff = datetime.utcnow() - timedelta(days=days)
            old_logs = db.exec(select(SystemLog).where(SystemLog.created_at < cutoff)).all()
            count = 0
            for l in old_logs:
                try:
                    db.delete(l)
                    count += 1
                except Exception:
                    pass
            db.commit()
            return {"success": True, "deleted": count}

        @router.get("/status")
        def get_status(
            db: Session = Depends(get_session), user: Administrator = Depends(get_current_user)
        ):
            # DB check
            db_ok = True
            try:
                _ = db.exec(select(SystemLog).limit(1)).all()
            except Exception:
                db_ok = False

            # LINE API check (best-effort)
            line_ok = None
            try:
                url = (
                    Utilities.get_config_value("LINE_API")
                    if hasattr(Utilities, "get_config_value")
                    else None
                )
                if not url:
                    # fallback to settings in config if available
                    from core.config_settings import settings

                    url = getattr(settings, "LINE_API", None)
                if url:
                    r = requests.get(url, timeout=2)
                    line_ok = r.status_code == 200
            except Exception:
                line_ok = False

            return {"success": True, "status": {"db": db_ok, "line_api": line_ok}}
