import traceback

from sqlmodel import Session

from core.config_settings import settings
from model.models import SystemLog


class JodNidLogger:
    def __init__(self, db: Session):
        self.db = db
        self.env = "Dev" if settings.TEST_MODE else "Prod"

    def _write_log(self, level: str, module: str, message: str, **kwargs):
        # ดึง Stack Trace อัตโนมัติถ้าเป็นระดับ ERROR หรือ CRITICAL
        stack = None
        if level in ["ERROR", "CRITICAL"]:
            stack = traceback.format_exc()

        log_entry = SystemLog(
            level=level,
            module=module,
            message=message,
            user_id=kwargs.get("user_id"),
            payload=kwargs.get("payload"),
            stack_trace=stack,
            environment=self.env,
        )

        try:
            self.db.add(log_entry)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            print(f"🚨 Log Saving Failed: {e}")

    # วิธีเรียกใช้แบบสั้นๆ
    def info(self, module: str, message: str, user_id: str = None, payload: dict = None):
        self._write_log("INFO", module, message, user_id=user_id, payload=payload)

    def error(self, module: str, message: str, user_id: str = None, payload: dict = None):
        self._write_log("ERROR", module, message, user_id=user_id, payload=payload)
