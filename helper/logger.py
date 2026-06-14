import traceback
from typing import Optional

from sqlmodel import Session
from sqlmodel import Session as SQLSession

from core.config_settings import settings
from model.models import SystemLog, engine


class JodNidLogger:
    """Lightweight app logger that writes into the SystemLog table.

    Accepts an optional short-lived `db` session. If none is provided the
    logger will create a short-lived session for each write to avoid keeping
    a long-lived session open across requests.
    """

    def __init__(self, db: Optional[Session] = None):
        self._external_db = db
        self.env = "Dev" if settings.TEST_MODE else "Prod"

    def _write_log(self, level: str, module: str, message: str, **kwargs):
        # Capture stack trace automatically if called in an exception context
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

        # Use provided session if available, otherwise open a short-lived session
        if self._external_db is not None:
            try:
                self._external_db.add(log_entry)
                self._external_db.commit()
            except Exception as e:
                try:
                    self._external_db.rollback()
                finally:
                    print(f"🚨 Log Saving Failed: {e}")
            return

        try:
            with SQLSession(engine) as session:
                session.add(log_entry)
                session.commit()
        except Exception as e:
            print(f"🚨 Log Saving Failed (short-lived session): {e}")

    def info(self, module: str, message: str, user_id: str = None, payload: dict = None):
        self._write_log("INFO", module, message, user_id=user_id, payload=payload)

    def error(self, module: str, message: str, user_id: str = None, payload: dict = None):
        self._write_log("ERROR", module, message, user_id=user_id, payload=payload)
